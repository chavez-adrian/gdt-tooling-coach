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


if __name__ == "__main__":
    unittest.main()
