import re


STRONG_SIGNALS = ("datum",)


def extract_candidate_snippets(candidates, page_text_by_key):
    snippets = []
    for candidate in candidates:
        if candidate.get("priority_bucket") != "high":
            continue
        text = page_text_by_key.get((candidate.get("source_title"), candidate.get("page_number")), "")
        for sentence in _sentence_windows(text):
            lowered = sentence.lower()
            for signal in STRONG_SIGNALS:
                if signal in lowered:
                    snippet_words = sentence.split()[:80]
                    snippets.append(
                        {
                            "matched_signal": signal,
                            "snippet_word_count": len(snippet_words),
                            "snippet_text": " ".join(snippet_words),
                        }
                    )
                    break
            if len(snippets) >= 3:
                break
    return snippets


def _sentence_windows(text):
    windows = [window.strip() for window in re.split(r"(?<=[.!?])\s+", text) if window.strip()]
    return windows or [text]
