# gdt-tooling-coach

Knowledge base for an adaptive GD&T learning system focused on design, manufacture, inspection, and cost-conscious specification of sheet-metal deep-drawing dies.

The project stores a structured bilingual GD&T glossary and learning dataset in PostgreSQL/Neon. It is not a user-facing application yet.

## Purpose

Build a relational database that supports:

- GD&T concept glossary
- ASME Y14.5-2018 English terms and current technical authority
- ASME Y14.5-2009 Spanish normative terminology and Spanish definitions
- AAMC International course terminology and review-question patterns
- GD&T symbols with Unicode/SVG/text fallback logic
- version comparison between ASME 2009 and 2018
- tooling examples for deep-drawing dies
- future adaptive learning exercises

## Source hierarchy

1. **ASME Y14.5-2018 English**  
   Current technical authority.

2. **ASME Y14.5-2009 Spanish**  
   Primary Spanish normative language source, unless 2018 changed the concept significantly.

3. **AAMC International course PDFs**  
   Pedagogical source for course explanations, review questions, and learning patterns.

## Editorial rules

- Do not invent internal Peltre Nacional terminology.
- Train users to use ASME/AAMC terminology in Spanish and English.
- Literal quotes are allowed up to **80 continuous words** only when pedagogically useful.
- Long sections, full tables, figures, and extended examples must not be reproduced.
- Use faithful paraphrase when direct quotation is not necessary.
- For definitions with clauses/incisos, cover each clause with brief quote and/or faithful paraphrase.
- Unicode symbols are preferred; if unreliable, use SVG; if unavailable, use text fallback.

## Tech stack

- PostgreSQL on Neon
- Python scripts
- `psycopg`
- `python-dotenv`
- SQL migrations

## Repo structure

```text
gdt-tooling-coach/
  AGENTS.md
  README.md
  .env.example
  requirements.txt
  /docs
    project_spec.md
    editorial_rules.md
    data_model.md
    ingestion_plan.md
  /db
    /migrations
      001_initial_schema.sql
    /views
      v_glossary_flat.sql
  /scripts
    check_connection.py
    run_migrations.py
    ingest_sources.py
    extract_definitions.py
    compare_versions.py
    probe_pdf_text.py
    verify_pdf_text_probe.py
    locate_definition_candidates.py
    verify_definition_candidates.py
    rank_definition_candidates.py
    verify_ranked_candidates.py
    extract_candidate_snippets.py
    verify_candidate_snippets.py
  /data
    /raw
      /asme_2018
      /asme_2009_es
      /aamc_course
    /processed
  /tests
```

## Quick start

### 1. Create virtual environment

```bash
python -m venv .venv
```

Activate it:

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

Copy:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and add the Neon connection string.

### 4. Check database connection

```bash
python scripts/check_connection.py
```

### 5. Run migrations

```bash
python scripts/run_migrations.py
```

## Important

Do not commit `.env` or real database credentials.

Do not ingest source documents until the schema has been created and reviewed.

## Controlled PDF metadata probes

The repo includes local-only PDF inspection scripts that support source review
without ingesting normative content into PostgreSQL/Neon.

```bash
python scripts/probe_pdf_text.py
python scripts/verify_pdf_text_probe.py
python scripts/locate_definition_candidates.py
python scripts/verify_definition_candidates.py
python scripts/rank_definition_candidates.py
python scripts/verify_ranked_candidates.py
python scripts/extract_candidate_snippets.py
python scripts/verify_candidate_snippets.py
```

Generated reports are written under `data/processed/`, which is ignored by Git:

- `data/processed/pdf_text_probe.json`
- `data/processed/definition_candidate_pages.json`
- `data/processed/ranked_definition_candidates.json`
- `data/processed/candidate_snippets.json`

These reports contain metrics and page metadata only. They must not contain full
page text, definitions, long quotes, textual samples, OCR output, credentials, or
validated source content. They do not connect to Neon.

The ranked candidate report orders definition-candidate pages for editorial
review and summarizes total candidates, high/medium/low priority counts, and top
sources by high-priority candidates. No se conecta a Neon.

The controlled snippet phase is the first local step that may preserve brief
literal text for human review. It is limited to high-priority ranked pages, at
most 80 continuous words per snippet, at most 3 snippets per page, and at most
100 snippets total for the phase. Snippets remain `raw_import`, set
`requires_human_review = true`, and must never be inserted into Neon or marked
validated by the script. `python scripts/verify_candidate_snippets.py` reports
high-priority pages processed, snippets generated, snippets by source, maximum
word count, safety checks, command checks, and Git evidence without printing
snippet text. No se conecta a Neon.

`python scripts/verify_snippet_coverage.py` is the candidate-to-snippet coverage explanation
step. It compares ranked high-priority page metadata with generated
snippet metadata and reports counts plus missing-page reason codes without
opening PDFs, contacting Neon, marking anything validated, or printing snippet
text.

`python scripts/verify_snippet_insertion_dry_run.py` verifies
`data/processed/snippet_insertion_dry_run.json` as a dry-run planning and safety verification
report. It checks required summary fields, intended raw/unvalidated
literal-quote metadata, ignored-output status, no executable SQL, sanitized
console output, and no database writes. It is not an ingestion or validation command.
