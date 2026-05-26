-- 003_definition_import_fingerprint.sql
-- Add an idempotent import key for controlled candidate snippet imports.

ALTER TABLE definitions
ADD COLUMN IF NOT EXISTS import_fingerprint TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_definitions_import_fingerprint
ON definitions(import_fingerprint)
WHERE import_fingerprint IS NOT NULL;
