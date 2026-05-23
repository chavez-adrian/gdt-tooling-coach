-- 002_adaptive_exercises.sql
-- Adds fake-course-question and adaptive-exercise storage after the live 001 migration.

CREATE TABLE IF NOT EXISTS course_question_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id UUID NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
  concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  question_pattern TEXT NOT NULL,
  context TEXT,
  application_area TEXT,
  difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_course_question_patterns_updated_at ON course_question_patterns;
CREATE TRIGGER trg_course_question_patterns_updated_at
BEFORE UPDATE ON course_question_patterns
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS adaptive_exercises (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question_pattern_id UUID NOT NULL REFERENCES course_question_patterns(id) ON DELETE CASCADE,
  exercise_prompt TEXT NOT NULL,
  context TEXT,
  application_area TEXT,
  difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
  rubric TEXT,
  feedback_if_wrong TEXT,
  exercise_status TEXT NOT NULL DEFAULT 'draft',
  review_status TEXT NOT NULL DEFAULT 'needs_human_review',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_adaptive_exercises_updated_at ON adaptive_exercises;
CREATE TRIGGER trg_adaptive_exercises_updated_at
BEFORE UPDATE ON adaptive_exercises
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_course_question_patterns_source_id ON course_question_patterns(source_id);
CREATE INDEX IF NOT EXISTS idx_course_question_patterns_concept_id ON course_question_patterns(concept_id);
CREATE INDEX IF NOT EXISTS idx_adaptive_exercises_question_pattern_id ON adaptive_exercises(question_pattern_id);
