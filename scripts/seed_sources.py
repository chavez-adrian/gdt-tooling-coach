"""Seed initial source metadata without ingesting protected content."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SourceSeed:
    source_type: str
    title: str
    edition: str | None
    language: str
    notes: str


INITIAL_SOURCES = (
    SourceSeed(
        source_type="asme_2018_en",
        title="ASME Y14.5-2018 English",
        edition="2018",
        language="en",
        notes="Initial source metadata only; no normative content ingested.",
    ),
    SourceSeed(
        source_type="asme_2009_es",
        title="ASME Y14.5-2009 Español",
        edition="2009",
        language="es",
        notes="Initial source metadata only; no normative content ingested.",
    ),
    SourceSeed(
        source_type="aamc_course",
        title="Módulo 0 Contenido del curso básico",
        edition=None,
        language="es",
        notes="Initial AAMC course module metadata only; no questions ingested.",
    ),
    SourceSeed(
        source_type="aamc_course",
        title="Módulo 1 Dimensionamiento y tolerancias",
        edition=None,
        language="es",
        notes="Initial AAMC course module metadata only; no questions ingested.",
    ),
    SourceSeed(
        source_type="aamc_course",
        title="Módulo 2 Definiciones dentro de las GD&T",
        edition=None,
        language="es",
        notes="Initial AAMC course module metadata only; no questions ingested.",
    ),
    SourceSeed(
        source_type="aamc_course",
        title="Módulo 3 Tolerancias de forma",
        edition=None,
        language="es",
        notes="Initial AAMC course module metadata only; no questions ingested.",
    ),
    SourceSeed(
        source_type="aamc_course",
        title="Módulo 4 Tolerancias de orientación y datum de referencia",
        edition=None,
        language="es",
        notes="Initial AAMC course module metadata only; no questions ingested.",
    ),
    SourceSeed(
        source_type="aamc_course",
        title="Módulo 5 Tolerancias de perfil",
        edition=None,
        language="es",
        notes="Initial AAMC course module metadata only; no questions ingested.",
    ),
    SourceSeed(
        source_type="aamc_course",
        title="Módulo 6 Tolerancias de localización",
        edition=None,
        language="es",
        notes="Initial AAMC course module metadata only; no questions ingested.",
    ),
    SourceSeed(
        source_type="aamc_course",
        title="Módulo 7 Tolerancia de cabeceo",
        edition=None,
        language="es",
        notes="Initial AAMC course module metadata only; no questions ingested.",
    ),
)


SOURCE_EXISTS_SQL = """
SELECT 1
FROM sources
WHERE source_type = %s
  AND title = %s
  AND language = %s
  AND edition IS NOT DISTINCT FROM %s
LIMIT 1;
"""


INSERT_SOURCE_SQL = """
INSERT INTO sources (
  source_type,
  title,
  edition,
  language,
  notes
)
VALUES (%s, %s, %s, %s, %s);
"""


TOTAL_SOURCES_SQL = "SELECT COUNT(*) FROM sources;"


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


def seed_sources(database_url: str) -> tuple[int, int, int]:
    inserted = 0
    existing = 0

    with psycopg.connect(database_url) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                for source in INITIAL_SOURCES:
                    key_params = (
                        source.source_type,
                        source.title,
                        source.language,
                        source.edition,
                    )
                    cur.execute(SOURCE_EXISTS_SQL, key_params)

                    if cur.fetchone():
                        existing += 1
                        continue

                    cur.execute(
                        INSERT_SOURCE_SQL,
                        (
                            source.source_type,
                            source.title,
                            source.edition,
                            source.language,
                            source.notes,
                        ),
                    )
                    inserted += 1

                cur.execute(TOTAL_SOURCES_SQL)
                total_sources = cur.fetchone()[0]

    return inserted, existing, total_sources


def main() -> int:
    try:
        database_url = load_database_url()
        inserted, existing, total_sources = seed_sources(database_url)
    except Exception as exc:
        print("Source seeding failed.", file=sys.stderr)
        print(f"Error type: {type(exc).__name__}", file=sys.stderr)
        return 1

    print("Source seed complete.")
    print(f"Inserted sources: {inserted}")
    print(f"Already existing sources: {existing}")
    print(f"Total sources: {total_sources}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
