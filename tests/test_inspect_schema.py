from pathlib import Path
import re
import unittest

from scripts import inspect_schema


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "inspect_schema.py"


class InspectSchemaTests(unittest.TestCase):
    def test_key_tables_match_live_schema_expectations(self):
        self.assertEqual(
            inspect_schema.KEY_TABLES,
            (
                "sources",
                "concepts",
                "terms",
                "definitions",
                "symbols",
                "concept_changes",
                "tooling_examples",
                "course_question_patterns",
                "adaptive_exercises",
                "review_events",
            ),
        )

    def test_queries_are_read_only(self):
        forbidden = re.compile(r"\b(INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b", re.I)
        queries = [
            inspect_schema.PUBLIC_TABLES_SQL,
            inspect_schema.PUBLIC_VIEWS_SQL,
            inspect_schema.COLUMN_COUNTS_SQL,
            inspect_schema.APPLIED_MIGRATIONS_SQL,
        ]

        for query in queries:
            self.assertIsNone(forbidden.search(query))

        query_text = "\n".join(queries)
        self.assertIn("information_schema.tables", query_text)
        self.assertIn("information_schema.views", query_text)
        self.assertIn("schema_migrations", query_text)

    def test_output_does_not_include_connection_details(self):
        script = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertNotIn("current_user", script)
        self.assertNotIn("inet_server_addr", script)
        self.assertNotIn("postgresql://", script)
        self.assertNotIn("postgres://", script)
        self.assertNotIn("password", script.lower())
        self.assertNotIn("token", script.lower())


if __name__ == "__main__":
    unittest.main()
