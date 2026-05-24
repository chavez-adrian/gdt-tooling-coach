import unittest

from scripts.extract_candidate_snippets import extract_candidate_snippets


class ExtractCandidateSnippetsTests(unittest.TestCase):
    def test_high_priority_candidate_with_definition_signal_yields_one_snippet(self):
        candidate = {
            "source_title": "ASME Y14.5",
            "source_type": "standard",
            "source_language": "en",
            "source_path": "data/sources/asme-y14-5.pdf",
            "page_number": 12,
            "candidate_score": 91,
            "global_rank": 1,
            "priority_bucket": "high",
        }
        page_text = "A datum is a theoretically exact point, axis, line, plane, or combination used for reference."

        snippets = extract_candidate_snippets([candidate], {("ASME Y14.5", 12): page_text})

        self.assertEqual(1, len(snippets))
        self.assertEqual("datum", snippets[0]["matched_signal"])
        self.assertEqual(page_text, snippets[0]["snippet_text"])

    def test_medium_and_low_priority_candidates_yield_no_snippets(self):
        candidates = [
            {
                "source_title": "Medium Source",
                "page_number": 1,
                "priority_bucket": "medium",
            },
            {
                "source_title": "Low Source",
                "page_number": 2,
                "priority_bucket": "low",
            },
        ]
        page_text_by_key = {
            ("Medium Source", 1): "A datum definition appears here.",
            ("Low Source", 2): "A datum definition appears here too.",
        }

        snippets = extract_candidate_snippets(candidates, page_text_by_key)

        self.assertEqual([], snippets)

    def test_literal_snippet_is_capped_at_80_words(self):
        candidate = {
            "source_title": "Long Source",
            "page_number": 7,
            "priority_bucket": "high",
        }
        page_text = " ".join(["datum"] + [f"word{i}" for i in range(1, 100)])

        snippets = extract_candidate_snippets([candidate], {("Long Source", 7): page_text})

        self.assertEqual(80, snippets[0]["snippet_word_count"])
        self.assertEqual(80, len(snippets[0]["snippet_text"].split()))

    def test_returns_at_most_three_snippets_per_page(self):
        candidate = {
            "source_title": "Crowded Source",
            "page_number": 4,
            "priority_bucket": "high",
        }
        page_text = (
            "First datum sentence. "
            "Second datum sentence. "
            "Third datum sentence. "
            "Fourth datum sentence."
        )

        snippets = extract_candidate_snippets([candidate], {("Crowded Source", 4): page_text})

        self.assertEqual(3, len(snippets))

    def test_detects_required_english_spanish_and_gdt_signals(self):
        signals = [
            "definition",
            "definitions",
            "definición",
            "definiciones",
            "terminology",
            "terminología",
            "glossary",
            "datum",
            "feature control frame",
            "tolerance zone",
            "MMC",
            "LMC",
            "RFS",
        ]
        candidates = [
            {"source_title": f"Signal {index}", "page_number": index, "priority_bucket": "high"}
            for index, _signal in enumerate(signals, start=1)
        ]
        page_text_by_key = {
            (f"Signal {index}", index): f"This page contains {signal} for review."
            for index, signal in enumerate(signals, start=1)
        }

        snippets = extract_candidate_snippets(candidates, page_text_by_key)

        self.assertEqual(signals, [snippet["matched_signal"] for snippet in snippets])


if __name__ == "__main__":
    unittest.main()
