"""Inspect the live PostgreSQL/Neon schema without modifying the database."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

KEY_TABLES = (
    "sources",
    "concepts",
    "terms",
    "definitions",
    "symbols",
    "concept_changes",
    "tooling_examples",
    "course_question_patterns",
    "adaptive_exercises",
    "review_events",
)

PUBLIC_TABLES_SQL = """
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
"""

PUBLIC_VIEWS_SQL = """
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public'
ORDER BY table_name;
"""

COLUMN_COUNTS_SQL = """
SELECT table_name, COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;
"""

APPLIED_MIGRATIONS_SQL = """
SELECT version, applied_at
FROM schema_migrations
ORDER BY applied_at, version;
"""


def load_database_url() -> str:
    env_path = PROJECT_ROOT / ".env"

    if env_path.exists():
        load_dotenv(env_path)
    else:
        print("Warning: .env file not found. Falling back to environment variables.")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Create a .env file based on .env.example."
        )

    return database_url


def fetch_single_column(cur: psycopg.Cursor[Any], sql: str) -> list[str]:
    cur.execute(sql)
    return [row[0] for row in cur.fetchall()]


def inspect_schema(database_url: str) -> tuple[int, list[str]]:
    output: list[str] = []

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database();")
            database_name = cur.fetchone()[0]

            public_tables = fetch_single_column(cur, PUBLIC_TABLES_SQL)
            public_views = fetch_single_column(cur, PUBLIC_VIEWS_SQL)

            cur.execute(COLUMN_COUNTS_SQL)
            column_counts = [(row[0], row[1]) for row in cur.fetchall()]

            has_schema_migrations = "schema_migrations" in public_tables
            has_glossary_view = "v_glossary_flat" in public_views
            missing_tables = [
                table_name for table_name in KEY_TABLES if table_name not in public_tables
            ]

            applied_migrations: list[tuple[str, Any]] = []
            if has_schema_migrations:
                cur.execute(APPLIED_MIGRATIONS_SQL)
                applied_migrations = [(row[0], row[1]) for row in cur.fetchall()]

    output.append(f"Database: {database_name}")
    output.append("")
    output.append("Public tables:")
    output.extend(f"- {table_name}" for table_name in public_tables)
    output.append("")
    output.append("Public views:")
    output.extend(f"- {view_name}" for view_name in public_views)
    output.append("")
    output.append("Column counts:")
    output.extend(f"- {table_name}: {column_count}" for table_name, column_count in column_counts)
    output.append("")
    output.append(f"schema_migrations exists: {'yes' if has_schema_migrations else 'no'}")
    output.append("Applied migrations:")
    if applied_migrations:
        output.extend(f"- {version} ({applied_at})" for version, applied_at in applied_migrations)
    else:
        output.append("- none")
    output.append("")
    output.append(f"v_glossary_flat exists: {'yes' if has_glossary_view else 'no'}")
    output.append("Key table check:")
    if missing_tables:
        output.extend(f"- missing: {table_name}" for table_name in missing_tables)
    else:
        output.append("- all key tables present")

    return 1 if missing_tables or not has_schema_migrations or not has_glossary_view else 0, output


def main() -> int:
    try:
        database_url = load_database_url()
        exit_code, output = inspect_schema(database_url)
    except Exception as exc:
        print("Schema inspection failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    for line in output:
        print(line)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
