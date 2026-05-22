"""Build local PostgreSQL verification SQL for fake concept changes."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_concept_change.sql"


REVIEW_QUERY = """
-- Equivalent concept-change review output.
SELECT
  c.slug,
  cc.change_type,
  cc.change_summary,
  cc.impact_for_learning,
  cc.impact_for_tooling,
  cc.review_status,
  s2009.title AS source_2009_title,
  s2018.title AS source_2018_title
FROM concepts c
JOIN concept_changes cc
  ON cc.concept_id = c.id
LEFT JOIN sources s2009
  ON s2009.id = cc.source_2009_id
LEFT JOIN sources s2018
  ON s2018.id = cc.source_2018_id
WHERE c.slug = 'fake-concept-changed-meaning';
"""


ACCEPTANCE_QUERY = """
-- Acceptance checks for issue #8.
SELECT
  EXISTS (
    SELECT 1
    FROM concepts c
    JOIN concept_changes cc
      ON cc.concept_id = c.id
    WHERE c.slug = 'fake-concept-changed-meaning'
      AND cc.change_type = 'changed_meaning'
  ) AS has_changed_meaning_case,
  EXISTS (
    SELECT 1
    FROM concepts c
    JOIN concept_changes cc
      ON cc.concept_id = c.id
    WHERE c.slug = 'fake-concept-no-significant-change'
      AND cc.change_type = 'no_significant_change'
  ) AS has_no_significant_change_case,
  NOT EXISTS (
    SELECT 1
    FROM concept_changes
    WHERE review_status = 'validated'
  ) AS default_review_status_is_unvalidated,
  NOT EXISTS (
    SELECT 1
    FROM concept_changes
    WHERE source_2009_id IS NULL
  ) AS source_2009_linked,
  NOT EXISTS (
    SELECT 1
    FROM concept_changes
    WHERE source_2018_id IS NULL
  ) AS source_2018_linked;
"""


def build_verification_sql() -> str:
    parts = [
        "-- Local fake concept-change verification SQL.",
        "-- Run against disposable PostgreSQL only; no Neon credentials required.",
        SCHEMA_PATH.read_text(encoding="utf-8"),
        FIXTURE_PATH.read_text(encoding="utf-8"),
        REVIEW_QUERY.strip(),
        ACCEPTANCE_QUERY.strip(),
    ]
    return "\n\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build local SQL proving fake concept-change reviewability."
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print verification SQL to stdout.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the generated verification SQL.",
    )
    args = parser.parse_args()

    sql = build_verification_sql()

    if args.output:
        args.output.write_text(sql, encoding="utf-8")

    if args.print or not args.output:
        print(sql, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
