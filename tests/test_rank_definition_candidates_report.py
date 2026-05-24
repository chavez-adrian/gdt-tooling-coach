import json
import tempfile
import unittest
from pathlib import Path

from scripts.rank_definition_candidates import (
    DEFAULT_INPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    build_ranked_definition_candidate_report,
    build_ranked_definition_candidate_rows,
    format_console_summary,
    ranked_report_output_is_ignored,
    write_ranked_definition_candidate_report,
)


class RankedDefinitionCandidatesReportTests(unittest.TestCase):
    def test_ranked_rows_expose_candidate_score(self):
        rows = build_ranked_definition_candidate_rows(
            [
                {
                    "source_title": "ASME",
                    "source_type": "standard",
                    "language": "en",
                    "page_number": 5,
                    "matched_signals": ["definition"],
                    "signal_count": 1,
                    "approximate_word_count": 250,
                }
            ]
        )

        self.assertEqual(1, len(rows))
        self.assertEqual("ASME", rows[0]["source_title"])
        self.assertEqual(8, rows[0]["candidate_score"])
        self.assertNotIn("definition_score", rows[0])

    def test_ranked_rows_assign_global_rank_by_candidate_score(self):
        rows = build_ranked_definition_candidate_rows(
            [
                {
                    "source_title": "Low",
                    "page_number": 1,
                    "signal_count": 1,
                    "matched_signals": [],
                },
                {
                    "source_title": "High",
                    "page_number": 2,
                    "signal_count": 2,
                    "matched_signals": ["definition", "datum"],
                },
            ]
        )

        self.assertEqual("High", rows[0]["source_title"])
        self.assertEqual(1, rows[0]["global_rank"])
        self.assertEqual("Low", rows[1]["source_title"])
        self.assertEqual(2, rows[1]["global_rank"])

    def test_ranked_rows_assign_rank_within_each_source(self):
        rows = build_ranked_definition_candidate_rows(
            [
                {
                    "source_title": "ASME",
                    "page_number": 1,
                    "signal_count": 1,
                    "matched_signals": [],
                },
                {
                    "source_title": "ISO",
                    "page_number": 2,
                    "signal_count": 4,
                    "matched_signals": ["definition"],
                },
                {
                    "source_title": "ASME",
                    "page_number": 3,
                    "signal_count": 3,
                    "matched_signals": ["definition"],
                },
            ]
        )

        ranks = {
            (row["source_title"], row["page_number"]): row["rank_within_source"]
            for row in rows
        }
        self.assertEqual(1, ranks[("ASME", 3)])
        self.assertEqual(2, ranks[("ASME", 1)])
        self.assertEqual(1, ranks[("ISO", 2)])

    def test_report_summary_counts_priority_buckets(self):
        report = build_ranked_definition_candidate_report(
            [
                {
                    "source_title": "High",
                    "signal_count": 3,
                    "matched_signals": ["definition", "glossary", "datum"],
                },
                {
                    "source_title": "Medium",
                    "signal_count": 1,
                    "matched_signals": ["definition"],
                },
                {"source_title": "Low", "signal_count": 1, "matched_signals": []},
            ]
        )

        self.assertEqual(3, report["summary"]["total_candidates"])
        self.assertEqual({"high": 1, "medium": 1, "low": 1}, report["summary"]["priority_buckets"])

    def test_report_summary_lists_top_sources_by_high_priority_candidates(self):
        report = build_ranked_definition_candidate_report(
            [
                {
                    "source_title": "ASME",
                    "signal_count": 3,
                    "matched_signals": ["definition", "glossary", "datum"],
                },
                {
                    "source_title": "ISO",
                    "signal_count": 5,
                    "matched_signals": ["definition", "glossary"],
                },
                {
                    "source_title": "ASME",
                    "signal_count": 5,
                    "matched_signals": ["definition", "glossary"],
                },
            ]
        )

        self.assertEqual(
            [
                {"source_title": "ASME", "high_priority_candidates": 2},
                {"source_title": "ISO", "high_priority_candidates": 1},
            ],
            report["summary"]["top_sources_by_high_priority_candidates"],
        )

    def test_json_writer_reads_candidate_pages_and_writes_ranked_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "definition_candidate_pages.json"
            output_path = Path(tmpdir) / "nested" / "ranked_definition_candidates.json"
            input_path.write_text(
                json.dumps(
                    {
                        "candidate_pages": [
                            {
                                "source_title": "ASME",
                                "signal_count": 1,
                                "matched_signals": ["definition"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            report = write_ranked_definition_candidate_report(input_path, output_path)

            written = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(report, written)
            self.assertEqual(1, written["summary"]["total_candidates"])
            self.assertEqual("ASME", written["ranked_candidates"][0]["source_title"])

    def test_cli_defaults_to_processed_candidate_input_and_ranked_output(self):
        self.assertEqual(
            Path("data/processed/definition_candidate_pages.json"),
            DEFAULT_INPUT_PATH.relative_to(DEFAULT_INPUT_PATH.parents[2]),
        )
        self.assertEqual(
            Path("data/processed/ranked_definition_candidates.json"),
            DEFAULT_OUTPUT_PATH.relative_to(DEFAULT_OUTPUT_PATH.parents[2]),
        )

    def test_ranked_report_output_path_is_confirmed_ignored(self):
        calls = []

        def fake_run(command, cwd, capture_output, text):
            calls.append((command, cwd, capture_output, text))

            class Result:
                returncode = 0

            return Result()

        self.assertTrue(ranked_report_output_is_ignored(run_command=fake_run))
        self.assertEqual(
            ["git", "check-ignore", "data/processed/ranked_definition_candidates.json"],
            calls[0][0],
        )

    def test_ranked_output_excludes_forbidden_text_fields(self):
        report = build_ranked_definition_candidate_report(
            [
                {
                    "source_title": "ASME",
                    "source_type": "standard",
                    "language": "en",
                    "page_number": 5,
                    "matched_signals": ["definition"],
                    "signal_count": 1,
                    "approximate_word_count": 250,
                    "page_text": "definition text must not be stored",
                    "excerpt": "long quote must not be stored",
                    "definition": "sample definition must not be stored",
                    "candidate_reason": "matched 1 definition candidate signals: definition",
                }
            ]
        )

        row = report["ranked_candidates"][0]
        self.assertEqual(
            {
                "source_title",
                "source_type",
                "language",
                "page_number",
                "matched_signals",
                "signal_count",
                "approximate_word_count",
                "candidate_score",
                "rank_within_source",
                "global_rank",
                "priority_bucket",
            },
            set(row),
        )
        self.assertNotIn("definition text must not be stored", row.values())

    def test_console_summary_includes_counts_and_top_sources(self):
        report = build_ranked_definition_candidate_report(
            [
                {
                    "source_title": "ASME",
                    "signal_count": 5,
                    "matched_signals": ["definition", "glossary"],
                },
                {"source_title": "ISO", "signal_count": 1, "matched_signals": []},
            ]
        )

        summary = format_console_summary(report)

        self.assertIn("Total candidates: 2", summary)
        self.assertIn("High: 1", summary)
        self.assertIn("Medium: 0", summary)
        self.assertIn("Low: 1", summary)
        self.assertIn("ASME: 1", summary)


if __name__ == "__main__":
    unittest.main()
