import unittest

from scripts.verify_inserted_candidate_snippets import (
    POST_INSERT_VERIFICATION_SQL,
    format_console_summary,
    verify_post_insert_metrics,
)


def complete_metrics(**overrides):
    metrics = {
        "definitions_inserted": 100,
        "raw_import_count": 100,
        "requires_human_review_count": 100,
        "validated_false_count": 100,
        "literal_quote_count": 100,
        "word_count_within_limit": 100,
        "source_id_present": 100,
        "concept_id_present": 100,
        "import_fingerprint_present": 100,
        "duplicate_import_fingerprint_count": 0,
    }
    metrics.update(overrides)
    return metrics


class VerifyInsertedCandidateSnippetsTests(unittest.TestCase):
    def test_passes_when_all_inserted_candidate_snippet_invariants_hold(self):
        result = verify_post_insert_metrics(complete_metrics())

        self.assertTrue(result["passed"])
        self.assertEqual(100, result["definitions_inserted"])
        self.assertEqual(0, result["duplicate_import_fingerprint_count"])
        self.assertTrue(result["no_database_writes"])
        self.assertFalse(result["definition_text_printed"])
        self.assertFalse(result["snippet_text_printed"])

    def test_fails_when_duplicate_import_fingerprints_exist(self):
        result = verify_post_insert_metrics(
            complete_metrics(duplicate_import_fingerprint_count=1)
        )

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["duplicate_import_fingerprint_count"])

    def test_fails_when_required_raw_import_contract_is_incomplete(self):
        result = verify_post_insert_metrics(
            complete_metrics(
                raw_import_count=99,
                requires_human_review_count=99,
                validated_false_count=99,
                word_count_within_limit=99,
            )
        )

        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["review_state_raw_import"])
        self.assertFalse(result["checks"]["requires_human_review_true"])
        self.assertFalse(result["checks"]["validated_false"])
        self.assertFalse(result["checks"]["word_count_within_limit"])

    def test_console_summary_does_not_print_text_or_credentials(self):
        result = verify_post_insert_metrics(complete_metrics())
        summary = format_console_summary(result)

        self.assertIn("Definitions inserted: 100", summary)
        self.assertIn("Duplicate import fingerprint count: 0", summary)
        self.assertNotIn("definition_text", summary)
        self.assertNotIn("snippet_text", summary)
        self.assertNotIn("DATABASE_URL", summary)
        self.assertNotIn("password", summary)

    def test_select_query_does_not_fetch_definition_text(self):
        normalized_sql = " ".join(POST_INSERT_VERIFICATION_SQL.lower().split())

        self.assertIn("from definitions", normalized_sql)
        self.assertNotIn(" text,", normalized_sql)
        self.assertNotIn("snippet_text", normalized_sql)


if __name__ == "__main__":
    unittest.main()
