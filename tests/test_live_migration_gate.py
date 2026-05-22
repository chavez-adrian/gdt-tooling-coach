from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GATE_DOC_PATH = ROOT / "docs" / "live_migration_gate.md"


class LiveMigrationGateTests(unittest.TestCase):
    def test_gate_confirms_target_without_storing_secrets(self):
        text = GATE_DOC_PATH.read_text(encoding="utf-8")
        lower_text = text.lower()

        self.assertIn("Neon project: `gdt-tooling-coach`", text)
        self.assertIn("Database: `gdt_tooling_coach`", text)
        self.assertIn("Connection owner: `neondb_owner`", text)
        self.assertNotIn("postgres://", lower_text)
        self.assertNotIn("postgresql://", lower_text)
        self.assertNotIn("password=", lower_text)
        self.assertNotIn("database_url=", lower_text)


if __name__ == "__main__":
    unittest.main()
