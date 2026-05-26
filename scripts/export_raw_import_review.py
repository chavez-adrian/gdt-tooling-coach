import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

import psycopg

try:
    from prepare_snippet_insertion_dry_run import load_database_url
except ModuleNotFoundError:
    from scripts.prepare_snippet_insertion_dry_run import load_database_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "raw_import_review_export.csv"
CSV_FIELDS = [
    "definition_id",
    "concept_key",
    "source_title",
    "source_type",
    "language",
    "page_number",
    "matched_signal",
    "extraction_type",
    "word_count",
    "definition_text",
    "import_fingerprint",
    "review_status",
    "requires_human_review",
    "validated",
    "review_recommendation",
    "reviewer_notes",
]


RAW_IMPORT_REVIEW_SQL = """
SELECT
  d.id::text AS definition_id,
  c.slug AS concept_key,
  s.title AS source_title,
  s.source_type,
  s.language,
  d.notes::jsonb ->> 'page_number' AS page_number,
  d.notes::jsonb ->> 'matched_signal' AS matched_signal,
  d.extraction_type,
  d.word_count,
  d.text AS definition_text,
  d.import_fingerprint,
  d.review_status,
  d.notes::jsonb ->> 'requires_human_review' AS requires_human_review,
  d.notes::jsonb ->> 'validated' AS validated,
  '' AS review_recommendation,
  '' AS reviewer_notes
FROM definitions d
JOIN concepts c ON c.id = d.concept_id
JOIN sources s ON s.id = d.source_id
WHERE d.definition_type = 'candidate_snippet'
  AND d.review_status = 'raw_import'
  AND d.extraction_type = 'literal_quote'
  AND d.notes::jsonb ->> 'requires_human_review' = 'true'
  AND d.notes::jsonb ->> 'validated' = 'false'
  AND d.import_fingerprint IS NOT NULL
ORDER BY c.slug, s.source_type, (d.notes::jsonb ->> 'page_number')::integer, d.id;
"""


def fetch_raw_import_review_rows(database_url, connect=psycopg.connect):
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(RAW_IMPORT_REVIEW_SQL)
            rows = cur.fetchall()
    return [_row_to_export_record(row) for row in rows]


def write_review_export(rows, output_path=DEFAULT_OUTPUT_PATH):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    return output_path


def summarize_export(rows, output_path=DEFAULT_OUTPUT_PATH):
    return {
        "rows_exported": len(rows),
        "concepts_included": dict(sorted(Counter(row["concept_key"] for row in rows).items())),
        "sources_included": dict(
            sorted(
                Counter(
                    f"{row['source_title']}|{row['source_type']}|{row['language']}"
                    for row in rows
                ).items()
            )
        ),
        "output_path": str(Path(output_path).as_posix()),
        "no_database_writes": True,
        "definition_text_printed": False,
    }


def format_console_summary(summary):
    return "\n".join(
        [
            "Raw import review export complete.",
            f"Rows exported: {summary['rows_exported']}",
            f"Concepts included: {_format_key_counts(summary['concepts_included'])}",
            f"Sources included: {_format_key_counts(summary['sources_included'])}",
            f"Output file: {summary['output_path']}",
            f"No database writes: {str(summary['no_database_writes']).lower()}",
            "Definition text printed: false",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Export raw_import candidate definitions for human review."
    )
    parser.add_argument("--database-url")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args(argv)

    try:
        database_url = args.database_url or load_database_url()
        rows = fetch_raw_import_review_rows(database_url)
        write_review_export(rows, args.output)
        summary = summarize_export(rows, args.output)
    except Exception as exc:
        print("Raw import review export failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(summary))
    return 0


def _row_to_export_record(row):
    return {field: "" if value is None else str(value) for field, value in zip(CSV_FIELDS, row)}


def _format_key_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


if __name__ == "__main__":
    raise SystemExit(main())
