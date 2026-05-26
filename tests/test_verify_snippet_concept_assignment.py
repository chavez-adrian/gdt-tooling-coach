import unittest

from scripts.verify_snippet_concept_assignment import verify_assignment_draft


def snippet(**overrides):
    row = {
        "source_title": "ASME",
        "source_type": "asme_2018_en",
        "language": "en",
        "page_number": 12,
        "matched_signal": "datum",
        "snippet_text": "literal text must never appear in verifier output",
    }
    row.update(overrides)
    return row


def assignment(**overrides):
    row = {
        "snippet_index": 0,
        "matched_signal": "datum",
        "metadata_reason": None,
        "concept_key": "datum",
        "concept_id": "concept-datum",
        "status": "ready_to_insert",
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


class VerifySnippetConceptAssignmentTests(unittest.TestCase):
    def test_valid_assignment_report_is_safe_and_distributed(self):
        result = verify_assignment_draft(
            snippets=[
                snippet(),
                snippet(
                    source_type="asme_2009_es",
                    language="es",
                    matched_signal="MMC",
                ),
            ],
            assignment_draft={
                "assignments": [
                    assignment(),
                    assignment(
                        snippet_index=1,
                        matched_signal="MMC",
                        concept_key="maximum_material_condition",
                        concept_id="concept-mmc",
                    ),
                ]
            },
            concepts=[
                concept(),
                concept(id="concept-mmc", slug="maximum_material_condition"),
            ],
            manifest_concepts=[
                {"concept_key": "datum"},
                {"concept_key": "maximum_material_condition"},
            ],
        )

        self.assertTrue(result["passed"])
        self.assertEqual(2, result["total_assignments"])
        self.assertEqual({}, result["block_reasons"])
        self.assertEqual({"datum": 1, "maximum_material_condition": 1}, result["assignments_by_concept_key"])
        self.assertEqual({"asme_2009_es|es": 1, "asme_2018_en|en": 1}, result["assignments_by_source_type_language"])
        self.assertEqual({"MMC": 1, "datum": 1}, result["assignments_by_matched_signal"])
        self.assertEqual([], result["unknown_concept_ids"])
        self.assertEqual([], result["snippets_without_assignment"])
        self.assertTrue(result["no_database_writes"])

    def test_rejects_missing_duplicate_and_unknown_assignment_cardinality(self):
        result = verify_assignment_draft(
            snippets=[
                snippet(),
                snippet(matched_signal="MMC"),
                snippet(matched_signal="RFS"),
            ],
            assignment_draft={
                "assignments": [
                    assignment(),
                    assignment(
                        snippet_index=0,
                        concept_id="concept-datum-duplicate",
                    ),
                    assignment(
                        snippet_index=1,
                        matched_signal="MMC",
                        concept_key="maximum_material_condition",
                        concept_id="concept-missing",
                    ),
                ]
            },
            concepts=[concept()],
            manifest_concepts=[
                {"concept_key": "datum"},
                {"concept_key": "maximum_material_condition"},
                {"concept_key": "regardless_of_feature_size"},
            ],
        )

        self.assertFalse(result["passed"])
        self.assertEqual(
            {
                "duplicate_assignment": 1,
                "missing_assignment": 1,
                "unknown_concept_id": 2,
            },
            result["block_reasons"],
        )
        self.assertEqual(["concept-datum-duplicate", "concept-missing"], result["unknown_concept_ids"])
        self.assertEqual([2], result["snippets_without_assignment"])

    def test_rejects_manifest_mismatch_signal_mismatch_and_validated_concepts(self):
        result = verify_assignment_draft(
            snippets=[
                snippet(matched_signal="datum"),
                snippet(matched_signal="MMC"),
                snippet(matched_signal="RFS"),
            ],
            assignment_draft={
                "assignments": [
                    assignment(
                        concept_key="tolerance_zone",
                        concept_id="concept-tolerance-zone",
                    ),
                    assignment(
                        snippet_index=1,
                        matched_signal="MMC",
                        concept_key="outside_manifest",
                        concept_id="concept-outside",
                    ),
                    assignment(
                        snippet_index=2,
                        matched_signal="RFS",
                        concept_key="regardless_of_feature_size",
                        concept_id="concept-rfs",
                    ),
                ]
            },
            concepts=[
                concept(id="concept-tolerance-zone", slug="tolerance_zone"),
                concept(id="concept-outside", slug="outside_manifest"),
                concept(
                    id="concept-rfs",
                    slug="regardless_of_feature_size",
                    current_status="validated",
                ),
            ],
            manifest_concepts=[
                {"concept_key": "datum"},
                {"concept_key": "tolerance_zone"},
                {"concept_key": "maximum_material_condition"},
                {"concept_key": "regardless_of_feature_size"},
            ],
        )

        self.assertFalse(result["passed"])
        self.assertEqual(
            {
                "automatically_validated_concept": 1,
                "concept_key_not_in_manifest": 1,
                "signal_concept_mismatch": 2,
            },
            result["block_reasons"],
        )


if __name__ == "__main__":
    unittest.main()
