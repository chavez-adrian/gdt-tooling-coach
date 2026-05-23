from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNBOOK_PATH = ROOT / "docs" / "database_runbook.md"


class DatabaseRunbookTests(unittest.TestCase):
    def test_runbook_lists_local_setup_and_database_commands(self):
        text = RUNBOOK_PATH.read_text(encoding="utf-8")

        required_phrases = [
            "python -m venv .venv",
            "python -m pip install -r requirements.txt",
            "copy .env.example .env",
            "python scripts/check_connection.py",
            "python scripts/run_migrations.py",
            "db/views/v_glossary_flat.sql",
        ]

        for phrase in required_phrases:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
