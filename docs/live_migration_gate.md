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
