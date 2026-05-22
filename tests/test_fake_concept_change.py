from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_concept_change.sql"


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


if __name__ == "__main__":
    unittest.main()
