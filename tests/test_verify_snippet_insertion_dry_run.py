import unittest

from scripts.verify_snippet_insertion_dry_run import verify_dry_run_report


class VerifySnippetInsertionDryRunTests(unittest.TestCase):
    def test_verifies_required_summary_fields(self):
        report = {
            "total_snippets": 1,
            "insertable_snippets": 1,
            "blocked_snippets": 0,
            "block_reasons": {},
            "source_match_summary": {"matched_sources": 1, "unmatched_sources": 0},
        }

        result = verify_dry_run_report(report)

        self.assertEqual([], result["errors"])
        self.assertIn("required_summary_fields", result["checks"])


if __name__ == "__main__":
    unittest.main()
