import json
import subprocess
import tempfile
import unittest
from pathlib import Path

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

    def test_cli_reads_artifacts_and_prints_sanitized_total_assignment_evidence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            snippets_path = Path(tmp_dir) / "candidate_snippets.json"
            draft_path = Path(tmp_dir) / "snippet_concept_assignment_draft.json"
            concepts_path = Path(tmp_dir) / "concepts.json"
            manifest_path = Path(tmp_dir) / "manifest.json"
            snippets_path.write_text(
                json.dumps({"candidate_snippets": [snippet()]}),
                encoding="utf-8",
            )
            draft_path.write_text(
                json.dumps({"assignments": [assignment()]}),
                encoding="utf-8",
            )
            concepts_path.write_text(json.dumps([concept()]), encoding="utf-8")
            manifest_path.write_text(json.dumps([{"concept_key": "datum"}]), encoding="utf-8")

            result = subprocess.run(
                [
                    "python",
                    "scripts/verify_snippet_concept_assignment.py",
                    "--input",
                    str(snippets_path),
                    "--assignment-draft",
                    str(draft_path),
                    "--concepts-fixture",
                    str(concepts_path),
                    "--manifest",
                    str(manifest_path),
                    "--expected-total",
                    "1",
                    "--database-url",
                    "postgresql://user:password@hidden-host/db",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Snippet concept assignment verification complete.", result.stdout)
        self.assertIn("Total assignments: 1", result.stdout)
        self.assertIn("Assignments by concept_key: datum=1", result.stdout)
        self.assertIn("No database writes: true", result.stdout)
        self.assertNotIn("literal text must never appear", result.stdout)
        self.assertNotIn("snippet_text", result.stdout)
        self.assertNotIn("DATABASE_URL", result.stdout)
        self.assertNotIn("password", result.stdout)
        self.assertNotIn("hidden-host", result.stdout)


if __name__ == "__main__":
    unittest.main()
