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


def analyze_definition_candidate_page(page_text, page_metadata=None):
    metadata = dict(page_metadata or {})
    normalized_text = page_text.lower()
    matched_signals = [
        signal
        for signal in SIGNALS
        if re.search(rf"(?<!\w){re.escape(signal.lower())}(?!\w)", normalized_text)
    ]

    return {
        **metadata,
        "matched_signals": matched_signals,
        "signal_count": len(matched_signals),
    }
