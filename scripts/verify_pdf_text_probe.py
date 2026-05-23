"""Local verification helpers for the controlled PDF text probe."""

from __future__ import annotations


def summarize_probe_report(report: dict[str, object]) -> dict[str, object]:
    pdfs = report.get("pdfs", [])
    sample_size_distribution: dict[int, int] = {}
    sampled_pages_by_quartile = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    for pdf in pdfs:
        sample_size = int(pdf.get("sample_size", 0))
        sample_size_distribution[sample_size] = (
            sample_size_distribution.get(sample_size, 0) + 1
        )
        for quartile, pages in pdf.get("sampled_pages_by_quartile", {}).items():
            sampled_pages_by_quartile[quartile] = (
                sampled_pages_by_quartile.get(quartile, 0) + len(pages)
            )

    return {
        "total_pdfs_processed": len(pdfs),
        "pdfs_with_extractable_text": sum(
            1 for pdf in pdfs if pdf.get("has_extractable_text")
        ),
        "sample_size_distribution": sample_size_distribution,
        "sampled_pages_by_quartile": sampled_pages_by_quartile,
    }
