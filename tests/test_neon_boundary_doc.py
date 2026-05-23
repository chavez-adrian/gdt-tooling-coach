from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "neon_boundary.md"


class NeonBoundaryDocTests(unittest.TestCase):
    def test_document_records_required_decisions(self):
        text = DOC_PATH.read_text(encoding="utf-8")

        required_phrases = [
            "Neon project",
            "Database",
            "Connection owner",
            "Allowed live actions",
            "Forbidden live actions",
            "Human approval",
            "Neon target boundary approved",
            "Live Neon execution still requires an explicit approval comment",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, text)

    def test_document_does_not_store_credentials(self):
        text = DOC_PATH.read_text(encoding="utf-8").lower()

        forbidden_fragments = [
            "postgresql://",
            "postgres://",
            "password=",
            "apikey",
            "api_key",
        ]

        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
