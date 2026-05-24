"""Local verification for the definition-candidate locator report."""

from collections import Counter

FORBIDDEN_CONTENT_KEYS = {
    "content",
    "definition",
    "definitions",
    "excerpt",
    "long_quote",
    "page_text",
    "quote",
    "sample",
    "text",
    "text_sample",
}


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


def report_contains_forbidden_content_fields(report):
    field_paths = []

    def visit(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                if key in FORBIDDEN_CONTENT_KEYS:
                    field_paths.append(child_path)
                visit(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(report, "")
    return {
        "has_forbidden_content_fields": bool(field_paths),
        "field_paths": field_paths,
    }
