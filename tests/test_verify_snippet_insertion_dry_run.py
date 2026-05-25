import unittest

from scripts.verify_snippet_insertion_dry_run import verify_dry_run_report


def valid_report(**overrides):
    report = {
        "total_snippets": 0,
        "insertable_snippets": 0,
        "blocked_snippets": 0,
        "block_reasons": {},
        "source_match_summary": {"matched_sources": 0, "unmatched_sources": 0},
        "intended_insertion_metadata": {
            "review_state": "raw_import",
            "requires_human_review": True,
            "validated": False,
            "extraction_type": "literal_quote",
        },
    }
    report.update(overrides)
    return report


class VerifySnippetInsertionDryRunTests(unittest.TestCase):
    def test_verifies_required_summary_fields(self):
        report = {
            "total_snippets": 1,
            "insertable_snippets": 1,
            "blocked_snippets": 0,
            "block_reasons": {},
            "source_match_summary": {"matched_sources": 1, "unmatched_sources": 0},
            "intended_insertion_metadata": {
                "review_state": "raw_import",
                "requires_human_review": True,
                "validated": False,
                "extraction_type": "literal_quote",
            },
        }

        result = verify_dry_run_report(report)

        self.assertEqual([], result["errors"])
        self.assertIn("required_summary_fields", result["checks"])

    def test_verifies_intended_insertion_constants(self):
        report = {
            "total_snippets": 0,
            "insertable_snippets": 0,
            "blocked_snippets": 0,
            "block_reasons": {},
            "source_match_summary": {"matched_sources": 0, "unmatched_sources": 0},
            "intended_insertion_metadata": {
                "review_state": "raw_import",
                "requires_human_review": True,
                "validated": False,
                "extraction_type": "literal_quote",
            },
        }

        result = verify_dry_run_report(report)

        self.assertEqual([], result["errors"])
        self.assertIn("intended_insertion_constants", result["checks"])

    def test_rejects_executable_sql_with_literal_snippet_text(self):
        report = valid_report(
            executable_sql="INSERT INTO definitions (definition_text) VALUES ('literal quote');"
        )

        result = verify_dry_run_report(report)

        self.assertIn("executable SQL is not allowed in dry-run reports", result["errors"])


if __name__ == "__main__":
    unittest.main()
