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
)
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
FROM fake_concept;
