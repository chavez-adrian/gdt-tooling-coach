import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.diagnose_source_matching import (
    compare_source_matching,
    format_diagnostic_summary,
    normalize_for_diagnostic,
    summarize_snippet_sources,
)


class DiagnoseSourceMatchingTests(unittest.TestCase):
    def test_normalization_trims_collapses_case_and_removes_accents(self):
        self.assertEqual(
            "modulo 2 definiciones",
            normalize_for_diagnostic("  Módulo   2 Definiciones  "),
        )

    def test_summarizes_unique_snippet_sources_without_snippet_text(self):
        sources = summarize_snippet_sources(
            [
                {
                    "source_title": "ASME Y14.5-2018 English",
                    "source_type": "asme_2018_en",
                    "language": None,
                    "snippet_text": "literal text must stay private",
                },
                {
                    "source_title": "ASME Y14.5-2018 English",
                    "source_type": "asme_2018_en",
                    "language": None,
                    "snippet_text": "another literal text must stay private",
                },
            ]
        )

        self.assertEqual(
            [
                {
                    "source_title": "ASME Y14.5-2018 English",
                    "source_type": "asme_2018_en",
                    "language": None,
                    "snippet_count": 2,
                }
            ],
            sources,
        )
        self.assertNotIn("snippet_text", json.dumps(sources))

    def test_diagnoses_missing_snippet_language_when_title_and_type_match(self):
        diagnostic = compare_source_matching(
            [
                {
                    "source_title": "ASME Y14.5-2018 English",
                    "source_type": "asme_2018_en",
                    "language": None,
                    "snippet_text": "literal text must stay private",
                }
            ],
            [
                {
                    "title": "ASME Y14.5-2018 English",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
        )

        self.assertEqual([], diagnostic["exact_matches"])
        self.assertEqual(1, len(diagnostic["exact_mismatches"]))
        self.assertEqual(
            ["snippet_language_missing_while_sources_have_language"],
            diagnostic["probable_causes"],
        )
        self.assertEqual(
            "title_source_type_match_language_diff",
            diagnostic["normalized_match_candidates"][0]["candidate_matches"][0][
                "match_reason"
            ],
        )

    def test_exact_match_is_reported_when_title_type_and_language_match(self):
        diagnostic = compare_source_matching(
            [
                {
                    "source_title": "ASME Y14.5-2018 English",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
            [
                {
                    "title": "ASME Y14.5-2018 English",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
        )

        self.assertEqual(1, len(diagnostic["exact_matches"]))
        self.assertEqual([], diagnostic["exact_mismatches"])
        self.assertEqual(["no_mismatch_detected"], diagnostic["probable_causes"])

    def test_console_summary_is_safe_and_reports_comparison(self):
        summary = format_diagnostic_summary(
            compare_source_matching(
                [
                    {
                        "source_title": "ASME Y14.5-2009 Español",
                        "source_type": "asme_2009_es",
                        "language": None,
                        "snippet_text": "literal text must not print",
                    }
                ],
                [
                    {
                        "title": "ASME Y14.5-2009 Español",
                        "source_type": "asme_2009_es",
                        "language": "es",
                    }
                ],
            )
        )

        self.assertIn("Snippet unique sources:", summary)
        self.assertIn("Database sources:", summary)
        self.assertIn("Exact mismatches: 1", summary)
        self.assertIn("snippet_language_missing_while_sources_have_language", summary)
        self.assertIn("No database writes: true", summary)
        self.assertNotIn("literal text must not print", summary)
        self.assertNotIn("snippet_text", summary)

    def test_cli_uses_fixture_without_printing_snippet_text_or_secrets(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "candidate_snippets.json"
            sources_path = Path(tmp_dir) / "sources.json"
            input_path.write_text(
                json.dumps(
                    {
                        "candidate_snippets": [
                            {
                                "source_title": "ASME Y14.5-2018 English",
                                "source_type": "asme_2018_en",
                                "language": None,
                                "snippet_text": "literal text must not print",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            sources_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "ASME Y14.5-2018 English",
                            "source_type": "asme_2018_en",
                            "language": "en",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python",
                    "scripts/diagnose_source_matching.py",
                    "--input",
                    str(input_path),
                    "--sources-fixture",
                    str(sources_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Probable causes: snippet_language_missing_while_sources_have_language", result.stdout)
        self.assertNotIn("literal text must not print", result.stdout)
        self.assertNotIn("DATABASE_URL", result.stdout)
        self.assertNotIn("password", result.stdout.lower())
        self.assertNotIn("token", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
