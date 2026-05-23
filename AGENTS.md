# gdt-tooling-coach

## Objetivo

Construir una base de conocimiento en PostgreSQL/Neon para un glosario adaptativo de GD&T aplicado a diseno y manufactura de troqueles de embutido de lamina.

No construir una app todavia. Primero establecer estructura, modelo de datos, reglas editoriales, flujo de ingestion y base de datos.

## Reglas del proyecto

- PostgreSQL es la fuente maestra; Excel solo puede ser salida de revision/exportacion.
- Neon sera el destino compatible de PostgreSQL, sin credenciales reales en el repo.
- No ingerir PDFs hasta que la estructura y reglas esten listas.
- No inventar contenido normativo.
- No copiar extensamente material de normas o cursos.
- Crear una vista plana solo para revision humana.
- Mantener scripts en Python.

## Fuentes previstas

- ASME Y14.5-2018 en ingles como referencia tecnica actual.
- ASME Y14.5-2009 en espanol como fuente normativa de lenguaje espanol cuando aplique.
- PDFs de AAMC International como material pedagogico, no como autoridad normativa.

## Alcance inicial

Crear scaffolding del repo, documentacion base, migracion inicial, vista plana y scripts iniciales sin conectar a Neon ni ingerir documentos.

## Agent skills

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for `chavez-adrian/gdt-tooling-coach`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the canonical triage labels `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repo; read root/domain docs and `docs/adr/` when present. See `docs/agents/domain.md`.
