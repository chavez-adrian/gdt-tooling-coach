"""Build local PostgreSQL verification SQL for fake adaptive exercise."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_adaptive_exercise.sql"


TRACEABILITY_QUERY = """
-- Traceability output: fake adaptive exercise lineage.
SELECT
  ae.exercise_prompt AS adaptive_exercise_prompt,
  ae.exercise_status,
  ae.review_status,
  cqp.question_pattern,
  src.title AS source_title,
  src.source_type,
  c.slug AS concept_slug
FROM adaptive_exercises ae
JOIN course_question_patterns cqp
  ON cqp.id = ae.question_pattern_id
JOIN sources src
  ON src.id = cqp.source_id
JOIN concepts c
  ON c.id = cqp.concept_id
WHERE c.slug = 'fake-course-question-datum-target';
"""


def build_verification_sql() -> str:
    parts = [
        "-- Local fake adaptive exercise verification SQL.",
        "-- Run against disposable PostgreSQL only; no Neon credentials required.",
        SCHEMA_PATH.read_text(encoding="utf-8"),
        FIXTURE_PATH.read_text(encoding="utf-8"),
        TRACEABILITY_QUERY.strip(),
    ]
    return "\n\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build local SQL proving fake adaptive exercise traceability."
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
