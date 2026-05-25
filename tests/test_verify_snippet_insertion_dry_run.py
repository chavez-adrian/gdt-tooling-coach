import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.verify_snippet_insertion_dry_run import (
    DEFAULT_REPORT_RELATIVE_PATH,
    format_verification_summary,
    verify_default_report_path_is_ignored,
    verify_dry_run_report,
)


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

    def test_console_summary_excludes_snippet_text_and_forbidden_text_fields(self):
        report = valid_report(
            total_snippets=2,
            insertable_snippets=1,
            blocked_snippets=1,
            block_reasons={"missing_matched_signal": 1},
            source_match_summary={"matched_sources": 1, "unmatched_sources": 1},
        )
        result = verify_dry_run_report(report)

        summary = format_verification_summary(report, result)

        self.assertIn("Total snippets: 2", summary)
        self.assertNotIn("snippet_text", summary)
        self.assertNotIn("definition_text", summary)
        self.assertNotIn("literal quote", summary)

    def test_verifier_declares_no_database_access_or_writes_required(self):
        result = verify_dry_run_report(valid_report())

        self.assertEqual(
            {
                "database_access_required": False,
                "database_writes_attempted": False,
                "neon_required": False,
            },
            result["runtime_contract"],
        )

    def test_verifies_default_dry_run_report_path_is_ignored(self):
        calls = []

        class Result:
            returncode = 0

        def fake_run(command, cwd, capture_output, text):
            calls.append((command, cwd, capture_output, text))
            return Result()

        self.assertTrue(verify_default_report_path_is_ignored(run_command=fake_run))
        self.assertEqual(
            ["git", "check-ignore", DEFAULT_REPORT_RELATIVE_PATH.as_posix()],
            calls[0][0],
        )

    def test_cli_prints_safe_totals_source_matching_and_no_write_evidence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "snippet_insertion_dry_run.json"
            report_path.write_text(json.dumps(valid_report(total_snippets=2)), encoding="utf-8")

            result = subprocess.run(
                [
                    "python",
                    "scripts/verify_snippet_insertion_dry_run.py",
                    "--report",
                    str(report_path),
                    "--skip-ignore-check",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Total snippets: 2", result.stdout)
        self.assertIn("Source match summary: matched_sources=0, unmatched_sources=0", result.stdout)
        self.assertIn("No database writes: true", result.stdout)
        self.assertNotIn("snippet_text", result.stdout)

    def test_readme_documents_dry_run_verifier_as_planning_not_ingestion(self):
        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("python scripts/verify_snippet_insertion_dry_run.py", readme)
        self.assertIn("dry-run planning and safety verification", readme)
        self.assertIn("not an ingestion or validation command", readme)

    def test_ingestion_and_editorial_docs_keep_dry_run_verification_non_ingesting(self):
        repo_root = Path(__file__).resolve().parents[1]
        ingestion_plan = (repo_root / "docs" / "ingestion_plan.md").read_text(
            encoding="utf-8"
        )
        editorial_rules = (repo_root / "docs" / "editorial_rules.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("verify_snippet_insertion_dry_run.py", ingestion_plan)
        self.assertIn("dry-run planning and safety verification", ingestion_plan)
        self.assertIn("verify_snippet_insertion_dry_run.py", editorial_rules)
        self.assertIn("must not print snippet_text", editorial_rules)


if __name__ == "__main__":
    unittest.main()
