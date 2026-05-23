"""Build local PostgreSQL verification SQL for fake tooling example."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
VIEW_PATH = ROOT / "db" / "views" / "v_glossary_flat.sql"
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_tooling_example.sql"


REVIEW_QUERY = """
-- Review/export inspection output.
SELECT
  c.slug,
  te.tool_component,
  te.example_text,
  te.when_to_use,
  te.when_not_to_use,
  te.inspection_method,
  te.cost_warning,
  te.review_status
FROM concepts c
JOIN tooling_examples te
  ON te.concept_id = c.id
WHERE c.slug = 'fake-deep-drawing-die-demo';
"""


def build_verification_sql() -> str:
    parts = [
        "-- Local fake tooling example verification SQL.",
        "-- Run against disposable PostgreSQL only; no Neon credentials required.",
        SCHEMA_PATH.read_text(encoding="utf-8"),
        VIEW_PATH.read_text(encoding="utf-8"),
        FIXTURE_PATH.read_text(encoding="utf-8"),
        REVIEW_QUERY.strip(),
    ]
    return "\n\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build local SQL proving fake tooling example review output."
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
