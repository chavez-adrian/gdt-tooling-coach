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


if __name__ == "__main__":
    unittest.main()
