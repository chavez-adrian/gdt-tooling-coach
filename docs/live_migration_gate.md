# Live Migration Gate

Issue: #4

Status: first approved live migration run completed.

## Confirmed Neon target

- Neon project: `gdt-tooling-coach`
- Database: `gdt_tooling_coach`
- Connection owner: `neondb_owner`

No connection string, password, token, or secret value belongs in this file.

## Local proof

Local proof from issue #3: complete.

Evidence path:

- `python scripts/build_fake_glossary_verification.py --print`
- The generated SQL builds the schema, applies `v_glossary_flat`, inserts fake non-normative fixture rows, and selects from `v_glossary_flat` without using Neon credentials.

## Exact live command

Load the approved Neon `DATABASE_URL` outside git, then run exactly:

```powershell
python scripts/run_migrations.py
```

## Expected successful output

For the first live run, success should include:

```text
Applying migration: 001_initial_schema.sql
Applied: 001_initial_schema.sql
Applying view: v_glossary_flat.sql
Applied view: v_glossary_flat.sql
Migrations and views are up to date.
```

If `001_initial_schema.sql` was already applied by a prior approved run, `No pending migrations.` may appear instead of the migration apply lines, followed by the view apply lines and final up-to-date message.

## Post-run read-only verification

After an approved live run, verify with read-only checks only:

```sql
SELECT COUNT(*) AS applied_migrations
FROM schema_migrations
WHERE version = '001_initial_schema.sql';

SELECT COUNT(*) AS flat_rows
FROM v_glossary_flat;
```

## Human approval gate

Approval status: received in GitHub issue #4 and Codex conversation on 2026-05-22.

Approved Neon target and command:

- Neon project: `gdt-tooling-coach`
- Database: `gdt_tooling_coach`
- Connection owner: `neondb_owner`
- Command: `python scripts/run_migrations.py`

## Live run result

The approved command was executed on 2026-05-22.

Observed successful output:

```text
Applying migration: 001_initial_schema.sql
Applied: 001_initial_schema.sql
Applying view: v_glossary_flat.sql
Applied view: v_glossary_flat.sql
Migrations and views are up to date.
```

Read-only verification result:

```text
applied_migrations: 1
flat_rows: 0
core_tables: 9
```

No PDF ingestion or content import was run.
