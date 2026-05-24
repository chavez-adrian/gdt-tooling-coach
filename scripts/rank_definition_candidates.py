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


def score_definition_candidates(candidates):
    scored = []
    for candidate in candidates:
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
        scored.append({**candidate, "definition_score": score})
    return sorted(scored, key=lambda item: item["definition_score"], reverse=True)
