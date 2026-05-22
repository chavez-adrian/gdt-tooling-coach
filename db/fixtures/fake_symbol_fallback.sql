-- Fake/non-normative symbol fallback fixture for local review checks.
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
    'fake-symbol-position-demo',
    'fake-location-control',
    'fake-symbol-fallback',
    2,
    'Fake concept inserted for local symbol fallback review.'
  )
  RETURNING id
)
INSERT INTO symbols (
  concept_id,
  unicode_symbol,
  unicode_reliable,
  svg_path,
  text_fallback,
  symbol_name,
  notes
)
SELECT
  id,
  '⌖',
  TRUE,
  'M 4 12 H 20 M 12 4 V 20',
  'position symbol',
  'Fake position symbol',
  'Unicode is reliable for this fake concept.'
FROM fake_concept;
