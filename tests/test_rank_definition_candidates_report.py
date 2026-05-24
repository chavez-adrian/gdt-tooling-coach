import unittest

from scripts.rank_definition_candidates import build_ranked_definition_candidate_rows


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


if __name__ == "__main__":
    unittest.main()
