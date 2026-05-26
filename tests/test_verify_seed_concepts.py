import unittest

from scripts.verify_seed_concepts import format_verification_summary, verify_seed_gate


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

    def test_verifies_only_approved_execute_gate_and_parameterized_insert_sql(self):
        result = verify_seed_gate([valid_concept()], existing_concepts=[])

        self.assertTrue(result["approved_execute_gate_verified"])
        self.assertTrue(result["parameterized_insert_verified"])
        self.assertEqual(["--execute-approved-insert"], result["live_write_gates"])
        self.assertEqual([], result["forbidden_sql_verbs_found"])

    def test_verifies_invalid_manifest_concepts_are_blocked(self):
        result = verify_seed_gate(
            [
                valid_concept(concept_key="published", review_state="published"),
                valid_concept(concept_key="validated", review_state="validated"),
                valid_concept(concept_key="definition_field", definition="forbidden"),
                valid_concept(
                    concept_key="long_content",
                    notes=" ".join(f"word{i}" for i in range(25)),
                ),
                valid_concept(concept_key="duplicate"),
                valid_concept(concept_key="duplicate"),
                valid_concept(concept_key="already_exists"),
            ],
            existing_concepts=[{"slug": "already_exists"}],
        )

        self.assertTrue(result["invalid_manifest_blocks_verified"])
        self.assertEqual(
            {
                "concept_already_exists": 1,
                "content_too_long": 1,
                "definition_field_not_allowed": 1,
                "duplicate_concept_key": 2,
                "review_state_not_needs_human_review": 2,
                "validated_state_not_allowed": 1,
            },
            result["block_reasons"],
        )

    def test_verifier_summary_is_credential_safe_and_keeps_snippets_separate(self):
        result = verify_seed_gate([valid_concept()], existing_concepts=[])

        summary = format_verification_summary(result)

        self.assertTrue(result["credential_safe_output_verified"])
        self.assertTrue(result["snippets_unchanged_verified"])
        self.assertTrue(result["snippet_assignment_unchanged_verified"])
        self.assertIn("Credential-safe output: true", summary)
        self.assertIn("Snippets modified: false", summary)
        self.assertIn("Snippet assignments modified: false", summary)
        self.assertNotIn("DATABASE_URL", summary)
        self.assertNotIn("postgresql://", summary)
        self.assertNotIn("password", summary.lower())
        self.assertNotIn("token", summary.lower())


if __name__ == "__main__":
    unittest.main()
