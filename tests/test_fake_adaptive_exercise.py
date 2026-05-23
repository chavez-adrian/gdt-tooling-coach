from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "db" / "fixtures" / "fake_adaptive_exercise.sql"


class FakeAdaptiveExerciseTests(unittest.TestCase):
    def test_fixture_links_fake_question_pattern_to_fake_source_and_concept(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("INSERT INTO sources", sql)
        self.assertIn("'aamc_course_fake'", sql)
        self.assertIn("INSERT INTO concepts", sql)
        self.assertIn("'fake-course-question-datum-target'", sql)
        self.assertIn("INSERT INTO course_question_patterns", sql)
        self.assertIn("fake_source.id", sql)
        self.assertIn("fake_concept.id", sql)
        self.assertIn("FROM fake_source", sql)
        self.assertIn("CROSS JOIN fake_concept", sql)
        self.assertNotIn("DATABASE_URL", sql)
        self.assertNotIn("postgres://", sql.lower())
        self.assertNotIn("postgresql://", sql.lower())


if __name__ == "__main__":
    unittest.main()
