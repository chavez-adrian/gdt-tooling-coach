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
                {"source_title": "ASME", "page_number": 10},
                {"source_title": "ASME", "page_number": 10},
                {"source_title": "Other", "page_number": 99},
            ]
        }

        summary = summarize_snippet_coverage(ranked_report, snippet_report)

        self.assertEqual(1, summary["high_priority_pages_with_snippets"])


if __name__ == "__main__":
    unittest.main()
