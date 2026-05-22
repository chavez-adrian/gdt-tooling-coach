from pathlib import Path
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_glossary_tracer_bullet.sql"
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
VIEW_PATH = ROOT / "db" / "views" / "v_glossary_flat.sql"
VERIFY_SCRIPT_PATH = ROOT / "scripts" / "build_fake_glossary_verification.py"


class FakeGlossaryTracerBulletTests(unittest.TestCase):
    def test_fake_verification_fixture_exists_without_neon_credentials(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("fake-flatness-demo", sql)
        self.assertIn("INSERT INTO sources", sql)
        self.assertIn("INSERT INTO concepts", sql)
        self.assertNotIn("DATABASE_URL", sql)
        self.assertNotIn("postgres://", sql.lower())
        self.assertNotIn("postgresql://", sql.lower())

    def test_fixture_inserts_one_fake_english_and_spanish_primary_term(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("INSERT INTO terms", sql)
        self.assertIn("'en'", sql)
        self.assertIn("'es'", sql)
        self.assertIn("'Fake flatness'", sql)
        self.assertIn("'Planitud falsa'", sql)
        self.assertEqual(sql.count("TRUE"), 2)

    def test_fixture_inserts_fake_definition_that_defaults_to_unvalidated(self):
        fixture_sql = FIXTURE_PATH.read_text(encoding="utf-8")
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        definition_insert = re.search(
            r"INSERT INTO definitions\s*\((?P<columns>.*?)\)",
            fixture_sql,
            re.DOTALL,
        )

        self.assertIsNotNone(definition_insert)
        self.assertIn("Fake non-normative definition", fixture_sql)
        self.assertNotIn("review_status", definition_insert.group("columns"))
        self.assertRegex(
            schema_sql,
            r"review_status\s+TEXT\s+NOT\s+NULL\s+DEFAULT\s+'raw_import'",
        )
        self.assertRegex(
            schema_sql,
            r"current_status\s+TEXT\s+NOT\s+NULL\s+DEFAULT\s+'needs_review'",
        )

    def test_flat_view_is_separate_and_does_not_filter_out_fake_fixture(self):
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        view_sql = VIEW_PATH.read_text(encoding="utf-8")

        self.assertNotIn("CREATE OR REPLACE VIEW v_glossary_flat", schema_sql)
        self.assertIn("CREATE OR REPLACE VIEW v_glossary_flat", view_sql)
        self.assertNotIn("en.source_type = 'asme_2018_en'", view_sql)
        self.assertNotIn("es.source_type = 'asme_2009_es'", view_sql)
        self.assertNotIn("def_en.definition_type = 'normative_en_2018'", view_sql)

    def test_local_script_prints_postgres_verification_sql_without_credentials(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT_PATH), "--print"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("CREATE OR REPLACE VIEW v_glossary_flat", result.stdout)
        self.assertIn("fake-flatness-demo", result.stdout)
        self.assertIn("SELECT", result.stdout)
        self.assertIn("FROM v_glossary_flat", result.stdout)
        self.assertNotIn("DATABASE_URL", result.stdout)
        self.assertNotIn("postgres://", result.stdout.lower())
        self.assertNotIn("postgresql://", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
