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


if __name__ == "__main__":
    unittest.main()
