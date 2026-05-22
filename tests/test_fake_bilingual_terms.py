from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_bilingual_terms.sql"
VERIFY_SCRIPT_PATH = ROOT / "scripts" / "build_fake_bilingual_terms_verification.py"


class FakeBilingualTermsTests(unittest.TestCase):
    def test_fixture_inserts_one_fake_concept_with_primary_asme_english_and_spanish_terms(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("INSERT INTO concepts", sql)
        self.assertIn("'fake-bilingual-profile-demo'", sql)
        self.assertIn("INSERT INTO terms", sql)
        self.assertIn("'en', 'asme_2018_en', 'Fake profile control'", sql)
        self.assertIn("'es', 'asme_2009_es', 'Control de perfil falso'", sql)
        self.assertEqual(sql.count("TRUE"), 2)
        self.assertNotIn("DATABASE_URL", sql)
        self.assertNotIn("postgres://", sql.lower())
        self.assertNotIn("postgresql://", sql.lower())

    def test_fixture_covers_english_abbreviation_when_present(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("abbreviation", sql)
        self.assertIn("'FPC'", sql)
        self.assertIn("'en', 'asme_2018_en', 'Fake profile control', 'FPC'", sql)
        self.assertIn("'es', 'asme_2009_es', 'Control de perfil falso', NULL", sql)

    def test_local_script_prints_flat_review_view_columns_for_bilingual_terms(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT_PATH), "--print"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("CREATE OR REPLACE VIEW v_glossary_flat", result.stdout)
        self.assertIn("FROM v_glossary_flat", result.stdout)
        self.assertIn("asme_2018_english_term", result.stdout)
        self.assertIn("english_abbreviation", result.stdout)
        self.assertIn("asme_2009_spanish_term", result.stdout)
        self.assertIn("fake-bilingual-profile-demo", result.stdout)

    def test_local_script_keeps_relational_terms_as_source_of_truth(self):
        result = subprocess.run(
            [sys.executable, str(VERIFY_SCRIPT_PATH), "--print"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("-- Relational source-of-truth output.", result.stdout)
        self.assertIn("JOIN terms", result.stdout)
        self.assertIn("t.source_type", result.stdout)
        self.assertIn("t.language", result.stdout)
        self.assertIn("t.abbreviation", result.stdout)
        self.assertNotIn("Fake profile control", (ROOT / "db" / "views" / "v_glossary_flat.sql").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
