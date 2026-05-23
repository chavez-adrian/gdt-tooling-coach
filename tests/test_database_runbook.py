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

    def test_runbook_explains_relational_source_of_truth_and_flat_view_role(self):
        text = RUNBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("PostgreSQL relational tables are the source of truth", text)
        self.assertIn("flat view is for review and export only", text)
        self.assertIn("Do not edit the flat view as canonical data", text)

    def test_runbook_references_neon_boundary_and_live_approval_gates(self):
        text = RUNBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("Neon boundary issue #2", text)
        self.assertIn("live approval issue #4", text)
        self.assertIn("docs/neon_boundary.md", text)
        self.assertIn("docs/live_migration_gate.md", text)
        self.assertIn("Do not run live Neon migrations from this runbook", text)


if __name__ == "__main__":
    unittest.main()
