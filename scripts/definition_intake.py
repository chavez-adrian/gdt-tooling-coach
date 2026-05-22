"""Validate fake definition intake records without external services."""

from __future__ import annotations

import re


WORD_RE = re.compile(r"\b[\w'-]+\b")


class DefinitionIntakeError(ValueError):
    pass


def intake_fake_definition(*, text: str, extraction_type: str) -> dict[str, object]:
    word_count = len(WORD_RE.findall(text))
    if extraction_type == "literal_quote" and word_count > 80:
        raise DefinitionIntakeError("literal fake quotes must be 80 words or fewer")

    return {
        "text": text,
        "extraction_type": extraction_type,
        "word_count": word_count,
    }
