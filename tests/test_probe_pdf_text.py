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

    def test_divides_zero_based_page_indexes_into_four_quartiles(self):
        self.assertEqual(
            probe_pdf_text.divide_page_indexes_into_quartiles(10),
            {
                "Q1": [0, 1, 2],
                "Q2": [3, 4, 5],
                "Q3": [6, 7],
                "Q4": [8, 9],
            },
        )

    def test_allocates_sample_counts_approximately_evenly_by_quartile(self):
        self.assertEqual(
            probe_pdf_text.allocate_sample_counts_by_quartile(6),
            {"Q1": 2, "Q2": 2, "Q3": 1, "Q4": 1},
        )

    def test_sample_plan_is_reproducible_with_fixed_seed(self):
        first_plan = probe_pdf_text.build_sample_plan(page_count=40, random_seed=123)
        second_plan = probe_pdf_text.build_sample_plan(page_count=40, random_seed=123)

        self.assertEqual(first_plan, second_plan)
        self.assertEqual(first_plan["random_seed"], 123)


if __name__ == "__main__":
    unittest.main()
