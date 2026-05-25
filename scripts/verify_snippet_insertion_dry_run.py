import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_RELATIVE_PATH = Path("data/processed/snippet_insertion_dry_run.json")
DEFAULT_REPORT_PATH = PROJECT_ROOT / DEFAULT_REPORT_RELATIVE_PATH
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
    contract = report.get("contract", {})
    if contract.get("database_writes") or contract.get("database_modifications"):
        errors.append("dry-run contract cannot declare database writes")
    if contract.get("validated_content"):
        errors.append("dry-run contract cannot declare validated content")
    if contract.get("executable_sql_saved"):
        errors.append("dry-run contract cannot declare saved executable SQL")
    if not any(
        [
            contract.get("database_writes"),
            contract.get("database_modifications"),
            contract.get("validated_content"),
            contract.get("executable_sql_saved"),
        ]
    ):
        checks.append("safe_report_contract")
    return {
        "checks": checks,
        "errors": errors,
        "runtime_contract": {
            "database_access_required": False,
            "database_writes_attempted": False,
            "neon_required": False,
        },
    }


def format_verification_summary(report, result):
    status = "passed" if not result["errors"] else "failed"
    return "\n".join(
        [
            "Snippet insertion dry-run verification complete.",
            f"Status: {status}",
            f"Total snippets: {report['total_snippets']}",
            f"Insertable snippets: {report['insertable_snippets']}",
            f"Blocked snippets: {report['blocked_snippets']}",
            f"Block reasons: {_format_key_counts(report.get('block_reasons', {}))}",
            f"Source match summary: {_format_key_counts(report.get('source_match_summary', {}))}",
            "No database writes: true",
            "Console output sanitized: true",
        ]
    )


def load_report(report_path=DEFAULT_REPORT_PATH):
    with open(report_path, "r", encoding="utf-8") as report_file:
        return json.load(report_file)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify the snippet insertion dry-run report without database access."
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument(
        "--skip-ignore-check",
        action="store_true",
        help="Skip git ignore verification for temp-file tests.",
    )
    args = parser.parse_args(argv)

    try:
        report = load_report(args.report)
        result = verify_dry_run_report(report)
        if not args.skip_ignore_check and not verify_default_report_path_is_ignored():
            result["errors"].append(
                f"{DEFAULT_REPORT_RELATIVE_PATH.as_posix()} is not ignored by Git"
            )
        print(format_verification_summary(report, result))
        if result["errors"]:
            for error in result["errors"]:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        return 0
    except Exception as exc:
        print("Snippet insertion dry-run verification failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1


def verify_default_report_path_is_ignored(run_command=subprocess.run):
    result = run_command(
        ["git", "check-ignore", DEFAULT_REPORT_RELATIVE_PATH.as_posix()],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _contains_executable_sql(value):
    if isinstance(value, dict):
        return any(_contains_executable_sql(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_executable_sql(item) for item in value)
    if not isinstance(value, str):
        return False
    normalized = value.lower().replace(";", " ")
    return any(word in normalized.split() for word in FORBIDDEN_SQL_WORDS)


def _format_key_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


if __name__ == "__main__":
    raise SystemExit(main())
