import json
import tempfile
import unittest
from pathlib import Path

from scripts.locate_definition_candidates import build_definition_candidate_report


class DefinitionCandidateReportTests(unittest.TestCase):
    def test_missing_manifest_pdf_produces_no_candidate_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            manifest_path = project_root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    [
                        {
                            "title": "Missing Source",
                            "expected_local_path": "data/raw/missing.pdf",
                        }
                    ]
                ),
                encoding="utf-8",
            )

            report = build_definition_candidate_report(manifest_path, project_root)

        self.assertEqual([], report["candidate_pages"])
        self.assertEqual(1, report["summary"]["total_sources"])
        self.assertEqual(0, report["summary"]["existing_pdfs"])
        self.assertEqual(1, report["summary"]["missing_pdfs"])


if __name__ == "__main__":
    unittest.main()
