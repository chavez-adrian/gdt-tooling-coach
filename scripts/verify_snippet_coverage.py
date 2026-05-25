"""Local coverage verification for ranked candidates and generated snippets."""


def summarize_snippet_coverage(ranked_report, snippet_report):
    high_priority_candidates = [
        candidate
        for candidate in ranked_report.get("ranked_candidates", [])
        if candidate.get("priority_bucket") == "high"
    ]
    high_priority_pages = {_page_key(candidate) for candidate in high_priority_candidates}
    return {
        "high_priority_candidates_total": len(high_priority_candidates),
        "unique_high_priority_pages_total": len(high_priority_pages),
    }


def _page_key(row):
    return (
        row.get("expected_local_path") or row.get("source_path") or row.get("source_title"),
        row.get("page_number"),
    )
