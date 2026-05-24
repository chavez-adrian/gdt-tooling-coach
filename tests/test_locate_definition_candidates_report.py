import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.locate_definition_candidates import build_definition_candidate_report


class DefinitionCandidateReportTests(unittest.TestCase):
    def test_missing_manifest_pdf_produces_no_candidate_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            manifest_path = project_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "Missing Source",
                            "expected_local_path": "data/raw/missing.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            report = build_definition_candidate_report(manifest_path, project_root)

        self.assertEqual([], report["candidate_pages"])
        self.assertEqual(1, report["summary"]["total_sources"])
        self.assertEqual(0, report["summary"]["existing_pdfs"])
        self.assertEqual(1, report["summary"]["missing_pdfs"])

    def test_existing_pdf_emits_candidate_page_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            pdf_path = project_root / "data/raw/source.pdf"
            pdf_path.parent.mkdir(parents=True)
            pdf_path.write_bytes(b"%PDF fake")
            manifest_path = project_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "ASME Fake",
                            "expected_local_path": "data/raw/source.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            page = Mock()
            page.extract_text.return_value = "Definitions include MMC and datum references."

            with patch("scripts.locate_definition_candidates.PdfReader") as pdf_reader:
                pdf_reader.return_value.pages = [page]
                report = build_definition_candidate_report(manifest_path, project_root)

        self.assertEqual(1, report["summary"]["existing_pdfs"])
        self.assertEqual(1, len(report["candidate_pages"]))
        self.assertEqual(
            {
                "source_title": "ASME Fake",
                "expected_local_path": "data/raw/source.pdf",
                "page_number": 1,
                "matched_signals": ["definitions", "datum", "MMC"],
                "signal_count": 3,
                "approximate_char_count": 45,
                "approximate_word_count": 6,
                "candidate_reason": (
                    "matched 3 definition candidate signals: definitions, datum, MMC"
                ),
            },
            report["candidate_pages"][0],
        )


if __name__ == "__main__":
    unittest.main()
