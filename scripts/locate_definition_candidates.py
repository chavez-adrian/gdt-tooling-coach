"""Metadata-only definition-candidate detection for PDF page text."""

import json
import re
from pathlib import Path

from pypdf import PdfReader

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


def build_definition_candidate_report(manifest_path, project_root):
    manifest_path = Path(manifest_path)
    project_root = Path(project_root)
    manifest_entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing_pdfs = 0
    existing_pdfs = 0
    no_match_pdfs = 0
    candidate_pages = []

    for entry in manifest_entries:
        pdf_path = project_root / entry["expected_local_path"]
        if pdf_path.exists():
            existing_pdfs += 1
            reader = PdfReader(str(pdf_path))
            pages = []
            for page_index, page in enumerate(reader.pages, start=1):
                pages.append(
                    {
                        "source_title": entry["title"],
                        "expected_local_path": entry["expected_local_path"],
                        "page_number": page_index,
                        "page_text": page.extract_text() or "",
                    }
                )
            source_candidates = locate_definition_candidates(pages)
            if source_candidates:
                candidate_pages.extend(source_candidates)
            else:
                no_match_pdfs += 1
        else:
            missing_pdfs += 1

    return {
        "summary": {
            "total_sources": len(manifest_entries),
            "existing_pdfs": existing_pdfs,
            "missing_pdfs": missing_pdfs,
            "no_match_pdfs": no_match_pdfs,
            "candidate_pages": len(candidate_pages),
        },
        "candidate_pages": candidate_pages,
    }


def locate_definition_candidates(pages):
    candidates = []
    for page in pages:
        page_text = page.get("page_text", "")
        page_metadata = {key: value for key, value in page.items() if key != "page_text"}
        result = analyze_definition_candidate_page(page_text, page_metadata)
        if result["is_candidate"]:
            result = {key: value for key, value in result.items() if key != "is_candidate"}
            candidates.append(result)
    return candidates


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
