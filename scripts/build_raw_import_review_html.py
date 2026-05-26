import argparse
import csv
import html
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_PATH = PROJECT_ROOT / "data" / "processed" / "raw_import_review_export.csv"
DEFAULT_HTML_PATH = PROJECT_ROOT / "data" / "processed" / "raw_import_review.html"
ALLOWED_REVIEW_DECISIONS = [
    "accept_as_candidate",
    "reject_not_definition",
    "wrong_concept",
    "duplicate",
    "needs_more_context",
    "needs_2018_comparison",
    "needs_spanish_term_review",
]


def load_review_rows(path=DEFAULT_EXPORT_PATH):
    with Path(path).open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def build_review_html(rows):
    cards = "\n".join(_render_card(row) for row in rows)
    controls = _render_controls(rows)
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
    {controls}
    {cards}
  </main>
</body>
</html>
"""


def _render_controls(rows):
    concepts = sorted({row.get("concept_key", "") for row in rows if row.get("concept_key", "")})
    sources = sorted({row.get("source_title", "") for row in rows if row.get("source_title", "")})
    languages = sorted({row.get("language", "") for row in rows if row.get("language", "")})
    return f"""<section class="controls" aria-label="Review filters">
      <label>Concept <select id="filter-concept"><option value="">All concepts</option>{_render_options(concepts)}</select></label>
      <label>Source <select id="filter-source"><option value="">All sources</option>{_render_options(sources)}</select></label>
      <label>Language <select id="filter-language"><option value="">All languages</option>{_render_options(languages)}</select></label>
      <label>Review decision <select id="filter-review-decision"><option value="">All decisions</option>{_render_options(ALLOWED_REVIEW_DECISIONS)}</select></label>
      <label>Search <input id="filter-search" type="search"></label>
    </section>"""


def _render_options(values):
    return "".join(f'<option value="{_escape(value)}">{_escape(value)}</option>' for value in values)


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
    required_fields = [
        "definition_id",
        "concept_key",
        "source_title",
        "source_type",
        "language",
        "page_number",
        "matched_signal",
        "word_count",
        "definition_text",
        "import_fingerprint",
    ]
    fields = "\n    ".join(_render_field(field, row.get(field, "")) for field in required_fields)
    return f"""<article data-definition-id="{_escape(row.get('definition_id', ''))}">
  <dl>
    {fields}
  </dl>
  <div class="review-fields">
    <label>Decision <select name="review_decision" data-field="review_decision"><option value="">Unreviewed</option>{_render_options(ALLOWED_REVIEW_DECISIONS)}</select></label>
    <label>Reviewer notes <textarea name="reviewer_notes" data-field="reviewer_notes"></textarea></label>
    <label>Corrected concept <input name="corrected_concept_key" data-field="corrected_concept_key" type="text"></label>
    <label>Reject reason <input name="reject_reason" data-field="reject_reason" type="text"></label>
  </div>
</article>"""


def _render_field(name, value):
    if name == "definition_text":
        return f"<dt>{name}</dt><dd><pre>{_escape(value)}</pre></dd>"
    return f"<dt>{name}</dt><dd>{_escape(value)}</dd>"


def _escape(value):
    return html.escape(str(value), quote=True)


if __name__ == "__main__":
    raise SystemExit(main())
