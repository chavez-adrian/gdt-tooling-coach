from pathlib import Path
import re
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

    def test_fixture_derives_draft_adaptive_exercise_from_fake_question_pattern(self):
        sql = FIXTURE_PATH.read_text(encoding="utf-8")

        self.assertIn("fake_question_pattern AS", sql)
        self.assertIn("RETURNING id", sql)
        self.assertIn("INSERT INTO adaptive_exercises", sql)
        self.assertIn("question_pattern_id", sql)
        self.assertIn("fake_question_pattern.id", sql)
        self.assertIn("'draft'", sql)

    def test_draft_exercise_stores_learning_fields_and_defaults_unvalidated_review(self):
        fixture_sql = FIXTURE_PATH.read_text(encoding="utf-8")
        schema_sql = (ROOT / "db" / "migrations" / "001_initial_schema.sql").read_text(
            encoding="utf-8"
        )
        exercise_insert = re.search(
            r"INSERT INTO adaptive_exercises\s*\((?P<columns>.*?)\)",
            fixture_sql,
            re.DOTALL,
        )

        self.assertIsNotNone(exercise_insert)
        for field in [
            "context",
            "application_area",
            "difficulty_level",
            "rubric",
            "feedback_if_wrong",
        ]:
            self.assertIn(field, fixture_sql)
            self.assertRegex(schema_sql, rf"\b{field}\b")

        self.assertNotIn("review_status", exercise_insert.group("columns"))
        self.assertRegex(
            schema_sql,
            r"CREATE TABLE IF NOT EXISTS adaptive_exercises[\s\S]*?"
            r"review_status\s+TEXT\s+NOT\s+NULL\s+DEFAULT\s+'needs_human_review'",
        )
        self.assertNotIn("'validated'", fixture_sql)


if __name__ == "__main__":
    unittest.main()
