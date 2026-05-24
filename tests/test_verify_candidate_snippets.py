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


if __name__ == "__main__":
    unittest.main()
