-- Fake/non-normative source-to-definition trace fixture.
-- Disposable PostgreSQL only; no Neon credentials required.

WITH fake_source AS (
  INSERT INTO sources (
    source_type,
    title,
    edition,
    language,
    file_name,
    notes
  )
  VALUES (
    'fake_asme_aamc_style',
    'Fake ASME/AAMC Review Source',
    '2026 fake edition',
    'en',
    'fake-asme-aamc-review-source.pdf',
    'Fake file metadata: sha256:fake-source-definition-trace; bytes=12345; mime=application/pdf.'
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
    'fake-source-definition-demo',
    'fake-datum-reference',
    'fake-review-trace',
    1,
    'Fake concept for source-to-definition trace.'
  FROM fake_source
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
  copyright_notes
)
SELECT
  fake_concept.id,
  fake_source.id,
  'fake_reviewable_definition',
  'Fake reviewable definition linked to one fake source and one fake concept.',
  11,
  'fake_manual',
  FALSE,
  'Fake non-normative summary; no standard text copied.'
FROM fake_concept
CROSS JOIN fake_source;
