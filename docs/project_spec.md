# Project Spec

## Objetivo

Crear una base de conocimiento en PostgreSQL/Neon para un glosario adaptativo de GD&T orientado a troqueles de embutido de lamina.

## Fuera de alcance inicial

- App de usuario.
- Conexion real a Neon.
- Ingestion de PDFs.
- Extraccion o redaccion de contenido normativo.

## Dentro de alcance local controlado

- Probar si los PDFs locales exponen texto extraible usando solo metricas.
- Localizar paginas candidatas para definiciones, terminos, simbolos o glosarios.
- Escribir reportes locales ignorados por Git con metadatos y conteos solamente.
- Verificar que los reportes no contengan texto completo, definiciones, citas largas ni muestras textuales.
- Rankear paginas candidatas con metadatos permitidos para priorizar revision.
- Extraer snippets literales breves desde paginas high-priority solo como material crudo de revision humana.

## Decisiones base

- PostgreSQL sera la fuente maestra.
- El modelo sera relacional, no una tabla plana.
- Una vista plana existira solo para revision/exportacion.
- Todo contenido importado o derivado debera conservar trazabilidad de fuente y estado de revision.
- Los probes locales de PDF no son ingestion y no validan contenido.
- Los snippets locales deben permanecer en `raw_import`, requerir revision humana y no insertarse en Neon.
