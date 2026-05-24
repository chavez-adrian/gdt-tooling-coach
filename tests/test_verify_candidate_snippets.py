import unittest

from scripts.verify_candidate_snippets import summarize_candidate_snippet_report


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


if __name__ == "__main__":
    unittest.main()
