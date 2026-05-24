"""Local verification for the definition-candidate locator report."""


def summarize_candidate_report(report):
    summary = report.get("summary", {})
    return {
        "pdfs_processed": summary.get("existing_pdfs", 0)
        + summary.get("pdf_open_errors", 0),
        "total_candidate_pages": summary.get("candidate_pages", 0),
    }
