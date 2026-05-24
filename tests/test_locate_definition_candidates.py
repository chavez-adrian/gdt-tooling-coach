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

    def test_returns_approximate_page_text_metrics(self):
        page_text = "Definition words here."
        result = analyze_definition_candidate_page(page_text, {"page_number": 16})

        self.assertEqual(len(page_text), result["approximate_char_count"])
        self.assertEqual(3, result["approximate_word_count"])

    def test_returns_no_candidate_for_pages_without_signals(self):
        result = analyze_definition_candidate_page(
            "This page only contains an exercise answer key.",
            {"source_id": "fake-source", "page_number": 17},
        )

        self.assertFalse(result["is_candidate"])
        self.assertEqual([], result["matched_signals"])
        self.assertEqual(0, result["signal_count"])

    def test_candidate_reason_summarizes_signals_without_page_text(self):
        result = analyze_definition_candidate_page(
            "Definition appears near a datum explanation that must not be echoed.",
            {"source_id": "fake-reason", "page_number": 18},
        )

        self.assertEqual(
            "matched 2 definition candidate signals: definition, datum",
            result["candidate_reason"],
        )
        self.assertNotIn("appears near", result["candidate_reason"])

    def test_public_metadata_shape_excludes_extracted_text_fields(self):
        page_text = "Glossary content that must remain in memory only."
        result = analyze_definition_candidate_page(
            page_text,
            {
                "source_id": "fake-safe",
                "page_number": 19,
                "content": page_text,
                "sample": "Glossary content",
                "text": page_text,
            },
        )

        self.assertEqual("fake-safe", result["source_id"])
        self.assertEqual(19, result["page_number"])
        self.assertNotIn("content", result)
        self.assertNotIn("sample", result)
        self.assertNotIn("text", result)
        self.assertNotIn(page_text, result.values())


if __name__ == "__main__":
    unittest.main()
