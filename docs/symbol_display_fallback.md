# Symbol Display Fallback

Use this order when a concept has symbol metadata:

1. Unicode when `unicode_symbol` is present and `unicode_reliable` is true.
2. SVG when Unicode is missing or marked unreliable and `svg_path` is present.
3. Text fallback when neither reliable Unicode nor SVG is available.

The fake issue #9 fixture is local review data only. It proves the storage path
without Neon credentials or source-document ingestion.
