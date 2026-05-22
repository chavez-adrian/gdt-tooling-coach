"""Build local PostgreSQL verification SQL for fake bilingual terminology."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
VIEW_PATH = ROOT / "db" / "views" / "v_glossary_flat.sql"
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_bilingual_terms.sql"


FLAT_REVIEW_QUERY = """
SELECT
  slug,
  asme_2018_english_term,
  english_abbreviation,
  asme_2009_spanish_term
FROM v_glossary_flat
WHERE slug = 'fake-bilingual-profile-demo';
"""


RELATIONAL_TERMS_QUERY = """
-- Relational source-of-truth output.
SELECT
  c.slug,
  t.language,
  t.source_type,
  t.term,
  t.abbreviation,
  t.is_primary
FROM concepts c
JOIN terms t
  ON t.concept_id = c.id
WHERE c.slug = 'fake-bilingual-profile-demo'
ORDER BY t.language;
"""


ACCEPTANCE_CHECK_QUERY = """
-- Acceptance check: issue #7 fake bilingual terminology.
SELECT
  EXISTS (
    SELECT 1
    FROM concepts c
    JOIN terms t ON t.concept_id = c.id
    WHERE c.slug = 'fake-bilingual-profile-demo'
      AND t.language = 'en'
      AND t.source_type = 'asme_2018_en'
      AND t.term = 'Fake profile control'
      AND t.is_primary = TRUE
  ) AS english_source_type_ok,
  EXISTS (
    SELECT 1
    FROM concepts c
    JOIN terms t ON t.concept_id = c.id
    WHERE c.slug = 'fake-bilingual-profile-demo'
      AND t.language = 'es'
      AND t.source_type = 'asme_2009_es'
      AND t.term = 'Control de perfil falso'
      AND t.is_primary = TRUE
  ) AS spanish_source_type_ok,
  EXISTS (
    SELECT 1
    FROM concepts c
    JOIN terms t ON t.concept_id = c.id
    WHERE c.slug = 'fake-bilingual-profile-demo'
      AND t.language = 'en'
      AND t.abbreviation = 'FPC'
  ) AS english_abbreviation_ok,
  EXISTS (
    SELECT 1
    FROM v_glossary_flat
    WHERE slug = 'fake-bilingual-profile-demo'
      AND asme_2018_english_term = 'Fake profile control'
      AND english_abbreviation = 'FPC'
      AND asme_2009_spanish_term = 'Control de perfil falso'
  ) AS flat_review_output_ok,
  EXISTS (
    SELECT 1
    FROM concepts c
    JOIN terms t ON t.concept_id = c.id
    WHERE c.slug = 'fake-bilingual-profile-demo'
  ) AS relational_source_of_truth_ok;
"""


def build_verification_sql() -> str:
    parts = [
        "-- Local fake bilingual terminology verification SQL.",
        "-- Run against disposable PostgreSQL only; no Neon credentials required.",
        SCHEMA_PATH.read_text(encoding="utf-8"),
        VIEW_PATH.read_text(encoding="utf-8"),
        FIXTURE_PATH.read_text(encoding="utf-8"),
        RELATIONAL_TERMS_QUERY.strip(),
        FLAT_REVIEW_QUERY.strip(),
        ACCEPTANCE_CHECK_QUERY.strip(),
    ]
    return "\n\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build local SQL proving fake bilingual term review output."
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
