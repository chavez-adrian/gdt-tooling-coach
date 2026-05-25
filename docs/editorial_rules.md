# Editorial Rules

## Reglas generales

- No inventar contenido normativo.
- No crear credenciales ni datos sensibles.
- No ingerir fuentes hasta que el flujo este definido.
- No marcar contenido importado como validado automaticamente.

## Trazabilidad

Cada definicion, termino, simbolo o ejercicio derivado debe poder rastrearse a una fuente o a una decision editorial revisable.

## Probes de PDF

Los probes locales de PDF solo pueden producir metadatos para revision:

- conteos aproximados de caracteres y palabras;
- paginas muestreadas o candidatas;
- senales detectadas;
- estados tecnicos de lectura.

No deben guardar texto completo de pagina, definiciones, citas largas, muestras
textuales, OCR ni contenido marcado como validado. Cualquier extraccion de texto
debe permanecer en memoria durante el proceso local.

## Ranking de paginas candidatas

`data/processed/ranked_definition_candidates.json` es solamente una
priorizacion editorial de paginas candidatas. Puede guardar conteos
high/medium/low, ranking, senales canonicas, titulos de fuente y metadatos de
pagina necesarios para decidir que revisar primero.

No debe guardar snippets, texto extraido, definiciones, citas largas, muestras
textuales, OCR ni contenido validado. No se conecta a Neon.

## Snippets controlados

Los snippets literales solo pueden generarse desde paginas high-priority ya
rankeadas. Cada snippet guardado debe ser breve y revisable:

- maximo 80 palabras continuas;
- maximo 3 snippets por pagina;
- maximo 100 snippets en la fase;
- `extraction_type = "literal_quote"`;
- `proposed_review_state = "raw_import"`;
- `requires_human_review = true`.

Los snippets no son definiciones validadas. No deben insertarse en Neon ni
marcarse como `validated` sin una revision humana posterior.

La verificacion de `data/processed/candidate_snippets.json` se hace con
`python scripts/extract_candidate_snippets.py` y
`python scripts/verify_candidate_snippets.py`. El verificador solo puede
imprimir conteos, fuentes, maximo conteo de palabras, estados `raw_import`,
`requires_human_review`, contrato sin Neon/base de datos y evidencia Git. No
debe imprimir `snippet_text` ni contenido normativo literal. No se conecta a
Neon.

La coverage verification must not print snippet text, campos de texto largo ni
contenido normativo. `python scripts/verify_snippet_coverage.py` solo puede
explicar conteos, paginas con snippets y paginas sin snippets con codigos de
razon metadata-only; must not mark snippets validated ni conectarse a Neon.

La verificacion de `data/processed/snippet_insertion_dry_run.json` con
`python scripts/verify_snippet_insertion_dry_run.py` es una revision de
planificacion y seguridad. It must not print snippet_text, contenido normativo,
SQL ejecutable ni campos de texto largo; must not connect to Neon, write to the
database, or mark snippets validated.

La insercion live de snippets solo puede pasar por
`python scripts/insert_candidate_snippets.py --execute-approved-insert`. Sin esa
bandera, el comando es dry-run. El gate debe bloquear cualquier fila sin
`concept_id` explicito, `source_id`, `page_number`, estado `raw_import`,
`requires_human_review = true`, `validated = false`, `literal_quote`, o con mas
de 80 palabras. El script no puede validar conceptos automaticamente.

El diagnostico `python scripts/diagnose_concept_readiness.py` solo puede usar
metadatos permitidos para explicar readiness de conceptos. No debe imprimir
`snippet_text`, credenciales ni contenido normativo, no debe escribir en Neon y
no debe asignar `concept_id` automaticamente.

## Uso de vista plana

La vista plana sirve para revision humana y exportacion. No es la fuente maestra.
