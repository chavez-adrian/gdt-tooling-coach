"""Local verification for the ranked definition-candidate workflow."""


def summarize_ranked_report(report):
    summary = report.get("summary", {})
    return {"total_ranked_candidates": summary.get("total_candidates", 0)}
