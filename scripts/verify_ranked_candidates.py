"""Local verification for the ranked definition-candidate workflow."""

import subprocess

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
