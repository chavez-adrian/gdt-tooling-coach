"""Local coverage verification for ranked candidates and generated snippets."""


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
        "high_priority_pages_with_snippets": len(high_priority_pages_with_snippets),
        "high_priority_pages_without_snippets": len(pages_without_snippets),
        "pages_without_snippets": pages_without_snippets,
        "snippets_total": len(snippets),
        "snippets_per_source": dict(sorted(snippets_per_source.items())),
    }


def _page_key(row):
    return (
        row.get("expected_local_path") or row.get("source_path") or row.get("source_title"),
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
