import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.diagnose_concept_readiness import (
    build_concept_readiness_report,
    fetch_concept_rows,
    format_console_summary,
)


def snippet(**overrides):
    row = {
        "source_title": "ASME Y14.5-2018 English",
        "source_type": "asme_2018_en",
        "language": "en",
        "page_number": 12,
        "matched_signal": "datum",
        "snippet_text": "literal text must never print",
    }
    row.update(overrides)
    return row


class DiagnoseConceptReadinessTests(unittest.TestCase):
    def test_report_counts_missing_concepts_and_metadata_summaries_without_text(self):
        report = build_concept_readiness_report(
            [
                snippet(),
                snippet(matched_signal="MMC", page_number=15, concept_id="concept-1"),
            ],
            [
                {
                    "id": "concept-1",
                    "slug": "datum-asme-2018-en-page-12",
                    "category": "datum",
                    "subcategory": None,
                    "current_status": "needs_review",
                }
            ],
        )

        self.assertEqual(2, report["total_snippets"])
        self.assertEqual(1, report["missing_concept_id"])
        self.assertEqual(1, report["existing_concepts_count"])
        self.assertEqual({"datum": 1, "MMC": 1}, report["matched_signal_summary"])
        self.assertEqual(
            {"asme_2018_en|en": 2},
            report["source_summary"],
        )
        self.assertEqual(1, report["potential_existing_concept_matches"])
        self.assertEqual(1, report["unmatched_snippets_count"])
        self.assertNotIn("snippet_text", json.dumps(report))
        self.assertNotIn("literal text must never print", json.dumps(report))

    def test_report_summarizes_concepts_by_review_state_or_current_status(self):
        report = build_concept_readiness_report(
            [],
            [
                {"id": "1", "slug": "a", "current_status": "needs_review"},
                {"id": "2", "slug": "b", "review_state": "ready_for_mapping"},
            ],
        )

        self.assertEqual(
            {"needs_review": 1, "ready_for_mapping": 1},
            report["concepts_by_review_state"],
        )

    def test_console_summary_reports_counts_without_secrets_or_snippet_text(self):
        report = build_concept_readiness_report([snippet()], [])

        summary = format_console_summary(report)

        self.assertIn("Total snippets: 1", summary)
        self.assertIn("Missing concept_id: 1", summary)
        self.assertIn("Existing concepts count: 0", summary)
        self.assertNotIn("literal text must never print", summary)
        self.assertNotIn("DATABASE_URL", summary)
        self.assertNotIn("password", summary.lower())
        self.assertNotIn("token", summary.lower())

    def test_fetch_concepts_uses_select_only_query(self):
        class FakeCursor:
            description = [
                ("id",),
                ("slug",),
                ("category",),
                ("subcategory",),
                ("current_status",),
            ]

            def __init__(self):
                self.sql = None

            def execute(self, sql):
                self.sql = sql

            def fetchall(self):
                return [("concept-1", "datum", "datum", None, "needs_review")]

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
        rows = fetch_concept_rows("postgresql://readonly", connect=lambda _url: fake_connection)

        normalized_sql = " ".join(fake_connection.cursor_instance.sql.split()).lower()
        self.assertTrue(normalized_sql.startswith("select "))
        self.assertIn(" from concepts", normalized_sql)
        self.assertNotRegex(normalized_sql, r"\b(insert|update|delete|create|drop|alter)\b")
        self.assertEqual("datum", rows[0]["slug"])

    def test_cli_writes_ignored_metadata_report_with_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            snippets_path = Path(tmp_dir) / "candidate_snippets.json"
            concepts_path = Path(tmp_dir) / "concepts.json"
            output_path = Path(tmp_dir) / "concept_readiness_report.json"
            snippets_path.write_text(
                json.dumps({"candidate_snippets": [snippet()]}),
                encoding="utf-8",
            )
            concepts_path.write_text("[]", encoding="utf-8")

            result = subprocess.run(
                [
                    "python",
                    "scripts/diagnose_concept_readiness.py",
                    "--input",
                    str(snippets_path),
                    "--concepts-fixture",
                    str(concepts_path),
                    "--output",
                    str(output_path),
                    "--skip-ignore-check",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Missing concept_id: 1", result.stdout)
        self.assertEqual(1, written["total_snippets"])
        self.assertNotIn("snippet_text", json.dumps(written))


if __name__ == "__main__":
    unittest.main()
