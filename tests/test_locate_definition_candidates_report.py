import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.locate_definition_candidates import (
    build_definition_candidate_report,
    definition_candidate_report_is_ignored,
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

    def test_page_extraction_errors_do_not_store_text_or_stop_later_pages(self):
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
                            "title": "Mixed PDF",
                            "expected_local_path": "data/raw/source.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            bad_page = Mock()
            bad_page.extract_text.side_effect = RuntimeError("cannot extract page text")
            good_page = Mock()
            good_page.extract_text.return_value = "Definitions include datum references."

            with patch("scripts.locate_definition_candidates.PdfReader") as pdf_reader:
                pdf_reader.return_value.pages = [bad_page, good_page]
                report = build_definition_candidate_report(manifest_path, project_root)

        self.assertEqual(1, report["summary"]["page_extraction_errors"])
        self.assertEqual([2], [page["page_number"] for page in report["candidate_pages"]])
        self.assertNotIn("cannot extract", json.dumps(report))

    def test_generated_report_path_can_be_confirmed_as_git_ignored(self):
        calls = []

        def fake_runner(command, cwd):
            calls.append((command, cwd))
            return Mock(returncode=0)

        ignored = definition_candidate_report_is_ignored(
            Path("repo"),
            runner=fake_runner,
        )

        self.assertTrue(ignored)
        self.assertEqual(
            (
                [
                    "git",
                    "check-ignore",
                    "data/processed/definition_candidate_pages.json",
                ],
                Path("repo"),
            ),
            calls[0],
        )

    def test_report_declares_metadata_only_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            manifest_path = project_root / "manifest.json"
            manifest_path.write_text("[]", encoding="utf-8")

            report = build_definition_candidate_report(manifest_path, project_root)

        self.assertEqual(
            {
                "stores_full_page_text": False,
                "stores_definitions": False,
                "stores_long_quotes_or_samples": False,
                "performs_ocr": False,
                "connects_to_neon": False,
            },
            report["metadata_only_contract"],
        )

    def test_manifest_source_title_field_is_used_for_candidate_records(self):
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
                            "source_title": "Manifest Source Title",
                            "expected_local_path": "data/raw/source.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            page = Mock()
            page.extract_text.return_value = "Definitions include datum references."

            with patch("scripts.locate_definition_candidates.PdfReader") as pdf_reader:
                pdf_reader.return_value.pages = [page]
                report = build_definition_candidate_report(manifest_path, project_root)

        self.assertEqual(
            "Manifest Source Title",
            report["candidate_pages"][0]["source_title"],
        )


if __name__ == "__main__":
    unittest.main()
