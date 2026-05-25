import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_snippet_insertion_dry_run import load_candidate_snippets


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


if __name__ == "__main__":
    unittest.main()
