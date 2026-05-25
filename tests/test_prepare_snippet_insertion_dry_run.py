import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_snippet_insertion_dry_run import (
    build_dry_run_report,
    load_candidate_snippets,
)


class PrepareSnippetInsertionDryRunTests(unittest.TestCase):
    def test_loads_candidate_snippets_from_processed_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "candidate_snippets.json"
            report_path.write_text(
                json.dumps(
                    {
                        "candidate_snippets": [
                            {
                                "source_title": "ASME",
                                "source_type": "asme_2018_en",
                                "language": "en",
                                "expected_local_path": "data/raw/asme.pdf",
                                "page_number": 10,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            snippets = load_candidate_snippets(report_path)

        self.assertEqual(1, len(snippets))
        self.assertEqual("ASME", snippets[0]["source_title"])

    def test_report_blocks_snippets_when_no_source_matches(self):
        report = build_dry_run_report(
            [
                {
                    "source_title": "Unknown",
                    "source_type": "asme_2018_en",
                    "language": "en",
                }
            ],
            source_rows=[],
        )

        self.assertEqual(1, report["total_snippets"])
        self.assertEqual(0, report["insertable_snippets"])
        self.assertEqual(1, report["blocked_snippets"])
        self.assertEqual({"source_not_found": 1}, report["block_reasons"])
        self.assertEqual(
            {"matched_sources": 0, "unmatched_sources": 1},
            report["source_match_summary"],
        )


if __name__ == "__main__":
    unittest.main()
