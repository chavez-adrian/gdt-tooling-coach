from pathlib import Path
import json
import hashlib
import tempfile
import unittest
from unittest.mock import patch

from scripts import inventory_pdfs


ROOT = Path(__file__).resolve().parents[1]


class FakePage:
    def __init__(self, text=None, raises=False):
        self.text = text
        self.raises = raises

    def extract_text(self):
        if self.raises:
            raise RuntimeError("fake text probe failure")
        return self.text


class FakePdfReader:
    def __init__(self, _path):
        self.pages = [FakePage("extractable text")]


class EmptyTextPdfReader:
    def __init__(self, _path):
        self.pages = [FakePage("")]


class UnreadablePdfReader:
    def __init__(self, _path):
        raise RuntimeError("fake unreadable pdf")


class PageCountFailedReader:
    def __init__(self, _path):
        self.pages = self

    def __len__(self):
        raise RuntimeError("fake page count failure")


class TextProbeFailedReader:
    def __init__(self, _path):
        self.pages = [FakePage(raises=True)]


class InventoryPdfsTests(unittest.TestCase):
    def test_build_inventory_reports_missing_files_without_pdf_content(self):
        manifest = [
            {
                "source_title": "Missing Source",
                "expected_local_path": "data/raw/aamc_course/missing.pdf",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            inventory = inventory_pdfs.build_inventory(manifest, Path(temp_dir))

        self.assertEqual(
            inventory,
            [
                {
                    "source_title": "Missing Source",
                    "expected_local_path": "data/raw/aamc_course/missing.pdf",
                    "exists": False,
                    "file_size_bytes": None,
                    "sha256": None,
                    "page_count": None,
                    "has_extractable_text_sample": None,
                    "inventory_status": "missing",
                }
            ],
        )

    def test_build_inventory_hashes_present_file_and_uses_pdf_metadata_probe(self):
        manifest = [
            {
                "source_title": "Present Source",
                "expected_local_path": "data/raw/aamc_course/present.pdf",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            pdf_path = project_root / "data" / "raw" / "aamc_course" / "present.pdf"
            pdf_path.parent.mkdir(parents=True)
            pdf_bytes = b"%PDF-1.4 fake bytes for technical inventory only"
            pdf_path.write_bytes(pdf_bytes)

            with patch.object(
                inventory_pdfs,
                "inspect_pdf_metadata",
                return_value=inventory_pdfs.PdfInspection(
                    page_count=3,
                    has_extractable_text_sample=True,
                    status="present_ok",
                ),
            ):
                inventory = inventory_pdfs.build_inventory(manifest, project_root)

        self.assertEqual(inventory[0]["exists"], True)
        self.assertEqual(inventory[0]["file_size_bytes"], len(pdf_bytes))
        self.assertEqual(inventory[0]["sha256"], hashlib.sha256(pdf_bytes).hexdigest())
        self.assertEqual(inventory[0]["page_count"], 3)
        self.assertEqual(inventory[0]["has_extractable_text_sample"], True)
        self.assertEqual(inventory[0]["inventory_status"], "present_ok")

    def test_inspect_pdf_metadata_reports_library_unavailable(self):
        with patch.object(inventory_pdfs, "load_pdf_reader_class", return_value=None):
            inspection = inventory_pdfs.inspect_pdf_metadata(Path("example.pdf"))

        self.assertEqual(inspection.status, "pdf_library_unavailable")
        self.assertIsNone(inspection.page_count)
        self.assertIsNone(inspection.has_extractable_text_sample)

    def test_inspect_pdf_metadata_reports_unreadable_pdf(self):
        with patch.object(
            inventory_pdfs, "load_pdf_reader_class", return_value=UnreadablePdfReader
        ):
            inspection = inventory_pdfs.inspect_pdf_metadata(Path("example.pdf"))

        self.assertEqual(inspection.status, "unreadable_pdf")

    def test_inspect_pdf_metadata_reports_page_count_failed(self):
        with patch.object(
            inventory_pdfs, "load_pdf_reader_class", return_value=PageCountFailedReader
        ):
            inspection = inventory_pdfs.inspect_pdf_metadata(Path("example.pdf"))

        self.assertEqual(inspection.status, "page_count_failed")
        self.assertIsNone(inspection.page_count)

    def test_inspect_pdf_metadata_reports_text_probe_failed(self):
        with patch.object(
            inventory_pdfs, "load_pdf_reader_class", return_value=TextProbeFailedReader
        ):
            inspection = inventory_pdfs.inspect_pdf_metadata(Path("example.pdf"))

        self.assertEqual(inspection.status, "text_probe_failed")
        self.assertEqual(inspection.page_count, 1)
        self.assertIsNone(inspection.has_extractable_text_sample)

    def test_inspect_pdf_metadata_reports_present_ok_without_storing_text(self):
        with patch.object(inventory_pdfs, "load_pdf_reader_class", return_value=FakePdfReader):
            inspection = inventory_pdfs.inspect_pdf_metadata(Path("example.pdf"))

        self.assertEqual(inspection.status, "present_ok")
        self.assertEqual(inspection.page_count, 1)
        self.assertEqual(inspection.has_extractable_text_sample, True)

    def test_inspect_pdf_metadata_reports_present_ok_without_extractable_text(self):
        with patch.object(
            inventory_pdfs, "load_pdf_reader_class", return_value=EmptyTextPdfReader
        ):
            inspection = inventory_pdfs.inspect_pdf_metadata(Path("example.pdf"))

        self.assertEqual(inspection.status, "present_ok")
        self.assertEqual(inspection.page_count, 1)
        self.assertEqual(inspection.has_extractable_text_sample, False)

    def test_write_inventory_writes_json_report(self):
        inventory = [
            {
                "source_title": "Example",
                "expected_local_path": "data/raw/example.pdf",
                "exists": False,
                "file_size_bytes": None,
                "sha256": None,
                "page_count": None,
                "has_extractable_text_sample": None,
                "inventory_status": "missing",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "data" / "processed" / "pdf_inventory.json"
            inventory_pdfs.write_inventory(inventory, output_path)
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(written, inventory)

    def test_inventory_report_path_is_ignored_by_git(self):
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("data/processed/**", gitignore)
        self.assertEqual(
            inventory_pdfs.DEFAULT_OUTPUT_PATH.relative_to(ROOT).as_posix(),
            "data/processed/pdf_inventory.json",
        )

    def test_build_output_includes_inventory_status_counts(self):
        inventory = [
            {
                "exists": True,
                "page_count": 2,
                "has_extractable_text_sample": True,
                "inventory_status": "present_ok",
            },
            {
                "exists": False,
                "page_count": None,
                "has_extractable_text_sample": None,
                "inventory_status": "missing",
            },
        ]

        output = inventory_pdfs.build_output(
            inventory, inventory_pdfs.DEFAULT_OUTPUT_PATH
        )

        self.assertIn("Inventory status counts:", output)
        self.assertIn("- missing: 1", output)
        self.assertIn("- present_ok: 1", output)


if __name__ == "__main__":
    unittest.main()
