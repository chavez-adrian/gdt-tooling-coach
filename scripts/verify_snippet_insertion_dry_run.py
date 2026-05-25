REQUIRED_SUMMARY_FIELDS = {
    "total_snippets",
    "insertable_snippets",
    "blocked_snippets",
    "block_reasons",
    "source_match_summary",
}
EXPECTED_INTENDED_INSERTION_METADATA = {
    "review_state": "raw_import",
    "requires_human_review": True,
    "validated": False,
    "extraction_type": "literal_quote",
}


def verify_dry_run_report(report):
    errors = []
    checks = ["required_summary_fields"]
    missing_fields = sorted(REQUIRED_SUMMARY_FIELDS - set(report))
    if missing_fields:
        errors.append(f"missing required summary fields: {', '.join(missing_fields)}")
    if report.get("intended_insertion_metadata") != EXPECTED_INTENDED_INSERTION_METADATA:
        errors.append("intended insertion metadata does not match raw unvalidated literal quote contract")
    else:
        checks.append("intended_insertion_constants")
    return {
        "checks": checks,
        "errors": errors,
    }
