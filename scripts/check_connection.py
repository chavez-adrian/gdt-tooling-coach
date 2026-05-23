"""
Check PostgreSQL/Neon database connectivity.

Usage:
    python scripts/check_connection.py

Requires:
    DATABASE_URL in .env
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def load_environment() -> str:
    """Load DATABASE_URL from .env and return it."""
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"

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


def main() -> int:
    """Connect to PostgreSQL and print a safe connection confirmation."""
    try:
        database_url = load_environment()

        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_database(), current_user, version();")
                db_name, db_user, version = cur.fetchone()

        print("Connection successful.")
        print(f"Database: {db_name}")
        print(f"User: {db_user}")
        print(f"PostgreSQL: {version.split(',')[0]}")
        return 0

    except Exception as exc:
        print("Connection failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
