"""
Run SQL migrations against PostgreSQL/Neon.

Usage:
    python scripts/run_migrations.py

Behavior:
    - Loads DATABASE_URL from .env.
    - Creates schema_migrations table if missing.
    - Runs .sql files in db/migrations in lexical order.
    - Skips migrations already recorded.
    - Runs each migration in a transaction.
    - Applies .sql files in db/views after migrations.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = PROJECT_ROOT / "db" / "migrations"
VIEWS_DIR = PROJECT_ROOT / "db" / "views"


CREATE_SCHEMA_MIGRATIONS_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def load_database_url() -> str:
    """Load DATABASE_URL from .env or environment variables."""
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


def get_migration_files() -> list[Path]:
    """Return SQL migration files in lexical order."""
    if not MIGRATIONS_DIR.exists():
        raise RuntimeError(f"Migrations directory not found: {MIGRATIONS_DIR}")

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not migration_files:
        print(f"No migration files found in {MIGRATIONS_DIR}")

    return migration_files


def get_view_files() -> list[Path]:
    """Return SQL view files in lexical order."""
    if not VIEWS_DIR.exists():
        return []

    return sorted(VIEWS_DIR.glob("*.sql"))


def ensure_schema_migrations_table(conn: psycopg.Connection) -> None:
    """Ensure the migration tracking table exists."""
    with conn.cursor() as cur:
        cur.execute(CREATE_SCHEMA_MIGRATIONS_SQL)
    conn.commit()


def get_applied_migrations(conn: psycopg.Connection) -> set[str]:
    """Fetch already-applied migration versions."""
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations;")
        return {row[0] for row in cur.fetchall()}


def apply_migration(conn: psycopg.Connection, migration_file: Path) -> None:
    """Apply a single SQL migration and record it."""
    version = migration_file.name
    sql = migration_file.read_text(encoding="utf-8")

    print(f"Applying migration: {version}")

    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s);",
                    (version,),
                )
        print(f"Applied: {version}")
    except Exception:
        print(f"Failed migration: {version}", file=sys.stderr)
        raise


def apply_view(conn: psycopg.Connection, view_file: Path) -> None:
    """Apply or replace a SQL view."""
    sql = view_file.read_text(encoding="utf-8")
    print(f"Applying view: {view_file.name}")

    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(sql)
        print(f"Applied view: {view_file.name}")
    except Exception:
        print(f"Failed view: {view_file.name}", file=sys.stderr)
        raise


def main() -> int:
    """Run pending migrations."""
    try:
        database_url = load_database_url()
        migration_files = get_migration_files()

        with psycopg.connect(database_url) as conn:
            ensure_schema_migrations_table(conn)
            applied = get_applied_migrations(conn)

            pending = [file for file in migration_files if file.name not in applied]

            if not pending:
                print("No pending migrations.")
            else:
                for migration_file in pending:
                    apply_migration(conn, migration_file)

            for view_file in get_view_files():
                apply_view(conn, view_file)

        print("Migrations and views are up to date.")
        return 0

    except Exception as exc:
        print("Migration run failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
