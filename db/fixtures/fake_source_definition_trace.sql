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
)
SELECT id
FROM fake_source;
