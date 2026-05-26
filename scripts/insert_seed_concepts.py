import argparse
import json
import os
import sys
from collections import Counter
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
FORBIDDEN_DEFINITION_FIELDS = {
    "definition",
    "definition_en",
    "definition_es",
    "text",
    "snippet_text",
}
MAX_FIELD_WORDS = 24


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
    duplicate_keys = _duplicate_concept_keys(manifest_concepts)
    existing_keys = {
        concept.get("slug")
        for concept in existing_concepts
        if concept.get("slug")
    }
    rows = []
    blocked_details = []
    block_reasons = Counter()

    for index, concept in enumerate(manifest_concepts):
        reasons = _concept_block_reasons(concept)
        concept_key = concept.get("concept_key")
        if concept_key in duplicate_keys:
            reasons.append("duplicate_concept_key")
        if concept_key in existing_keys:
            reasons.append("concept_already_exists")
        if reasons:
            blocked_details.append(
                {
                    "concept_index": index,
                    "concept_key": concept_key,
                    "reasons": reasons,
                }
            )
            block_reasons.update(reasons)
            continue
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
        "block_reasons": dict(sorted(block_reasons.items())),
        "duplicate_keys": sorted(duplicate_keys),
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
            f"Block reasons: {_format_key_counts(result.get('block_reasons', {}))}",
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


def _concept_block_reasons(concept):
    reasons = []
    if concept.get("review_state") != "needs_human_review":
        reasons.append("review_state_not_needs_human_review")
    if concept.get("review_state") == "validated" or concept.get("validated") is True:
        reasons.append("validated_state_not_allowed")
    if FORBIDDEN_DEFINITION_FIELDS.intersection(concept):
        reasons.append("definition_field_not_allowed")
    if _has_long_field(concept):
        reasons.append("content_too_long")
    return reasons


def _has_long_field(concept):
    for field, value in concept.items():
        if field in FORBIDDEN_DEFINITION_FIELDS:
            continue
        if isinstance(value, str) and len(value.split()) > MAX_FIELD_WORDS:
            return True
    return False


def _duplicate_concept_keys(concepts):
    counts = Counter(
        concept.get("concept_key")
        for concept in concepts
        if concept.get("concept_key") not in (None, "")
    )
    return {key for key, count in counts.items() if count > 1}


def _format_key_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


if __name__ == "__main__":
    raise SystemExit(main())
