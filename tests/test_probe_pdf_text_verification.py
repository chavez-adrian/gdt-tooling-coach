import unittest
import io
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from scripts import verify_pdf_text_probe


class ProbePdfTextVerificationTests(unittest.TestCase):
    def test_summary_reports_total_pdfs_processed_from_fake_metrics(self):
        report = {
            "pdfs": [
                {"source_path": "data/raw/asme_2018/a.pdf", "sample_size": 4},
                {"source_path": "data/raw/asme_2009_es/b.pdf", "sample_size": 8},
            ]
        }

        summary = verify_pdf_text_probe.summarize_probe_report(report)

        self.assertEqual(summary["total_pdfs_processed"], 2)

    def test_summary_reports_count_of_pdfs_with_extractable_text(self):
        report = {
            "pdfs": [
                {"source_path": "a.pdf", "has_extractable_text": True},
                {"source_path": "b.pdf", "has_extractable_text": False},
                {"source_path": "c.pdf", "has_extractable_text": True},
            ]
        }

        summary = verify_pdf_text_probe.summarize_probe_report(report)

        self.assertEqual(summary["pdfs_with_extractable_text"], 2)

    def test_summary_reports_sample_size_distribution(self):
        report = {
            "pdfs": [
                {"source_path": "a.pdf", "sample_size": 4},
                {"source_path": "b.pdf", "sample_size": 4},
                {"source_path": "c.pdf", "sample_size": 8},
            ]
        }

        summary = verify_pdf_text_probe.summarize_probe_report(report)

        self.assertEqual(summary["sample_size_distribution"], {4: 2, 8: 1})

    def test_summary_reports_sampled_pages_by_quartile_counts(self):
        report = {
            "pdfs": [
                {
                    "source_path": "a.pdf",
                    "sampled_pages_by_quartile": {
                        "Q1": [1, 2],
                        "Q2": [5],
                        "Q3": [],
                        "Q4": [10],
                    },
                },
                {
                    "source_path": "b.pdf",
                    "sampled_pages_by_quartile": {
                        "Q1": [1],
                        "Q2": [],
                        "Q3": [7],
                        "Q4": [12, 13],
                    },
                },
            ]
        }

        summary = verify_pdf_text_probe.summarize_probe_report(report)

        self.assertEqual(
            summary["sampled_pages_by_quartile"], {"Q1": 3, "Q2": 1, "Q3": 1, "Q4": 3}
        )

    def test_summary_flags_text_content_fields_without_echoing_text(self):
        report = {
            "pdfs": [
                {
                    "source_path": "a.pdf",
                    "extracted_text": "do not print this source text",
                    "sample_size": 4,
                }
            ]
        }

        summary = verify_pdf_text_probe.summarize_probe_report(report)

        self.assertTrue(summary["text_content_fields_present"])
        self.assertNotIn("do not print this source text", json.dumps(summary))

    def test_ignored_report_path_check_uses_injectable_git_runner(self):
        calls = []

        def fake_runner(command, cwd):
            calls.append((command, cwd))
            return SimpleNamespace(returncode=0)

        result = verify_pdf_text_probe.check_report_path_ignored(
            Path("repo"), command_runner=fake_runner
        )

        self.assertTrue(result["passed"])
        self.assertEqual(
            calls,
            [
                (
                    ["git", "check-ignore", "--quiet", "data/processed/pdf_text_probe.json"],
                    Path("repo"),
                )
            ],
        )

    def test_probe_script_check_runs_controlled_probe_command(self):
        calls = []

        def fake_runner(command, cwd):
            calls.append((command, cwd))
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        result = verify_pdf_text_probe.run_probe_script(
            Path("repo"), command_runner=fake_runner
        )

        self.assertTrue(result["passed"])
        self.assertEqual(calls, [(["python", "scripts/probe_pdf_text.py"], Path("repo"))])

    def test_unittest_check_runs_discover_command(self):
        calls = []

        def fake_runner(command, cwd):
            calls.append((command, cwd))
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        result = verify_pdf_text_probe.run_unittest_discover(
            Path("repo"), command_runner=fake_runner
        )

        self.assertTrue(result["passed"])
        self.assertEqual(
            calls,
            [(["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], Path("repo"))],
        )

    def test_git_evidence_runs_diff_stat_and_status_short(self):
        calls = []

        def fake_runner(command, cwd):
            calls.append((command, cwd))
            stdout = " scripts/verify_pdf_text_probe.py | 2 ++\n" if "--stat" in command else " M progress.txt\n"
            return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

        result = verify_pdf_text_probe.collect_git_evidence(
            Path("repo"), command_runner=fake_runner
        )

        self.assertEqual(
            calls,
            [
                (["git", "diff", "--stat"], Path("repo")),
                (["git", "status", "--short"], Path("repo")),
            ],
        )
        self.assertEqual(result["git_diff_stat"], "scripts/verify_pdf_text_probe.py | 2 ++")
        self.assertEqual(result["git_status_short"], "M progress.txt")

    def test_cli_prints_metrics_only_final_verification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            report_path = project_root / "data" / "processed" / "pdf_text_probe.json"
            report_path.parent.mkdir(parents=True)
            report_path.write_text(
                json.dumps(
                    [
                        {
                            "source_path": "a.pdf",
                            "source_title": "hidden source text",
                            "sample_size": 4,
                            "has_extractable_text": True,
                            "sampled_pages_by_quartile": {"Q1": [1], "Q2": [], "Q3": [], "Q4": []},
                        }
                    ]
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            def fake_runner(command, cwd):
                if command == ["git", "diff", "--stat"]:
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                if command == ["git", "status", "--short"]:
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            exit_code = verify_pdf_text_probe.main(
                ["--project-root", str(project_root)],
                command_runner=fake_runner,
                stdout=stdout,
            )

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("final_verification_passed: true", output)
        self.assertIn("total_pdfs_processed: 1", output)
        self.assertIn("pdfs_with_extractable_text: 1", output)
        self.assertNotIn("hidden source text", output)


if __name__ == "__main__":
    unittest.main()
