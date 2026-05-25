import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "candidate_snippets.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "snippet_insertion_dry_run.json"
DEFAULT_OUTPUT_RELATIVE_PATH = Path("data/processed/snippet_insertion_dry_run.json")
SELECT_SOURCES_SQL = """
SELECT id, title, source_type, language
FROM sources
ORDER BY title, source_type, language;
"""


def load_candidate_snippets(input_path=DEFAULT_INPUT_PATH):
    with open(input_path, "r", encoding="utf-8") as input_file:
        report = json.load(input_file)
    return report.get("candidate_snippets", [])


def load_source_rows_fixture(source_rows_path):
    with open(source_rows_path, "r", encoding="utf-8") as source_rows_file:
        return json.load(source_rows_file)


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
    block_reasons = {}
    matched_count = 0
    blocked_count = 0
    for snippet in snippets:
        reasons = []
        if _source_key(snippet) not in source_keys:
            reasons.append("source_not_found")
        if _word_count(snippet.get("snippet_text", "")) > 80:
            reasons.append("snippet_too_long")
        if reasons:
            blocked_count += 1
            for reason in reasons:
                block_reasons[reason] = block_reasons.get(reason, 0) + 1
        else:
            matched_count += 1
    return {
        "total_snippets": len(snippets),
        "insertable_snippets": matched_count,
        "blocked_snippets": blocked_count,
        "block_reasons": block_reasons,
        "source_match_summary": {
            "matched_sources": matched_count,
            "unmatched_sources": blocked_count,
        },
        "intended_review_state": "raw_import",
        "intended_requires_human_review": True,
        "intended_validated": False,
        "intended_extraction_type": "literal_quote",
        "contract": {
            "database_writes": False,
            "database_modifications": False,
            "validated_content": False,
        },
    }


def _source_key(row):
    return (
        row.get("source_title") or row.get("title"),
        row.get("source_type"),
        row.get("language"),
    )


def _word_count(text):
    return len(str(text).split())


def write_dry_run_report(report, output_path=DEFAULT_OUTPUT_PATH):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(report, output_file, indent=2, sort_keys=True)
        output_file.write("\n")


def dry_run_report_is_ignored(run_command=subprocess.run):
    result = run_command(
        ["git", "check-ignore", DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def fetch_source_rows(database_url, connect=psycopg.connect):
    with connect(database_url) as conn:
        cur = conn.cursor()
        cur.execute(SELECT_SOURCES_SQL)
        column_names = [column[0] for column in cur.description]
        return [dict(zip(column_names, row)) for row in cur.fetchall()]


def prepare_dry_run_report(
    input_path=DEFAULT_INPUT_PATH,
    output_path=DEFAULT_OUTPUT_PATH,
    database_url=None,
    source_fetcher=fetch_source_rows,
):
    resolved_database_url = database_url or load_database_url()
    snippets = load_candidate_snippets(input_path)
    source_rows = source_fetcher(resolved_database_url)
    report = build_dry_run_report(snippets, source_rows)
    write_dry_run_report(report, output_path)
    return report


def format_console_summary(report):
    block_reasons = _format_key_counts(report.get("block_reasons", {}))
    source_match_summary = _format_key_counts(report.get("source_match_summary", {}))
    return "\n".join(
        [
            "Snippet insertion dry-run complete.",
            f"Total snippets: {report['total_snippets']}",
            f"Insertable snippets: {report['insertable_snippets']}",
            f"Blocked snippets: {report['blocked_snippets']}",
            f"Block reasons: {block_reasons}",
            f"Source match summary: {source_match_summary}",
            "No database writes: true",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Prepare a local dry-run report for candidate snippet insertion."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--database-url")
    parser.add_argument(
        "--sources-fixture",
        type=Path,
        help="Use a local JSON source-row fixture instead of live Neon SELECT.",
    )
    args = parser.parse_args(argv)

    try:
        source_fetcher = fetch_source_rows
        if args.sources_fixture is not None:
            source_fetcher = lambda database_url: load_source_rows_fixture(args.sources_fixture)
        report = prepare_dry_run_report(
            input_path=args.input,
            output_path=args.output,
            database_url=args.database_url,
            source_fetcher=source_fetcher,
        )
    except Exception as exc:
        print("Snippet insertion dry-run failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(report))
    return 0


def _format_key_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


if __name__ == "__main__":
    raise SystemExit(main())
