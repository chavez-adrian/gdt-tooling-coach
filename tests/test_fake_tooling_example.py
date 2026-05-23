from pathlib import Path
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_tooling_example.sql"
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
VERIFY_SCRIPT_PATH = ROOT / "scripts" / "build_fake_tooling_example_verification.py"


class FakeToolingExampleTests(unittest.TestCase):
    def test_fixture_links_one_fake_tooling_example_to_one_fake_concept(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("INSERT INTO concepts", sql)
        self.assertIn("'fake-deep-drawing-die-demo'", sql)
        self.assertIn("INSERT INTO tooling_examples", sql)
        self.assertIn("fake_concept.id", sql)
        self.assertIn("FROM fake_concept", sql)
        self.assertNotIn("DATABASE_URL", sql)
        self.assertNotIn("postgres://", sql.lower())
        self.assertNotIn("postgresql://", sql.lower())

    def test_fixture_includes_component_guidance_inspection_and_cost_fields(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("tool_component", sql)
        self.assertIn("when_to_use", sql)
        self.assertIn("when_not_to_use", sql)
        self.assertIn("inspection_method", sql)
        self.assertIn("cost_warning", sql)
        self.assertIn("'blank holder'", sql)
        self.assertIn("Use this fake example", sql)
        self.assertIn("Do not use this fake example", sql)
        self.assertIn("Fake inspection method", sql)
        self.assertIn("Fake cost warning", sql)

    def test_fixture_uses_unvalidated_tooling_example_review_default(self):
        fixture_sql = FIXTURE_PATH.read_text(encoding="utf-8")
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        tooling_insert = re.search(
            r"INSERT INTO tooling_examples\s*\((?P<columns>.*?)\)",
            fixture_sql,
            re.DOTALL,
        )

        self.assertIsNotNone(tooling_insert)
        self.assertNotIn("review_status", tooling_insert.group("columns"))
        self.assertRegex(
            schema_sql,
            r"CREATE TABLE IF NOT EXISTS tooling_examples[\s\S]*?"
            r"review_status\s+TEXT\s+NOT\s+NULL\s+DEFAULT\s+'needs_human_review'",
        )
        self.assertNotIn("'validated'", fixture_sql)

    def test_local_script_prints_review_query_for_fake_tooling_example(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT_PATH), "--print"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("CREATE TABLE IF NOT EXISTS tooling_examples", result.stdout)
        self.assertIn("fake-deep-drawing-die-demo", result.stdout)
        self.assertIn("-- Review/export inspection output.", result.stdout)
        self.assertIn("JOIN tooling_examples", result.stdout)
        self.assertIn("tool_component", result.stdout)
        self.assertIn("when_to_use", result.stdout)
        self.assertIn("inspection_method", result.stdout)
        self.assertNotIn("DATABASE_URL", result.stdout)
        self.assertNotIn("postgres://", result.stdout.lower())
        self.assertNotIn("postgresql://", result.stdout.lower())

    def test_local_script_prints_full_tooling_acceptance_check(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT_PATH), "--print"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("-- Acceptance check: issue #10 fake tooling example.", result.stdout)
        self.assertIn("tooling_example_path_ok", result.stdout)
        self.assertIn("tooling_guidance_fields_ok", result.stdout)
        self.assertIn("tooling_review_status_unvalidated_ok", result.stdout)
        self.assertIn("te.tool_component = 'blank holder'", result.stdout)
        self.assertIn("te.review_status = 'needs_human_review'", result.stdout)
        self.assertIn("te.review_status <> 'validated'", result.stdout)


if __name__ == "__main__":
    unittest.main()
