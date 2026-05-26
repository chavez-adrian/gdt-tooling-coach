import json
import subprocess
import tempfile
import unittest
from pathlib import Path

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

    def test_signal_synonyms_map_to_six_approved_concept_keys(self):
        snippets = [
            snippet(matched_signal="feature control frame"),
            snippet(matched_signal="tolerance zone"),
            snippet(matched_signal="MMC"),
            snippet(matched_signal="LMC"),
            snippet(matched_signal="RFS"),
        ]
        concepts = [
            concept(id="concept-fcf", slug="feature_control_frame"),
            concept(id="concept-tz", slug="tolerance_zone"),
            concept(id="concept-mmc", slug="maximum_material_condition"),
            concept(id="concept-lmc", slug="least_material_condition"),
            concept(id="concept-rfs", slug="regardless_of_feature_size"),
        ]

        draft = build_assignment_draft(snippets, concepts)

        self.assertEqual(5, draft["ready_to_insert"])
        self.assertEqual(0, draft["blocked_snippets"])
        self.assertEqual(
            [
                "feature_control_frame",
                "tolerance_zone",
                "maximum_material_condition",
                "least_material_condition",
                "regardless_of_feature_size",
            ],
            [assignment["concept_key"] for assignment in draft["assignments"]],
        )
        self.assertEqual(
            [
                "concept-fcf",
                "concept-tz",
                "concept-mmc",
                "concept-lmc",
                "concept-rfs",
            ],
            [assignment["concept_id"] for assignment in draft["assignments"]],
        )

    def test_unmatched_signal_is_blocked_with_explicit_reason_codes(self):
        draft = build_assignment_draft(
            [snippet(matched_signal="thread profile")],
            [concept()],
        )

        self.assertEqual(0, draft["ready_to_insert"])
        self.assertEqual(1, draft["blocked_snippets"])
        self.assertEqual(1, draft["missing_concept_id"])
        self.assertEqual(
            {
                "snippet_index": 0,
                "matched_signal": "thread profile",
                "metadata_reason": None,
                "concept_key": None,
                "concept_id": None,
                "confidence": "none",
                "status": "blocked",
                "reason_codes": ["unmatched_signal", "missing_concept_id"],
                "audit_notes": [
                    "matched_signal is not one of the approved assignment signals",
                    "concept_id not found in existing concepts metadata",
                ],
            },
            draft["assignments"][0],
        )

    def test_cli_writes_local_assignment_draft_without_snippet_text(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_path = Path(tmp_dir) / "candidate_snippets.json"
            concepts_path = Path(tmp_dir) / "concepts.json"
            output_path = Path(tmp_dir) / "snippet_concept_assignment_draft.json"
            input_path.write_text(
                json.dumps(
                    {
                        "candidate_snippets": [
                            snippet(matched_signal="definición", page_number=214)
                        ]
                    }
                ),
                encoding="utf-8",
            )
            concepts_path.write_text(
                json.dumps(
                    [
                        concept(
                            id="concept-tolerance-zone",
                            slug="tolerance_zone",
                        )
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python",
                    "scripts/prepare_snippet_concept_assignment_draft.py",
                    "--input",
                    str(input_path),
                    "--concepts-fixture",
                    str(concepts_path),
                    "--output",
                    str(output_path),
                    "--skip-ignore-check",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Snippet concept assignment draft complete.", result.stdout)
        self.assertIn("Ready to insert: 1", result.stdout)
        self.assertNotIn("snippet_text", result.stdout)
        self.assertEqual("tolerance_zone", written["assignments"][0]["concept_key"])
        self.assertEqual(
            "spanish_definition_signal_allowed_metadata",
            written["assignments"][0]["metadata_reason"],
        )
        self.assertNotIn("snippet_text", json.dumps(written))


if __name__ == "__main__":
    unittest.main()
