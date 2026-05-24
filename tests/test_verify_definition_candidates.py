import unittest

from scripts.verify_definition_candidates import (
    check_report_path_ignored,
    run_locator_command,
    run_unittest_command,
    report_contains_forbidden_content_fields,
    summarize_candidate_report,
)


class VerifyDefinitionCandidatesTest(unittest.TestCase):
    def test_summarizes_total_pdfs_processed_from_report_metadata(self):
        report = {
            "summary": {
                "existing_pdfs": 7,
                "pdf_open_errors": 2,
                "missing_pdfs": 1,
            }
        }

        summary = summarize_candidate_report(report)

        self.assertEqual(9, summary["pdfs_processed"])

    def test_summarizes_total_candidate_pages(self):
        report = {"summary": {"candidate_pages": 12}}

        summary = summarize_candidate_report(report)

        self.assertEqual(12, summary["total_candidate_pages"])

    def test_summarizes_candidate_pages_by_source(self):
        report = {
            "candidate_pages": [
                {"source_title": "ASME Y14.5 2018", "page_number": 4},
                {"source_title": "ASME Y14.5 2018", "page_number": 5},
                {"source_title": "NOM Z 2010", "page_number": 2},
            ]
        }

        summary = summarize_candidate_report(report)

        self.assertEqual(
            {"ASME Y14.5 2018": 2, "NOM Z 2010": 1},
            summary["candidate_pages_by_source"],
        )

    def test_summarizes_top_signals_found(self):
        report = {
            "candidate_pages": [
                {"matched_signals": ["definition", "datum"]},
                {"matched_signals": ["definition", "MMC"]},
                {"matched_signals": ["datum"]},
            ]
        }

        summary = summarize_candidate_report(report)

        self.assertEqual(
            [("definition", 2), ("datum", 2), ("MMC", 1)],
            summary["top_signals_found"],
        )

    def test_detects_forbidden_text_content_fields_without_returning_values(self):
        report = {
            "candidate_pages": [
                {
                    "source_title": "ASME",
                    "page_text": "definition sample that must not be echoed",
                }
            ]
        }

        safety = report_contains_forbidden_content_fields(report)

        self.assertTrue(safety["has_forbidden_content_fields"])
        self.assertEqual(["candidate_pages[0].page_text"], safety["field_paths"])
        self.assertNotIn("definition sample", str(safety))

    def test_checks_report_path_is_ignored_with_injectable_runner(self):
        calls = []

        def fake_runner(command, cwd=None, capture_output=None, text=None):
            calls.append((command, cwd, capture_output, text))

            class Result:
                returncode = 0
                stdout = "data/processed/definition_candidate_pages.json\n"
                stderr = ""

            return Result()

        check = check_report_path_ignored("repo-root", runner=fake_runner)

        self.assertTrue(check["passed"])
        self.assertEqual(
            ["git", "check-ignore", "data/processed/definition_candidate_pages.json"],
            calls[0][0],
        )
        self.assertEqual("repo-root", calls[0][1])

    def test_runs_locator_command_with_injectable_runner(self):
        calls = []

        def fake_runner(command, cwd=None, capture_output=None, text=None):
            calls.append(command)

            class Result:
                returncode = 0
                stdout = "locator ok"
                stderr = ""

            return Result()

        check = run_locator_command("repo-root", runner=fake_runner)

        self.assertTrue(check["passed"])
        self.assertEqual(["python", "scripts/locate_definition_candidates.py"], calls[0])
        self.assertEqual(
            "python scripts/locate_definition_candidates.py",
            check["command"],
        )

    def test_runs_unittest_command_with_injectable_runner(self):
        calls = []

        def fake_runner(command, cwd=None, capture_output=None, text=None):
            calls.append(command)

            class Result:
                returncode = 0
                stdout = ""
                stderr = "OK"

            return Result()

        check = run_unittest_command("repo-root", runner=fake_runner)

        self.assertTrue(check["passed"])
        self.assertEqual(
            ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            calls[0],
        )


if __name__ == "__main__":
    unittest.main()
