import unittest

from scripts.verify_seed_concepts import verify_seed_gate


def valid_concept(**overrides):
    concept = {
        "concept_key": "datum",
        "preferred_label_en": "Datum",
        "preferred_label_es": "Datum",
        "concept_type": "reference",
        "review_state": "needs_human_review",
        "source_authority_hint": "ASME Y14.5 / GD&T course metadata",
        "notes": "Seed label from matched_signal datum; no definition stored.",
    }
    concept.update(overrides)
    return concept


class VerifySeedConceptsTests(unittest.TestCase):
    def test_verifies_default_seed_gate_is_dry_run_without_writes(self):
        result = verify_seed_gate([valid_concept()], existing_concepts=[])

        self.assertTrue(result["default_dry_run_verified"])
        self.assertEqual("dry-run", result["default_mode"])
        self.assertFalse(result["default_database_writes_attempted"])
        self.assertFalse(result["default_execute_requested"])
        self.assertEqual(1, result["ready_to_insert"])
        self.assertEqual(0, result["blocked_concepts"])


if __name__ == "__main__":
    unittest.main()
