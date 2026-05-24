"""Local verification for the definition-candidate locator report."""

import subprocess
from collections import Counter

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
