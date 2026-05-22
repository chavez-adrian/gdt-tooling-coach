from pathlib import Path
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_source_definition_trace.sql"
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
VERIFY_SCRIPT_PATH = ROOT / "scripts" / "build_fake_source_definition_trace.py"


class FakeSourceDefinitionTraceTests(unittest.TestCase):
    def test_fixture_registers_fake_asme_aamc_style_source_metadata(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("INSERT INTO sources", sql)
        self.assertIn("'fake_asme_aamc_style'", sql)
        self.assertIn("'Fake ASME/AAMC Review Source'", sql)
        self.assertIn("'2026 fake edition'", sql)
        self.assertIn("'en'", sql)
        self.assertIn("'fake-asme-aamc-review-source.pdf'", sql)
        self.assertIn("sha256:fake-source-definition-trace", sql)
        self.assertNotIn("DATABASE_URL", sql)
        self.assertNotIn("postgres://", sql.lower())
        self.assertNotIn("postgresql://", sql.lower())

    def test_fixture_links_fake_definition_to_fake_source_and_concept(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("fake_concept AS", sql)
        self.assertIn("INSERT INTO concepts", sql)
        self.assertIn("'fake-source-definition-demo'", sql)
        self.assertIn("INSERT INTO definitions", sql)
        self.assertIn("fake_concept.id", sql)
        self.assertIn("fake_source.id", sql)
        self.assertIn("CROSS JOIN fake_source", sql)

    def test_fixture_definition_has_review_metadata_and_defaults_unvalidated(self):
        fixture_sql = FIXTURE_PATH.read_text(encoding="utf-8")
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        definition_insert = re.search(
            r"INSERT INTO definitions\s*\((?P<columns>.*?)\)",
            fixture_sql,
            re.DOTALL,
        )

        self.assertIsNotNone(definition_insert)
        columns = definition_insert.group("columns")
        self.assertIn("extraction_type", columns)
        self.assertIn("word_count", columns)
        self.assertIn("is_literal", columns)
        self.assertIn("copyright_notes", columns)
        self.assertNotIn("review_status", columns)
        self.assertIn("'fake_manual'", fixture_sql)
        self.assertIn("11", fixture_sql)
        self.assertIn("FALSE", fixture_sql)
        self.assertIn("Fake non-normative summary; no standard text copied.", fixture_sql)
        self.assertRegex(
            schema_sql,
            r"review_status\s+TEXT\s+NOT\s+NULL\s+DEFAULT\s+'raw_import'",
        )
        self.assertNotIn("'validated'", fixture_sql)

    def test_local_script_prints_disposable_source_definition_verification_sql(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT_PATH), "--print"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("CREATE TABLE IF NOT EXISTS sources", result.stdout)
        self.assertIn("CREATE OR REPLACE VIEW v_glossary_flat", result.stdout)
        self.assertIn("fake-source-definition-demo", result.stdout)
        self.assertIn("JOIN sources", result.stdout)
        self.assertIn("JOIN definitions", result.stdout)
        self.assertNotIn("DATABASE_URL", result.stdout)
        self.assertNotIn("postgres://", result.stdout.lower())
        self.assertNotIn("postgresql://", result.stdout.lower())

    def test_local_script_prints_review_export_output_for_fake_definition(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT_PATH), "--print"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("-- Review/export inspection output.", result.stdout)
        self.assertIn("asme_2018_english_definition", result.stdout)
        self.assertIn("review_status", result.stdout)
        self.assertIn("FROM v_glossary_flat", result.stdout)
        self.assertIn("WHERE slug = 'fake-source-definition-demo'", result.stdout)


if __name__ == "__main__":
    unittest.main()
