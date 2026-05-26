import argparse
import sys

import psycopg

try:
    from prepare_snippet_insertion_dry_run import load_database_url
except ModuleNotFoundError:
    from scripts.prepare_snippet_insertion_dry_run import load_database_url


EXPECTED_TOTAL = 100

POST_INSERT_VERIFICATION_SQL = """
WITH candidate_definitions AS (
  SELECT
    id,
    concept_id,
    source_id,
    definition_type,
    word_count,
    extraction_type,
    review_status,
    import_fingerprint,
    notes::jsonb AS notes_json
  FROM definitions
  WHERE definition_type = 'candidate_snippet'
    AND import_fingerprint IS NOT NULL
)
SELECT
  COUNT(*) AS definitions_inserted,
  COUNT(*) FILTER (WHERE review_status = 'raw_import') AS raw_import_count,
  COUNT(*) FILTER (WHERE notes_json ->> 'requires_human_review' = 'true') AS requires_human_review_count,
  COUNT(*) FILTER (WHERE notes_json ->> 'validated' = 'false') AS validated_false_count,
  COUNT(*) FILTER (WHERE extraction_type = 'literal_quote') AS literal_quote_count,
  COUNT(*) FILTER (WHERE word_count <= 80) AS word_count_within_limit,
  COUNT(*) FILTER (WHERE source_id IS NOT NULL) AS source_id_present,
  COUNT(*) FILTER (WHERE concept_id IS NOT NULL) AS concept_id_present,
  COUNT(*) FILTER (WHERE import_fingerprint IS NOT NULL) AS import_fingerprint_present,
  (
    SELECT COUNT(*)
    FROM (
      SELECT import_fingerprint
      FROM candidate_definitions
      GROUP BY import_fingerprint
      HAVING COUNT(*) > 1
    ) duplicate_fingerprints
  ) AS duplicate_import_fingerprint_count
FROM candidate_definitions;
"""


def fetch_post_insert_metrics(database_url, connect=psycopg.connect):
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(POST_INSERT_VERIFICATION_SQL)
            row = cur.fetchone()
    return _row_to_metrics(row)


def verify_post_insert_metrics(metrics, expected_total=EXPECTED_TOTAL):
    checks = {
        "definitions_inserted": metrics.get("definitions_inserted") == expected_total,
        "review_state_raw_import": metrics.get("raw_import_count") == expected_total,
        "requires_human_review_true": metrics.get("requires_human_review_count") == expected_total,
        "validated_false": metrics.get("validated_false_count") == expected_total,
        "extraction_type_literal_quote": metrics.get("literal_quote_count") == expected_total,
        "word_count_within_limit": metrics.get("word_count_within_limit") == expected_total,
        "source_id_present": metrics.get("source_id_present") == expected_total,
        "concept_id_present": metrics.get("concept_id_present") == expected_total,
        "import_fingerprint_present": metrics.get("import_fingerprint_present") == expected_total,
        "duplicate_import_fingerprint_count": metrics.get("duplicate_import_fingerprint_count") == 0,
    }
    return {
        "passed": all(checks.values()),
        "expected_total": expected_total,
        "checks": checks,
        **metrics,
        "no_database_writes": True,
        "definition_text_printed": False,
        "snippet_text_printed": False,
    }


def format_console_summary(result):
    return "\n".join(
        [
            "Inserted candidate snippet verification complete.",
            f"Passed: {str(result['passed']).lower()}",
            f"Definitions inserted: {result['definitions_inserted']}",
            f"Review state raw_import: {result['raw_import_count']}",
            f"Requires human review true: {result['requires_human_review_count']}",
            f"Validated false: {result['validated_false_count']}",
            f"Extraction type literal_quote: {result['literal_quote_count']}",
            f"Word count <= 80: {result['word_count_within_limit']}",
            f"Source id present: {result['source_id_present']}",
            f"Concept id present: {result['concept_id_present']}",
            f"Import fingerprint present: {result['import_fingerprint_present']}",
            f"Duplicate import fingerprint count: {result['duplicate_import_fingerprint_count']}",
            f"No database writes: {str(result['no_database_writes']).lower()}",
            "Definition text printed: false",
            "Snippet text printed: false",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify inserted candidate snippets with SELECT-only aggregate checks."
    )
    parser.add_argument("--database-url")
    parser.add_argument("--expected-total", type=int, default=EXPECTED_TOTAL)
    args = parser.parse_args(argv)

    try:
        database_url = args.database_url or load_database_url()
        metrics = fetch_post_insert_metrics(database_url)
        result = verify_post_insert_metrics(metrics, expected_total=args.expected_total)
    except Exception as exc:
        print("Inserted candidate snippet verification failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(result))
    return 0 if result["passed"] else 1


def _row_to_metrics(row):
    keys = [
        "definitions_inserted",
        "raw_import_count",
        "requires_human_review_count",
        "validated_false_count",
        "literal_quote_count",
        "word_count_within_limit",
        "source_id_present",
        "concept_id_present",
        "import_fingerprint_present",
        "duplicate_import_fingerprint_count",
    ]
    return {key: int(value or 0) for key, value in zip(keys, row)}


if __name__ == "__main__":
    raise SystemExit(main())
