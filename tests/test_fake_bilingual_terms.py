from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_bilingual_terms.sql"


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


if __name__ == "__main__":
    unittest.main()
