import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import psycopg

try:
    from insert_seed_concepts import DEFAULT_MANIFEST_PATH, load_manifest
    from prepare_snippet_concept_assignment_draft import (
        DEFAULT_OUTPUT_PATH as DEFAULT_ASSIGNMENT_DRAFT_PATH,
        SIGNAL_TO_CONCEPT_KEY,
        _normalize_signal,
    )
    from prepare_snippet_insertion_dry_run import DEFAULT_INPUT_PATH, load_candidate_snippets, load_database_url
except ModuleNotFoundError:
    from scripts.insert_seed_concepts import DEFAULT_MANIFEST_PATH, load_manifest
    from scripts.prepare_snippet_concept_assignment_draft import (
        DEFAULT_OUTPUT_PATH as DEFAULT_ASSIGNMENT_DRAFT_PATH,
        SIGNAL_TO_CONCEPT_KEY,
        _normalize_signal,
    )
    from scripts.prepare_snippet_insertion_dry_run import DEFAULT_INPUT_PATH, load_candidate_snippets, load_database_url


ALLOWED_METADATA_REASONS = {"spanish_definition_signal_allowed_metadata"}
VALIDATED_CONCEPT_STATUSES = {"validated", "published", "approved"}
EXPECTED_ASSIGNMENT_TOTAL = 100
SELECT_CONCEPTS_SQL = """
SELECT id, slug, category, current_status
FROM concepts
ORDER BY slug;
"""


def load_assignment_draft(path=DEFAULT_ASSIGNMENT_DRAFT_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_concepts_fixture(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fetch_existing_concepts(database_url, connect=psycopg.connect):
    with connect(database_url) as conn:
        cur = conn.cursor()
        cur.execute(SELECT_CONCEPTS_SQL)
        column_names = [column[0] for column in cur.description]
        return [dict(zip(column_names, row)) for row in cur.fetchall()]


def verify_assignment_draft(
    snippets,
    assignment_draft,
    concepts,
    manifest_concepts,
    expected_total_assignments=None,
):
    assignments = assignment_draft.get("assignments", [])
    assignments_by_index = {}
    assignment_counts_by_index = Counter()
    for assignment in assignments:
        snippet_index = assignment.get("snippet_index")
        assignment_counts_by_index[snippet_index] += 1
        assignments_by_index[snippet_index] = assignment
    existing_concept_ids = {str(concept.get("id")) for concept in concepts if concept.get("id")}
    existing_concepts_by_id = {
        str(concept.get("id")): concept
        for concept in concepts
        if concept.get("id")
    }
    approved_concept_keys = {
        concept.get("concept_key")
        for concept in manifest_concepts
        if concept.get("concept_key")
    }
    block_reasons = Counter()
    unknown_concept_ids = []
    snippets_without_assignment = []
    by_concept_key = Counter()
    by_source_language = Counter()
    by_matched_signal = Counter()

    for index, snippet in enumerate(snippets):
        if assignment_counts_by_index[index] > 1:
            block_reasons["duplicate_assignment"] += 1
        assignment = assignments_by_index.get(index)
        if assignment is None:
            snippets_without_assignment.append(index)
            block_reasons["missing_assignment"] += 1
            continue
        concept_id = assignment.get("concept_id")
        concept_key = assignment.get("concept_key")
        if concept_id not in existing_concept_ids:
            unknown_concept_ids.append(concept_id)
            block_reasons["unknown_concept_id"] += 1
        elif _concept_is_validated(existing_concepts_by_id[concept_id]):
            block_reasons["automatically_validated_concept"] += 1
        if concept_key not in approved_concept_keys:
            block_reasons["concept_key_not_in_manifest"] += 1
        if not _concept_matches_signal(snippet, assignment):
            block_reasons["signal_concept_mismatch"] += 1
        by_concept_key[concept_key] += 1
        by_source_language[f"{snippet.get('source_type') or 'unknown'}|{snippet.get('language') or 'unknown'}"] += 1
        by_matched_signal[snippet.get("matched_signal") or "unknown"] += 1

    return {
        "passed": not block_reasons,
        "total_assignments": len(assignments),
        "block_reasons": dict(sorted(block_reasons.items())),
        "assignments_by_concept_key": dict(sorted(by_concept_key.items())),
        "assignments_by_source_type_language": dict(sorted(by_source_language.items())),
        "assignments_by_matched_signal": dict(sorted(by_matched_signal.items())),
        "unknown_concept_ids": unknown_concept_ids,
        "snippets_without_assignment": snippets_without_assignment,
        "no_database_writes": True,
        "select_only_concept_lookup": True,
    }


def format_console_summary(result):
    return "\n".join(
        [
            "Snippet concept assignment verification complete.",
            f"Passed: {str(result['passed']).lower()}",
            f"Total assignments: {result['total_assignments']}",
            f"Block reasons: {_format_key_counts(result.get('block_reasons', {}))}",
            f"Assignments by concept_key: {_format_key_counts(result.get('assignments_by_concept_key', {}))}",
            f"Assignments by source_type/language: {_format_key_counts(result.get('assignments_by_source_type_language', {}))}",
            f"Assignments by matched_signal: {_format_key_counts(result.get('assignments_by_matched_signal', {}))}",
            f"Unknown concept ids: {_format_list(result.get('unknown_concept_ids', []))}",
            f"Snippets without assignment: {_format_list(result.get('snippets_without_assignment', []))}",
            "No database writes: true",
            "Concept lookup: SELECT only",
            "Snippet text printed: false",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify snippet-to-concept assignment safety before snippet insertion."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--assignment-draft", type=Path, default=DEFAULT_ASSIGNMENT_DRAFT_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--database-url")
    parser.add_argument("--concepts-fixture", type=Path)
    parser.add_argument("--expected-total", type=int, default=EXPECTED_ASSIGNMENT_TOTAL)
    args = parser.parse_args(argv)

    try:
        snippets = load_candidate_snippets(args.input)
        assignment_draft = load_assignment_draft(args.assignment_draft)
        manifest_concepts = load_manifest(args.manifest)
        if args.concepts_fixture is None:
            concepts = fetch_existing_concepts(args.database_url or load_database_url())
        else:
            concepts = load_concepts_fixture(args.concepts_fixture)
        result = verify_assignment_draft(
            snippets,
            assignment_draft,
            concepts,
            manifest_concepts,
            expected_total_assignments=args.expected_total,
        )
    except Exception:
        print("Snippet concept assignment verification failed.", file=sys.stderr)
        print("A required safe input or SELECT-only concept lookup failed.", file=sys.stderr)
        return 1

    print(format_console_summary(result))
    return 0 if result["passed"] else 1


def _concept_matches_signal(snippet, assignment):
    metadata_reason = assignment.get("metadata_reason")
    if metadata_reason in ALLOWED_METADATA_REASONS:
        return True
    expected_concept_key = SIGNAL_TO_CONCEPT_KEY.get(_normalize_signal(snippet.get("matched_signal")))
    return assignment.get("concept_key") == expected_concept_key


def _concept_is_validated(concept):
    status = concept.get("current_status") or concept.get("review_state")
    return concept.get("validated") is True or status in VALIDATED_CONCEPT_STATUSES


def _format_key_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def _format_list(values):
    if not values:
        return "none"
    return ", ".join(str(value) for value in values)


if __name__ == "__main__":
    raise SystemExit(main())
    expected_total = expected_total_assignments
    if expected_total is not None and len(assignments) != expected_total:
        block_reasons["assignment_total_mismatch"] += 1
