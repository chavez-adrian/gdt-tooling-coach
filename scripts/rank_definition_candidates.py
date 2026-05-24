"""Metadata-only scoring for definition candidate pages."""

STRONG_SIGNALS = {
    "definition",
    "definitions",
    "definiciÃ³n",
    "definiciones",
    "terminology",
    "terminologÃ­a",
    "glossary",
}
MEDIUM_SIGNALS = {
    "datum",
    "feature control frame",
    "tolerance zone",
    "MMC",
    "LMC",
    "RFS",
    "sÃ­mbolo",
    "sÃ­mbolos",
}
GENERIC_SIGNALS = {"term", "terms", "tÃ©rmino", "tÃ©rminos"}
PREFERRED_SOURCE_TYPES = {"standard", "official_standard", "norm"}
SUPPORTED_LANGUAGES = {"en", "es", "english", "spanish"}
FORBIDDEN_TEXT_KEYS = {
    "content",
    "definition",
    "definitions",
    "excerpt",
    "long_quote",
    "page_text",
    "quote",
    "sample",
    "text",
    "text_sample",
}


def _priority_bucket(score):
    if score >= 12:
        return "high"
    if score >= 5:
        return "medium"
    return "low"


def score_definition_candidate(candidate):
    score = candidate.get("signal_count", 0)
    word_count = candidate.get("approximate_word_count", 0)
    if 100 <= word_count <= 1600:
        score += 1
    if candidate.get("source_type") in PREFERRED_SOURCE_TYPES:
        score += 1
    if candidate.get("language") in SUPPORTED_LANGUAGES:
        score += 1
    for signal in candidate.get("matched_signals", []):
        if signal in STRONG_SIGNALS:
            score += 4
        elif signal in MEDIUM_SIGNALS:
            score += 2
        elif signal in GENERIC_SIGNALS:
            score -= 1
    safe_candidate = {
        key: value for key, value in candidate.items() if key not in FORBIDDEN_TEXT_KEYS
    }
    return {
        **safe_candidate,
        "definition_score": score,
        "priority_bucket": _priority_bucket(score),
    }


def score_definition_candidates(candidates):
    scored = [score_definition_candidate(candidate) for candidate in candidates]
    return sorted(scored, key=lambda item: item["definition_score"], reverse=True)


def build_ranked_definition_candidate_rows(candidates):
    rows = []
    source_ranks = {}
    for global_rank, candidate in enumerate(score_definition_candidates(candidates), 1):
        row = dict(candidate)
        row["candidate_score"] = row.pop("definition_score")
        row["global_rank"] = global_rank
        source_title = row.get("source_title", "")
        source_ranks[source_title] = source_ranks.get(source_title, 0) + 1
        row["rank_within_source"] = source_ranks[source_title]
        rows.append(row)
    return rows
