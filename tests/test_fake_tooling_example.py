from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_tooling_example.sql"


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


if __name__ == "__main__":
    unittest.main()
