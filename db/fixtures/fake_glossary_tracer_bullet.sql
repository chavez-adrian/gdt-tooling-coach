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
)
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
FROM fake_source;
