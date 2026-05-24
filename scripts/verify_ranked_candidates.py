"""Local verification for the ranked definition-candidate workflow."""

import argparse
import json
import subprocess
from pathlib import Path

REPORT_PATH = "data/processed/ranked_definition_candidates.json"
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


def _run_command_check(name, command, project_root, runner=subprocess.run):
    result = runner(command, cwd=project_root, capture_output=True, text=True)
    return {
        "name": name,
        "command": " ".join(command),
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_ranker_command(project_root, runner=subprocess.run):
    return _run_command_check(
        "ranked definition candidate command",
        ["python", "scripts/rank_definition_candidates.py"],
        project_root,
        runner=runner,
    )


def run_verifier_command(project_root, runner=subprocess.run):
    return _run_command_check(
        "ranked candidate verifier command",
        ["python", "scripts/verify_ranked_candidates.py"],
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
        "generated ranked report path is ignored by Git",
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
    safety = report_contains_forbidden_content_fields(report)
    command_checks = [
        run_ranker_command(project_root, runner=runner),
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
        "summary": summarize_ranked_report(report),
        "content_safety": safety,
        "command_checks": command_checks,
        "git_evidence": git_evidence,
    }


def print_metrics_summary(verification):
    summary = verification["summary"]
    buckets = summary["priority_buckets"]
    safety = verification["content_safety"]
    print("Ranked definition candidate verification")
    print(f"Overall result: {'PASS' if verification['passed'] else 'FAIL'}")
    print(f"Total ranked candidates: {summary['total_ranked_candidates']}")
    print(f"High: {buckets['high']}")
    print(f"Medium: {buckets['medium']}")
    print(f"Low: {buckets['low']}")
    print("Top sources by high-priority candidates:")
    top_sources = summary["top_sources_by_high_priority_candidates"]
    if not top_sources:
        print("  none")
    else:
        for source in top_sources:
            print(
                f"  {source['source_title']}: "
                f"{source['high_priority_candidates']}"
            )
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
