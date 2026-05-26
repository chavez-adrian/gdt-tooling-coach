import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "data" / "concept_seed_manifest.example.json"
DEFAULT_OUTPUT_RELATIVE_PATH = Path("data/processed/concept_seed_dry_run.json")
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / DEFAULT_OUTPUT_RELATIVE_PATH
REQUIRED_FIELDS = {
    "concept_key",
    "preferred_label_en",
    "concept_type",
    "review_state",
    "source_authority_hint",
    "notes",
}
OPTIONAL_FIELDS = {"preferred_label_es"}
FORBIDDEN_DEFINITION_FIELDS = {
    "definition",
    "definition_en",
    "definition_es",
    "text",
    "snippet_text",
}
MAX_FIELD_WORDS = 24
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
        raise RuntimeError("DATABASE_URL is not set. Provide read-only Neon config.")
    return database_url


def fetch_existing_concepts(database_url, connect=psycopg.connect):
    with connect(database_url) as conn:
        cur = conn.cursor()
        cur.execute(SELECT_CONCEPTS_SQL)
        column_names = [column[0] for column in cur.description]
        return [dict(zip(column_names, row)) for row in cur.fetchall()]


def build_concept_seed_dry_run(manifest_concepts, existing_concepts):
    duplicate_keys = _duplicate_concept_keys(manifest_concepts)
    existing_keys = {
        concept.get("slug")
        for concept in existing_concepts
        if concept.get("slug")
    }
    block_reasons = Counter()
    blocked_details = []
    insertable_count = 0

    for index, concept in enumerate(manifest_concepts):
        reasons = _concept_block_reasons(concept)
        concept_key = concept.get("concept_key")
        if concept_key in duplicate_keys:
            reasons.append("duplicate_concept_key")
        if concept_key in existing_keys:
            reasons.append("concept_already_exists")
        if reasons:
            blocked_details.append({"concept_index": index, "concept_key": concept_key, "reasons": reasons})
            block_reasons.update(reasons)
        else:
            insertable_count += 1

    return {
        "total_manifest_concepts": len(manifest_concepts),
        "existing_concepts_count": len(existing_concepts),
        "insertable_concepts": insertable_count,
        "blocked_concepts": len(blocked_details),
        "block_reasons": dict(sorted(block_reasons.items())),
        "duplicate_keys": sorted(duplicate_keys),
        "blocked_concept_details": blocked_details,
        "no_database_writes": True,
        "contract": {
            "select_only": True,
            "database_writes": False,
            "database_modifications": False,
            "validated_content": False,
            "stores_text": False,
        },
    }


def write_report(report, output_path=DEFAULT_OUTPUT_PATH):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dry_run_report_is_ignored(run_command=subprocess.run):
    result = run_command(
        ["git", "check-ignore", DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def format_console_summary(report):
    return "\n".join(
        [
            "Concept seed dry-run complete.",
            f"Total manifest concepts: {report['total_manifest_concepts']}",
            f"Existing concepts count: {report['existing_concepts_count']}",
            f"Insertable concepts: {report['insertable_concepts']}",
            f"Blocked concepts: {report['blocked_concepts']}",
            f"Block reasons: {_format_key_counts(report.get('block_reasons', {}))}",
            f"Duplicate keys: {_format_list(report.get('duplicate_keys', []))}",
            "No database writes: true",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Prepare a SELECT-only dry-run report for concept seed insertion."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--database-url")
    parser.add_argument("--concepts-fixture", type=Path)
    parser.add_argument("--skip-ignore-check", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest = load_manifest(args.manifest)
        if args.concepts_fixture is None:
            concepts = fetch_existing_concepts(args.database_url or load_database_url())
        else:
            concepts = load_concepts_fixture(args.concepts_fixture)
        report = build_concept_seed_dry_run(manifest, concepts)
        write_report(report, args.output)
        if not args.skip_ignore_check and args.output == DEFAULT_OUTPUT_PATH and not dry_run_report_is_ignored():
            raise RuntimeError(f"{DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()} is not ignored by Git")
    except Exception as exc:
        print("Concept seed dry-run failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(report))
    return 0


def _concept_block_reasons(concept):
    reasons = []
    missing_required = [
        field
        for field in REQUIRED_FIELDS
        if concept.get(field) in (None, "")
    ]
    if missing_required:
        reasons.append("missing_required_field")
    if concept.get("review_state") != "needs_human_review":
        reasons.append("review_state_not_needs_human_review")
    if concept.get("review_state") == "validated" or concept.get("validated") is True:
        reasons.append("validated_state_not_allowed")
    if FORBIDDEN_DEFINITION_FIELDS.intersection(concept):
        reasons.append("definition_field_not_allowed")
    if _has_long_field(concept):
        reasons.append("content_too_long")
    return reasons


def _duplicate_concept_keys(concepts):
    counts = Counter(
        concept.get("concept_key")
        for concept in concepts
        if concept.get("concept_key") not in (None, "")
    )
    return {key for key, count in counts.items() if count > 1}


def _has_long_field(concept):
    for field, value in concept.items():
        if field in FORBIDDEN_DEFINITION_FIELDS:
            continue
        if isinstance(value, str) and len(value.split()) > MAX_FIELD_WORDS:
            return True
    return False


def _format_key_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def _format_list(values):
    if not values:
        return "none"
    return ", ".join(values)


if __name__ == "__main__":
    raise SystemExit(main())
