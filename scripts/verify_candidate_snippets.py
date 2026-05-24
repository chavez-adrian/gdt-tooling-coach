"""Local verification for the controlled candidate-snippet workflow."""


def summarize_candidate_snippet_report(report):
    snippets = report.get("candidate_snippets", [])
    snippets_by_source = {}
    for snippet in snippets:
        source_title = snippet.get("source_title") or "unknown"
        snippets_by_source[source_title] = snippets_by_source.get(source_title, 0) + 1
    return {
        "snippets_generated": len(snippets),
        "snippets_by_source": dict(sorted(snippets_by_source.items())),
        "max_snippet_word_count": max(
            [snippet.get("snippet_word_count", 0) for snippet in snippets] or [0]
        ),
    }
