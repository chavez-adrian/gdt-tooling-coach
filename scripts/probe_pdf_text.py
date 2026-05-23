"""Controlled PDF text probe helpers.

This module only plans deterministic page samples. It does not read, print,
store, or ingest PDF text.
"""

from __future__ import annotations

import math
import random

QUARTILE_NAMES = ("Q1", "Q2", "Q3", "Q4")


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


def build_sample_plan(page_count: int, random_seed: int) -> dict[str, object]:
    sample_size = calculate_sample_size(page_count)
    quartiles = divide_page_indexes_into_quartiles(page_count)
    sample_counts = allocate_sample_counts_by_quartile(sample_size)
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
