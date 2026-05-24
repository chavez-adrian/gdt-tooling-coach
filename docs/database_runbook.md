# Database Runbook

## Local Setup Commands

Run these from the repository root.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python scripts/check_connection.py
python scripts/run_migrations.py
```

The migration runner applies table migrations and then the review view in
`db/views/v_glossary_flat.sql`.

## Data Ownership

PostgreSQL relational tables are the source of truth. Concepts, sources, terms,
definitions, symbols, and review metadata must be corrected in normalized tables
through migrations or controlled import/review tooling.

The flat view is for review and export only. Do not edit the flat view as canonical data.
Do not treat exported rows as a replacement for the relational model.

## Live Neon Boundary

Use `docs/neon_boundary.md` for the Neon boundary issue #2 decision and
`docs/live_migration_gate.md` for the live approval issue #4 decision. Do not run live Neon migrations from this runbook.
This runbook is for local setup, handoff, and review; live work remains gated by
the approval document.

## Fake Verification

Fake-data verification path:

```powershell
python scripts/build_fake_glossary_verification.py --print
python scripts/build_fake_bilingual_terms_verification.py --print
python scripts/build_fake_source_definition_trace.py --print
python scripts/build_fake_concept_change_verification.py --print
python scripts/build_fake_symbol_fallback_verification.py --print
python scripts/build_fake_tooling_example_verification.py --print
```

These tracer bullets compose schema, views, and fake fixtures into SQL that can
be inspected or run locally. To execute them, pipe the output into a disposable local PostgreSQL database.
No Neon connection is required, and no source documents are needed.

## Local PDF Metadata Verification

The PDF metadata probes are local-only review aids. They may open local PDFs and
extract text in memory, but they write only metrics or candidate-page metadata
to ignored files under `data/processed/`.

```powershell
python scripts/probe_pdf_text.py
python scripts/verify_pdf_text_probe.py
python scripts/locate_definition_candidates.py
python scripts/verify_definition_candidates.py
```

Expected generated reports:

- `data/processed/pdf_text_probe.json`
- `data/processed/definition_candidate_pages.json`

Safety checks:

```powershell
git check-ignore data/processed/pdf_text_probe.json
git check-ignore data/processed/definition_candidate_pages.json
python -m unittest discover -s tests -p "test_*.py"
```

These reports must remain metadata-only. They must not include full page text,
definitions, long quotes, textual samples, OCR output, Neon credentials, or any
validated/imported source content.

## Troubleshooting

- Missing `DATABASE_URL`: copy `.env.example` to `.env` for local shape, then set
  the variable only in your private environment. Do not commit or paste the value.
- Missing dependencies: rerun `python -m pip install -r requirements.txt` inside
  the activated virtual environment.
- Failed migrations: verify the target is disposable or approved, rerun
  `python scripts/check_connection.py`, then inspect the failing migration file
  before retrying.

No real credentials are included here. No source-document excerpts are included
or required for this handoff runbook.
