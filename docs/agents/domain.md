# Domain Docs

This is a single-context repo.

Before planning or implementation, read:

- `AGENTS.md`
- `README.md`
- `docs/project_spec.md`
- `docs/editorial_rules.md`
- `docs/data_model.md`
- `docs/ingestion_plan.md`
- `docs/adr/` when it exists

The project domain is a PostgreSQL/Neon knowledge base for a bilingual GD&T glossary and future adaptive learning system for sheet-metal deep-drawing die tooling.

Use the project's domain vocabulary consistently:

- GD&T concept
- source
- term
- definition
- symbol
- review state
- concept change
- tooling example
- adaptive exercise
- flat review/export view

Do not treat the flat review view as the source of truth. PostgreSQL relational tables are the master model.
