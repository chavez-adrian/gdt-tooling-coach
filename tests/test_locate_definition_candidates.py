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

    def test_matching_is_case_insensitive_for_gdt_acronyms(self):
        result = analyze_definition_candidate_page(
            "mmc, LmC, and rfs are listed in the DEFINITIONS section.",
            {"source_id": "fake-case", "page_number": 14},
        )

        self.assertEqual(["definitions", "MMC", "LMC", "RFS"], result["matched_signals"])

    def test_counts_unique_canonical_signals_in_stable_order(self):
        result = analyze_definition_candidate_page(
            "Definitions, terminology, terms, glossary, símbolos, definiciones, término.",
            {"source_id": "fake-count", "page_number": 15},
        )

        self.assertEqual(
            [
                "definitions",
                "terminology",
                "terms",
                "glossary",
                "símbolos",
                "definiciones",
                "término",
            ],
            result["matched_signals"],
        )
        self.assertEqual(7, result["signal_count"])


if __name__ == "__main__":
    unittest.main()
