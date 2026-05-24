"""Local verification for the definition-candidate locator report."""

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

REPORT_PATH = "data/processed/definition_candidate_pages.json"
FORBIDDEN_CONTENT_KEYS = {
    "content",
    "definition",
    "definitions",
    "excerpt",
    "long_quote",
    "page_text",
    "quote",
    "sample",
    "text",
    "text_sample",
}


def summarize_candidate_report(report):
    summary = report.get("summary", {})
    candidate_pages = report.get("candidate_pages", [])
    signal_counts = Counter(
        signal
        for page in candidate_pages
        for signal in page.get("matched_signals", [])
    )
    return {
        "pdfs_processed": summary.get("existing_pdfs", 0)
        + summary.get("pdf_open_errors", 0),
        "total_candidate_pages": summary.get("candidate_pages", 0),
        "candidate_pages_by_source": dict(
            Counter(page.get("source_title", "unknown") for page in candidate_pages)
        ),
        "top_signals_found": signal_counts.most_common(),
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


def check_report_path_ignored(project_root, runner=subprocess.run):
    result = runner(
        ["git", "check-ignore", REPORT_PATH],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    return {
        "name": "generated report path is ignored by Git",
        "command": f"git check-ignore {REPORT_PATH}",
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
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


def run_locator_command(project_root, runner=subprocess.run):
    return _run_command_check(
        "definition candidate locator command",
        ["python", "scripts/locate_definition_candidates.py"],
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
    safety = report_contains_forbidden_content_fields(report)
    command_checks = [
        run_locator_command(project_root, runner=runner),
        run_unittest_command(project_root, runner=runner),
        check_report_path_ignored(project_root, runner=runner),
    ]
    git_evidence = collect_git_evidence(project_root, runner=runner)
    passed = (
        all(check["passed"] for check in command_checks)
        and not safety["has_forbidden_content_fields"]
    )
    return {
        "passed": passed,
        "summary": summarize_candidate_report(report),
        "content_safety": safety,
        "command_checks": command_checks,
        "git_evidence": git_evidence,
    }


def print_metrics_summary(verification):
    summary = verification["summary"]
    safety = verification["content_safety"]
    print("Definition candidate locator verification")
    print(f"Overall result: {'PASS' if verification['passed'] else 'FAIL'}")
    print(f"PDFs processed: {summary['pdfs_processed']}")
    print(f"Total candidate pages: {summary['total_candidate_pages']}")
    print("Candidate pages by source:")
    for source, count in summary["candidate_pages_by_source"].items():
        print(f"  {source}: {count}")
    print("Top signals found:")
    for signal, count in summary["top_signals_found"]:
        print(f"  {signal}: {count}")
    if safety["has_forbidden_content_fields"]:
        print(f"Forbidden content fields: {', '.join(safety['field_paths'])}")
    else:
        print("Forbidden content fields: none")
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
