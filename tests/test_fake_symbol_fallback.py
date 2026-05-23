from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_symbol_fallback.sql"
VIEW_PATH = ROOT / "db" / "views" / "v_glossary_flat.sql"
DOC_PATH = ROOT / "docs" / "symbol_display_fallback.md"
VERIFY_SCRIPT_PATH = ROOT / "scripts" / "build_fake_symbol_fallback_verification.py"


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

    def test_flat_review_view_exposes_symbol_fallback_fields(self):
        view_sql = VIEW_PATH.read_text(encoding="utf-8")

        self.assertIn("s.unicode_symbol", view_sql)
        self.assertIn("s.unicode_reliable", view_sql)
        self.assertIn("s.svg_path", view_sql)
        self.assertIn("s.text_fallback", view_sql)
        self.assertIn("LEFT JOIN symbols s", view_sql)

    def test_docs_define_symbol_display_priority(self):
        doc = DOC_PATH.read_text(encoding="utf-8")

        unicode_pos = doc.index("1. Unicode")
        svg_pos = doc.index("2. SVG")
        text_pos = doc.index("3. Text fallback")

        self.assertLess(unicode_pos, svg_pos)
        self.assertLess(svg_pos, text_pos)
        self.assertIn("unicode_reliable", doc)

    def test_local_script_prints_symbol_fallback_verification_sql_without_credentials(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT_PATH), "--print"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("DROP VIEW IF EXISTS public.v_glossary_flat", result.stdout)
        self.assertIn("CREATE VIEW public.v_glossary_flat", result.stdout)
        self.assertIn("fake-symbol-position-demo", result.stdout)
        self.assertIn("unicode_symbol", result.stdout)
        self.assertIn("unicode_reliable", result.stdout)
        self.assertIn("svg_path", result.stdout)
        self.assertIn("text_fallback", result.stdout)
        self.assertIn("symbol_fallback_path_ok", result.stdout)
        self.assertNotIn("DATABASE_URL", result.stdout)
        self.assertNotIn("postgres://", result.stdout.lower())
        self.assertNotIn("postgresql://", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
