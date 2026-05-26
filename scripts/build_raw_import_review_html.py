import argparse
import csv
import html
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_PATH = PROJECT_ROOT / "data" / "processed" / "raw_import_review_export.csv"
DEFAULT_HTML_PATH = PROJECT_ROOT / "data" / "processed" / "raw_import_review.html"


def load_review_rows(path=DEFAULT_EXPORT_PATH):
    with Path(path).open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def build_review_html(rows):
    cards = "\n".join(_render_card(row) for row in rows)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Raw Import Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2933; background: #f8fafc; }}
    main {{ max-width: 1100px; margin: 0 auto; }}
    article {{ background: #ffffff; border: 1px solid #d8dee4; border-radius: 6px; padding: 16px; margin: 12px 0; }}
    dl {{ display: grid; grid-template-columns: 180px 1fr; gap: 6px 12px; }}
    dt {{ font-weight: 700; color: #334e68; }}
    dd {{ margin: 0; }}
    pre {{ white-space: pre-wrap; font-family: inherit; }}
  </style>
</head>
<body>
  <main>
    <h1>Raw Import Review</h1>
    <p>Rows included: {len(rows)}</p>
    {cards}
  </main>
</body>
</html>
"""


def write_review_html(document, output_path=DEFAULT_HTML_PATH):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8", newline="\n")
    return output_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build local raw_import review HTML.")
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_HTML_PATH)
    args = parser.parse_args(argv)

    try:
        rows = load_review_rows(args.export)
        write_review_html(build_review_html(rows), args.output)
    except Exception as exc:
        print("Raw import review HTML build failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print("Raw import review HTML build complete.")
    print(f"Rows included: {len(rows)}")
    print(f"Output file: {args.output.as_posix()}")
    print("No database writes: true")
    return 0


def _render_card(row):
    return f"""<article data-definition-id="{_escape(row.get('definition_id', ''))}">
  <dl>
    <dt>definition_id</dt><dd>{_escape(row.get('definition_id', ''))}</dd>
    <dt>concept_key</dt><dd>{_escape(row.get('concept_key', ''))}</dd>
    <dt>definition_text</dt><dd><pre>{_escape(row.get('definition_text', ''))}</pre></dd>
  </dl>
</article>"""


def _escape(value):
    return html.escape(str(value), quote=True)


if __name__ == "__main__":
    raise SystemExit(main())
