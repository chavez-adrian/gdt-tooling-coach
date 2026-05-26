import csv
import tempfile
import unittest
from pathlib import Path

from scripts.build_raw_import_review_html import (
    build_review_html,
    load_review_rows,
    write_review_html,
)


def review_row(**overrides):
    row = {
        "definition_id": "definition-1",
        "concept_key": "datum",
        "source_title": "ASME Y14.5",
        "source_type": "asme_2018_en",
        "language": "en",
        "page_number": "12",
        "matched_signal": "datum",
        "extraction_type": "literal_quote",
        "word_count": "4",
        "definition_text": "A datum is a reference.",
        "import_fingerprint": "fingerprint-1",
        "review_status": "raw_import",
        "requires_human_review": "true",
        "validated": "false",
        "review_recommendation": "",
        "reviewer_notes": "",
    }
    row.update(overrides)
    return row


def write_fixture_csv(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(review_row().keys()))
        writer.writeheader()
        writer.writerows(rows)


class RawImportReviewHtmlTests(unittest.TestCase):
    def test_build_review_html_reads_csv_and_writes_self_contained_html(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "raw_import_review_export.csv"
            html_path = Path(tmp_dir) / "raw_import_review.html"
            write_fixture_csv(csv_path, [review_row()])

            rows = load_review_rows(csv_path)
            write_review_html(build_review_html(rows), html_path)
            html = html_path.read_text(encoding="utf-8")

        self.assertIn("definition-1", html)
        self.assertIn("A datum is a reference.", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)


if __name__ == "__main__":
    unittest.main()
