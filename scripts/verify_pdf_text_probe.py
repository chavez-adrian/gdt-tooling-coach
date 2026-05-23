"""Local verification helpers for the controlled PDF text probe."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, TextIO

TEXT_CONTENT_FIELD_NAMES = {"text", "content", "extracted_text", "raw_text"}
REPORT_RELATIVE_PATH = Path("data/processed/pdf_text_probe.json")


def normalize_probe_report(report: object) -> dict[str, object]:
    if isinstance(report, list):
        return {"pdfs": report}
    return report


def summarize_probe_report(report: object) -> dict[str, object]:
    pdfs = normalize_probe_report(report).get("pdfs", [])
    sample_size_distribution: dict[int, int] = {}
    sampled_pages_by_quartile = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
    text_content_fields_present = False
    for pdf in pdfs:
        text_content_fields_present = text_content_fields_present or any(
            field_name in TEXT_CONTENT_FIELD_NAMES for field_name in pdf
        )
        sample_size = int(pdf.get("sample_size", 0))
        sample_size_distribution[sample_size] = (
            sample_size_distribution.get(sample_size, 0) + 1
        )
        for quartile, pages in pdf.get("sampled_pages_by_quartile", {}).items():
            sampled_pages_by_quartile[quartile] = (
                sampled_pages_by_quartile.get(quartile, 0) + len(pages)
            )

    return {
        "total_pdfs_processed": len(pdfs),
        "pdfs_with_extractable_text": sum(
            1 for pdf in pdfs if pdf.get("has_extractable_text")
        ),
        "sample_size_distribution": sample_size_distribution,
        "sampled_pages_by_quartile": sampled_pages_by_quartile,
        "text_content_fields_present": text_content_fields_present,
    }


def check_report_path_ignored(
    project_root: Path,
    command_runner: Callable[..., object] = subprocess.run,
) -> dict[str, object]:
    report_path = REPORT_RELATIVE_PATH.as_posix()
    result = run_command(command_runner, ["git", "check-ignore", "--quiet", report_path], project_root)
    return {
        "name": "report_path_ignored_by_git",
        "passed": result.returncode == 0,
        "path": report_path,
    }


def run_probe_script(
    project_root: Path,
    command_runner: Callable[..., object] = subprocess.run,
) -> dict[str, object]:
    command = ["python", "scripts/probe_pdf_text.py"]
    result = run_command(command_runner, command, project_root)
    return {
        "name": "probe_script",
        "passed": result.returncode == 0,
        "command": " ".join(command),
    }


def run_unittest_discover(
    project_root: Path,
    command_runner: Callable[..., object] = subprocess.run,
) -> dict[str, object]:
    command = ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    result = run_command(command_runner, command, project_root)
    return {
        "name": "unittest_discover",
        "passed": result.returncode == 0,
        "command": " ".join(command),
    }


def collect_git_evidence(
    project_root: Path,
    command_runner: Callable[..., object] = subprocess.run,
) -> dict[str, str]:
    diff_stat = run_command(command_runner, ["git", "diff", "--stat"], project_root)
    status_short = run_command(command_runner, ["git", "status", "--short"], project_root)
    return {
        "git_diff_stat": (diff_stat.stdout or "").strip(),
        "git_status_short": (status_short.stdout or "").strip(),
    }


def run_command(
    command_runner: Callable[..., object], command: list[str], project_root: Path
) -> object:
    try:
        return command_runner(
            command, cwd=project_root, capture_output=True, text=True, check=False
        )
    except TypeError:
        return command_runner(command, cwd=project_root)


def build_verification(
    project_root: Path,
    command_runner: Callable[..., object] = subprocess.run,
) -> dict[str, object]:
    checks = [
        run_probe_script(project_root, command_runner=command_runner),
        run_unittest_discover(project_root, command_runner=command_runner),
        check_report_path_ignored(project_root, command_runner=command_runner),
    ]
    report = json.loads((project_root / REPORT_RELATIVE_PATH).read_text(encoding="utf-8"))
    summary = summarize_probe_report(report)
    git_evidence = collect_git_evidence(project_root, command_runner=command_runner)
    return {
        "checks": checks,
        "summary": summary,
        **git_evidence,
        "final_verification_passed": all(check["passed"] for check in checks)
        and not summary["text_content_fields_present"],
    }


def print_verification(verification: dict[str, object], stdout: TextIO) -> None:
    summary = verification["summary"]
    stdout.write(f"final_verification_passed: {str(verification['final_verification_passed']).lower()}\n")
    stdout.write(f"total_pdfs_processed: {summary['total_pdfs_processed']}\n")
    stdout.write(f"pdfs_with_extractable_text: {summary['pdfs_with_extractable_text']}\n")
    stdout.write(f"sample_size_distribution: {summary['sample_size_distribution']}\n")
    stdout.write(f"sampled_pages_by_quartile: {summary['sampled_pages_by_quartile']}\n")
    stdout.write(f"text_content_fields_present: {str(summary['text_content_fields_present']).lower()}\n")
    for check in verification["checks"]:
        stdout.write(f"check {check['name']}: {str(check['passed']).lower()}\n")
    stdout.write("git_diff_stat:\n")
    stdout.write(f"{verification['git_diff_stat']}\n")
    stdout.write("git_status_short:\n")
    stdout.write(f"{verification['git_status_short']}\n")


def main(
    argv: list[str] | None = None,
    command_runner: Callable[..., object] = subprocess.run,
    stdout: TextIO = sys.stdout,
) -> int:
    parser = argparse.ArgumentParser(description="Verify controlled PDF text probe locally.")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)

    verification = build_verification(args.project_root, command_runner=command_runner)
    print_verification(verification, stdout)
    return 0 if verification["final_verification_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
