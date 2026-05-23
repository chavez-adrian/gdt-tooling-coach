import unittest

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


if __name__ == "__main__":
    unittest.main()
