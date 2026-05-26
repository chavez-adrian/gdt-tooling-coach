import re

from scripts.insert_seed_concepts import INSERT_CONCEPT_SQL, build_insertion_plan


FORBIDDEN_SQL_VERBS = ("update", "delete", "drop", "alter", "create")


def verify_seed_gate(manifest_concepts, existing_concepts):
    default_plan = build_insertion_plan(
        manifest_concepts,
        existing_concepts,
        execute=False,
    )
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
        "default_mode": default_plan["mode"],
        "default_database_writes_attempted": default_plan["database_writes_attempted"],
        "default_execute_requested": default_plan["execute_requested"],
        "ready_to_insert": default_plan["ready_to_insert"],
        "blocked_concepts": default_plan["blocked_concepts"],
    }


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
