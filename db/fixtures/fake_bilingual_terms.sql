-- Fake/non-normative bilingual terminology fixture for local checks.
-- Does not require or contain Neon credentials.

WITH fake_concept AS (
  INSERT INTO concepts (
    slug,
    category,
    subcategory,
    difficulty_level,
    notes
  )
  VALUES (
    'fake-bilingual-profile-demo',
    'fake-profile-control',
    'fake-surface-profile',
    2,
    'Fake concept for bilingual terminology tracer bullet.'
  )
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
SELECT id, 'en', 'asme_2018_en', 'Fake profile control', TRUE, 'Fake English primary term.'
FROM fake_concept
UNION ALL
SELECT id, 'es', 'asme_2009_es', 'Control de perfil falso', TRUE, 'Fake Spanish primary term.'
FROM fake_concept;
