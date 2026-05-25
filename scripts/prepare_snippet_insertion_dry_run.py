import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "candidate_snippets.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "snippet_insertion_dry_run.json"


def load_candidate_snippets(input_path=DEFAULT_INPUT_PATH):
    with open(input_path, "r", encoding="utf-8") as input_file:
        report = json.load(input_file)
    return report.get("candidate_snippets", [])


def build_dry_run_report(snippets, source_rows):
    source_keys = {
        _source_key(source)
        for source in source_rows
    }
    matched_count = sum(1 for snippet in snippets if _source_key(snippet) in source_keys)
    blocked_count = len(snippets) - matched_count
    return {
        "total_snippets": len(snippets),
        "insertable_snippets": matched_count,
        "blocked_snippets": blocked_count,
        "block_reasons": {"source_not_found": blocked_count} if blocked_count else {},
        "source_match_summary": {
            "matched_sources": matched_count,
            "unmatched_sources": blocked_count,
        },
    }


def _source_key(row):
    return (
        row.get("source_title") or row.get("title"),
        row.get("source_type"),
        row.get("language"),
    )
