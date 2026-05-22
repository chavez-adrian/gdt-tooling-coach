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


if __name__ == "__main__":
    unittest.main()
