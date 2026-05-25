import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "candidate_snippets.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "snippet_insertion_dry_run.json"
SELECT_SOURCES_SQL = """
SELECT id, title, source_type, language
FROM sources
ORDER BY title, source_type, language;
"""


def load_candidate_snippets(input_path=DEFAULT_INPUT_PATH):
    with open(input_path, "r", encoding="utf-8") as input_file:
        report = json.load(input_file)
    return report.get("candidate_snippets", [])


def load_database_url(env=os.environ, env_path=PROJECT_ROOT / ".env"):
    if env_path.exists():
        load_dotenv(env_path)
    database_url = env.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Provide read-only Neon config via .env or environment."
        )
    return database_url


def build_dry_run_report(snippets, source_rows):
    source_keys = {
        _source_key(source)
        for source in source_rows
    }
    matched_count = sum(1 for snippet in snippets if _source_key(snippet) in source_keys)
    blocked_count = len(snippets) - matched_count
    return {
        "total_snippets": len(snippets),
        "insertable_snippets": matched_count,
        "blocked_snippets": blocked_count,
        "block_reasons": {"source_not_found": blocked_count} if blocked_count else {},
        "source_match_summary": {
            "matched_sources": matched_count,
            "unmatched_sources": blocked_count,
        },
        "intended_review_state": "raw_import",
        "intended_requires_human_review": True,
        "intended_validated": False,
        "intended_extraction_type": "literal_quote",
    }


def _source_key(row):
    return (
        row.get("source_title") or row.get("title"),
        row.get("source_type"),
        row.get("language"),
    )


def write_dry_run_report(report, output_path=DEFAULT_OUTPUT_PATH):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(report, output_file, indent=2, sort_keys=True)
        output_file.write("\n")


def fetch_source_rows(database_url, connect=psycopg.connect):
    with connect(database_url) as conn:
        cur = conn.cursor()
        cur.execute(SELECT_SOURCES_SQL)
        column_names = [column[0] for column in cur.description]
        return [dict(zip(column_names, row)) for row in cur.fetchall()]
