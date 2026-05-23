# Project Spec

## Objetivo

Crear una base de conocimiento en PostgreSQL/Neon para un glosario adaptativo de GD&T orientado a troqueles de embutido de lamina.

## Fuera de alcance inicial

- App de usuario.
- Conexion real a Neon.
- Ingestion de PDFs.
- Extraccion o redaccion de contenido normativo.

## Decisiones base

- PostgreSQL sera la fuente maestra.
- El modelo sera relacional, no una tabla plana.
- Una vista plana existira solo para revision/exportacion.
- Todo contenido importado o derivado debera conservar trazabilidad de fuente y estado de revision.
