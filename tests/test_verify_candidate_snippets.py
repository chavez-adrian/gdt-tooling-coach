import unittest

from scripts.verify_candidate_snippets import (
    check_report_path_ignored,
    collect_git_evidence,
    run_extractor_command,
    run_unittest_command,
    summarize_candidate_snippet_report,
    verify_report_contract,
    verify_review_state_fields,
    verify_snippet_word_limit,
)


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

    def test_reports_maximum_snippet_word_count(self):
        report = {
            "candidate_snippets": [
                {"snippet_word_count": 12},
                {"snippet_word_count": 80},
                {"snippet_word_count": 5},
            ]
        }

        summary = summarize_candidate_snippet_report(report)

        self.assertEqual(80, summary["max_snippet_word_count"])

    def test_fails_word_limit_safety_when_any_snippet_exceeds_80_words(self):
        report = {
            "candidate_snippets": [
                {"source_title": "ASME", "snippet_word_count": 80},
                {"source_title": "AAMC", "snippet_word_count": 81},
            ]
        }

        safety = verify_snippet_word_limit(report)

        self.assertFalse(safety["passed"])
        self.assertEqual(80, safety["max_allowed_words"])
        self.assertEqual([1], safety["over_limit_indexes"])

    def test_fails_review_state_safety_when_snippet_is_not_raw_literal_reviewable(self):
        report = {
            "candidate_snippets": [
                {
                    "extraction_type": "literal_quote",
                    "proposed_review_state": "raw_import",
                    "requires_human_review": True,
                },
                {
                    "extraction_type": "paraphrase",
                    "proposed_review_state": "validated",
                    "requires_human_review": False,
                },
            ]
        }

        safety = verify_review_state_fields(report)

        self.assertFalse(safety["passed"])
        self.assertEqual([1], safety["invalid_review_state_indexes"])

    def test_fails_contract_safety_when_report_touches_neon_database_or_validation(self):
        report = {
            "contract": {
                "neon_writes": True,
                "database_modifications": True,
                "validated_content": True,
            }
        }

        safety = verify_report_contract(report)

        self.assertFalse(safety["passed"])
        self.assertEqual(
            ["neon_writes", "database_modifications", "validated_content"],
            safety["violated_contract_flags"],
        )

    def test_runs_extractor_and_unittest_commands_with_injectable_runner(self):
        calls = []

        def fake_runner(command, cwd=None, capture_output=None, text=None):
            calls.append((command, cwd, capture_output, text))

            class Result:
                returncode = 0
                stdout = "ok"
                stderr = ""

            return Result()

        extractor_check = run_extractor_command("repo-root", runner=fake_runner)
        unittest_check = run_unittest_command("repo-root", runner=fake_runner)

        self.assertTrue(extractor_check["passed"])
        self.assertTrue(unittest_check["passed"])
        self.assertEqual(
            [
                ["python", "scripts/extract_candidate_snippets.py"],
                ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            ],
            [call[0] for call in calls],
        )

    def test_collects_git_evidence_and_checks_candidate_snippet_report_is_ignored(self):
        calls = []

        def fake_runner(command, cwd=None, capture_output=None, text=None):
            calls.append(command)

            class Result:
                returncode = 0
                stdout = (
                    "data/processed/candidate_snippets.json\n"
                    if command[:2] == ["git", "check-ignore"]
                    else "scripts/verify_candidate_snippets.py | 2 ++\n"
                    if command[-1] == "--stat"
                    else " M scripts/verify_candidate_snippets.py\n"
                )
                stderr = ""

            return Result()

        ignore_check = check_report_path_ignored("repo-root", runner=fake_runner)
        evidence = collect_git_evidence("repo-root", runner=fake_runner)

        self.assertTrue(ignore_check["passed"])
        self.assertEqual(
            [
                ["git", "check-ignore", "data/processed/candidate_snippets.json"],
                ["git", "diff", "--stat"],
                ["git", "status", "--short"],
            ],
            calls,
        )
        self.assertEqual(
            "scripts/verify_candidate_snippets.py | 2 ++\n",
            evidence["git_diff_stat"]["stdout"],
        )
        self.assertEqual(
            " M scripts/verify_candidate_snippets.py\n",
            evidence["git_status_short"]["stdout"],
        )


if __name__ == "__main__":
    unittest.main()
