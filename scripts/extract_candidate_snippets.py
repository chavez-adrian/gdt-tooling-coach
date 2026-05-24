import re


STRONG_SIGNALS = (
    "definition",
    "definitions",
    "definición",
    "definiciones",
    "terminology",
    "terminología",
    "glossary",
    "datum",
    "feature control frame",
    "tolerance zone",
    "MMC",
    "LMC",
    "RFS",
)


def extract_candidate_snippets(candidates, page_text_by_key):
    snippets = []
    for candidate in candidates:
        if candidate.get("priority_bucket") != "high":
            continue
        text = page_text_by_key.get((candidate.get("source_title"), candidate.get("page_number")), "")
        page_snippet_count = 0
        for sentence in _sentence_windows(text):
            for signal in STRONG_SIGNALS:
                if _contains_signal(sentence, signal):
                    snippet_words = sentence.split()[:80]
                    snippets.append(
                        {
                            "matched_signal": signal,
                            "snippet_word_count": len(snippet_words),
                            "snippet_text": " ".join(snippet_words),
                            "extraction_type": "literal_quote",
                            "proposed_review_state": "raw_import",
                            "requires_human_review": True,
                        }
                    )
                    page_snippet_count += 1
                    break
            if page_snippet_count >= 3:
                break
    return snippets


def _sentence_windows(text):
    windows = [window.strip() for window in re.split(r"(?<=[.!?])\s+", text) if window.strip()]
    return windows or [text]


def _contains_signal(text, signal):
    return re.search(rf"(?<!\w){re.escape(signal)}(?!\w)", text, flags=re.IGNORECASE) is not None
