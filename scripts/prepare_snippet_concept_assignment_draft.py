import argparse
import json
import subprocess
import sys
from pathlib import Path

import psycopg

try:
    from prepare_snippet_insertion_dry_run import (
        DEFAULT_INPUT_PATH,
        load_candidate_snippets,
        load_database_url,
    )
    from diagnose_concept_readiness import fetch_concept_rows, load_concept_rows_fixture
except ModuleNotFoundError:
    from scripts.prepare_snippet_insertion_dry_run import (
        DEFAULT_INPUT_PATH,
        load_candidate_snippets,
        load_database_url,
    )
    from scripts.diagnose_concept_readiness import fetch_concept_rows, load_concept_rows_fixture


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_RELATIVE_PATH = Path("data/processed/snippet_concept_assignment_draft.json")
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / DEFAULT_OUTPUT_RELATIVE_PATH

SIGNAL_TO_CONCEPT_KEY = {
    "datum": "datum",
    "feature control frame": "feature_control_frame",
    "tolerance zone": "tolerance_zone",
    "mmc": "maximum_material_condition",
    "lmc": "least_material_condition",
    "rfs": "regardless_of_feature_size",
    "definicion": "tolerance_zone",
    "definiciones": "tolerance_zone",
}


def build_assignment_draft(snippets, concepts):
    concept_ids_by_key = {
        concept["slug"]: concept["id"]
        for concept in concepts
    }
    assignments = []
    ready_to_insert = 0
    missing_concept_id = 0
    for index, snippet in enumerate(snippets):
        concept_key = _concept_key_for_signal(snippet.get("matched_signal"))
        signal_is_approved = concept_key is not None
        metadata_reason = _metadata_reason_for_signal(snippet.get("matched_signal"))
        concept_id = concept_ids_by_key.get(concept_key)
        if concept_id:
            ready_to_insert += 1
        else:
            missing_concept_id += 1
        reason_codes = []
        audit_notes = []
        if signal_is_approved:
            audit_notes.append("matched_signal normalized to approved concept_key")
        else:
            reason_codes.append("unmatched_signal")
            audit_notes.append("matched_signal is not one of the approved assignment signals")
        if concept_id:
            audit_notes.append("concept_id resolved from existing concepts metadata")
        else:
            reason_codes.append("missing_concept_id")
            audit_notes.append("concept_id not found in existing concepts metadata")
        assignments.append(
            {
                "snippet_index": index,
                "matched_signal": snippet.get("matched_signal"),
                "metadata_reason": metadata_reason,
                "concept_key": concept_key,
                "concept_id": concept_id,
                "confidence": "high" if concept_id else "none",
                "status": "ready_to_insert" if concept_id else "blocked",
                "reason_codes": reason_codes,
                "audit_notes": audit_notes,
            }
        )
    return {
        "total_snippets": len(snippets),
        "ready_to_insert": ready_to_insert,
        "blocked_snippets": len(snippets) - ready_to_insert,
        "missing_concept_id": missing_concept_id,
        "assignments": assignments,
        "contract": {
            "database_writes": False,
            "database_modifications": False,
            "snippet_content_saved": False,
            "concept_ids_assigned_in_database": False,
        },
    }


def prepare_assignment_draft(
    input_path=DEFAULT_INPUT_PATH,
    output_path=DEFAULT_OUTPUT_PATH,
    database_url=None,
    concept_fetcher=fetch_concept_rows,
):
    resolved_database_url = database_url or load_database_url()
    snippets = load_candidate_snippets(input_path)
    concepts = concept_fetcher(resolved_database_url)
    draft = build_assignment_draft(snippets, concepts)
    write_assignment_draft(draft, output_path)
    return draft


def write_assignment_draft(draft, output_path=DEFAULT_OUTPUT_PATH):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(draft, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def assignment_draft_path_is_ignored(run_command=subprocess.run):
    result = run_command(
        ["git", "check-ignore", DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def format_console_summary(draft):
    return "\n".join(
        [
            "Snippet concept assignment draft complete.",
            f"Total snippets: {draft['total_snippets']}",
            f"Ready to insert: {draft['ready_to_insert']}",
            f"Blocked snippets: {draft['blocked_snippets']}",
            f"Missing concept_id: {draft['missing_concept_id']}",
            "No database writes: true",
            "Snippet text printed: false",
            "Concept ids assigned in database: false",
        ]
    )


def _concept_key_for_signal(signal):
    normalized_signal = _normalize_signal(signal)
    return SIGNAL_TO_CONCEPT_KEY.get(normalized_signal)


def _metadata_reason_for_signal(signal):
    if _normalize_signal(signal) in {"definicion", "definiciones"}:
        return "spanish_definition_signal_allowed_metadata"
    return None


def _normalize_signal(signal):
    text = " ".join(str(signal or "").strip().lower().split())
    replacements = str.maketrans({"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"})
    return text.translate(replacements)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Prepare a local snippet-to-concept assignment draft."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--database-url")
    parser.add_argument("--concepts-fixture", type=Path)
    parser.add_argument("--skip-ignore-check", action="store_true")
    args = parser.parse_args(argv)

    try:
        concept_fetcher = fetch_concept_rows
        if args.concepts_fixture is not None:
            concept_fetcher = lambda database_url: load_concept_rows_fixture(args.concepts_fixture)
        draft = prepare_assignment_draft(
            input_path=args.input,
            output_path=args.output,
            database_url=args.database_url,
            concept_fetcher=concept_fetcher,
        )
        if not args.skip_ignore_check and args.output == DEFAULT_OUTPUT_PATH:
            if not assignment_draft_path_is_ignored():
                raise RuntimeError(f"{DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()} is not ignored by Git")
    except Exception as exc:
        print("Snippet concept assignment draft failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(draft))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
