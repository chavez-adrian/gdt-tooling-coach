"""Controlled PDF text probe helpers.

This module only plans deterministic page samples. It does not read, print,
store, or ingest PDF text.
"""

from __future__ import annotations

import math

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
