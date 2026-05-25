import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.verify_snippet_coverage import main, summarize_snippet_coverage


class VerifySnippetCoverageTest(unittest.TestCase):
    def test_counts_high_priority_candidates_from_ranked_report(self):
        ranked_report = {
            "ranked_candidates": [
                {"priority_bucket": "high"},
                {"priority_bucket": "medium"},
                {"priority_bucket": "high"},
            ]
        }

        summary = summarize_snippet_coverage(ranked_report, {"candidate_snippets": []})

        self.assertEqual(2, summary["high_priority_candidates_total"])

    def test_counts_unique_high_priority_pages_from_ranked_report(self):
        ranked_report = {
            "ranked_candidates": [
                {"priority_bucket": "high", "source_title": "ASME", "page_number": 10},
                {"priority_bucket": "high", "source_title": "ASME", "page_number": 10},
                {"priority_bucket": "high", "source_title": "AAMC", "page_number": 10},
                {"priority_bucket": "low", "source_title": "AAMC", "page_number": 11},
            ]
        }

        summary = summarize_snippet_coverage(ranked_report, {"candidate_snippets": []})

        self.assertEqual(2, summary["unique_high_priority_pages_total"])

    def test_counts_snippets_total_and_snippets_by_source(self):
        snippet_report = {
            "candidate_snippets": [
                {"source_title": "ASME"},
                {"source_title": "AAMC"},
                {"source_title": "ASME"},
            ]
        }

        summary = summarize_snippet_coverage({"ranked_candidates": []}, snippet_report)

        self.assertEqual(3, summary["snippets_total"])
        self.assertEqual({"AAMC": 1, "ASME": 2}, summary["snippets_per_source"])

    def test_counts_high_priority_pages_with_snippets(self):
        ranked_report = {
            "ranked_candidates": [
                {"priority_bucket": "high", "source_title": "ASME", "page_number": 10},
                {"priority_bucket": "high", "source_title": "ASME", "page_number": 11},
            ]
        }
        snippet_report = {
            "candidate_snippets": [
                {
                    "source_title": "ASME",
                    "expected_local_path": "data/raw/asme.pdf",
                    "page_number": 10,
                },
                {"source_title": "Other", "page_number": 99},
            ]
        }

        summary = summarize_snippet_coverage(ranked_report, snippet_report)

        self.assertEqual(1, summary["high_priority_pages_with_snippets"])

    def test_reports_high_priority_pages_without_snippets(self):
        ranked_report = {
            "ranked_candidates": [
                {"priority_bucket": "high", "source_title": "ASME", "page_number": 10},
                {"priority_bucket": "high", "source_title": "ASME", "page_number": 11},
            ]
        }
        snippet_report = {
            "candidate_snippets": [
                {"source_title": "ASME", "page_number": 10},
            ]
        }

        summary = summarize_snippet_coverage(ranked_report, snippet_report)

        self.assertEqual(1, summary["high_priority_pages_without_snippets"])
        self.assertEqual(
            [{"source_title": "ASME", "page_number": 11, "reason": "unknown_reason"}],
            summary["pages_without_snippets"],
        )

    def test_reports_unknown_reason_for_pages_without_inferable_metadata_reason(self):
        ranked_report = {
            "ranked_candidates": [
                {"priority_bucket": "high", "source_title": "ASME", "page_number": 11},
            ]
        }

        summary = summarize_snippet_coverage(
            ranked_report,
            {"candidate_snippets": []},
        )

        self.assertEqual("unknown_reason", summary["pages_without_snippets"][0]["reason"])

    def test_uses_explicit_metadata_reason_for_pages_without_snippets(self):
        ranked_report = {
            "ranked_candidates": [
                {
                    "priority_bucket": "high",
                    "source_title": "ASME",
                    "page_number": 11,
                    "skip_reason": "missing_expected_local_path",
                },
            ]
        }

        summary = summarize_snippet_coverage(
            ranked_report,
            {"candidate_snippets": []},
        )

        self.assertEqual(
            "missing_expected_local_path",
            summary["pages_without_snippets"][0]["reason"],
        )

    def test_cli_reads_reports_and_prints_metadata_summary_without_snippet_text(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ranked_path = Path(tmpdir) / "ranked_definition_candidates.json"
            snippets_path = Path(tmpdir) / "candidate_snippets.json"
            ranked_path.write_text(
                json.dumps(
                    {
                        "ranked_candidates": [
                            {
                                "priority_bucket": "high",
                                "source_title": "ASME",
                                "page_number": 10,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            snippets_path.write_text(
                json.dumps(
                    {
                        "contract": {
                            "neon_writes": False,
                            "database_modifications": False,
                            "validated_content": False,
                        },
                        "candidate_snippets": [
                            {
                                "source_title": "ASME",
                                "page_number": 10,
                                "snippet_text": "do not print this",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    ["--ranked-report", str(ranked_path), "--snippet-report", str(snippets_path)]
                )

        printed = output.getvalue()
        self.assertEqual(0, exit_code)
        self.assertIn("Snippet coverage verification", printed)
        self.assertIn("High-priority candidates total: 1", printed)
        self.assertIn("High-priority pages processed: 1", printed)
        self.assertIn("Snippets total: 1", printed)
        self.assertIn("ASME: 1", printed)
        self.assertNotIn("do not print this", printed)

    def test_summary_certifies_printable_output_excludes_long_text_fields(self):
        ranked_report = {
            "ranked_candidates": [
                {
                    "priority_bucket": "high",
                    "source_title": "ASME",
                    "page_number": 10,
                    "page_text": "candidate page text must stay out of coverage output",
                    "definition": "candidate definition must stay out of coverage output",
                },
            ]
        }
        snippet_report = {
            "candidate_snippets": [
                {
                    "source_title": "ASME",
                    "page_number": 10,
                    "snippet_text": "snippet text must stay out of coverage output",
                    "quote": "quote must stay out of coverage output",
                },
            ]
        }

        summary = summarize_snippet_coverage(ranked_report, snippet_report)

        self.assertEqual(
            {
                "passed": True,
                "forbidden_output_fields": [],
            },
            summary["metadata_only_output"],
        )

    def test_reports_no_neon_database_or_validated_content_contract(self):
        snippet_report = {
            "contract": {
                "neon_writes": False,
                "database_modifications": False,
                "validated_content": False,
            },
            "candidate_snippets": [],
        }

        summary = summarize_snippet_coverage({"ranked_candidates": []}, snippet_report)

        self.assertTrue(summary["contract"]["passed"])
        self.assertEqual([], summary["contract"]["violated_flags"])

    def test_cli_returns_failure_when_contract_is_violated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ranked_path = Path(tmpdir) / "ranked_definition_candidates.json"
            snippets_path = Path(tmpdir) / "candidate_snippets.json"
            ranked_path.write_text(json.dumps({"ranked_candidates": []}), encoding="utf-8")
            snippets_path.write_text(
                json.dumps(
                    {
                        "contract": {
                            "neon_writes": True,
                            "database_modifications": False,
                            "validated_content": False,
                        },
                        "candidate_snippets": [],
                    }
                ),
                encoding="utf-8",
            )

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    ["--ranked-report", str(ranked_path), "--snippet-report", str(snippets_path)]
                )

        self.assertEqual(1, exit_code)
        self.assertIn("No Neon/database/validated contract: FAIL", output.getvalue())


if __name__ == "__main__":
    unittest.main()
