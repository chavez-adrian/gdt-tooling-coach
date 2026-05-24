import unittest

from scripts.rank_definition_candidates import (
    build_ranked_definition_candidate_report,
    build_ranked_definition_candidate_rows,
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


if __name__ == "__main__":
    unittest.main()
