import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.locate_definition_candidates import (
    build_definition_candidate_report,
    main,
    write_definition_candidate_report,
)


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

    def test_multiple_pages_include_only_candidate_pages(self):
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
            pages = [Mock(), Mock(), Mock()]
            pages[0].extract_text.return_value = "Practice problems only."
            pages[1].extract_text.return_value = "Glossary page for feature control frame."
            pages[2].extract_text.return_value = "Plain appendix index."

            with patch("scripts.locate_definition_candidates.PdfReader") as pdf_reader:
                pdf_reader.return_value.pages = pages
                report = build_definition_candidate_report(manifest_path, project_root)

        self.assertEqual(1, report["summary"]["candidate_pages"])
        self.assertEqual([2], [page["page_number"] for page in report["candidate_pages"]])
        self.assertEqual(
            ["glossary", "feature control frame"],
            report["candidate_pages"][0]["matched_signals"],
        )

    def test_no_match_pdf_produces_no_false_candidate_records(self):
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
                            "title": "No Match",
                            "expected_local_path": "data/raw/source.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            page = Mock()
            page.extract_text.return_value = "Practice problems and answer key only."

            with patch("scripts.locate_definition_candidates.PdfReader") as pdf_reader:
                pdf_reader.return_value.pages = [page]
                report = build_definition_candidate_report(manifest_path, project_root)

        self.assertEqual([], report["candidate_pages"])
        self.assertEqual(0, report["summary"]["candidate_pages"])
        self.assertEqual(1, report["summary"]["no_match_pdfs"])

    def test_writes_definition_candidate_report_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            manifest_path = project_root / "manifest.json"
            output_path = project_root / "data/processed/definition_candidate_pages.json"
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

            report = write_definition_candidate_report(
                manifest_path,
                output_path,
                project_root,
            )

            written_report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report, written_report)
        self.assertEqual([], written_report["candidate_pages"])

    def test_cli_defaults_to_manifest_and_processed_report_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            manifest_path = project_root / "data/source_manifest.example.json"
            manifest_path.parent.mkdir(parents=True)
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

            exit_code = main([], project_root=project_root)
            output_path = project_root / "data/processed/definition_candidate_pages.json"
            output_exists = output_path.exists()

        self.assertEqual(0, exit_code)
        self.assertTrue(output_exists)

    def test_pdf_open_errors_are_reported_without_candidate_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            pdf_path = project_root / "data/raw/bad.pdf"
            pdf_path.parent.mkdir(parents=True)
            pdf_path.write_bytes(b"not a pdf")
            manifest_path = project_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "Bad PDF",
                            "expected_local_path": "data/raw/bad.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            with patch("scripts.locate_definition_candidates.PdfReader") as pdf_reader:
                pdf_reader.side_effect = RuntimeError("cannot open")
                report = build_definition_candidate_report(manifest_path, project_root)

        self.assertEqual([], report["candidate_pages"])
        self.assertEqual(1, report["summary"]["pdf_open_errors"])
        self.assertEqual(
            [
                {
                    "source_title": "Bad PDF",
                    "expected_local_path": "data/raw/bad.pdf",
                    "status": "pdf_open_error",
                }
            ],
            report["source_statuses"],
        )


if __name__ == "__main__":
    unittest.main()
