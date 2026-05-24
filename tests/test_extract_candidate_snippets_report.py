import json
import tempfile
import unittest
from pathlib import Path

from scripts.extract_candidate_snippets import load_high_priority_ranked_candidates


class ExtractCandidateSnippetsReportTests(unittest.TestCase):
    def test_ranked_report_reader_filters_high_priority_candidates_only(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            ranked_path = Path(tmp_dir) / "ranked_definition_candidates.json"
            ranked_path.write_text(
                json.dumps(
                    {
                        "ranked_candidates": [
                            {"source_title": "High", "priority_bucket": "high"},
                            {"source_title": "Medium", "priority_bucket": "medium"},
                            {"source_title": "Low", "priority_bucket": "low"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            candidates = load_high_priority_ranked_candidates(ranked_path)

        self.assertEqual(
            [{"source_title": "High", "priority_bucket": "high"}],
            candidates,
        )


if __name__ == "__main__":
    unittest.main()
