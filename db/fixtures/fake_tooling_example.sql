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
  example_text,
  when_to_use,
  when_not_to_use,
  inspection_method,
  cost_warning
)
SELECT
  fake_concept.id,
  'blank holder',
  'Fake deep-drawing die example linking a blank holder to a fake form-control concept.',
  'Use this fake example when a drawn cup demo needs a simple blank-holder conversation.',
  'Do not use this fake example for validated tooling design or production process limits.',
  'Fake inspection method: review a non-production tryout panel with a check fixture note.',
  'Fake cost warning: blank-holder changes can add tryout time and soft tooling expense.'
FROM fake_concept;
