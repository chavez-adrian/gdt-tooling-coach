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
                snippets.append(
                    {
                        "matched_signal": signal,
                        "snippet_word_count": len(text.split()),
                        "snippet_text": text,
                    }
                )
                break
    return snippets
