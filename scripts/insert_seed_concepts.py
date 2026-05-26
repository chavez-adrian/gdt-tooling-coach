import argparse
import json
import os
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "concept_seed_manifest.example.json"
SELECT_CONCEPTS_SQL = """
SELECT id, slug, category, current_status
FROM concepts
ORDER BY slug;
"""


def load_manifest(manifest_path=DEFAULT_MANIFEST_PATH):
    return json.loads(Path(manifest_path).read_text(encoding="utf-8"))


def load_concepts_fixture(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_database_url(env=os.environ, env_path=PROJECT_ROOT / ".env"):
    if env_path.exists():
        load_dotenv(env_path)
    database_url = env.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set. Provide Neon config.")
    return database_url


def fetch_existing_concepts(database_url, connect=psycopg.connect):
    with connect(database_url) as conn:
        cur = conn.cursor()
        cur.execute(SELECT_CONCEPTS_SQL)
        column_names = [column[0] for column in cur.description]
        return [dict(zip(column_names, row)) for row in cur.fetchall()]


def build_insertion_plan(manifest_concepts, existing_concepts, execute=False):
    rows = []
    blocked_details = []

    for index, concept in enumerate(manifest_concepts):
        rows.append(
            {
                "concept_index": index,
                "slug": concept["concept_key"],
                "category": concept["concept_type"],
                "notes": concept.get("notes", ""),
            }
        )

    return {
        "mode": "execute" if execute else "dry-run",
        "execute_requested": execute,
        "database_writes_attempted": False,
        "total_manifest_concepts": len(manifest_concepts),
        "ready_to_insert": len(rows),
        "blocked_concepts": len(blocked_details),
        "blocked_concept_details": blocked_details,
        "inserted_concepts": 0,
        "insertion_rows": rows,
        "existing_concepts_count": len(existing_concepts),
    }


def format_console_summary(result):
    return "\n".join(
        [
            "Approved concept seed insertion gate complete.",
            f"Mode: {result['mode']}",
            f"Total manifest concepts: {result['total_manifest_concepts']}",
            f"Ready to insert: {result['ready_to_insert']}",
            f"Blocked concepts: {result['blocked_concepts']}",
            f"Inserted concepts: {result.get('inserted_concepts', 0)}",
            f"Database writes attempted: {str(result['database_writes_attempted']).lower()}",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Gate approved concept seed insertion behind an explicit approval flag."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--database-url")
    parser.add_argument(
        "--concepts-fixture",
        type=Path,
        help="Use a local JSON concept-row fixture instead of live Neon SELECT.",
    )
    parser.add_argument("--execute-approved-insert", action="store_true")
    args = parser.parse_args(argv)

    try:
        database_url = args.database_url or load_database_url()
        manifest = load_manifest(args.manifest)
        if args.concepts_fixture is None:
            existing_concepts = fetch_existing_concepts(database_url)
        else:
            existing_concepts = load_concepts_fixture(args.concepts_fixture)
        result = build_insertion_plan(
            manifest,
            existing_concepts,
            execute=args.execute_approved_insert,
        )
    except Exception as exc:
        print("Approved concept seed insertion gate failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
