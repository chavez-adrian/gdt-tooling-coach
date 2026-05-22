"""Validate fake definition intake records without external services."""

from __future__ import annotations

import re


WORD_RE = re.compile(r"\b[\w'-]+\b")


def intake_fake_definition(*, text: str, extraction_type: str) -> dict[str, object]:
    return {
        "text": text,
        "extraction_type": extraction_type,
        "word_count": len(WORD_RE.findall(text)),
    }
