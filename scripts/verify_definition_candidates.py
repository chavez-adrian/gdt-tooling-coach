"""Local verification for the definition-candidate locator report."""

from collections import Counter


def summarize_candidate_report(report):
    summary = report.get("summary", {})
    candidate_pages = report.get("candidate_pages", [])
    signal_counts = Counter(
        signal
        for page in candidate_pages
        for signal in page.get("matched_signals", [])
    )
    return {
        "pdfs_processed": summary.get("existing_pdfs", 0)
        + summary.get("pdf_open_errors", 0),
        "total_candidate_pages": summary.get("candidate_pages", 0),
        "candidate_pages_by_source": dict(
            Counter(page.get("source_title", "unknown") for page in candidate_pages)
        ),
        "top_signals_found": signal_counts.most_common(),
    }
