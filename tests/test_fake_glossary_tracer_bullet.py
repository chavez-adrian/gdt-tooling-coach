from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_glossary_tracer_bullet.sql"
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"


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


if __name__ == "__main__":
    unittest.main()
