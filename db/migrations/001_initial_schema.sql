-- 001_initial_schema.sql
-- Initial PostgreSQL/Neon-compatible schema for gdt-tooling-coach.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type TEXT NOT NULL,
  title TEXT NOT NULL,
  edition TEXT,
  language TEXT NOT NULL,
  file_name TEXT,
  section TEXT,
  page TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_sources_updated_at ON sources;
CREATE TRIGGER trg_sources_updated_at
BEFORE UPDATE ON sources
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS concepts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  subcategory TEXT,
  current_status TEXT NOT NULL DEFAULT 'needs_review',
  difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_concepts_updated_at ON concepts;
CREATE TRIGGER trg_concepts_updated_at
BEFORE UPDATE ON concepts
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS terms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  language TEXT NOT NULL,
  source_type TEXT NOT NULL,
  term TEXT NOT NULL,
  abbreviation TEXT,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_terms_updated_at ON terms;
CREATE TRIGGER trg_terms_updated_at
BEFORE UPDATE ON terms
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS definitions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  source_id UUID NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
  definition_type TEXT NOT NULL,
  text TEXT NOT NULL,
  word_count INTEGER CHECK (word_count IS NULL OR word_count >= 0),
  extraction_type TEXT NOT NULL,
  is_literal BOOLEAN NOT NULL DEFAULT FALSE,
  copyright_notes TEXT,
  review_status TEXT NOT NULL DEFAULT 'raw_import',
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_definitions_literal_limit CHECK (
    is_literal = FALSE OR word_count <= 80
  )
);

DROP TRIGGER IF EXISTS trg_definitions_updated_at ON definitions;
CREATE TRIGGER trg_definitions_updated_at
BEFORE UPDATE ON definitions
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS symbols (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  unicode_symbol TEXT,
  unicode_reliable BOOLEAN NOT NULL DEFAULT FALSE,
  svg_path TEXT,
  text_fallback TEXT,
  symbol_name TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_symbols_updated_at ON symbols;
CREATE TRIGGER trg_symbols_updated_at
BEFORE UPDATE ON symbols
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS concept_changes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  change_type TEXT NOT NULL DEFAULT 'needs_review',
  change_summary TEXT,
  impact_for_learning TEXT,
  impact_for_tooling TEXT,
  source_2018_id UUID REFERENCES sources(id) ON DELETE SET NULL,
  source_2009_id UUID REFERENCES sources(id) ON DELETE SET NULL,
  review_status TEXT NOT NULL DEFAULT 'needs_human_review',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_concept_changes_updated_at ON concept_changes;
CREATE TRIGGER trg_concept_changes_updated_at
BEFORE UPDATE ON concept_changes
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS tooling_examples (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  concept_id UUID NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
  tool_component TEXT NOT NULL,
  example_text TEXT NOT NULL,
  when_to_use TEXT,
  when_not_to_use TEXT,
  inspection_method TEXT,
  cost_warning TEXT,
  review_status TEXT NOT NULL DEFAULT 'needs_human_review',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_tooling_examples_updated_at ON tooling_examples;
CREATE TRIGGER trg_tooling_examples_updated_at
BEFORE UPDATE ON tooling_examples
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

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
  exercise_status TEXT NOT NULL DEFAULT 'draft',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_adaptive_exercises_updated_at ON adaptive_exercises;
CREATE TRIGGER trg_adaptive_exercises_updated_at
BEFORE UPDATE ON adaptive_exercises
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS review_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_table TEXT NOT NULL,
  entity_id UUID NOT NULL,
  previous_status TEXT,
  new_status TEXT NOT NULL,
  reviewer TEXT,
  review_note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_terms_concept_id ON terms(concept_id);
CREATE INDEX IF NOT EXISTS idx_definitions_concept_id ON definitions(concept_id);
CREATE INDEX IF NOT EXISTS idx_definitions_source_id ON definitions(source_id);
CREATE INDEX IF NOT EXISTS idx_symbols_concept_id ON symbols(concept_id);
CREATE INDEX IF NOT EXISTS idx_concept_changes_concept_id ON concept_changes(concept_id);
CREATE INDEX IF NOT EXISTS idx_tooling_examples_concept_id ON tooling_examples(concept_id);
CREATE INDEX IF NOT EXISTS idx_course_question_patterns_source_id ON course_question_patterns(source_id);
CREATE INDEX IF NOT EXISTS idx_course_question_patterns_concept_id ON course_question_patterns(concept_id);
CREATE INDEX IF NOT EXISTS idx_adaptive_exercises_question_pattern_id ON adaptive_exercises(question_pattern_id);
CREATE INDEX IF NOT EXISTS idx_review_events_entity ON review_events(entity_table, entity_id);
