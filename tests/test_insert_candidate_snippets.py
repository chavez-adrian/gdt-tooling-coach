import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.insert_candidate_snippets import (
    INSERT_DEFINITION_SQL,
    apply_assignment_draft,
    build_insertion_plan,
    calculate_import_fingerprint,
    execute_approved_insert,
    format_console_summary,
)


def valid_snippet(**overrides):
    snippet = {
        "source_title": "ASME",
        "source_type": "asme_2018_en",
        "language": "en",
        "page_number": 12,
        "snippet_text": "short literal quote",
        "snippet_word_count": 3,
        "matched_signal": "datum",
        "extraction_type": "literal_quote",
        "proposed_review_state": "raw_import",
        "requires_human_review": True,
        "concept_id": "concept-1",
    }
    snippet.update(overrides)
    return snippet


SOURCE_ROWS = [
    {
        "id": "source-1",
        "title": "ASME",
        "source_type": "asme_2018_en",
        "language": "en",
    }
]


class InsertCandidateSnippetsTests(unittest.TestCase):
    def test_migration_003_adds_definition_import_fingerprint_unique_index(self):
        migration = Path("db/migrations/003_definition_import_fingerprint.sql").read_text(encoding="utf-8").lower()

        self.assertIn("alter table definitions", migration)
        self.assertIn("add column if not exists import_fingerprint text", migration)
        self.assertIn("create unique index if not exists", migration)
        self.assertIn("definitions", migration)
        self.assertIn("import_fingerprint", migration)

    def test_import_fingerprint_is_stable_for_same_snippet_identity(self):
        first = calculate_import_fingerprint(valid_snippet(), "source-1")
        second = calculate_import_fingerprint(valid_snippet(), "source-1")

        self.assertEqual(first, second)
        self.assertEqual(64, len(first))

    def test_import_fingerprint_changes_when_identity_fields_change(self):
        base = calculate_import_fingerprint(valid_snippet(), "source-1")

        changed = {
            "source_id": calculate_import_fingerprint(valid_snippet(), "source-2"),
            "concept_id": calculate_import_fingerprint(valid_snippet(concept_id="concept-2"), "source-1"),
            "page_number": calculate_import_fingerprint(valid_snippet(page_number=13), "source-1"),
            "snippet_text": calculate_import_fingerprint(valid_snippet(snippet_text="different quote"), "source-1"),
        }

        self.assertNotIn(base, changed.values())

    def test_default_plan_is_dry_run_and_contains_no_database_writes(self):
        plan = build_insertion_plan([valid_snippet()], SOURCE_ROWS, execute=False)

        self.assertEqual(1, plan["total_snippets"])
        self.assertEqual(1, plan["ready_to_insert"])
        self.assertEqual(0, plan["blocked_snippets"])
        self.assertFalse(plan["execute_requested"])
        self.assertFalse(plan["database_writes_attempted"])
        self.assertEqual({"matched_sources": 1, "unmatched_sources": 0}, plan["source_match_summary"])
        self.assertEqual(
            calculate_import_fingerprint(valid_snippet(), "source-1"),
            plan["insertion_rows"][0]["import_fingerprint"],
        )

    def test_plan_blocks_without_explicit_concept_id_to_avoid_automatic_validation(self):
        plan = build_insertion_plan(
            [valid_snippet(concept_id=None)],
            SOURCE_ROWS,
            execute=False,
        )

        self.assertEqual(0, plan["ready_to_insert"])
        self.assertEqual(1, plan["blocked_snippets"])
        self.assertEqual({"missing_concept_id": 1}, plan["block_reasons"])

    def test_plan_enforces_non_negotiable_raw_literal_contract(self):
        plan = build_insertion_plan(
            [
                valid_snippet(extraction_type="paraphrase"),
                valid_snippet(proposed_review_state="validated"),
                valid_snippet(requires_human_review=False),
                valid_snippet(snippet_text=" ".join(f"word{i}" for i in range(81))),
                valid_snippet(page_number=None),
            ],
            SOURCE_ROWS,
            execute=True,
        )

        self.assertEqual(0, plan["ready_to_insert"])
        self.assertEqual(5, plan["blocked_snippets"])
        self.assertEqual(
            {
                "extraction_type_not_literal_quote": 1,
                "review_state_not_raw_import": 1,
                "requires_human_review_not_true": 1,
                "snippet_too_long": 1,
                "missing_page_number": 1,
            },
            plan["block_reasons"],
        )

    def test_execute_approved_insert_requires_explicit_flag(self):
        calls = []

        def fail_if_called(_rows):
            calls.append("called")

        plan = build_insertion_plan([valid_snippet()], SOURCE_ROWS, execute=False)
        result = execute_approved_insert(plan, insert_rows=fail_if_called)

        self.assertEqual(0, result["inserted_snippets"])
        self.assertFalse(result["database_writes_attempted"])
        self.assertEqual([], calls)

    def test_execute_approved_insert_uses_parameterized_insert_when_approved(self):
        captured_rows = []
        plan = build_insertion_plan([valid_snippet()], SOURCE_ROWS, execute=True)

        result = execute_approved_insert(plan, insert_rows=captured_rows.extend)

        self.assertEqual(1, result["inserted_snippets"])
        self.assertTrue(result["database_writes_attempted"])
        self.assertEqual("source-1", captured_rows[0]["source_id"])
        self.assertEqual("concept-1", captured_rows[0]["concept_id"])
        self.assertNotIn("short literal quote", INSERT_DEFINITION_SQL)
        self.assertNotIn("validated", INSERT_DEFINITION_SQL.lower())
        self.assertIn("import_fingerprint", INSERT_DEFINITION_SQL)
        self.assertIn("ON CONFLICT (import_fingerprint) DO NOTHING", INSERT_DEFINITION_SQL)

    def test_console_summary_does_not_print_snippet_text(self):
        plan = build_insertion_plan([valid_snippet()], SOURCE_ROWS, execute=False)
        summary = format_console_summary({**plan, "inserted_snippets": 0})

        self.assertIn("Mode: dry-run", summary)
        self.assertIn("Ready to insert: 1", summary)
        self.assertNotIn("short literal quote", summary)
        self.assertNotIn("snippet_text", summary)

    def test_cli_defaults_to_dry_run_with_fixture_sources(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            snippets_path = Path(tmp_dir) / "candidate_snippets.json"
            sources_path = Path(tmp_dir) / "sources.json"
            snippets_path.write_text(
                json.dumps({"candidate_snippets": [valid_snippet()]}),
                encoding="utf-8",
            )
            sources_path.write_text(json.dumps(SOURCE_ROWS), encoding="utf-8")

            result = subprocess.run(
                [
                    "python",
                    "scripts/insert_candidate_snippets.py",
                    "--input",
                    str(snippets_path),
                    "--database-url",
                    "postgresql://readonly",
                    "--sources-fixture",
                    str(sources_path),
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Mode: dry-run", result.stdout)
        self.assertIn("Database writes attempted: false", result.stdout)
        self.assertNotIn("short literal quote", result.stdout)

    def test_assignment_draft_overlay_adds_concept_ids_without_copying_snippet_text(self):
        snippets = [valid_snippet(concept_id=None)]
        assignment_draft = {
            "assignments": [
                {
                    "snippet_index": 0,
                    "concept_key": "datum",
                    "concept_id": "concept-1",
                    "status": "ready_to_insert",
                }
            ]
        }

        updated = apply_assignment_draft(snippets, assignment_draft)

        self.assertEqual("concept-1", updated[0]["concept_id"])
        self.assertEqual("datum", updated[0]["concept_key"])
        self.assertEqual("short literal quote", updated[0]["snippet_text"])
        self.assertIsNot(updated[0], snippets[0])


if __name__ == "__main__":
    unittest.main()
