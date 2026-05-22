from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_source_definition_trace.sql"


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


if __name__ == "__main__":
    unittest.main()
