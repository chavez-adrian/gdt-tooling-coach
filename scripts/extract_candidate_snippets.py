import argparse
import json
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "ranked_definition_candidates.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "candidate_snippets.json"
DEFAULT_OUTPUT_RELATIVE_PATH = Path("data/processed/candidate_snippets.json")
MAX_TOTAL_SNIPPETS = 100
REPORT_CONTRACT = {
    "neon_writes": False,
    "database_modifications": False,
    "validated_content": False,
}


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
    candidates, pdf_reader_factory=PdfReader, max_total_snippets=MAX_TOTAL_SNIPPETS
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
    return [
        _to_public_report_row(snippet)
        for snippet in extract_candidate_snippets(normalized_candidates, page_text_by_key)
    ][:max_total_snippets]


def write_candidate_snippets_report(
    ranked_report_path, output_path, pdf_reader_factory=PdfReader
):
    snippets = build_candidate_snippets_from_ranked_candidates(
        load_high_priority_ranked_candidates(ranked_report_path),
        pdf_reader_factory=pdf_reader_factory,
    )
    report = {
        "contract": REPORT_CONTRACT,
        "candidate_snippets": snippets,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(report, output_file, indent=2, sort_keys=True)
        output_file.write("\n")
    return report


def candidate_snippets_report_is_ignored(run_command=subprocess.run):
    result = run_command(
        ["git", "check-ignore", DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def format_console_summary(report):
    contract = report["contract"]
    return "\n".join(
        [
            f"Candidate snippets written: {len(report['candidate_snippets'])}",
            f"Neon writes: {str(contract['neon_writes']).lower()}",
            f"Database modifications: {str(contract['database_modifications']).lower()}",
            f"Validated content: {str(contract['validated_content']).lower()}",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Write controlled candidate snippets for human review."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args(argv)
    report = write_candidate_snippets_report(args.input, args.output)
    print(format_console_summary(report))
    return 0


def _to_public_report_row(snippet):
    return {
        "source_title": snippet.get("source_title"),
        "source_type": snippet.get("source_type"),
        "language": snippet.get("language") or snippet.get("source_language"),
        "expected_local_path": snippet.get("expected_local_path")
        or snippet.get("source_path"),
        "page_number": snippet.get("page_number"),
        "matched_signal": snippet.get("matched_signal"),
        "snippet_word_count": snippet.get("snippet_word_count"),
        "snippet_text": snippet.get("snippet_text"),
        "extraction_type": snippet.get("extraction_type"),
        "proposed_review_state": snippet.get("proposed_review_state"),
        "requires_human_review": snippet.get("requires_human_review"),
        "candidate_score": snippet.get("candidate_score"),
        "global_rank": snippet.get("global_rank"),
    }


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


if __name__ == "__main__":
    raise SystemExit(main())
