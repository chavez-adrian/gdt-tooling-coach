"""Controlled PDF text probe helpers.

This module only plans deterministic page samples. It does not read, print,
store, or ingest PDF text.
"""

from __future__ import annotations

import math


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
    for quartile_index, quartile_size in enumerate(quartile_sizes, start=1):
        quartile_pages = list(range(next_page_index, next_page_index + quartile_size))
        quartiles[f"Q{quartile_index}"] = quartile_pages
        next_page_index += quartile_size

    return quartiles
