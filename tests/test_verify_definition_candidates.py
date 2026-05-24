import unittest

from scripts.verify_definition_candidates import summarize_candidate_report


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


if __name__ == "__main__":
    unittest.main()
