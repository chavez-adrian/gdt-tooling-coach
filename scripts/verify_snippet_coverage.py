"""Local coverage verification for ranked candidates and generated snippets."""

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RANKED_REPORT = PROJECT_ROOT / "data" / "processed" / "ranked_definition_candidates.json"
DEFAULT_SNIPPET_REPORT = PROJECT_ROOT / "data" / "processed" / "candidate_snippets.json"
SAFE_CONTRACT_FLAGS = {
    "neon_writes": False,
    "database_modifications": False,
    "validated_content": False,
}


def summarize_snippet_coverage(ranked_report, snippet_report):
    high_priority_candidates = [
        candidate
        for candidate in ranked_report.get("ranked_candidates", [])
        if candidate.get("priority_bucket") == "high"
    ]
    high_priority_pages = {_page_key(candidate) for candidate in high_priority_candidates}
    snippets = snippet_report.get("candidate_snippets", [])
    snippet_pages = {_page_key(snippet) for snippet in snippets}
    snippets_per_source = {}
    for snippet in snippets:
        source_title = snippet.get("source_title") or "unknown"
        snippets_per_source[source_title] = snippets_per_source.get(source_title, 0) + 1
    high_priority_pages_with_snippets = high_priority_pages & snippet_pages
    pages_without_snippets = [
        _page_summary(candidate)
        for candidate in high_priority_candidates
        if _page_key(candidate) not in snippet_pages
    ]
    return {
        "high_priority_candidates_total": len(high_priority_candidates),
        "unique_high_priority_pages_total": len(high_priority_pages),
        "high_priority_pages_processed": len(snippet_pages),
        "high_priority_pages_with_snippets": len(high_priority_pages_with_snippets),
        "high_priority_pages_without_snippets": len(pages_without_snippets),
        "pages_without_snippets": pages_without_snippets,
        "snippets_total": len(snippets),
        "snippets_per_source": dict(sorted(snippets_per_source.items())),
        "contract": _contract_summary(snippet_report),
    }


def _page_key(row):
    return (
        row.get("source_title"),
        row.get("page_number"),
    )


def _page_summary(row):
    summary = {
        "source_title": row.get("source_title"),
        "page_number": row.get("page_number"),
    }
    if row.get("expected_local_path") or row.get("source_path"):
        summary["source_path"] = row.get("expected_local_path") or row.get("source_path")
    summary["reason"] = _metadata_reason(row)
    return summary


def _metadata_reason(row):
    for field_name in ("skip_reason", "skipped_reason", "exclusion_reason", "reason"):
        if row.get(field_name):
            return row[field_name]
    return "unknown_reason"


def _contract_summary(snippet_report):
    contract = snippet_report.get("contract", {})
    violated_flags = [
        flag
        for flag, expected_value in SAFE_CONTRACT_FLAGS.items()
        if contract.get(flag) != expected_value
    ]
    return {
        "passed": not violated_flags,
        "violated_flags": violated_flags,
    }


def print_coverage_summary(summary):
    print("Snippet coverage verification")
    print(f"High-priority candidates total: {summary['high_priority_candidates_total']}")
    print(f"Unique high-priority pages total: {summary['unique_high_priority_pages_total']}")
    print(f"High-priority pages processed: {summary['high_priority_pages_processed']}")
    print(f"High-priority pages with snippets: {summary['high_priority_pages_with_snippets']}")
    print(
        "High-priority pages without snippets: "
        f"{summary['high_priority_pages_without_snippets']}"
    )
    print(f"Snippets total: {summary['snippets_total']}")
    print("Snippets per source:")
    if not summary["snippets_per_source"]:
        print("  none")
    else:
        for source_title, count in summary["snippets_per_source"].items():
            print(f"  {source_title}: {count}")
    print("Pages without snippets:")
    if not summary["pages_without_snippets"]:
        print("  none")
    else:
        for page in summary["pages_without_snippets"]:
            print(
                "  "
                f"{page.get('source_title')} page {page.get('page_number')}: "
                f"{page.get('reason')}"
            )
    print(
        "No Neon/database/validated contract: "
        f"{'PASS' if summary['contract']['passed'] else 'FAIL'}"
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--ranked-report", type=Path, default=DEFAULT_RANKED_REPORT)
    parser.add_argument("--snippet-report", type=Path, default=DEFAULT_SNIPPET_REPORT)
    args = parser.parse_args(argv)

    ranked_report = json.loads(args.ranked_report.read_text(encoding="utf-8"))
    snippet_report = json.loads(args.snippet_report.read_text(encoding="utf-8"))
    summary = summarize_snippet_coverage(ranked_report, snippet_report)
    print_coverage_summary(summary)
    return 0 if summary["contract"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
