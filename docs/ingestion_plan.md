# Ingestion Plan

## Fase 0

Crear estructura base, documentacion, migracion inicial, vista plana y scripts.

## Fases futuras

1. Registrar fuentes en `sources`.
2. Usar probes locales de PDFs para medir extractabilidad y localizar paginas candidatas.
3. Extraer definiciones con trazabilidad.
4. Mapear terminos y conceptos por fuente e idioma.
5. Comparar versiones/fuentes antes de asumir vigencia.
6. Generar ejemplos y ejercicios solo como contenido derivado revisable.

No se ingieren PDFs en esta fase.

## Probes locales permitidos

Los scripts de probes locales pueden abrir PDFs y extraer texto solo en memoria
para producir reportes de metadatos ignorados por Git:

- `python scripts/probe_pdf_text.py`
- `python scripts/locate_definition_candidates.py`
- `python scripts/rank_definition_candidates.py`
- `python scripts/verify_ranked_candidates.py`
- `python scripts/extract_candidate_snippets.py`
- `python scripts/verify_candidate_snippets.py`

Los reportes permitidos son:

- `data/processed/pdf_text_probe.json`
- `data/processed/definition_candidate_pages.json`
- `data/processed/ranked_definition_candidates.json`
- `data/processed/candidate_snippets.json` en la fase controlada de snippets.

Estos reportes no son ingestion. No insertan datos en Neon, no marcan contenido
como validado, no guardan texto completo, no guardan definiciones, no guardan
citas largas y no hacen OCR. Sirven solamente para decidir donde revisar
manual o editorialmente en una fase posterior.

El reporte rankeado prioriza paginas candidatas para revision editorial y el
verificador resume candidatos totales, conteos high/medium/low y fuentes con mas
candidatos high-priority. No se conecta a Neon.

## Fase controlada de snippets

La extraccion limitada de snippets debe partir solamente de paginas
high-priority del reporte rankeado. Puede abrir PDFs y extraer texto solo de
esas paginas, pero el reporte local debe quedar acotado:

- maximo 80 palabras continuas por snippet literal;
- maximo 3 snippets por pagina;
- maximo 100 snippets totales en la fase;
- `extraction_type = "literal_quote"`;
- `proposed_review_state = "raw_import"`;
- `requires_human_review = true`.

Esta fase no inserta en Neon, no modifica tablas, no modifica `sources` ni
`definitions`, y no marca contenido como validado. El resultado es material
crudo para revision humana posterior.

El verificador `python scripts/verify_candidate_snippets.py` debe ejecutarse
despues del extractor. Reporta paginas high-priority procesadas, snippets
generados, snippets por fuente, maximo conteo de palabras, confirmacion del
limite de 80 palabras, campos `raw_import` y `requires_human_review`, contrato
sin Neon ni modificaciones de base de datos, `git diff --stat` y
`git status --short`. No imprime texto de snippets. No se conecta a Neon.

El verificador `python scripts/verify_snippet_coverage.py` es metadata-only snippet coverage verification.
Compara paginas high-priority rankeadas contra
metadatos de snippets generados para explicar cobertura y faltantes; does not open PDFs or contact Neon,
no modifica base de datos y no marca contenido como
validado.

El verificador `python scripts/verify_snippet_insertion_dry_run.py` revisa
`data/processed/snippet_insertion_dry_run.json` como dry-run planning and safety verification.
Debe confirmar totales, razones de bloqueo, resumen de matching de fuentes,
metadata `raw_import`/`requires_human_review`/`validated = false`/`literal_quote`,
salida ignorada por Git, ausencia de SQL ejecutable y contrato sin escrituras de
base de datos. No es ingestion ni validacion.
