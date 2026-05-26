import argparse
import hashlib
import json
import sys
from pathlib import Path

import psycopg

try:
    from prepare_snippet_insertion_dry_run import (
        DEFAULT_INPUT_PATH,
        fetch_source_rows,
        load_candidate_snippets,
        load_database_url,
        load_source_rows_fixture,
    )
except ModuleNotFoundError:
    from scripts.prepare_snippet_insertion_dry_run import (
        DEFAULT_INPUT_PATH,
        fetch_source_rows,
        load_candidate_snippets,
        load_database_url,
        load_source_rows_fixture,
    )


INSERT_DEFINITION_SQL = """
INSERT INTO definitions (
  concept_id,
  source_id,
  definition_type,
  text,
  word_count,
  extraction_type,
  is_literal,
  review_status,
  import_fingerprint,
  notes
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (import_fingerprint) DO NOTHING;
"""

REVIEW_STATE = "raw_import"
EXTRACTION_TYPE = "literal_quote"
MAX_WORDS = 80


def calculate_import_fingerprint(snippet, source_id):
    parts = [
        str(source_id),
        str(snippet["concept_id"]),
        str(snippet["page_number"]),
        str(snippet.get("matched_signal") or ""),
        EXTRACTION_TYPE,
        _normalize_snippet_text(snippet["snippet_text"]),
    ]
    payload = json.dumps(parts, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_insertion_plan(snippets, source_rows, execute=False, existing_definition_fingerprints=None):
    existing_definition_fingerprints = set(existing_definition_fingerprints or [])
    source_ids_by_key = {
        _source_key(source): source["id"]
        for source in source_rows
    }
    rows = []
    blocked_details = []
    duplicate_details = []
    block_reasons = {}
    matched_sources = 0
    unmatched_sources = 0

    for index, snippet in enumerate(snippets):
        reasons = _snippet_block_reasons(snippet)
        source_id = source_ids_by_key.get(_source_key(snippet))
        if source_id is None:
            reasons.append("source_id_not_resolved")
            unmatched_sources += 1
        else:
            matched_sources += 1
        if reasons:
            blocked_details.append({"snippet_index": index, "reasons": reasons})
            for reason in reasons:
                block_reasons[reason] = block_reasons.get(reason, 0) + 1
            continue
        row = _insertion_row(snippet, source_id)
        if row["import_fingerprint"] in existing_definition_fingerprints:
            duplicate_details.append(
                {
                    "snippet_index": index,
                    "import_fingerprint": row["import_fingerprint"],
                }
            )
            continue
        rows.append(row)

    return {
        "mode": "execute" if execute else "dry-run",
        "execute_requested": execute,
        "database_writes_attempted": False,
        "total_snippets": len(snippets),
        "ready_to_insert": len(rows),
        "blocked_snippets": len(blocked_details),
        "duplicate_snippets": len(duplicate_details),
        "skipped_existing_definitions": len(duplicate_details),
        "block_reasons": block_reasons,
        "blocked_snippet_details": blocked_details,
        "duplicate_details": duplicate_details,
        "source_match_summary": {
            "matched_sources": matched_sources,
            "unmatched_sources": unmatched_sources,
        },
        "insertion_rows": rows,
        "contract": {
            "review_state": REVIEW_STATE,
            "requires_human_review": True,
            "validated": False,
            "extraction_type": EXTRACTION_TYPE,
            "max_words": MAX_WORDS,
            "source_id_required": True,
            "page_number_required": True,
            "automatic_concept_validation": False,
        },
    }


def load_assignment_draft(path):
    with open(path, "r", encoding="utf-8") as draft_file:
        return json.load(draft_file)


def apply_assignment_draft(snippets, assignment_draft):
    assignments_by_index = {
        assignment["snippet_index"]: assignment
        for assignment in assignment_draft.get("assignments", [])
        if assignment.get("status") == "ready_to_insert"
    }
    updated_snippets = []
    for index, snippet in enumerate(snippets):
        updated_snippet = dict(snippet)
        assignment = assignments_by_index.get(index)
        if assignment is not None:
            updated_snippet["concept_id"] = assignment.get("concept_id")
            updated_snippet["concept_key"] = assignment.get("concept_key")
        updated_snippets.append(updated_snippet)
    return updated_snippets


def execute_approved_insert(plan, insert_rows):
    if not plan.get("execute_requested") or plan.get("blocked_snippets"):
        return {
            **plan,
            "database_writes_attempted": False,
            "inserted_snippets": 0,
        }
    rows = plan.get("insertion_rows", [])
    insert_rows(rows)
    return {
        **plan,
        "database_writes_attempted": bool(rows),
        "inserted_snippets": len(rows),
    }


def insert_rows(database_url, rows, connect=psycopg.connect):
    with connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(
                        INSERT_DEFINITION_SQL,
                        (
                            row["concept_id"],
                            row["source_id"],
                            row["definition_type"],
                            row["text"],
                            row["word_count"],
                            row["extraction_type"],
                            row["is_literal"],
                            row["review_status"],
                            row["import_fingerprint"],
                            row["notes"],
                        ),
                    )


def format_console_summary(result):
    return "\n".join(
        [
            "Candidate snippet insertion gate complete.",
            f"Mode: {result['mode']}",
            f"Total snippets: {result['total_snippets']}",
            f"Ready to insert: {result['ready_to_insert']}",
            f"Blocked snippets: {result['blocked_snippets']}",
            f"Block reasons: {_format_key_counts(result.get('block_reasons', {}))}",
            f"Source match summary: {_format_key_counts(result.get('source_match_summary', {}))}",
            f"Inserted snippets: {result.get('inserted_snippets', 0)}",
            f"Database writes attempted: {str(result['database_writes_attempted']).lower()}",
            "Review state: raw_import",
            "Requires human review: true",
            "Validated: false",
            "Extraction type: literal_quote",
            "Automatic concept validation: false",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Gate candidate snippet insertion behind an explicit approval flag."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--database-url")
    parser.add_argument(
        "--sources-fixture",
        type=Path,
        help="Use a local JSON source-row fixture instead of live Neon SELECT.",
    )
    parser.add_argument(
        "--assignment-draft",
        type=Path,
        help="Overlay explicit concept_id values from a local assignment draft.",
    )
    parser.add_argument(
        "--execute-approved-insert",
        action="store_true",
        help="Actually insert ready snippets. Without this flag the command is dry-run only.",
    )
    args = parser.parse_args(argv)

    try:
        database_url = args.database_url or load_database_url()
        snippets = load_candidate_snippets(args.input)
        if args.assignment_draft is not None:
            snippets = apply_assignment_draft(snippets, load_assignment_draft(args.assignment_draft))
        if args.sources_fixture is None:
            source_rows = fetch_source_rows(database_url)
        else:
            source_rows = load_source_rows_fixture(args.sources_fixture)
        plan = build_insertion_plan(
            snippets,
            source_rows,
            execute=args.execute_approved_insert,
        )
        result = execute_approved_insert(
            plan,
            insert_rows=lambda rows: insert_rows(database_url, rows),
        )
    except Exception as exc:
        print("Candidate snippet insertion gate failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(result))
    return 0


def _snippet_block_reasons(snippet):
    reasons = []
    if not snippet.get("concept_id"):
        reasons.append("missing_concept_id")
    if snippet.get("page_number") is None:
        reasons.append("missing_page_number")
    if not snippet.get("snippet_text"):
        reasons.append("missing_snippet_text")
    if _word_count(snippet.get("snippet_text", "")) > MAX_WORDS:
        reasons.append("snippet_too_long")
    if snippet.get("extraction_type") != EXTRACTION_TYPE:
        reasons.append("extraction_type_not_literal_quote")
    if snippet.get("proposed_review_state") != REVIEW_STATE:
        reasons.append("review_state_not_raw_import")
    if snippet.get("requires_human_review") is not True:
        reasons.append("requires_human_review_not_true")
    if snippet.get("validated") is True or snippet.get("review_state") == "validated":
        reasons.append("validated_state_not_allowed")
    return reasons


def _insertion_row(snippet, source_id):
    return {
        "concept_id": snippet["concept_id"],
        "source_id": source_id,
        "import_fingerprint": calculate_import_fingerprint(snippet, source_id),
        "definition_type": "candidate_snippet",
        "text": snippet["snippet_text"],
        "word_count": _word_count(snippet["snippet_text"]),
        "extraction_type": EXTRACTION_TYPE,
        "is_literal": True,
        "review_status": REVIEW_STATE,
        "notes": json.dumps(
            {
                "page_number": snippet["page_number"],
                "matched_signal": snippet.get("matched_signal"),
                "requires_human_review": True,
                "validated": False,
                "automatic_concept_validation": False,
            },
            sort_keys=True,
        ),
    }


def _source_key(row):
    return (
        row.get("source_title") or row.get("title"),
        row.get("source_type"),
        row.get("language"),
    )


def _word_count(text):
    return len(str(text).split())


def _normalize_snippet_text(text):
    return " ".join(str(text).split()).strip().casefold()


def _format_key_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


if __name__ == "__main__":
    raise SystemExit(main())
