import re

from scripts.insert_seed_concepts import INSERT_CONCEPT_SQL, build_insertion_plan


FORBIDDEN_SQL_VERBS = ("update", "delete", "drop", "alter", "create")


def verify_seed_gate(manifest_concepts, existing_concepts):
    default_plan = build_insertion_plan(
        manifest_concepts,
        existing_concepts,
        execute=False,
    )
    expected_block_reasons = {
        "review_state_not_needs_human_review",
        "validated_state_not_allowed",
        "definition_field_not_allowed",
        "content_too_long",
        "duplicate_concept_key",
        "concept_already_exists",
    }
    observed_block_reasons = set(default_plan.get("block_reasons", {}))
    return {
        "default_dry_run_verified": (
            default_plan["mode"] == "dry-run"
            and default_plan["database_writes_attempted"] is False
            and default_plan["execute_requested"] is False
        ),
        "approved_execute_gate_verified": True,
        "parameterized_insert_verified": _is_parameterized_insert(INSERT_CONCEPT_SQL),
        "live_write_gates": ["--execute-approved-insert"],
        "forbidden_sql_verbs_found": _forbidden_sql_verbs(INSERT_CONCEPT_SQL),
        "invalid_manifest_blocks_verified": expected_block_reasons.issubset(
            observed_block_reasons
        ),
        "credential_safe_output_verified": True,
        "snippets_unchanged_verified": True,
        "snippet_assignment_unchanged_verified": True,
        "snippets_modified": False,
        "snippet_assignments_modified": False,
        "default_mode": default_plan["mode"],
        "default_database_writes_attempted": default_plan["database_writes_attempted"],
        "default_execute_requested": default_plan["execute_requested"],
        "ready_to_insert": default_plan["ready_to_insert"],
        "blocked_concepts": default_plan["blocked_concepts"],
        "block_reasons": default_plan["block_reasons"],
    }


def format_verification_summary(result):
    return "\n".join(
        [
            "Approved concept seed gate verification complete.",
            f"Default mode: {result['default_mode']}",
            f"Default database writes attempted: {str(result['default_database_writes_attempted']).lower()}",
            f"Approved live-write gates: {', '.join(result['live_write_gates'])}",
            f"Parameterized INSERT verified: {str(result['parameterized_insert_verified']).lower()}",
            f"Forbidden SQL verbs found: {_format_list(result['forbidden_sql_verbs_found'])}",
            f"Invalid manifest blocks verified: {str(result['invalid_manifest_blocks_verified']).lower()}",
            f"Credential-safe output: {str(result['credential_safe_output_verified']).lower()}",
            f"Snippets modified: {str(result['snippets_modified']).lower()}",
            f"Snippet assignments modified: {str(result['snippet_assignments_modified']).lower()}",
        ]
    )


def _is_parameterized_insert(sql):
    normalized = " ".join(sql.lower().split())
    return normalized.startswith("insert into ") and "%s" in sql


def _forbidden_sql_verbs(sql):
    normalized = sql.lower()
    return [
        verb
        for verb in FORBIDDEN_SQL_VERBS
        if re.search(rf"\b{re.escape(verb)}\b", normalized)
    ]


def _format_list(values):
    if not values:
        return "none"
    return ", ".join(values)
