import json
import unittest

from scripts.prepare_snippet_concept_assignment_draft import build_assignment_draft


def snippet(**overrides):
    row = {
        "source_title": "ASME Y14.5-2018 English",
        "source_type": "asme_2018_en",
        "language": "en",
        "page_number": 12,
        "matched_signal": "datum",
        "snippet_text": "literal text must not be copied to the assignment draft",
    }
    row.update(overrides)
    return row


def concept(**overrides):
    row = {
        "id": "concept-datum",
        "slug": "datum",
        "category": "reference",
        "current_status": "needs_review",
    }
    row.update(overrides)
    return row


class PrepareSnippetConceptAssignmentDraftTests(unittest.TestCase):
    def test_exact_signal_maps_to_existing_concept_id_without_snippet_text(self):
        draft = build_assignment_draft([snippet()], [concept()])

        self.assertEqual(1, draft["total_snippets"])
        self.assertEqual(1, draft["ready_to_insert"])
        self.assertEqual(0, draft["blocked_snippets"])
        self.assertEqual(0, draft["missing_concept_id"])
        self.assertEqual(
            {
                "snippet_index": 0,
                "matched_signal": "datum",
                "metadata_reason": None,
                "concept_key": "datum",
                "concept_id": "concept-datum",
                "confidence": "high",
                "status": "ready_to_insert",
                "reason_codes": [],
                "audit_notes": [
                    "matched_signal normalized to approved concept_key",
                    "concept_id resolved from existing concepts metadata",
                ],
            },
            draft["assignments"][0],
        )
        serialized = json.dumps(draft)
        self.assertNotIn("snippet_text", serialized)
        self.assertNotIn("literal text must not be copied", serialized)


if __name__ == "__main__":
    unittest.main()
