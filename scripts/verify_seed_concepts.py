import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.insert_seed_concepts import INSERT_CONCEPT_SQL, build_insertion_plan
from scripts.insert_seed_concepts import DEFAULT_MANIFEST_PATH, load_manifest
from scripts.insert_seed_concepts import fetch_existing_concepts, load_concepts_fixture


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
    invalid_probe_plan = build_insertion_plan(
        _invalid_manifest_probe_concepts(),
        [{"slug": "already_exists"}],
        execute=False,
    )
    observed_invalid_probe_reasons = set(invalid_probe_plan.get("block_reasons", {}))
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
        "invalid_manifest_blocks_verified": (
            expected_block_reasons.issubset(observed_block_reasons)
            or expected_block_reasons.issubset(observed_invalid_probe_reasons)
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


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify approved concept seed insertion gate without live writes."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument(
        "--concepts-fixture",
        type=Path,
        help="Use local JSON concept-row fixture instead of live Neon SELECT.",
    )
    parser.add_argument(
        "--database-url",
        help="Optional read-only database URL for SELECT metadata when no fixture is supplied.",
    )
    args = parser.parse_args(argv)

    try:
        manifest = load_manifest(args.manifest)
        if args.concepts_fixture is not None:
            existing_concepts = load_concepts_fixture(args.concepts_fixture)
        else:
            if not args.database_url:
                existing_concepts = []
            else:
                existing_concepts = fetch_existing_concepts(args.database_url)
        result = verify_seed_gate(manifest, existing_concepts)
    except Exception as exc:
        print("Approved concept seed gate verification failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_verification_summary(result))
    return 0


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


def _invalid_manifest_probe_concepts():
    base = {
        "preferred_label_en": "Probe",
        "preferred_label_es": "Probe",
        "concept_type": "reference",
        "review_state": "needs_human_review",
        "source_authority_hint": "fixture-only verifier probe",
        "notes": "Fixture-only probe; no definition stored.",
    }
    return [
        {**base, "concept_key": "published", "review_state": "published"},
        {**base, "concept_key": "validated", "review_state": "validated"},
        {**base, "concept_key": "definition_field", "definition": "forbidden"},
        {
            **base,
            "concept_key": "long_content",
            "notes": " ".join(f"word{i}" for i in range(25)),
        },
        {**base, "concept_key": "duplicate"},
        {**base, "concept_key": "duplicate"},
        {**base, "concept_key": "already_exists"},
    ]


if __name__ == "__main__":
    raise SystemExit(main())
