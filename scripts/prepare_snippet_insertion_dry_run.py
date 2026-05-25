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
    return {
        "total_snippets": len(snippets),
        "insertable_snippets": 0,
        "blocked_snippets": len(snippets),
        "block_reasons": {"source_not_found": len(snippets)} if snippets else {},
        "source_match_summary": {
            "matched_sources": 0,
            "unmatched_sources": len(snippets),
        },
    }
