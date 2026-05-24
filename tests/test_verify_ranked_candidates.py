import unittest

from scripts.verify_ranked_candidates import summarize_ranked_report


class VerifyRankedCandidatesTest(unittest.TestCase):
    def test_summarizes_total_ranked_candidates_from_report_metadata(self):
        report = {"summary": {"total_candidates": 7}}

        summary = summarize_ranked_report(report)

        self.assertEqual(7, summary["total_ranked_candidates"])

    def test_summarizes_priority_bucket_counts(self):
        report = {
            "summary": {
                "priority_buckets": {
                    "high": 3,
                    "medium": 5,
                    "low": 2,
                }
            }
        }

        summary = summarize_ranked_report(report)

        self.assertEqual(
            {"high": 3, "medium": 5, "low": 2},
            summary["priority_buckets"],
        )


if __name__ == "__main__":
    unittest.main()
