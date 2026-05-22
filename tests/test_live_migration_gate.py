from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
GATE_DOC_PATH = ROOT / "docs" / "live_migration_gate.md"
RUNNER_PATH = ROOT / "scripts" / "run_migrations.py"


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

    def test_gate_records_local_proof_from_issue_3_as_complete(self):
        text = GATE_DOC_PATH.read_text(encoding="utf-8")

        self.assertIn("Local proof from issue #3: complete", text)
        self.assertIn("scripts/build_fake_glossary_verification.py --print", text)
        self.assertIn("v_glossary_flat", text)

    def test_gate_lists_exact_live_command_and_existing_runner(self):
        text = GATE_DOC_PATH.read_text(encoding="utf-8")

        self.assertTrue(RUNNER_PATH.exists())
        self.assertIn("Exact live command", text)
        self.assertIn("python scripts/run_migrations.py", text)
        self.assertIn("Load the approved Neon `DATABASE_URL` outside git", text)

    def test_gate_describes_expected_successful_output(self):
        text = GATE_DOC_PATH.read_text(encoding="utf-8")

        self.assertIn("Expected successful output", text)
        self.assertIn("Applied: 001_initial_schema.sql", text)
        self.assertIn("Applied view: v_glossary_flat.sql", text)
        self.assertIn("Migrations and views are up to date.", text)

    def test_gate_lists_read_only_verification_and_live_result(self):
        text = GATE_DOC_PATH.read_text(encoding="utf-8")
        lower_text = text.lower()

        self.assertIn("Post-run read-only verification", text)
        self.assertIn("SELECT COUNT(*) AS applied_migrations", text)
        self.assertIn("FROM schema_migrations", text)
        self.assertIn("SELECT COUNT(*) AS flat_rows", text)
        self.assertIn("FROM v_glossary_flat", text)
        self.assertIn("Approval status: received", text)
        self.assertIn("first approved live migration run completed", text)
        self.assertIn("applied_migrations: 1", text)
        self.assertIn("core_tables: 9", text)
        self.assertNotIn("drop ", lower_text)
        self.assertNotIn("delete ", lower_text)
        self.assertNotIn("truncate ", lower_text)


if __name__ == "__main__":
    unittest.main()
