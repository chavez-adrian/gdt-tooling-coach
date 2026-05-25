import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "concept_seed_manifest.example.json"
REQUIRED_FIELDS = {
    "concept_key",
    "preferred_label_en",
    "concept_type",
    "review_state",
    "source_authority_hint",
    "notes",
}
EXPECTED_CONCEPT_KEYS = {
    "datum",
    "feature_control_frame",
    "tolerance_zone",
    "maximum_material_condition",
    "least_material_condition",
    "regardless_of_feature_size",
}
FORBIDDEN_FIELDS = {"definition", "definition_en", "definition_es", "text", "snippet_text"}


class ConceptSeedManifestTests(unittest.TestCase):
    def load_manifest(self):
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_contains_minimum_gdt_concepts_from_snippet_signals(self):
        manifest = self.load_manifest()

        self.assertTrue(EXPECTED_CONCEPT_KEYS.issubset({entry["concept_key"] for entry in manifest}))
        self.assertLessEqual(len(manifest), 8)

    def test_concept_keys_are_unique(self):
        manifest = self.load_manifest()
        keys = [entry["concept_key"] for entry in manifest]

        self.assertEqual(len(keys), len(set(keys)))

    def test_entries_have_required_fields_and_review_state(self):
        for entry in self.load_manifest():
            self.assertTrue(REQUIRED_FIELDS.issubset(entry))
            self.assertEqual("needs_human_review", entry["review_state"])
            self.assertNotEqual("validated", entry["review_state"])
            self.assertTrue(entry["concept_key"])
            self.assertTrue(entry["preferred_label_en"])
            self.assertTrue(entry["concept_type"])
            self.assertTrue(entry["source_authority_hint"])
            self.assertIn("preferred_label_es", entry)

    def test_manifest_does_not_store_definitions_or_long_content(self):
        serialized = json.dumps(self.load_manifest(), ensure_ascii=False).lower()

        for forbidden_field in FORBIDDEN_FIELDS:
            self.assertNotIn(f'"{forbidden_field}"', serialized)
        for entry in self.load_manifest():
            for value in entry.values():
                if isinstance(value, str):
                    self.assertLessEqual(len(value.split()), 24)
            self.assertNotIn(" is ", entry["notes"].lower())
            self.assertNotIn(" es ", entry["notes"].lower())


if __name__ == "__main__":
    unittest.main()
