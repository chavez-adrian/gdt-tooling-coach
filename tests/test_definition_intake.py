import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.definition_intake import DefinitionIntakeError, intake_fake_definition


class FakeDefinitionIntakeTests(unittest.TestCase):
    def test_computes_word_count_for_fake_definition_text(self):
        record = intake_fake_definition(
            text="Fake summary text for local validation only.",
            extraction_type="summary",
        )

        self.assertEqual(record["word_count"], 7)
        self.assertEqual(record["text"], "Fake summary text for local validation only.")

    def test_rejects_literal_quote_over_eighty_words(self):
        text = " ".join(f"fakeword{i}" for i in range(81))

        with self.assertRaisesRegex(DefinitionIntakeError, "80 words"):
            intake_fake_definition(text=text, extraction_type="literal_quote")

    def test_literal_fake_quotes_require_literal_quote_extraction_type(self):
        with self.assertRaisesRegex(DefinitionIntakeError, "literal_quote"):
            intake_fake_definition(
                text="Fake literal quote under the limit.",
                extraction_type="summary",
                is_literal=True,
            )

    def test_valid_fake_paraphrase_over_eighty_words_is_stored(self):
        text = " ".join(f"fakeparaphrase{i}" for i in range(120))

        record = intake_fake_definition(
            text=text,
            extraction_type="paraphrase",
            definition_type="fake_paraphrase",
        )

        self.assertEqual(record["word_count"], 120)
        self.assertEqual(record["definition_type"], "fake_paraphrase")
        self.assertFalse(record["is_literal"])

    def test_imported_fake_definition_defaults_to_reviewable_unvalidated_states(self):
        record = intake_fake_definition(
            text="Fake derived summary for review.",
            extraction_type="summary",
            definition_type="fake_summary",
        )

        self.assertEqual(record["review_status"], "raw_import")
        self.assertEqual(record["validation_status"], "unvalidated")
        self.assertEqual(record["current_status"], "needs_review")


if __name__ == "__main__":
    unittest.main()
