"""Local verification for the controlled candidate-snippet workflow."""

import argparse
import json
import subprocess
from pathlib import Path

MAX_SNIPPET_WORDS = 80
REPORT_PATH = "data/processed/candidate_snippets.json"
SAFE_CONTRACT_FLAGS = {
    "neon_writes": False,
    "database_modifications": False,
    "validated_content": False,
}


def summarize_candidate_snippet_report(report):
    snippets = report.get("candidate_snippets", [])
    snippets_by_source = {}
    page_keys = set()
    for snippet in snippets:
        source_title = snippet.get("source_title") or "unknown"
        snippets_by_source[source_title] = snippets_by_source.get(source_title, 0) + 1
        page_keys.add(
            (
                snippet.get("expected_local_path") or snippet.get("source_path"),
                snippet.get("source_title"),
                snippet.get("page_number"),
            )
        )
    return {
        "high_priority_pages_processed": len(page_keys),
        "snippets_generated": len(snippets),
        "snippets_by_source": dict(sorted(snippets_by_source.items())),
        "max_snippet_word_count": max(
            [snippet.get("snippet_word_count", 0) for snippet in snippets] or [0]
        ),
    }


def verify_snippet_word_limit(report):
    over_limit_indexes = [
        index
        for index, snippet in enumerate(report.get("candidate_snippets", []))
        if snippet.get("snippet_word_count", 0) > MAX_SNIPPET_WORDS
    ]
    return {
        "passed": not over_limit_indexes,
        "max_allowed_words": MAX_SNIPPET_WORDS,
        "over_limit_indexes": over_limit_indexes,
    }


def verify_review_state_fields(report):
    invalid_indexes = [
        index
        for index, snippet in enumerate(report.get("candidate_snippets", []))
        if snippet.get("extraction_type") != "literal_quote"
        or snippet.get("proposed_review_state") != "raw_import"
        or snippet.get("requires_human_review") is not True
    ]
    return {
        "passed": not invalid_indexes,
        "invalid_review_state_indexes": invalid_indexes,
    }


def verify_required_snippet_fields(report):
    required_fields = (
        "source_title",
        "source_type",
        "language",
        "page_number",
        "snippet_text",
        "extraction_type",
        "proposed_review_state",
        "requires_human_review",
    )
    invalid_indexes = [
        index
        for index, snippet in enumerate(report.get("candidate_snippets", []))
        if any(snippet.get(field) in (None, "") for field in required_fields)
    ]
    missing_language_count = sum(
        1
        for snippet in report.get("candidate_snippets", [])
        if snippet.get("language") in (None, "")
    )
    return {
        "passed": not invalid_indexes,
        "invalid_required_field_indexes": invalid_indexes,
        "missing_language_count": missing_language_count,
    }


def verify_report_contract(report):
    contract = report.get("contract", {})
    violated_flags = [
        flag
        for flag, expected_value in SAFE_CONTRACT_FLAGS.items()
        if contract.get(flag) != expected_value
    ]
    return {
        "passed": not violated_flags,
        "violated_contract_flags": violated_flags,
    }


def _run_command_check(name, command, project_root, runner=subprocess.run):
    result = runner(command, cwd=project_root, capture_output=True, text=True)
    return {
        "name": name,
        "command": " ".join(command),
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_extractor_command(project_root, runner=subprocess.run):
    return _run_command_check(
        "candidate snippet extractor command",
        ["python", "scripts/extract_candidate_snippets.py"],
        project_root,
        runner=runner,
    )


def run_unittest_command(project_root, runner=subprocess.run):
    return _run_command_check(
        "unittest discovery command",
        ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        project_root,
        runner=runner,
    )


def check_report_path_ignored(project_root, runner=subprocess.run):
    return _run_command_check(
        "generated candidate snippet report path is ignored by Git",
        ["git", "check-ignore", REPORT_PATH],
        project_root,
        runner=runner,
    )


def collect_git_evidence(project_root, runner=subprocess.run):
    return {
        "git_diff_stat": _run_command_check(
            "git diff stat",
            ["git", "diff", "--stat"],
            project_root,
            runner=runner,
        ),
        "git_status_short": _run_command_check(
            "git status short",
            ["git", "status", "--short"],
            project_root,
            runner=runner,
        ),
    }


def build_verification(report, project_root, runner=subprocess.run):
    word_limit = verify_snippet_word_limit(report)
    review_state = verify_review_state_fields(report)
    required_fields = verify_required_snippet_fields(report)
    contract = verify_report_contract(report)
    command_checks = [
        run_extractor_command(project_root, runner=runner),
        run_unittest_command(project_root, runner=runner),
        check_report_path_ignored(project_root, runner=runner),
    ]
    git_evidence = collect_git_evidence(project_root, runner=runner)
    passed = (
        word_limit["passed"]
        and review_state["passed"]
        and required_fields["passed"]
        and contract["passed"]
        and all(check["passed"] for check in command_checks)
    )
    return {
        "passed": passed,
        "summary": summarize_candidate_snippet_report(report),
        "word_limit": word_limit,
        "review_state": review_state,
        "required_fields": required_fields,
        "contract": contract,
        "command_checks": command_checks,
        "git_evidence": git_evidence,
    }


def print_metrics_summary(verification):
    summary = verification["summary"]
    print("Candidate snippet verification")
    print(f"Overall result: {'PASS' if verification['passed'] else 'FAIL'}")
    print(f"High-priority pages processed: {summary['high_priority_pages_processed']}")
    print(f"Snippets generated: {summary['snippets_generated']}")
    print("Snippets by source:")
    if not summary["snippets_by_source"]:
        print("  none")
    else:
        for source_title, count in summary["snippets_by_source"].items():
            print(f"  {source_title}: {count}")
    print(
        "Maximum snippet word count observed: "
        f"{summary['max_snippet_word_count']}"
    )
    print(
        "No snippet exceeds 80 words: "
        f"{'PASS' if verification['word_limit']['passed'] else 'FAIL'}"
    )
    print(
        "Raw literal human-review fields: "
        f"{'PASS' if verification['review_state']['passed'] else 'FAIL'}"
    )
    print(f"Snippets with language=None: {verification['required_fields']['missing_language_count']}")
    print(
        "Required snippet fields: "
        f"{'PASS' if verification['required_fields']['passed'] else 'FAIL'}"
    )
    print(
        "No Neon/database/validated contract: "
        f"{'PASS' if verification['contract']['passed'] else 'FAIL'}"
    )
    for check in verification["command_checks"]:
        print(f"{check['command']}: {'PASS' if check['passed'] else 'FAIL'}")
    print("git diff --stat:")
    print(verification["git_evidence"]["git_diff_stat"]["stdout"].rstrip())
    print("git status --short:")
    print(verification["git_evidence"]["git_status_short"]["stdout"].rstrip())


def main(argv=None, runner=subprocess.run):
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default=REPORT_PATH)
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root)
    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = project_root / report_path
    report = json.loads(report_path.read_text(encoding="utf-8"))
    verification = build_verification(report, project_root, runner=runner)
    print_metrics_summary(verification)
    return 0 if verification["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
