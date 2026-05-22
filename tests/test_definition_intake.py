import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.definition_intake import intake_fake_definition


class FakeDefinitionIntakeTests(unittest.TestCase):
    def test_computes_word_count_for_fake_definition_text(self):
        record = intake_fake_definition(
            text="Fake summary text for local validation only.",
            extraction_type="summary",
        )

        self.assertEqual(record["word_count"], 7)
        self.assertEqual(record["text"], "Fake summary text for local validation only.")


if __name__ == "__main__":
    unittest.main()
