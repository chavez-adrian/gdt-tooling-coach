"""Metadata-only definition-candidate detection for PDF page text."""

SIGNALS = [
    "definition",
    "símbolo",
    "definición",
    "terminología",
]


def analyze_definition_candidate_page(page_text, page_metadata=None):
    metadata = dict(page_metadata or {})
    normalized_text = page_text.lower()
    matched_signals = [signal for signal in SIGNALS if signal in normalized_text]

    return {
        **metadata,
        "matched_signals": matched_signals,
        "signal_count": len(matched_signals),
    }
