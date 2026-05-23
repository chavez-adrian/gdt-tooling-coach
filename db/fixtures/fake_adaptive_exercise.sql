-- Fake issue #11 course question to adaptive exercise fixture.
-- All text is fabricated for local verification and is not normative course content.

WITH fake_source AS (
  INSERT INTO sources (
    source_type,
    title,
    edition,
    language,
    file_name,
    section,
    page,
    notes
  )
  VALUES (
    'aamc_course_fake',
    'Fake AAMC-style GD&T course handout',
    'fake training edition',
    'en',
    'fake-aamc-course-handout.pdf',
    'fake lesson 1',
    'fake page 1',
    'Fabricated source metadata for issue #11 only; no PDF was ingested.'
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
  VALUES (
    'fake-course-question-datum-target',
    'datum reference',
    'course question pattern',
    2,
    'Fake concept used to prove course-question traceability.'
  )
  RETURNING id
)
INSERT INTO course_question_patterns (
  source_id,
  concept_id,
  question_pattern,
  context,
  application_area,
  difficulty_level,
  notes
)
SELECT
  fake_source.id,
  fake_concept.id,
  'Fake learner is asked which datum target setup would stabilize a trial panel.',
  'Fake classroom prompt about locating a sheet-metal panel before inspection.',
  'deep drawing die tryout',
  2,
  'Fabricated AAMC-style question pattern; not copied from a course.'
FROM fake_source
CROSS JOIN fake_concept;
