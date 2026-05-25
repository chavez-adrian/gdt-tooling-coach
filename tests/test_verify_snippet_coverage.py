import unittest

from scripts.verify_snippet_coverage import summarize_snippet_coverage


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


if __name__ == "__main__":
    unittest.main()
