-- v_glossary_flat.sql
-- Review/export view only. The relational tables remain the source of truth.
-- Drop first so this file can be reapplied when the view column structure changes.

DROP VIEW IF EXISTS public.v_glossary_flat;

CREATE VIEW public.v_glossary_flat AS
SELECT
  c.id AS concept_id,
  c.slug,
  c.category,
  c.subcategory,
  c.current_status,
  c.difficulty_level,
  en.term AS asme_2018_english_term,
  en.abbreviation AS english_abbreviation,
  es.term AS asme_2009_spanish_term,
  s.unicode_symbol,
  s.unicode_reliable,
  s.svg_path,
  s.text_fallback,
  def_en.text AS asme_2018_english_definition,
  def_es.text AS asme_2009_spanish_definition,
  cc.change_type AS change_status_2009_vs_2018,
  te.example_text AS tooling_example,
  COALESCE(def_en.review_status, def_es.review_status, cc.review_status, te.review_status, c.current_status) AS review_status
FROM concepts c
LEFT JOIN terms en
  ON en.concept_id = c.id
  AND en.language = 'en'
  AND en.is_primary = TRUE
LEFT JOIN terms es
  ON es.concept_id = c.id
  AND es.language = 'es'
  AND es.is_primary = TRUE
LEFT JOIN symbols s
  ON s.concept_id = c.id
LEFT JOIN definitions def_en
  ON def_en.concept_id = c.id
  AND def_en.definition_type NOT LIKE '%es%'
LEFT JOIN definitions def_es
  ON def_es.concept_id = c.id
  AND def_es.definition_type = 'normative_es_2009'
LEFT JOIN concept_changes cc
  ON cc.concept_id = c.id
LEFT JOIN tooling_examples te
  ON te.concept_id = c.id;
