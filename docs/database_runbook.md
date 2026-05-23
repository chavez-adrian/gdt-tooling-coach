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
