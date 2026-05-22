-- Fake/non-normative tracer bullet fixture for local review-view checks.
-- Does not require or contain Neon credentials.

WITH fake_source AS (
  INSERT INTO sources (
    source_type,
    title,
    edition,
    language,
    notes
  )
  VALUES (
    'fake_training_source',
    'Fake GD&T Training Source',
    'demo',
    'en',
    'Non-normative fixture for local verification only.'
  )
  RETURNING id
),
fake_concept AS (
  INSERT INTO concepts (
    slug,
    category,
    subcategory,
    difficulty_level,
    notes
  )
  SELECT
    'fake-flatness-demo',
    'fake-form-control',
    'fake-flat-surface',
    1,
    'Fake concept inserted by local tracer bullet.'
  FROM fake_source
  RETURNING id
),
fake_terms AS (
  INSERT INTO terms (
    concept_id,
    language,
    source_type,
    term,
    is_primary,
    notes
  )
  SELECT id, 'en', 'fake_training_en', 'Fake flatness', TRUE, 'Fake English term.'
  FROM fake_concept
  UNION ALL
  SELECT id, 'es', 'fake_training_es', 'Planitud falsa', TRUE, 'Fake Spanish term.'
  FROM fake_concept
  RETURNING id
)
INSERT INTO definitions (
  concept_id,
  source_id,
  definition_type,
  text,
  word_count,
  extraction_type,
  is_literal,
  notes
)
SELECT
  fake_concept.id,
  fake_source.id,
  'fake_training_definition',
  'Fake non-normative definition for local tracer bullet review.',
  8,
  'fake_manual',
  FALSE,
  'Review status intentionally omitted so the schema default stays unvalidated.'
FROM fake_concept
CROSS JOIN fake_source
WHERE EXISTS (SELECT 1 FROM fake_terms);
