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
