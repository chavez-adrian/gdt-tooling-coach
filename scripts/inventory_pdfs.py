"""Inventory local PDF files referenced by the source manifest.

This script records technical metadata only. It does not extract, print, store,
or OCR normative PDF content, and it does not connect to Neon.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "source_manifest.example.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "pdf_inventory.json"


@dataclass(frozen=True)
class PdfInspection:
    page_count: int | None
    has_extractable_text_sample: bool | None
    status: str


def load_manifest(manifest_path: Path = DEFAULT_MANIFEST_PATH) -> list[dict[str, Any]]:
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        manifest = json.load(manifest_file)

    if not isinstance(manifest, list):
        raise ValueError("Source manifest must be a JSON array.")

    return manifest


def calculate_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as pdf_file:
        for chunk in iter(lambda: pdf_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pdf_reader_class() -> Any | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None

    return PdfReader


def inspect_pdf_metadata(file_path: Path) -> PdfInspection:
    pdf_reader_class = load_pdf_reader_class()
    if pdf_reader_class is None:
        return PdfInspection(
            page_count=None,
            has_extractable_text_sample=None,
            status="pdf_library_unavailable",
        )

    try:
        reader = pdf_reader_class(str(file_path))
    except Exception:
        return PdfInspection(
            page_count=None,
            has_extractable_text_sample=None,
            status="unreadable_pdf",
        )

    try:
        page_count = len(reader.pages)
    except Exception:
        return PdfInspection(
            page_count=None,
            has_extractable_text_sample=None,
            status="page_count_failed",
        )

    try:
        has_text = has_extractable_text_sample(reader, page_count)
    except Exception:
        return PdfInspection(
            page_count=page_count,
            has_extractable_text_sample=None,
            status="text_probe_failed",
        )

    return PdfInspection(
        page_count=page_count,
        has_extractable_text_sample=has_text,
        status="present_ok",
    )


def has_extractable_text_sample(reader: Any, page_count: int, sample_pages: int = 3) -> bool:
    for page_index in range(min(page_count, sample_pages)):
        sample_text = reader.pages[page_index].extract_text() or ""
        if sample_text.strip():
            return True

    return False


def build_inventory(
    manifest: list[dict[str, Any]], project_root: Path = PROJECT_ROOT
) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []

    for entry in manifest:
        relative_path = entry["expected_local_path"]
        file_path = project_root / relative_path

        inventory_entry: dict[str, Any] = {
            "source_title": entry["source_title"],
            "expected_local_path": relative_path,
            "exists": file_path.is_file(),
            "file_size_bytes": None,
            "sha256": None,
            "page_count": None,
            "has_extractable_text_sample": None,
            "inventory_status": "missing",
        }

        if file_path.is_file():
            inspection = inspect_pdf_metadata(file_path)
            inventory_entry.update(
                {
                    "file_size_bytes": file_path.stat().st_size,
                    "sha256": calculate_sha256(file_path),
                    "page_count": inspection.page_count,
                    "has_extractable_text_sample": inspection.has_extractable_text_sample,
                    "inventory_status": inspection.status,
                }
            )

        inventory.append(inventory_entry)

    return inventory


def write_inventory(
    inventory: list[dict[str, Any]], output_path: Path = DEFAULT_OUTPUT_PATH
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_output(inventory: list[dict[str, Any]], output_path: Path) -> list[str]:
    present_count = sum(1 for entry in inventory if entry["exists"])
    missing_count = len(inventory) - present_count
    text_sample_count = sum(
        1 for entry in inventory if entry["has_extractable_text_sample"] is True
    )
    page_count_available = sum(1 for entry in inventory if entry["page_count"] is not None)
    status_counts = Counter(entry["inventory_status"] for entry in inventory)

    output = [
        "PDF inventory complete.",
        f"Manifest entries: {len(inventory)}",
        f"Present PDFs: {present_count}",
        f"Missing PDFs: {missing_count}",
        f"Page counts available: {page_count_available}",
        f"Extractable text samples detected: {text_sample_count}",
        "Inventory status counts:",
    ]
    output.extend(f"- {status}: {status_counts[status]}" for status in sorted(status_counts))
    output.append(
        f"Report written: {output_path.relative_to(PROJECT_ROOT)}",
    )
    return output


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory local PDF metadata without extracting content."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to source manifest JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to write the inventory JSON report.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or [])

    try:
        manifest = load_manifest(args.manifest)
        inventory = build_inventory(manifest)
        write_inventory(inventory, args.output)
    except Exception as exc:
        print("PDF inventory failed.", file=sys.stderr)
        print(f"Error type: {type(exc).__name__}", file=sys.stderr)
        return 1

    for line in build_output(inventory, args.output):
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
