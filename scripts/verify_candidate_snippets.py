"""Local verification for the controlled candidate-snippet workflow."""

MAX_SNIPPET_WORDS = 80


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


def verify_snippet_word_limit(report):
    over_limit_indexes = [
        index
        for index, snippet in enumerate(report.get("candidate_snippets", []))
        if snippet.get("snippet_word_count", 0) > MAX_SNIPPET_WORDS
    ]
    return {
        "passed": not over_limit_indexes,
        "max_allowed_words": MAX_SNIPPET_WORDS,
        "over_limit_indexes": over_limit_indexes,
    }


def verify_review_state_fields(report):
    invalid_indexes = [
        index
        for index, snippet in enumerate(report.get("candidate_snippets", []))
        if snippet.get("extraction_type") != "literal_quote"
        or snippet.get("proposed_review_state") != "raw_import"
        or snippet.get("requires_human_review") is not True
    ]
    return {
        "passed": not invalid_indexes,
        "invalid_review_state_indexes": invalid_indexes,
    }
