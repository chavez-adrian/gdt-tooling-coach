"""Build local PostgreSQL verification SQL for fake symbol fallback."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
VIEW_PATH = ROOT / "db" / "views" / "v_glossary_flat.sql"
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_symbol_fallback.sql"


FLAT_SYMBOL_QUERY = """
SELECT
  slug,
  unicode_symbol,
  unicode_reliable,
  svg_path,
  text_fallback
FROM v_glossary_flat
WHERE slug = 'fake-symbol-position-demo';
"""


ACCEPTANCE_CHECK_QUERY = """
-- Acceptance check: issue #9 fake symbol fallback.
SELECT
  EXISTS (
    SELECT 1
    FROM v_glossary_flat
    WHERE slug = 'fake-symbol-position-demo'
      AND unicode_symbol = '⌖'
      AND unicode_reliable = TRUE
      AND svg_path = 'M 4 12 H 20 M 12 4 V 20'
      AND text_fallback = 'position symbol'
  ) AS symbol_fallback_path_ok;
"""


def build_verification_sql() -> str:
    parts = [
        "-- Local fake symbol fallback verification SQL.",
        "-- Run against disposable PostgreSQL only; no Neon credentials required.",
        SCHEMA_PATH.read_text(encoding="utf-8"),
        VIEW_PATH.read_text(encoding="utf-8"),
        FIXTURE_PATH.read_text(encoding="utf-8"),
        FLAT_SYMBOL_QUERY.strip(),
        ACCEPTANCE_CHECK_QUERY.strip(),
    ]
    return "\n\n".join(parts) + "\n"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Build local SQL proving fake symbol fallback review output."
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
