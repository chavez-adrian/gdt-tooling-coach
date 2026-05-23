"""Local verification helpers for the controlled PDF text probe."""

from __future__ import annotations


def summarize_probe_report(report: dict[str, object]) -> dict[str, int]:
    pdfs = report.get("pdfs", [])
    return {"total_pdfs_processed": len(pdfs)}
