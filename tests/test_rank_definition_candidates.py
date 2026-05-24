import unittest

from scripts.rank_definition_candidates import score_definition_candidates


class RankDefinitionCandidatesTests(unittest.TestCase):
    def test_score_increases_from_signal_count(self):
        scored = score_definition_candidates(
            [
                {"source_id": "one", "page_number": 1, "signal_count": 1},
                {"source_id": "two", "page_number": 2, "signal_count": 3},
            ]
        )

        self.assertGreater(scored[0]["definition_score"], scored[1]["definition_score"])
        self.assertEqual("two", scored[0]["source_id"])
        self.assertEqual("one", scored[1]["source_id"])


if __name__ == "__main__":
    unittest.main()
