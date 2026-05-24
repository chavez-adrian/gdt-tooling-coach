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


if __name__ == "__main__":
    unittest.main()
