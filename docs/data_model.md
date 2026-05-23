# Data Model

## Entidades iniciales

- `sources`: documentos o referencias fuente.
- `concepts`: conceptos GD&T.
- `terms`: terminos por concepto, idioma y fuente.
- `definitions`: definiciones, parafrasis o explicaciones trazables.
- `symbols`: simbolos asociados a conceptos.
- `concept_changes`: comparaciones entre versiones/fuentes.
- `tooling_examples`: aplicaciones practicas a componentes de troqueles.
- `review_events`: historial de revision.

## Fuente maestra

Las tablas relacionales son la fuente maestra. `v_glossary_flat` es solo una vista de lectura para revision/exportacion.
