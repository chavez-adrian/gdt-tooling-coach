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

    def test_detects_spanish_definition_and_symbol_signals(self):
        result = analyze_definition_candidate_page(
            "La definición del símbolo aparece en la terminología del anexo.",
            {"source_id": "fake-spanish", "page_number": 8},
        )

        self.assertEqual(["símbolo", "definición", "terminología"], result["matched_signals"])
        self.assertEqual(3, result["signal_count"])

    def test_detects_gdt_definition_signals(self):
        result = analyze_definition_candidate_page(
            "Datum references define the feature control frame and tolerance zone.",
            {"source_id": "fake-gdt", "page_number": 12},
        )

        self.assertEqual(
            ["datum", "feature control frame", "tolerance zone"],
            result["matched_signals"],
        )
        self.assertEqual(3, result["signal_count"])


if __name__ == "__main__":
    unittest.main()
