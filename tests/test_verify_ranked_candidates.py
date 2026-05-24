import unittest

from scripts.verify_ranked_candidates import (
    report_contains_forbidden_content_fields,
    summarize_ranked_report,
)


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

    def test_summarizes_top_sources_by_high_priority_candidates(self):
        report = {
            "summary": {
                "top_sources_by_high_priority_candidates": [
                    {"source_title": "ASME Y14.5 2018", "high_priority_candidates": 4},
                    {"source_title": "NOM Z 2010", "high_priority_candidates": 2},
                ]
            }
        }

        summary = summarize_ranked_report(report)

        self.assertEqual(
            [
                {"source_title": "ASME Y14.5 2018", "high_priority_candidates": 4},
                {"source_title": "NOM Z 2010", "high_priority_candidates": 2},
            ],
            summary["top_sources_by_high_priority_candidates"],
        )

    def test_detects_forbidden_text_content_fields_without_returning_values(self):
        report = {
            "ranked_candidates": [
                {
                    "source_title": "ASME",
                    "snippet": "definition sample that must not be echoed",
                }
            ]
        }

        safety = report_contains_forbidden_content_fields(report)

        self.assertTrue(safety["has_forbidden_content_fields"])
        self.assertEqual(["ranked_candidates[0].snippet"], safety["field_paths"])
        self.assertNotIn("definition sample", str(safety))


if __name__ == "__main__":
    unittest.main()
