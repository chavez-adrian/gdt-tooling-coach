STRONG_SIGNALS = ("datum",)


def extract_candidate_snippets(candidates, page_text_by_key):
    snippets = []
    for candidate in candidates:
        if candidate.get("priority_bucket") != "high":
            continue
        text = page_text_by_key.get((candidate.get("source_title"), candidate.get("page_number")), "")
        lowered = text.lower()
        for signal in STRONG_SIGNALS:
            if signal in lowered:
                snippet_words = text.split()[:80]
                snippets.append(
                    {
                        "matched_signal": signal,
                        "snippet_word_count": len(snippet_words),
                        "snippet_text": " ".join(snippet_words),
                    }
                )
                break
    return snippets
