from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_glossary_tracer_bullet.sql"


class FakeGlossaryTracerBulletTests(unittest.TestCase):
    def test_fake_verification_fixture_exists_without_neon_credentials(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("fake-flatness-demo", sql)
        self.assertIn("INSERT INTO sources", sql)
        self.assertIn("INSERT INTO concepts", sql)
        self.assertNotIn("DATABASE_URL", sql)
        self.assertNotIn("postgres://", sql.lower())
        self.assertNotIn("postgresql://", sql.lower())


if __name__ == "__main__":
    unittest.main()
