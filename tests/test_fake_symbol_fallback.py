from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_symbol_fallback.sql"


class FakeSymbolFallbackTests(unittest.TestCase):
    def test_fixture_stores_fake_symbol_unicode_with_reliability_flag(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("INSERT INTO concepts", sql)
        self.assertIn("'fake-symbol-position-demo'", sql)
        self.assertIn("INSERT INTO symbols", sql)
        self.assertIn("unicode_symbol", sql)
        self.assertIn("unicode_reliable", sql)
        self.assertIn("'⌖'", sql)
        self.assertIn("TRUE", sql)
        self.assertNotIn("DATABASE_URL", sql)
        self.assertNotIn("postgres://", sql.lower())
        self.assertNotIn("postgresql://", sql.lower())

    def test_fixture_stores_svg_path_and_text_fallback_on_same_symbol_row(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("svg_path", sql)
        self.assertIn("text_fallback", sql)
        self.assertIn("'M 4 12 H 20 M 12 4 V 20'", sql)
        self.assertIn("'position symbol'", sql)


if __name__ == "__main__":
    unittest.main()
