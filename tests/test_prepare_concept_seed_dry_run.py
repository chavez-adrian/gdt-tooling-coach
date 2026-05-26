import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_concept_seed_dry_run import (
    build_concept_seed_dry_run,
    fetch_existing_concepts,
    format_console_summary,
)


def concept(**overrides):
    row = {
        "concept_key": "datum",
        "preferred_label_en": "Datum",
        "preferred_label_es": "Datum",
        "concept_type": "reference",
        "review_state": "needs_human_review",
        "source_authority_hint": "ASME Y14.5 / GD&T course metadata",
        "notes": "Seed label from matched_signal datum; no definition stored.",
    }
    row.update(overrides)
    return row


class PrepareConceptSeedDryRunTests(unittest.TestCase):
    def test_reports_insertable_manifest_concepts_against_empty_database(self):
        report = build_concept_seed_dry_run([concept()], existing_concepts=[])

        self.assertEqual(1, report["total_manifest_concepts"])
        self.assertEqual(0, report["existing_concepts_count"])
        self.assertEqual(1, report["insertable_concepts"])
        self.assertEqual(0, report["blocked_concepts"])
        self.assertEqual({}, report["block_reasons"])
        self.assertEqual([], report["duplicate_keys"])
        self.assertTrue(report["no_database_writes"])

    def test_blocks_duplicate_concept_keys_and_existing_concepts(self):
        report = build_concept_seed_dry_run(
            [
                concept(concept_key="datum"),
                concept(concept_key="datum"),
                concept(concept_key="feature_control_frame"),
            ],
            existing_concepts=[
                {"slug": "feature_control_frame", "category": "symbolic_notation"}
            ],
        )

        self.assertEqual(["datum"], report["duplicate_keys"])
        self.assertEqual(0, report["insertable_concepts"])
        self.assertEqual(3, report["blocked_concepts"])
        self.assertEqual(
            {"duplicate_concept_key": 2, "concept_already_exists": 1},
            report["block_reasons"],
        )

    def test_blocks_invalid_manifest_contract(self):
        report = build_concept_seed_dry_run(
            [
                concept(concept_key="missing_label", preferred_label_en=""),
                concept(concept_key="validated", review_state="validated"),
                concept(concept_key="definition_field", definition="forbidden field"),
                concept(concept_key="long_notes", notes=" ".join(f"word{i}" for i in range(25))),
            ],
            existing_concepts=[],
        )

        self.assertEqual(0, report["insertable_concepts"])
        self.assertEqual(4, report["blocked_concepts"])
        self.assertEqual(
            {
                "missing_required_field": 1,
                "review_state_not_needs_human_review": 1,
                "validated_state_not_allowed": 1,
                "definition_field_not_allowed": 1,
                "content_too_long": 1,
            },
            report["block_reasons"],
        )

    def test_fetch_existing_concepts_uses_select_only_query(self):
        class FakeCursor:
            description = [("id",), ("slug",), ("category",), ("current_status",)]

            def __init__(self):
                self.sql = None

            def execute(self, sql):
                self.sql = sql

            def fetchall(self):
                return [("concept-1", "datum", "reference", "needs_review")]

        class FakeConnection:
            def __init__(self):
                self.cursor_instance = FakeCursor()

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def cursor(self):
                return self.cursor_instance

        fake_connection = FakeConnection()

        rows = fetch_existing_concepts("postgresql://readonly", connect=lambda _url: fake_connection)

        normalized_sql = " ".join(fake_connection.cursor_instance.sql.split()).lower()
        self.assertTrue(normalized_sql.startswith("select "))
        self.assertIn(" from concepts", normalized_sql)
        self.assertNotRegex(normalized_sql, r"\b(insert|update|delete|create|drop|alter)\b")
        self.assertEqual("datum", rows[0]["slug"])

    def test_console_summary_does_not_print_credentials_or_definitions(self):
        report = build_concept_seed_dry_run([concept()], existing_concepts=[])

        summary = format_console_summary(report)

        self.assertIn("Total manifest concepts: 1", summary)
        self.assertIn("Insertable concepts: 1", summary)
        self.assertIn("No database writes: true", summary)
        self.assertNotIn("DATABASE_URL", summary)
        self.assertNotIn("password", summary.lower())
        self.assertNotIn("token", summary.lower())
        self.assertNotIn("definition", summary.lower())

    def test_cli_writes_metadata_report_with_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest_path = Path(tmp_dir) / "concept_seed_manifest.example.json"
            concepts_path = Path(tmp_dir) / "concepts.json"
            output_path = Path(tmp_dir) / "concept_seed_dry_run.json"
            manifest_path.write_text(json.dumps([concept()]), encoding="utf-8")
            concepts_path.write_text("[]", encoding="utf-8")

            result = subprocess.run(
                [
                    "python",
                    "scripts/prepare_concept_seed_dry_run.py",
                    "--manifest",
                    str(manifest_path),
                    "--concepts-fixture",
                    str(concepts_path),
                    "--output",
                    str(output_path),
                    "--skip-ignore-check",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, written["total_manifest_concepts"])
        self.assertTrue(written["no_database_writes"])
        self.assertNotIn("definition", json.dumps(written).lower())


if __name__ == "__main__":
    unittest.main()
