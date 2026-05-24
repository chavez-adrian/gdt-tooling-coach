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

    def test_strong_signals_weight_more_than_medium_signals(self):
        scored = score_definition_candidates(
            [
                {
                    "source_id": "medium",
                    "signal_count": 1,
                    "matched_signals": ["datum"],
                },
                {
                    "source_id": "strong",
                    "signal_count": 1,
                    "matched_signals": ["definition"],
                },
            ]
        )

        self.assertGreater(scored[0]["definition_score"], scored[1]["definition_score"])
        self.assertEqual("strong", scored[0]["source_id"])

    def test_medium_gdt_signals_contribute_to_score(self):
        scored = score_definition_candidates(
            [
                {
                    "source_id": "gdt",
                    "signal_count": 8,
                    "matched_signals": [
                        "datum",
                        "feature control frame",
                        "tolerance zone",
                        "MMC",
                        "LMC",
                        "RFS",
                        "sÃ­mbolo",
                        "sÃ­mbolos",
                    ],
                }
            ]
        )

        self.assertEqual(24, scored[0]["definition_score"])

    def test_overly_generic_signals_are_penalized(self):
        scored = score_definition_candidates(
            [
                {
                    "source_id": "generic",
                    "signal_count": 1,
                    "matched_signals": ["terms"],
                },
                {
                    "source_id": "plain",
                    "signal_count": 1,
                    "matched_signals": [],
                },
            ]
        )

        self.assertLess(scored[1]["definition_score"], scored[0]["definition_score"])
        self.assertEqual("plain", scored[0]["source_id"])

    def test_approximate_word_count_adds_bounded_metadata_boost(self):
        scored = score_definition_candidates(
            [
                {
                    "source_id": "too-short",
                    "signal_count": 1,
                    "approximate_word_count": 20,
                },
                {
                    "source_id": "useful-page",
                    "signal_count": 1,
                    "approximate_word_count": 450,
                },
                {
                    "source_id": "oversized",
                    "signal_count": 1,
                    "approximate_word_count": 4000,
                },
            ]
        )

        self.assertEqual("useful-page", scored[0]["source_id"])
        self.assertEqual(scored[1]["definition_score"], scored[2]["definition_score"])

    def test_source_type_and_language_metadata_can_influence_score(self):
        scored = score_definition_candidates(
            [
                {
                    "source_id": "unknown-source",
                    "signal_count": 1,
                    "source_type": "notes",
                    "language": "unknown",
                },
                {
                    "source_id": "standard-source",
                    "signal_count": 1,
                    "source_type": "standard",
                    "language": "es",
                },
            ]
        )

        self.assertEqual("standard-source", scored[0]["source_id"])
        self.assertGreater(scored[0]["definition_score"], scored[1]["definition_score"])


if __name__ == "__main__":
    unittest.main()
