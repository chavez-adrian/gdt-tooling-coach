"""Build local PostgreSQL verification SQL for fake source-definition trace."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
VIEW_PATH = ROOT / "db" / "views" / "v_glossary_flat.sql"
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_source_definition_trace.sql"


VERIFY_QUERY = """
SELECT
  c.slug,
  src.title AS source_title,
  src.edition AS source_edition,
  src.language AS source_language,
  src.file_name,
  def.definition_type,
  def.extraction_type,
  def.word_count,
  def.is_literal,
  def.copyright_notes,
  def.review_status
FROM concepts c
JOIN definitions def
  ON def.concept_id = c.id
JOIN sources src
  ON src.id = def.source_id
WHERE c.slug = 'fake-source-definition-demo';
"""


def build_verification_sql() -> str:
    parts = [
        "-- Local fake source-definition trace verification SQL.",
        "-- Run against disposable PostgreSQL only; no Neon credentials required.",
        SCHEMA_PATH.read_text(encoding="utf-8"),
        VIEW_PATH.read_text(encoding="utf-8"),
        FIXTURE_PATH.read_text(encoding="utf-8"),
        VERIFY_QUERY.strip(),
    ]
    return "\n\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build local SQL proving fake source-to-definition traceability."
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
