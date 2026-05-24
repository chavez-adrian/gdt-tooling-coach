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

## Uso de vista plana

La vista plana sirve para revision humana y exportacion. No es la fuente maestra.
