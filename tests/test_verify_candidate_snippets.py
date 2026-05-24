import unittest

from scripts.verify_candidate_snippets import (
    summarize_candidate_snippet_report,
    verify_review_state_fields,
    verify_snippet_word_limit,
)


class VerifyCandidateSnippetsTest(unittest.TestCase):
    def test_summarizes_snippet_count_from_report(self):
        report = {
            "candidate_snippets": [
                {"source_title": "ASME"},
                {"source_title": "AAMC"},
            ]
        }

        summary = summarize_candidate_snippet_report(report)

        self.assertEqual(2, summary["snippets_generated"])

    def test_summarizes_snippets_by_source(self):
        report = {
            "candidate_snippets": [
                {"source_title": "ASME Y14.5-2018"},
                {"source_title": "AAMC Course"},
                {"source_title": "ASME Y14.5-2018"},
            ]
        }

        summary = summarize_candidate_snippet_report(report)

        self.assertEqual(
            {"AAMC Course": 1, "ASME Y14.5-2018": 2},
            summary["snippets_by_source"],
        )

    def test_reports_maximum_snippet_word_count(self):
        report = {
            "candidate_snippets": [
                {"snippet_word_count": 12},
                {"snippet_word_count": 80},
                {"snippet_word_count": 5},
            ]
        }

        summary = summarize_candidate_snippet_report(report)

        self.assertEqual(80, summary["max_snippet_word_count"])

    def test_fails_word_limit_safety_when_any_snippet_exceeds_80_words(self):
        report = {
            "candidate_snippets": [
                {"source_title": "ASME", "snippet_word_count": 80},
                {"source_title": "AAMC", "snippet_word_count": 81},
            ]
        }

        safety = verify_snippet_word_limit(report)

        self.assertFalse(safety["passed"])
        self.assertEqual(80, safety["max_allowed_words"])
        self.assertEqual([1], safety["over_limit_indexes"])

    def test_fails_review_state_safety_when_snippet_is_not_raw_literal_reviewable(self):
        report = {
            "candidate_snippets": [
                {
                    "extraction_type": "literal_quote",
                    "proposed_review_state": "raw_import",
                    "requires_human_review": True,
                },
                {
                    "extraction_type": "paraphrase",
                    "proposed_review_state": "validated",
                    "requires_human_review": False,
                },
            ]
        }

        safety = verify_review_state_fields(report)

        self.assertFalse(safety["passed"])
        self.assertEqual([1], safety["invalid_review_state_indexes"])


if __name__ == "__main__":
    unittest.main()
