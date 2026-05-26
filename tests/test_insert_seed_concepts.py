import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.insert_seed_concepts import (
    INSERT_CONCEPT_SQL,
    build_insertion_plan,
    execute_approved_insert,
    fetch_existing_concepts,
    format_console_summary,
)


def valid_concept(**overrides):
    concept = {
        "concept_key": "datum",
        "preferred_label_en": "Datum",
        "preferred_label_es": "Datum",
        "concept_type": "reference",
        "review_state": "needs_human_review",
        "source_authority_hint": "ASME Y14.5 / GD&T course metadata",
        "notes": "Seed label from matched_signal datum; no definition stored.",
    }
    concept.update(overrides)
    return concept


class InsertSeedConceptsTests(unittest.TestCase):
    def test_default_plan_is_dry_run_and_contains_no_database_writes(self):
        plan = build_insertion_plan([valid_concept()], existing_concepts=[], execute=False)

        self.assertEqual("dry-run", plan["mode"])
        self.assertEqual(1, plan["total_manifest_concepts"])
        self.assertEqual(1, plan["ready_to_insert"])
        self.assertEqual(0, plan["blocked_concepts"])
        self.assertEqual(0, plan["inserted_concepts"])
        self.assertFalse(plan["database_writes_attempted"])
        self.assertFalse(plan["execute_requested"])

    def test_console_summary_reports_safe_required_counts(self):
        plan = build_insertion_plan([valid_concept()], existing_concepts=[], execute=False)
        summary = format_console_summary(plan)

        self.assertIn("Mode: dry-run", summary)
        self.assertIn("Total manifest concepts: 1", summary)
        self.assertIn("Ready to insert: 1", summary)
        self.assertIn("Blocked concepts: 0", summary)
        self.assertIn("Inserted concepts: 0", summary)
        self.assertIn("Database writes attempted: false", summary)
        self.assertNotIn("DATABASE_URL", summary)
        self.assertNotIn("password", summary.lower())
        self.assertNotIn("token", summary.lower())

    def test_blocks_unsafe_manifest_concepts(self):
        plan = build_insertion_plan(
            [
                valid_concept(concept_key="published", review_state="published"),
                valid_concept(concept_key="validated", review_state="validated"),
                valid_concept(concept_key="definition_field", definition="forbidden"),
                valid_concept(
                    concept_key="long_content",
                    notes=" ".join(f"word{i}" for i in range(25)),
                ),
            ],
            existing_concepts=[],
            execute=False,
        )

        self.assertEqual(0, plan["ready_to_insert"])
        self.assertEqual(4, plan["blocked_concepts"])
        self.assertEqual(
            {
                "review_state_not_needs_human_review": 2,
                "validated_state_not_allowed": 1,
                "definition_field_not_allowed": 1,
                "content_too_long": 1,
            },
            plan["block_reasons"],
        )

    def test_blocks_duplicate_and_existing_concept_keys(self):
        plan = build_insertion_plan(
            [
                valid_concept(concept_key="datum"),
                valid_concept(concept_key="datum"),
                valid_concept(concept_key="feature_control_frame"),
            ],
            existing_concepts=[
                {"slug": "feature_control_frame", "category": "symbolic_notation"}
            ],
            execute=False,
        )

        self.assertEqual(0, plan["ready_to_insert"])
        self.assertEqual(3, plan["blocked_concepts"])
        self.assertEqual(
            {"duplicate_concept_key": 2, "concept_already_exists": 1},
            plan["block_reasons"],
        )

    def test_execute_approved_insert_requires_explicit_flag(self):
        calls = []
        plan = build_insertion_plan([valid_concept()], existing_concepts=[], execute=False)

        result = execute_approved_insert(plan, insert_rows=calls.extend)

        self.assertEqual(0, result["inserted_concepts"])
        self.assertFalse(result["database_writes_attempted"])
        self.assertEqual([], calls)

    def test_execute_approved_insert_uses_parameterized_insert_when_approved(self):
        captured_rows = []
        plan = build_insertion_plan([valid_concept()], existing_concepts=[], execute=True)

        result = execute_approved_insert(plan, insert_rows=captured_rows.extend)

        self.assertEqual(1, result["inserted_concepts"])
        self.assertTrue(result["database_writes_attempted"])
        self.assertEqual("datum", captured_rows[0]["slug"])
        self.assertEqual("needs_review", captured_rows[0]["current_status"])
        self.assertNotIn("datum", INSERT_CONCEPT_SQL)
        self.assertNotRegex(INSERT_CONCEPT_SQL.lower(), r"\b(update|delete|drop|alter|create)\b")

    def test_fetch_existing_concepts_uses_select_only_metadata_query(self):
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

    def test_cli_defaults_to_dry_run_with_fixture_concepts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            manifest_path = Path(tmp_dir) / "concept_seed_manifest.example.json"
            concepts_path = Path(tmp_dir) / "concepts.json"
            manifest_path.write_text(json.dumps([valid_concept()]), encoding="utf-8")
            concepts_path.write_text("[]", encoding="utf-8")

            result = subprocess.run(
                [
                    "python",
                    "scripts/insert_seed_concepts.py",
                    "--manifest",
                    str(manifest_path),
                    "--concepts-fixture",
                    str(concepts_path),
                    "--database-url",
                    "postgresql://readonly",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Mode: dry-run", result.stdout)
        self.assertIn("Database writes attempted: false", result.stdout)


if __name__ == "__main__":
    unittest.main()
