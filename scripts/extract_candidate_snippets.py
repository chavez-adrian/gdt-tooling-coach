import json
import re

from pypdf import PdfReader


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
        text = _page_text_for_candidate(candidate, page_text_by_key)
        page_snippet_count = 0
        for sentence in _sentence_windows(text):
            for signal in STRONG_SIGNALS:
                if _contains_signal(sentence, signal):
                    snippet_words = sentence.split()[:80]
                    snippets.append(
                        {
                            "source_title": candidate.get("source_title"),
                            "source_type": candidate.get("source_type"),
                            "source_language": candidate.get("source_language"),
                            "source_path": candidate.get("source_path"),
                            "page_number": candidate.get("page_number"),
                            "candidate_score": candidate.get("candidate_score"),
                            "global_rank": candidate.get("global_rank"),
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


def load_high_priority_ranked_candidates(ranked_report_path):
    with open(ranked_report_path, "r", encoding="utf-8") as ranked_file:
        report = json.load(ranked_file)
    return [
        candidate
        for candidate in report.get("ranked_candidates", [])
        if candidate.get("priority_bucket") == "high"
    ]


def build_candidate_snippets_from_ranked_candidates(
    candidates, pdf_reader_factory=PdfReader
):
    high_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("priority_bucket") == "high"
    ]
    page_text_by_key = {}
    normalized_candidates = []
    for candidate in high_candidates:
        pdf_path = candidate.get("expected_local_path") or candidate.get("source_path")
        if not pdf_path:
            continue
        reader = pdf_reader_factory(pdf_path)
        page_number = candidate.get("page_number")
        page_text = reader.pages[page_number - 1].extract_text() or ""
        normalized = {**candidate, "source_path": pdf_path}
        normalized_candidates.append(normalized)
        page_text_by_key[(pdf_path, page_number)] = page_text
    return extract_candidate_snippets(normalized_candidates, page_text_by_key)


def _sentence_windows(text):
    windows = [window.strip() for window in re.split(r"(?<=[.!?])\s+", text) if window.strip()]
    return windows or [text]


def _contains_signal(text, signal):
    return re.search(rf"(?<!\w){re.escape(signal)}(?!\w)", text, flags=re.IGNORECASE) is not None


def _page_text_for_candidate(candidate, page_text_by_key):
    page_number = candidate.get("page_number")
    for source_key in (candidate.get("source_path"), candidate.get("source_title")):
        text = page_text_by_key.get((source_key, page_number))
        if text is not None:
            return text
    return ""
