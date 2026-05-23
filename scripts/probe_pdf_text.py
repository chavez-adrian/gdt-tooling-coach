"""Controlled PDF text probe helpers.

This module only plans deterministic page samples. It does not read, print,
store, or ingest PDF text.
"""

from __future__ import annotations

import math
import json
import random
from pathlib import Path

from pypdf import PdfReader

QUARTILE_NAMES = ("Q1", "Q2", "Q3", "Q4")
DEFAULT_RANDOM_SEED = 20260523


def calculate_sample_size(page_count: int) -> int:
    if page_count <= 4:
        return page_count
    return min(max(math.ceil(page_count * 0.10), 4), 25)


def divide_page_indexes_into_quartiles(page_count: int) -> dict[str, list[int]]:
    quartile_sizes = [page_count // 4] * 4
    for index in range(page_count % 4):
        quartile_sizes[index] += 1

    quartiles: dict[str, list[int]] = {}
    next_page_index = 0
    for quartile_name, quartile_size in zip(QUARTILE_NAMES, quartile_sizes):
        quartile_pages = list(range(next_page_index, next_page_index + quartile_size))
        quartiles[quartile_name] = quartile_pages
        next_page_index += quartile_size

    return quartiles


def allocate_sample_counts_by_quartile(sample_size: int) -> dict[str, int]:
    base_per_quartile = sample_size // 4
    remainder = sample_size % 4

    return {
        quartile_name: base_per_quartile + (1 if index < remainder else 0)
        for index, quartile_name in enumerate(QUARTILE_NAMES)
    }


def redistribute_sample_counts(
    quartiles: dict[str, list[int]], requested_counts: dict[str, int]
) -> dict[str, int]:
    sample_counts = requested_counts.copy()
    shortfall = 0

    for quartile_name in QUARTILE_NAMES:
        available_count = len(quartiles[quartile_name])
        if sample_counts[quartile_name] > available_count:
            shortfall += sample_counts[quartile_name] - available_count
            sample_counts[quartile_name] = available_count

    while shortfall:
        redistributed = False
        for quartile_name in QUARTILE_NAMES:
            if sample_counts[quartile_name] < len(quartiles[quartile_name]):
                sample_counts[quartile_name] += 1
                shortfall -= 1
                redistributed = True
                if shortfall == 0:
                    break
        if not redistributed:
            break

    return sample_counts


def build_sample_plan(
    page_count: int, random_seed: int = DEFAULT_RANDOM_SEED
) -> dict[str, object]:
    sample_size = calculate_sample_size(page_count)
    quartiles = divide_page_indexes_into_quartiles(page_count)
    sample_counts = redistribute_sample_counts(
        quartiles, allocate_sample_counts_by_quartile(sample_size)
    )
    rng = random.Random(random_seed)
    sampled_pages_by_quartile = {
        quartile_name: sorted(
            rng.sample(quartiles[quartile_name], sample_counts[quartile_name])
        )
        for quartile_name in QUARTILE_NAMES
    }
    sampled_page_indexes = sorted(
        page_index
        for pages in sampled_pages_by_quartile.values()
        for page_index in pages
    )

    return {
        "page_count": page_count,
        "sample_size": sample_size,
        "random_seed": random_seed,
        "sampled_page_indexes": sampled_page_indexes,
        "sampled_page_numbers": [page_index + 1 for page_index in sampled_page_indexes],
        "sampled_pages_by_quartile": sampled_pages_by_quartile,
    }


def build_probe_report(
    project_root: Path,
    manifest_path: Path,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, object]]:
    manifest_entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    report_entries: list[dict[str, object]] = []

    for manifest_entry in manifest_entries:
        expected_local_path = manifest_entry["expected_local_path"]
        pdf_path = project_root / expected_local_path
        if not pdf_path.exists():
            report_entries.append(
                {
                    "source_title": manifest_entry["source_title"],
                    "expected_local_path": expected_local_path,
                    "page_count": 0,
                    "sample_size": 0,
                    "random_seed": random_seed,
                    "sampled_page_numbers": [],
                    "sampled_page_indexes": [],
                    "sampled_pages_by_quartile": {name: [] for name in QUARTILE_NAMES},
                    "extracted_char_count": 0,
                    "extracted_word_count": 0,
                    "pages_with_extractable_text": 0,
                    "has_extractable_text": False,
                    "extraction_status": "missing_pdf",
                }
            )
            continue

        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        sample_plan = build_sample_plan(page_count, random_seed=random_seed)
        extracted_texts = [
            reader.pages[page_index].extract_text() or ""
            for page_index in sample_plan["sampled_page_indexes"]
        ]
        extractable_texts = [text for text in extracted_texts if text]
        extraction_status = "extracted" if extractable_texts else "no_extractable_text"
        report_entries.append(
            {
                "source_title": manifest_entry["source_title"],
                "expected_local_path": expected_local_path,
                "page_count": page_count,
                "sample_size": sample_plan["sample_size"],
                "random_seed": sample_plan["random_seed"],
                "sampled_page_numbers": sample_plan["sampled_page_numbers"],
                "sampled_page_indexes": sample_plan["sampled_page_indexes"],
                "sampled_pages_by_quartile": sample_plan["sampled_pages_by_quartile"],
                "extracted_char_count": sum(len(text) for text in extractable_texts),
                "extracted_word_count": sum(
                    len(text.split()) for text in extractable_texts
                ),
                "pages_with_extractable_text": len(extractable_texts),
                "has_extractable_text": bool(extractable_texts),
                "extraction_status": extraction_status,
            }
        )

    return report_entries
