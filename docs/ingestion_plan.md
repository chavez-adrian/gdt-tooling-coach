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

Los reportes permitidos son:

- `data/processed/pdf_text_probe.json`
- `data/processed/definition_candidate_pages.json`

Estos reportes no son ingestion. No insertan datos en Neon, no marcan contenido
como validado, no guardan texto completo, no guardan definiciones, no guardan
citas largas y no hacen OCR. Sirven solamente para decidir donde revisar
manual o editorialmente en una fase posterior.
