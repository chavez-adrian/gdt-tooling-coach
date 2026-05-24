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
MEDIUM_SIGNALS = {"datum"}


def score_definition_candidates(candidates):
    scored = []
    for candidate in candidates:
        score = candidate.get("signal_count", 0)
        for signal in candidate.get("matched_signals", []):
            if signal in STRONG_SIGNALS:
                score += 4
            elif signal in MEDIUM_SIGNALS:
                score += 2
        scored.append({**candidate, "definition_score": score})
    return sorted(scored, key=lambda item: item["definition_score"], reverse=True)
