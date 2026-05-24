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


if __name__ == "__main__":
    unittest.main()
