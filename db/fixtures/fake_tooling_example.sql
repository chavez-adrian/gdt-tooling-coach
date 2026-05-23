-- Fake/non-normative deep-drawing die tooling example fixture.
-- Disposable PostgreSQL only; no Neon credentials required.

WITH fake_concept AS (
  INSERT INTO concepts (
    slug,
    category,
    subcategory,
    difficulty_level,
    notes
  )
  VALUES (
    'fake-deep-drawing-die-demo',
    'fake-form-control',
    'fake-deep-drawing-tooling',
    2,
    'Fake GD&T concept used only to prove tooling-example linkage.'
  )
  RETURNING id
)
INSERT INTO tooling_examples (
  concept_id,
  tool_component,
  example_text
)
SELECT
  fake_concept.id,
  'blank holder',
  'Fake deep-drawing die example linking a blank holder to a fake form-control concept.'
FROM fake_concept;
