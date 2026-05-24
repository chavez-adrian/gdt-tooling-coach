"""Metadata-only definition-candidate detection for PDF page text."""

import re

SIGNALS = [
    "definition",
    "definitions",
    "terminology",
    "terms",
    "glossary",
    "símbolo",
    "símbolos",
    "definición",
    "definiciones",
    "término",
    "terminología",
    "datum",
    "feature control frame",
    "tolerance zone",
    "MMC",
    "LMC",
    "RFS",
]

TEXT_METADATA_KEYS = {"content", "definition", "excerpt", "quote", "sample", "text"}


def analyze_definition_candidate_page(page_text, page_metadata=None):
    metadata = {
        key: value
        for key, value in dict(page_metadata or {}).items()
        if key not in TEXT_METADATA_KEYS
    }
    normalized_text = page_text.lower()
    matched_signals = [
        signal
        for signal in SIGNALS
        if re.search(rf"(?<!\w){re.escape(signal.lower())}(?!\w)", normalized_text)
    ]
    if matched_signals:
        candidate_reason = (
            f"matched {len(matched_signals)} definition candidate signals: "
            f"{', '.join(matched_signals)}"
        )
    else:
        candidate_reason = "matched 0 definition candidate signals"

    return {
        **metadata,
        "is_candidate": bool(matched_signals),
        "matched_signals": matched_signals,
        "signal_count": len(matched_signals),
        "approximate_char_count": len(page_text),
        "approximate_word_count": len(re.findall(r"\w+", page_text)),
        "candidate_reason": candidate_reason,
    }
