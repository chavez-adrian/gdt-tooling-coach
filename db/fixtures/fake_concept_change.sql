-- Fake/non-normative 2009-vs-2018 concept change fixture.
-- Disposable PostgreSQL only; no Neon credentials required.

WITH source_2009 AS (
  INSERT INTO sources (
    source_type,
    title,
    edition,
    language,
    file_name,
    notes
  )
  VALUES (
    'asme_2009_es_fake',
    'Fake ASME Y14.5 2009 Spanish Source',
    '2009 fake Spanish edition',
    'es',
    'fake-asme-y14-5-2009-es.pdf',
    'Fake source link for local concept-change verification only.'
  )
  RETURNING id
),
source_2018 AS (
  INSERT INTO sources (
    source_type,
    title,
    edition,
    language,
    file_name,
    notes
  )
  VALUES (
    'asme_2018_en_fake',
    'Fake ASME Y14.5 2018 English Source',
    '2018 fake English edition',
    'en',
    'fake-asme-y14-5-2018-en.pdf',
    'Fake source link for local concept-change verification only.'
  )
  RETURNING id
),
changed_concept AS (
  INSERT INTO concepts (
    slug,
    category,
    subcategory,
    difficulty_level,
    notes
  )
  SELECT
    'fake-concept-changed-meaning',
    'fake-concept-comparison',
    'changed-meaning',
    2,
    'Fake concept whose meaning changed between fake 2009 and fake 2018 sources.'
  FROM source_2009
  CROSS JOIN source_2018
  RETURNING id
),
no_change_concept AS (
  INSERT INTO concepts (
    slug,
    category,
    subcategory,
    difficulty_level,
    notes
  )
  SELECT
    'fake-concept-no-significant-change',
    'fake-concept-comparison',
    'no-significant-change',
    1,
    'Fake concept whose meaning stays stable between fake 2009 and fake 2018 sources.'
  FROM source_2009
  CROSS JOIN source_2018
  RETURNING id
)
INSERT INTO concept_changes (
  concept_id,
  change_type,
  change_summary,
  impact_for_learning,
  impact_for_tooling,
  source_2009_id,
  source_2018_id
)
SELECT
  changed_concept.id,
  'changed_meaning',
  'Fake 2018 wording narrows the comparison focus.',
  'Learners must review the newer fake phrasing before reusing memory aids.',
  'Tooling should flag stale fake 2009 guidance for review.',
  source_2009.id,
  source_2018.id
FROM changed_concept
CROSS JOIN source_2009
CROSS JOIN source_2018
UNION ALL
SELECT
  no_change_concept.id,
  'no_significant_change',
  'Fake 2018 wording preserves the fake 2009 meaning.',
  'Learners may keep the same fake mental model after review.',
  'Tooling can show a low-priority fake confirmation note.',
  source_2009.id,
  source_2018.id
FROM no_change_concept
CROSS JOIN source_2009
CROSS JOIN source_2018;
