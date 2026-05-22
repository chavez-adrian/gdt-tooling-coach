# Live Migration Gate

Issue: #4

Status: prepared; live execution blocked until explicit human approval is present in GitHub issue #4 comments.

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

Approval status: missing.

Do not run the live command until issue #4 has a human comment that explicitly approves this Neon target and command:

- Neon project: `gdt-tooling-coach`
- Database: `gdt_tooling_coach`
- Connection owner: `neondb_owner`
- Command: `python scripts/run_migrations.py`
