"""Local verification for the ranked definition-candidate workflow."""

FORBIDDEN_CONTENT_KEYS = {
    "content",
    "definition",
    "definitions",
    "excerpt",
    "long_quote",
    "page_text",
    "quote",
    "sample",
    "snippet",
    "text",
    "text_sample",
}


def summarize_ranked_report(report):
    summary = report.get("summary", {})
    return {
        "total_ranked_candidates": summary.get("total_candidates", 0),
        "priority_buckets": summary.get(
            "priority_buckets",
            {"high": 0, "medium": 0, "low": 0},
        ),
        "top_sources_by_high_priority_candidates": summary.get(
            "top_sources_by_high_priority_candidates", []
        ),
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
