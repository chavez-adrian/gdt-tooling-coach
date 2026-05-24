import unittest

from scripts.rank_definition_candidates import (
    score_definition_candidate,
    score_definition_candidates,
)


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

    def test_assigns_high_medium_and_low_priority_buckets(self):
        scored = score_definition_candidates(
            [
                {
                    "source_id": "high",
                    "signal_count": 3,
                    "matched_signals": ["definition", "glossary", "datum"],
                },
                {
                    "source_id": "medium",
                    "signal_count": 1,
                    "matched_signals": ["definition"],
                },
                {"source_id": "low", "signal_count": 1},
            ]
        )

        buckets_by_source = {
            candidate["source_id"]: candidate["priority_bucket"] for candidate in scored
        }
        self.assertEqual("high", buckets_by_source["high"])
        self.assertEqual("medium", buckets_by_source["medium"])
        self.assertEqual("low", buckets_by_source["low"])

    def test_empty_candidate_input_returns_empty_list(self):
        self.assertEqual([], score_definition_candidates([]))

    def test_scored_output_drops_forbidden_text_fields(self):
        page_text = "definition text that must not be stored"
        scored = score_definition_candidates(
            [
                {
                    "source_id": "safe",
                    "signal_count": 1,
                    "matched_signals": ["definition"],
                    "page_text": page_text,
                    "text": page_text,
                    "excerpt": "definition text",
                    "definition": "stored definition",
                }
            ]
        )

        self.assertEqual("safe", scored[0]["source_id"])
        self.assertNotIn("page_text", scored[0])
        self.assertNotIn("text", scored[0])
        self.assertNotIn("excerpt", scored[0])
        self.assertNotIn("definition", scored[0])
        self.assertNotIn(page_text, scored[0].values())

    def test_single_candidate_helper_returns_public_scored_metadata_shape(self):
        scored = score_definition_candidate(
            {
                "source_id": "public",
                "page_number": 4,
                "signal_count": 1,
                "matched_signals": ["glossary"],
                "approximate_word_count": 200,
                "source_type": "standard",
                "language": "en",
                "candidate_reason": "matched 1 definition candidate signals: glossary",
            }
        )

        self.assertEqual("public", scored["source_id"])
        self.assertEqual(4, scored["page_number"])
        self.assertEqual(8, scored["definition_score"])
        self.assertEqual("medium", scored["priority_bucket"])
        self.assertEqual(
            "matched 1 definition candidate signals: glossary",
            scored["candidate_reason"],
        )


if __name__ == "__main__":
    unittest.main()
