"""Metadata-only scoring for definition candidate pages."""


def score_definition_candidates(candidates):
    scored = []
    for candidate in candidates:
        score = candidate.get("signal_count", 0)
        scored.append({**candidate, "definition_score": score})
    return sorted(scored, key=lambda item: item["definition_score"], reverse=True)
