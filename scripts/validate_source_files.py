"""Validate local source file presence without reading or ingesting file content."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "source_manifest.example.json"
REQUIRED_FIELDS = {
    "source_title",
    "source_type",
    "language",
    "expected_local_path",
    "required",
    "notes",
}


@dataclass(frozen=True)
class SourceFileStatus:
    source_title: str
    expected_local_path: str
    required: bool
    present: bool


def load_manifest(manifest_path: Path = DEFAULT_MANIFEST_PATH) -> list[dict[str, Any]]:
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    if not isinstance(manifest, list):
        raise ValueError("Source manifest must be a JSON array.")

    return manifest


def validate_manifest_entries(
    manifest: list[dict[str, Any]], project_root: Path = PROJECT_ROOT
) -> list[str]:
    errors: list[str] = []

    for index, entry in enumerate(manifest, start=1):
        if not isinstance(entry, dict):
            errors.append(f"Entry {index} must be a JSON object.")
            continue

        missing_fields = sorted(REQUIRED_FIELDS - set(entry))
        if missing_fields:
            errors.append(f"Entry {index} missing fields: {', '.join(missing_fields)}")
            continue

        if not isinstance(entry["required"], bool):
            errors.append(f"Entry {index} required must be a boolean.")

        expected_path = entry["expected_local_path"]
        if not isinstance(expected_path, str) or not expected_path:
            errors.append(f"Entry {index} expected_local_path must be a non-empty string.")
            continue

        if Path(expected_path).is_absolute():
            errors.append(f"Entry {index} expected_local_path must be relative.")
            continue

        resolved_path = (project_root / expected_path).resolve()
        raw_root = (project_root / "data" / "raw").resolve()
        if not resolved_path.is_relative_to(raw_root):
            errors.append(f"Entry {index} expected_local_path must be inside data/raw/.")

    return errors


def inspect_source_files(
    manifest: list[dict[str, Any]], project_root: Path = PROJECT_ROOT
) -> list[SourceFileStatus]:
    statuses: list[SourceFileStatus] = []

    for entry in manifest:
        relative_path = entry["expected_local_path"]
        file_path = project_root / relative_path
        statuses.append(
            SourceFileStatus(
                source_title=entry["source_title"],
                expected_local_path=relative_path,
                required=entry["required"],
                present=file_path.is_file(),
            )
        )

    return statuses


def build_output(statuses: list[SourceFileStatus]) -> list[str]:
    present_count = sum(1 for status in statuses if status.present)
    missing_statuses = [status for status in statuses if not status.present]

    output = [
        "Source file validation complete.",
        f"Manifest entries: {len(statuses)}",
        f"Present files: {present_count}",
        f"Missing files: {len(missing_statuses)}",
        "",
        "File status:",
    ]

    for status in statuses:
        state = "present" if status.present else "missing"
        required = "required" if status.required else "optional"
        output.append(
            f"- {state}: {status.source_title} ({required}) -> {status.expected_local_path}"
        )

    return output


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate expected local source files without ingesting content."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to source manifest JSON.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or [])

    try:
        manifest = load_manifest(args.manifest)
        errors = validate_manifest_entries(manifest)
        if errors:
            print("Source manifest validation failed.", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

        statuses = inspect_source_files(manifest)
    except Exception as exc:
        print("Source file validation failed.", file=sys.stderr)
        print(f"Error type: {type(exc).__name__}", file=sys.stderr)
        return 1

    for line in build_output(statuses):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
