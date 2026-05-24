"""Metadata-only definition-candidate detection for PDF page text."""


def analyze_definition_candidate_page(page_text, page_metadata=None):
    metadata = dict(page_metadata or {})
    matched_signals = []
    if "definition" in page_text.lower():
        matched_signals.append("definition")

    return {
        **metadata,
        "matched_signals": matched_signals,
        "signal_count": len(matched_signals),
    }
