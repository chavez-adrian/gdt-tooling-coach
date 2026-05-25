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
FORBIDDEN_SQL_WORDS = {"insert", "update", "delete", "create", "drop", "alter"}


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
    if _contains_executable_sql(report):
        errors.append("executable SQL is not allowed in dry-run reports")
    else:
        checks.append("no_executable_sql")
    return {
        "checks": checks,
        "errors": errors,
    }


def _contains_executable_sql(value):
    if isinstance(value, dict):
        return any(_contains_executable_sql(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_executable_sql(item) for item in value)
    if not isinstance(value, str):
        return False
    normalized = value.lower().replace(";", " ")
    return any(word in normalized.split() for word in FORBIDDEN_SQL_WORDS)
