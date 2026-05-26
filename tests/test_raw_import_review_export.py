import csv
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.export_raw_import_review import (
    CSV_FIELDS,
    format_console_summary as format_export_summary,
    summarize_export,
    write_review_export,
)
from scripts.verify_raw_import_review_export import (
    format_console_summary as format_verify_summary,
    verify_review_export,
)


def export_row(**overrides):
    row = {
        "definition_id": "definition-1",
        "concept_key": "datum",
        "source_title": "ASME Y14.5",
        "source_type": "asme_2018_en",
        "language": "en",
        "page_number": "12",
        "matched_signal": "datum",
        "extraction_type": "literal_quote",
        "word_count": "3",
        "definition_text": "literal review text should not appear in console",
        "import_fingerprint": "fingerprint-1",
        "review_status": "raw_import",
        "requires_human_review": "true",
        "validated": "false",
        "review_recommendation": "",
        "reviewer_notes": "",
    }
    row.update(overrides)
    return row


class RawImportReviewExportTests(unittest.TestCase):
    def test_write_review_export_creates_csv_with_review_columns(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "raw_import_review_export.csv"
            write_review_export([export_row()], output_path)
            with output_path.open("r", encoding="utf-8", newline="") as csv_file:
                rows = list(csv.DictReader(csv_file))

        self.assertEqual(CSV_FIELDS, list(rows[0].keys()))
        self.assertEqual("raw_import", rows[0]["review_status"])
        self.assertEqual("", rows[0]["review_recommendation"])
        self.assertEqual("", rows[0]["reviewer_notes"])
        self.assertEqual("literal review text should not appear in console", rows[0]["definition_text"])

    def test_export_summary_reports_counts_without_printing_definition_text(self):
        summary = summarize_export(
            [
                export_row(),
                export_row(
                    definition_id="definition-2",
                    concept_key="maximum_material_condition",
                    source_type="asme_2009_es",
                    language="es",
                    import_fingerprint="fingerprint-2",
                ),
            ],
            "data/processed/raw_import_review_export.csv",
        )
        output = format_export_summary(summary)

        self.assertEqual(2, summary["rows_exported"])
        self.assertIn("datum=1", output)
        self.assertIn("maximum_material_condition=1", output)
        self.assertNotIn("literal review text", output)
        self.assertNotIn("definition_text", output)
        self.assertIn("No database writes: true", output)

    def test_verify_review_export_accepts_safe_expected_export(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_path = Path(tmp_dir) / "raw_import_review_export.csv"
            rows = [
                export_row(),
                export_row(definition_id="definition-2", import_fingerprint="fingerprint-2"),
            ]
            write_review_export(rows, export_path)
            result = verify_review_export(
                rows,
                export_path=export_path,
                expected_rows=2,
                check_ignore_func=lambda _path: True,
            )

        self.assertTrue(result["passed"])
        self.assertTrue(result["all_raw_import"])
        self.assertTrue(result["all_require_human_review"])
        self.assertTrue(result["none_validated"])
        self.assertEqual([], result["duplicate_import_fingerprints"])

    def test_verify_review_export_rejects_validated_or_duplicate_rows(self):
        result = verify_review_export(
            [
                export_row(validated="true"),
                export_row(definition_id="definition-2", import_fingerprint="fingerprint-1"),
            ],
            export_path=Path("data/processed/raw_import_review_export.csv"),
            expected_rows=2,
            check_ignore_func=lambda _path: True,
        )

        self.assertFalse(result["passed"])
        self.assertFalse(result["none_validated"])
        self.assertEqual(["fingerprint-1"], result["duplicate_import_fingerprints"])

    def test_verify_summary_does_not_print_definition_text(self):
        result = verify_review_export(
            [export_row()],
            export_path=Path("data/processed/raw_import_review_export.csv"),
            expected_rows=1,
            check_ignore_func=lambda _path: True,
        )
        output = format_verify_summary(result)

        self.assertIn("Rows: 1", output)
        self.assertNotIn("literal review text", output)
        self.assertNotIn("definition_text", output)

    def test_cli_fails_when_export_is_not_git_ignored_without_printing_text(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_path = Path(tmp_dir) / "raw_import_review_export.csv"
            write_review_export([export_row()], export_path)
            result = subprocess.run(
                [
                    "python",
                    "scripts/verify_raw_import_review_export.py",
                    "--export",
                    str(export_path),
                    "--expected-rows",
                    "1",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("Git ignored: false", result.stdout)
        self.assertNotIn("literal review text", result.stdout)


if __name__ == "__main__":
    unittest.main()
