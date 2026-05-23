import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import probe_pdf_text


class ProbePdfTextReportTests(unittest.TestCase):
    def test_report_marks_manifest_pdf_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            manifest_path = project_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    [
                        {
                            "source_title": "Missing Source",
                            "expected_local_path": "data/raw/missing.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            report = probe_pdf_text.build_probe_report(
                project_root=project_root,
                manifest_path=manifest_path,
            )

        self.assertEqual(
            report,
            [
                {
                    "source_title": "Missing Source",
                    "expected_local_path": "data/raw/missing.pdf",
                    "page_count": 0,
                    "sample_size": 0,
                    "random_seed": probe_pdf_text.DEFAULT_RANDOM_SEED,
                    "sampled_page_numbers": [],
                    "sampled_page_indexes": [],
                    "sampled_pages_by_quartile": {
                        "Q1": [],
                        "Q2": [],
                        "Q3": [],
                        "Q4": [],
                    },
                    "extracted_char_count": 0,
                    "extracted_word_count": 0,
                    "pages_with_extractable_text": 0,
                    "has_extractable_text": False,
                    "extraction_status": "missing_pdf",
                }
            ],
        )

    def test_report_opens_existing_pdf_with_pypdf_and_records_page_count(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            pdf_path = project_root / "data" / "raw" / "fake.pdf"
            pdf_path.parent.mkdir(parents=True)
            pdf_path.write_bytes(b"%PDF fake")
            manifest_path = project_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    [
                        {
                            "source_title": "Existing Source",
                            "expected_local_path": "data/raw/fake.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            fake_reader = type("FakeReader", (), {"pages": [object(), object()]})()

            with patch("scripts.probe_pdf_text.PdfReader", return_value=fake_reader) as reader:
                report = probe_pdf_text.build_probe_report(
                    project_root=project_root,
                    manifest_path=manifest_path,
                )

        reader.assert_called_once_with(pdf_path)
        self.assertEqual(report[0]["page_count"], 2)
        self.assertEqual(report[0]["extraction_status"], "extracted")


if __name__ == "__main__":
    unittest.main()
