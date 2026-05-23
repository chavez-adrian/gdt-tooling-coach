from pathlib import Path
import tempfile
import unittest

from scripts import validate_source_files


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "source_manifest.example.json"


class SourceManifestTests(unittest.TestCase):
    def test_manifest_has_expected_initial_sources(self):
        manifest = validate_source_files.load_manifest(MANIFEST_PATH)

        self.assertEqual(len(manifest), 10)
        self.assertEqual(
            [entry["source_title"] for entry in manifest],
            [
                "ASME Y14.5-2018 English",
                "ASME Y14.5-2009 Español",
                "Módulo 0 Contenido del curso básico",
                "Módulo 1 Dimensionamiento y tolerancias",
                "Módulo 2 Definiciones dentro de las GD&T",
                "Módulo 3 Tolerancias de forma",
                "Módulo 4 Tolerancias de orientación y datum de referencia",
                "Módulo 5 Tolerancias de perfil",
                "Módulo 6 Tolerancias de localización",
                "Módulo 7 Tolerancia de cabeceo",
            ],
        )

    def test_manifest_entries_have_required_shape(self):
        manifest = validate_source_files.load_manifest(MANIFEST_PATH)
        errors = validate_source_files.validate_manifest_entries(manifest, ROOT)

        self.assertEqual(errors, [])
        for entry in manifest:
            self.assertEqual(set(entry), validate_source_files.REQUIRED_FIELDS)
            self.assertTrue(entry["expected_local_path"].startswith("data/raw/"))
            self.assertIsInstance(entry["required"], bool)

    def test_inspect_source_files_reports_present_and_missing_without_real_pdfs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            present_path = project_root / "data" / "raw" / "aamc_course" / "present.pdf"
            present_path.parent.mkdir(parents=True)
            present_path.write_text("fake local placeholder", encoding="utf-8")

            manifest = [
                {
                    "source_title": "Present Source",
                    "source_type": "aamc_course",
                    "language": "es",
                    "expected_local_path": "data/raw/aamc_course/present.pdf",
                    "required": True,
                    "notes": "test metadata only",
                },
                {
                    "source_title": "Missing Source",
                    "source_type": "aamc_course",
                    "language": "es",
                    "expected_local_path": "data/raw/aamc_course/missing.pdf",
                    "required": True,
                    "notes": "test metadata only",
                },
            ]

            statuses = validate_source_files.inspect_source_files(manifest, project_root)

        self.assertEqual([status.present for status in statuses], [True, False])
        self.assertIn("Present files: 1", validate_source_files.build_output(statuses))
        self.assertIn("Missing files: 1", validate_source_files.build_output(statuses))

    def test_manifest_rejects_paths_outside_data_raw(self):
        manifest = [
            {
                "source_title": "Bad Source",
                "source_type": "aamc_course",
                "language": "es",
                "expected_local_path": "docs/bad.pdf",
                "required": True,
                "notes": "test metadata only",
            }
        ]

        errors = validate_source_files.validate_manifest_entries(manifest, ROOT)

        self.assertEqual(
            errors,
            ["Entry 1 expected_local_path must be inside data/raw/."],
        )


if __name__ == "__main__":
    unittest.main()
