import unittest

from scripts import probe_pdf_text


class ProbePdfTextSamplingTests(unittest.TestCase):
    def test_sample_size_for_small_pdfs_uses_all_pages(self):
        self.assertEqual(probe_pdf_text.calculate_sample_size(0), 0)
        self.assertEqual(probe_pdf_text.calculate_sample_size(1), 1)
        self.assertEqual(probe_pdf_text.calculate_sample_size(4), 4)

    def test_sample_size_for_larger_pdfs_uses_ten_percent_with_bounds(self):
        self.assertEqual(probe_pdf_text.calculate_sample_size(5), 4)
        self.assertEqual(probe_pdf_text.calculate_sample_size(41), 5)
        self.assertEqual(probe_pdf_text.calculate_sample_size(1000), 25)


if __name__ == "__main__":
    unittest.main()
