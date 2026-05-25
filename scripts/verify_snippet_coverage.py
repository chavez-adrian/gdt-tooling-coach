"""Local coverage verification for ranked candidates and generated snippets."""


def summarize_snippet_coverage(ranked_report, snippet_report):
    high_priority_candidates = [
        candidate
        for candidate in ranked_report.get("ranked_candidates", [])
        if candidate.get("priority_bucket") == "high"
    ]
    return {
        "high_priority_candidates_total": len(high_priority_candidates),
    }
