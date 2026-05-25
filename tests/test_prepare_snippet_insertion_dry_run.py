import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_snippet_insertion_dry_run import (
    DEFAULT_OUTPUT_RELATIVE_PATH,
    build_dry_run_report,
    dry_run_report_is_ignored,
    fetch_source_rows,
    format_console_summary,
    load_database_url,
    load_candidate_snippets,
    prepare_dry_run_report,
    write_dry_run_report,
)


class PrepareSnippetInsertionDryRunTests(unittest.TestCase):
    def test_loads_candidate_snippets_from_processed_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "candidate_snippets.json"
            report_path.write_text(
                json.dumps(
                    {
                        "candidate_snippets": [
                            {
                                "source_title": "ASME",
                                "source_type": "asme_2018_en",
                                "language": "en",
                                "expected_local_path": "data/raw/asme.pdf",
                                "page_number": 10,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            snippets = load_candidate_snippets(report_path)

        self.assertEqual(1, len(snippets))
        self.assertEqual("ASME", snippets[0]["source_title"])

    def test_report_blocks_snippets_when_no_source_matches(self):
        report = build_dry_run_report(
            [
                {
                    "source_title": "Unknown",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
            source_rows=[],
        )

        self.assertEqual(1, report["total_snippets"])
        self.assertEqual(0, report["insertable_snippets"])
        self.assertEqual(1, report["blocked_snippets"])
        self.assertEqual({"source_not_found": 1}, report["block_reasons"])
        self.assertEqual(
            {"matched_sources": 0, "unmatched_sources": 1},
            report["source_match_summary"],
        )

    def test_report_marks_snippets_insertable_when_source_matches(self):
        report = build_dry_run_report(
            [
                {
                    "source_title": "ASME",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
            source_rows=[
                {
                    "id": "source-1",
                    "title": "ASME",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
        )

        self.assertEqual(1, report["total_snippets"])
        self.assertEqual(1, report["insertable_snippets"])
        self.assertEqual(0, report["blocked_snippets"])
        self.assertEqual({}, report["block_reasons"])
        self.assertEqual(
            {"matched_sources": 1, "unmatched_sources": 0},
            report["source_match_summary"],
        )

    def test_report_blocks_snippets_longer_than_80_words(self):
        report = build_dry_run_report(
            [
                {
                    "source_title": "ASME",
                    "source_type": "asme_2018_en",
                    "language": "en",
                    "snippet_text": " ".join(f"word{i}" for i in range(81)),
                }
            ],
            source_rows=[
                {
                    "id": "source-1",
                    "title": "ASME",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
        )

        self.assertEqual(0, report["insertable_snippets"])
        self.assertEqual(1, report["blocked_snippets"])
        self.assertEqual({"snippet_too_long": 1}, report["block_reasons"])

    def test_report_blocks_snippets_with_validated_review_state(self):
        report = build_dry_run_report(
            [
                {
                    "source_title": "ASME",
                    "source_type": "asme_2018_en",
                    "language": "en",
                    "review_state": "validated",
                }
            ],
            source_rows=[
                {
                    "id": "source-1",
                    "title": "ASME",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
        )

        self.assertEqual(0, report["insertable_snippets"])
        self.assertEqual({"validated_review_state": 1}, report["block_reasons"])

    def test_report_declares_intended_unvalidated_literal_review_state(self):
        report = build_dry_run_report([], source_rows=[])

        self.assertEqual("raw_import", report["intended_review_state"])
        self.assertTrue(report["intended_requires_human_review"])
        self.assertFalse(report["intended_validated"])
        self.assertEqual("literal_quote", report["intended_extraction_type"])

    def test_writes_snippet_insertion_dry_run_report_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "snippet_insertion_dry_run.json"

            write_dry_run_report({"total_snippets": 0}, output_path)

            written_report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual({"total_snippets": 0}, written_report)

    def test_fetch_source_rows_uses_select_only_query(self):
        class FakeCursor:
            def __init__(self):
                self.sql = None
                self.description = [("id",), ("title",), ("source_type",), ("language",)]

            def execute(self, sql):
                self.sql = sql

            def fetchall(self):
                return [("source-1", "ASME", "asme_2018_en", "en")]

        class FakeConnection:
            def __init__(self):
                self.cursor_instance = FakeCursor()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def cursor(self):
                return self.cursor_instance

        fake_connection = FakeConnection()

        def fake_connect(database_url):
            self.assertEqual("postgresql://readonly", database_url)
            return fake_connection

        sources = fetch_source_rows("postgresql://readonly", connect=fake_connect)

        normalized_sql = " ".join(fake_connection.cursor_instance.sql.split()).lower()
        self.assertTrue(normalized_sql.startswith("select "))
        self.assertIn(" from sources", normalized_sql)
        self.assertNotRegex(normalized_sql, r"\b(insert|update|delete|create|drop|alter)\b")
        self.assertEqual(
            [
                {
                    "id": "source-1",
                    "title": "ASME",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
            sources,
        )

    def test_database_url_loader_fails_clearly_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing_env_path = Path(tmp_dir) / ".env"

            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL is not set"):
                load_database_url(env={}, env_path=missing_env_path)

    def test_prepares_dry_run_report_from_candidate_file_and_source_lookup(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "candidate_snippets.json"
            output_path = Path(tmp_dir) / "snippet_insertion_dry_run.json"
            input_path.write_text(
                json.dumps(
                    {
                        "candidate_snippets": [
                            {
                                "source_title": "ASME",
                                "source_type": "asme_2018_en",
                                "language": "en",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = prepare_dry_run_report(
                input_path=input_path,
                output_path=output_path,
                database_url="postgresql://readonly",
                source_fetcher=lambda database_url: [
                    {
                        "id": "source-1",
                        "title": "ASME",
                        "source_type": "asme_2018_en",
                        "language": "en",
                    }
                ],
            )

            written_report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report, written_report)
        self.assertEqual(1, written_report["insertable_snippets"])

    def test_console_summary_reports_counts_without_snippet_text(self):
        summary = format_console_summary(
            {
                "total_snippets": 2,
                "insertable_snippets": 1,
                "blocked_snippets": 1,
                "block_reasons": {"source_not_found": 1},
                "source_match_summary": {"matched_sources": 1, "unmatched_sources": 1},
            }
        )

        self.assertIn("Total snippets: 2", summary)
        self.assertIn("Insertable snippets: 1", summary)
        self.assertIn("Blocked snippets: 1", summary)
        self.assertIn("Block reasons: source_not_found=1", summary)
        self.assertIn("Source match summary: matched_sources=1, unmatched_sources=1", summary)
        self.assertIn("No database writes: true", summary)
        self.assertNotIn("snippet_text", summary)

    def test_cli_prints_metadata_only_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "candidate_snippets.json"
            output_path = Path(tmp_dir) / "snippet_insertion_dry_run.json"
            sources_path = Path(tmp_dir) / "sources.json"
            input_path.write_text(
                json.dumps({"candidate_snippets": []}),
                encoding="utf-8",
            )
            sources_path.write_text("[]", encoding="utf-8")

            result = subprocess.run(
                [
                    "python",
                    "scripts/prepare_snippet_insertion_dry_run.py",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                    "--database-url",
                    "postgresql://readonly",
                    "--sources-fixture",
                    str(sources_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Total snippets: 0", result.stdout)
        self.assertNotIn("snippet_text", result.stdout)

    def test_report_declares_no_database_writes_or_modifications(self):
        report = build_dry_run_report([], source_rows=[])

        self.assertEqual(
            {
                "database_writes": False,
                "database_modifications": False,
                "validated_content": False,
            },
            report["contract"],
        )

    def test_dry_run_report_path_is_checked_with_git_ignore(self):
        calls = []

        class Result:
            returncode = 0

        def fake_run(command, cwd, capture_output, text):
            calls.append((command, cwd, capture_output, text))
            return Result()

        self.assertTrue(dry_run_report_is_ignored(run_command=fake_run))
        self.assertEqual(
            ["git", "check-ignore", DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()],
            calls[0][0],
        )


if __name__ == "__main__":
    unittest.main()
