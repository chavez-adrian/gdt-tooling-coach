import json
import tempfile
import unittest
from pathlib import Path

from scripts.extract_candidate_snippets import (
    DEFAULT_INPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    candidate_snippets_report_is_ignored,
    build_candidate_snippets_from_ranked_candidates,
    enrich_candidates_from_manifest,
    format_console_summary,
    load_high_priority_ranked_candidates,
    write_candidate_snippets_report,
)


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakePdfReader:
    opened_paths = []

    def __init__(self, path):
        self.opened_paths.append(str(path))
        self.pages = [
            FakePage("This first page should not be read."),
            FakePage("A datum is a theoretically exact reference."),
        ]


class DenseFakePdfReader:
    def __init__(self, path):
        self.pages = [
            FakePage(
                "First datum sentence. "
                "Second datum sentence. "
                "Third datum sentence. "
                "Fourth datum sentence."
            )
        ]


class ExtractCandidateSnippetsReportTests(unittest.TestCase):
    def test_ranked_report_reader_filters_high_priority_candidates_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            ranked_path = Path(tmp_dir) / "ranked_definition_candidates.json"
            ranked_path.write_text(
                json.dumps(
                    {
                        "ranked_candidates": [
                            {"source_title": "High", "priority_bucket": "high"},
                            {"source_title": "Medium", "priority_bucket": "medium"},
                            {"source_title": "Low", "priority_bucket": "low"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            candidates = load_high_priority_ranked_candidates(ranked_path)

        self.assertEqual(
            [{"source_title": "High", "priority_bucket": "high"}],
            candidates,
        )

    def test_high_candidate_opens_pdf_and_extracts_requested_page_text(self):
        FakePdfReader.opened_paths = []
        candidate = {
            "source_title": "ASME",
            "expected_local_path": "data/raw/asme.pdf",
            "page_number": 2,
            "priority_bucket": "high",
        }

        snippets = build_candidate_snippets_from_ranked_candidates(
            [candidate],
            pdf_reader_factory=FakePdfReader,
        )

        self.assertEqual(["data/raw/asme.pdf"], FakePdfReader.opened_paths)
        self.assertEqual(1, len(snippets))
        self.assertEqual("datum", snippets[0]["matched_signal"])
        self.assertEqual(
            "A datum is a theoretically exact reference.",
            snippets[0]["snippet_text"],
        )

    def test_report_rows_use_public_field_names(self):
        candidate = {
            "source_title": "ASME",
            "source_type": "standard",
            "language": "en",
            "source_path": "data/raw/asme.pdf",
            "page_number": 2,
            "candidate_score": 91,
            "global_rank": 1,
            "priority_bucket": "high",
        }

        snippets = build_candidate_snippets_from_ranked_candidates(
            [candidate],
            pdf_reader_factory=FakePdfReader,
        )

        self.assertEqual("en", snippets[0]["language"])
        self.assertEqual("data/raw/asme.pdf", snippets[0]["expected_local_path"])
        self.assertNotIn("source_language", snippets[0])
        self.assertNotIn("source_path", snippets[0])

    def test_report_rows_preserve_language_enriched_from_manifest(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            ranked_path = Path(tmp_dir) / "ranked_definition_candidates.json"
            output_path = Path(tmp_dir) / "candidate_snippets.json"
            manifest_path = Path(tmp_dir) / "source_manifest.example.json"
            ranked_path.write_text(
                json.dumps(
                    {
                        "ranked_candidates": [
                            {
                                "source_title": "ASME",
                                "page_number": 2,
                                "priority_bucket": "high",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(
                    [
                        {
                            "source_title": "ASME",
                            "source_type": "asme_2018_en",
                            "language": "en",
                            "expected_local_path": "data/raw/asme.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            report = write_candidate_snippets_report(
                ranked_path,
                output_path,
                pdf_reader_factory=FakePdfReader,
                manifest_path=manifest_path,
            )

        self.assertEqual("en", report["candidate_snippets"][0]["language"])

    def test_candidates_missing_pdf_metadata_are_enriched_from_manifest(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest_path = Path(tmp_dir) / "source_manifest.example.json"
            manifest_path.write_text(
                json.dumps(
                    [
                        {
                            "source_title": "ASME",
                            "source_type": "asme_2018_en",
                            "language": "en",
                            "expected_local_path": "data/raw/asme.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            enriched = enrich_candidates_from_manifest(
                [{"source_title": "ASME", "priority_bucket": "high"}],
                manifest_path=manifest_path,
            )

        self.assertEqual("data/raw/asme.pdf", enriched[0]["expected_local_path"])
        self.assertEqual("asme_2018_en", enriched[0]["source_type"])
        self.assertEqual("en", enriched[0]["language"])

    def test_missing_medium_and_low_candidates_do_not_open_or_extract_pages(self):
        def fail_if_called(path):
            raise AssertionError(f"unexpected PDF open: {path}")

        candidates = [
            {
                "source_title": "Missing Path",
                "page_number": 1,
                "priority_bucket": "high",
            },
            {
                "source_title": "Medium",
                "expected_local_path": "data/raw/medium.pdf",
                "page_number": 1,
                "priority_bucket": "medium",
            },
            {
                "source_title": "Low",
                "expected_local_path": "data/raw/low.pdf",
                "page_number": 1,
                "priority_bucket": "low",
            },
        ]

        snippets = build_candidate_snippets_from_ranked_candidates(
            candidates,
            pdf_reader_factory=fail_if_called,
        )

        self.assertEqual([], snippets)

    def test_json_writer_creates_candidate_snippets_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            ranked_path = Path(tmp_dir) / "ranked_definition_candidates.json"
            output_path = Path(tmp_dir) / "candidate_snippets.json"
            ranked_path.write_text(
                json.dumps(
                    {
                        "ranked_candidates": [
                            {
                                "source_title": "ASME",
                                "expected_local_path": "data/raw/asme.pdf",
                                "page_number": 2,
                                "priority_bucket": "high",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            manifest_path = Path(tmp_dir) / "source_manifest.example.json"
            manifest_path.write_text("[]", encoding="utf-8")

            report = write_candidate_snippets_report(
                ranked_path,
                output_path,
                pdf_reader_factory=FakePdfReader,
                manifest_path=manifest_path,
            )
            written_report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(report, written_report)
        self.assertEqual(1, len(written_report["candidate_snippets"]))
        self.assertEqual(
            "A datum is a theoretically exact reference.",
            written_report["candidate_snippets"][0]["snippet_text"],
        )

    def test_report_is_capped_at_100_snippets_total(self):
        candidates = [
            {
                "source_title": f"Source {index}",
                "expected_local_path": f"data/raw/source-{index}.pdf",
                "page_number": 1,
                "priority_bucket": "high",
            }
            for index in range(34)
        ]

        snippets = build_candidate_snippets_from_ranked_candidates(
            candidates,
            pdf_reader_factory=DenseFakePdfReader,
        )

        self.assertEqual(100, len(snippets))

    def test_cli_defaults_to_ranked_input_and_snippets_output_paths(self):
        self.assertEqual(
            Path("data/processed/ranked_definition_candidates.json"),
            DEFAULT_INPUT_PATH.relative_to(DEFAULT_INPUT_PATH.parents[2]),
        )
        self.assertEqual(
            Path("data/processed/candidate_snippets.json"),
            DEFAULT_OUTPUT_PATH.relative_to(DEFAULT_OUTPUT_PATH.parents[2]),
        )

    def test_candidate_snippets_report_path_is_checked_with_git_ignore(self):
        calls = []

        class Result:
            returncode = 0

        def fake_run(command, cwd, capture_output, text):
            calls.append((command, cwd, capture_output, text))
            return Result()

        self.assertTrue(candidate_snippets_report_is_ignored(run_command=fake_run))
        self.assertEqual(
            ["git", "check-ignore", "data/processed/candidate_snippets.json"],
            calls[0][0],
        )

    def test_written_report_declares_no_neon_or_database_modifications(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            ranked_path = Path(tmp_dir) / "ranked_definition_candidates.json"
            output_path = Path(tmp_dir) / "candidate_snippets.json"
            ranked_path.write_text(
                json.dumps({"ranked_candidates": []}),
                encoding="utf-8",
            )

            manifest_path = Path(tmp_dir) / "source_manifest.example.json"
            manifest_path.write_text("[]", encoding="utf-8")

            report = write_candidate_snippets_report(
                ranked_path,
                output_path,
                pdf_reader_factory=FakePdfReader,
                manifest_path=manifest_path,
            )

        self.assertEqual(
            {
                "neon_writes": False,
                "database_modifications": False,
                "validated_content": False,
            },
            report["contract"],
        )

    def test_console_summary_reports_snippet_count_and_contract(self):
        report = {
            "candidate_snippets": [{}, {}],
            "contract": {
                "neon_writes": False,
                "database_modifications": False,
                "validated_content": False,
            },
        }

        summary = format_console_summary(report)

        self.assertIn("Candidate snippets written: 2", summary)
        self.assertIn("Neon writes: false", summary)
        self.assertIn("Database modifications: false", summary)
        self.assertIn("Validated content: false", summary)


if __name__ == "__main__":
    unittest.main()
