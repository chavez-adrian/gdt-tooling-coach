"""Local verification for the ranked definition-candidate workflow."""


def summarize_ranked_report(report):
    summary = report.get("summary", {})
    return {
        "total_ranked_candidates": summary.get("total_candidates", 0),
        "priority_buckets": summary.get(
            "priority_buckets",
            {"high": 0, "medium": 0, "low": 0},
        ),
    }
