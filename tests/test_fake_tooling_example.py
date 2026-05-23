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


if __name__ == "__main__":
    unittest.main()
