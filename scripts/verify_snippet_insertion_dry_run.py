REQUIRED_SUMMARY_FIELDS = {
    "total_snippets",
    "insertable_snippets",
    "blocked_snippets",
    "block_reasons",
    "source_match_summary",
}


def verify_dry_run_report(report):
    errors = []
    missing_fields = sorted(REQUIRED_SUMMARY_FIELDS - set(report))
    if missing_fields:
        errors.append(f"missing required summary fields: {', '.join(missing_fields)}")
    return {
        "checks": ["required_summary_fields"],
        "errors": errors,
    }
