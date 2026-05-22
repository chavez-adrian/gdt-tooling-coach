from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_concept_change.sql"
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"


class FakeConceptChangeTests(unittest.TestCase):
    def test_fixture_stores_2009_and_2018_source_links_for_changed_meaning(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("source_2009 AS", sql)
        self.assertIn("source_2018 AS", sql)
        self.assertIn("'Fake ASME Y14.5 2009 Spanish Source'", sql)
        self.assertIn("'Fake ASME Y14.5 2018 English Source'", sql)
        self.assertIn("source_2009_id", sql)
        self.assertIn("source_2018_id", sql)
        self.assertIn("source_2009.id", sql)
        self.assertIn("source_2018.id", sql)
        self.assertNotIn("DATABASE_URL", sql)
        self.assertNotIn("postgres://", sql.lower())
        self.assertNotIn("postgresql://", sql.lower())

    def test_fixture_stores_change_metadata_and_defaults_unvalidated_review_status(self):
        fixture_sql = FIXTURE_PATH.read_text(encoding="utf-8")
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        change_insert = re.search(
            r"INSERT INTO concept_changes\s*\((?P<columns>.*?)\)",
            fixture_sql,
            re.DOTALL,
        )

        self.assertIsNotNone(change_insert)
        columns = change_insert.group("columns")
        self.assertIn("change_type", columns)
        self.assertIn("change_summary", columns)
        self.assertIn("impact_for_learning", columns)
        self.assertIn("impact_for_tooling", columns)
        self.assertNotIn("review_status", columns)
        self.assertIn("'changed_meaning'", fixture_sql)
        self.assertIn("Fake 2018 wording narrows the comparison focus.", fixture_sql)
        self.assertIn("Learners must review the newer fake phrasing before reusing memory aids.", fixture_sql)
        self.assertIn("Tooling should flag stale fake 2009 guidance for review.", fixture_sql)
        self.assertRegex(
            schema_sql,
            r"review_status\s+TEXT\s+NOT\s+NULL\s+DEFAULT\s+'needs_human_review'",
        )
        self.assertNotIn("'validated'", fixture_sql)


if __name__ == "__main__":
    unittest.main()
