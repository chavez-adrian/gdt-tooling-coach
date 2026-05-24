import unittest

from scripts.locate_definition_candidates import analyze_definition_candidate_page


class DefinitionCandidateDetectionTests(unittest.TestCase):
    def test_detects_english_definition_signal(self):
        result = analyze_definition_candidate_page(
            "This page introduces a definition for a controlled feature.",
            {"source_id": "fake-source", "page_number": 3},
        )

        self.assertEqual(["definition"], result["matched_signals"])
        self.assertEqual(1, result["signal_count"])
        self.assertEqual("fake-source", result["source_id"])
        self.assertEqual(3, result["page_number"])


if __name__ == "__main__":
    unittest.main()
