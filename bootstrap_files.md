# Bootstrap files for `gdt-tooling-coach`

Este documento contiene los archivos iniciales recomendados para el repo. La migración SQL ya quedó definida como `db/migrations/001_initial_schema.sql`.

---

## `README.md`

```md
# gdt-tooling-coach

Knowledge base for an adaptive GD&T learning system focused on design, manufacture, inspection, and cost-conscious specification of sheet-metal deep-drawing dies.

The project stores a structured bilingual GD&T glossary and learning dataset in PostgreSQL/Neon. It is not a user-facing application yet.

## Purpose

Build a relational database that supports:

- GD&T concept glossary
- ASME Y14.5-2018 English terms and current technical authority
- ASME Y14.5-2009 Spanish normative terminology and Spanish definitions
- AAMC International course terminology and review-question patterns
- GD&T symbols with Unicode/SVG/text fallback logic
- version comparison between ASME 2009 and 2018
- tooling examples for deep-drawing dies
- future adaptive learning exercises

## Source hierarchy

1. **ASME Y14.5-2018 English**  
   Current technical authority.

2. **ASME Y14.5-2009 Spanish**  
   Primary Spanish normative language source, unless 2018 changed the concept significantly.

3. **AAMC International course PDFs**  
   Pedagogical source for course explanations, review questions, and learning patterns.

## Editorial rules

- Do not invent internal Peltre Nacional terminology.
- Train users to use ASME/AAMC terminology in Spanish and English.
- Literal quotes are allowed up to **80 continuous words** only when pedagogically useful.
- Long sections, full tables, figures, and extended examples must not be reproduced.
- Use faithful paraphrase when direct quotation is not necessary.
- For definitions with clauses/incisos, cover each clause with brief quote and/or faithful paraphrase.
- Unicode symbols are preferred; if unreliable, use SVG; if unavailable, use text fallback.

## Tech stack

- PostgreSQL on Neon
- Python scripts
- `psycopg`
- `python-dotenv`
- SQL migrations

## Repo structure

```text
gdt-tooling-coach/
  AGENTS.md
  README.md
  .env.example
  requirements.txt
  /docs
    project_spec.md
    editorial_rules.md
    data_model.md
    ingestion_plan.md
  /db
    /migrations
      001_initial_schema.sql
    /views
      v_glossary_flat.sql
  /scripts
    check_connection.py
    run_migrations.py
    ingest_sources.py
    extract_definitions.py
    compare_versions.py
  /data
    /raw
      /asme_2018
      /asme_2009_es
      /aamc_course
    /processed
  /tests
```

## Quick start

### 1. Create virtual environment

```bash
python -m venv .venv
```

Activate it:

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

Copy:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and add the Neon connection string.

### 4. Check database connection

```bash
python scripts/check_connection.py
```

### 5. Run migrations

```bash
python scripts/run_migrations.py
```

## Important

Do not commit `.env` or real database credentials.

Do not ingest source documents until the schema has been created and reviewed.
```

---

## `.env.example`

```bash
# Copy this file to .env and replace the placeholder with your Neon connection string.
# Do not commit .env to version control.

DATABASE_URL="postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require"
```

---

## `requirements.txt`

```txt
psycopg[binary]>=3.2.0
python-dotenv>=1.0.1
```

---

## `scripts/check_connection.py`

```python
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
```

---

## `scripts/run_migrations.py`

```python
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
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = PROJECT_ROOT / "db" / "migrations"


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
                return 0

            for migration_file in pending:
                apply_migration(conn, migration_file)

        print("All pending migrations applied.")
        return 0

    except Exception as exc:
        print("Migration run failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## Recommended `.gitignore`

```gitignore
# Environment
.env
.venv/

# Python
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/

# OS / editors
.DS_Store
Thumbs.db
.vscode/
.idea/

# Data outputs
data/processed/
*.sqlite
*.db

# Secrets / credentials
*.pem
*.key
```

---

## Next Codex task

After creating these files, ask Codex to:

```text
Create the repo structure exactly as specified. Add the files from bootstrap_files.md. Place the existing migration as db/migrations/001_initial_schema.sql. Do not ingest PDFs yet. Then run Python lint-style sanity checks and explain how to run the connection and migration scripts locally.
```

