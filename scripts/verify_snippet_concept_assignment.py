from collections import Counter

try:
    from prepare_snippet_concept_assignment_draft import SIGNAL_TO_CONCEPT_KEY, _normalize_signal
except ModuleNotFoundError:
    from scripts.prepare_snippet_concept_assignment_draft import SIGNAL_TO_CONCEPT_KEY, _normalize_signal


ALLOWED_METADATA_REASONS = {"spanish_definition_signal_allowed_metadata"}
VALIDATED_CONCEPT_STATUSES = {"validated", "published", "approved"}


def verify_assignment_draft(snippets, assignment_draft, concepts, manifest_concepts):
    assignments = assignment_draft.get("assignments", [])
    assignments_by_index = {}
    assignment_counts_by_index = Counter()
    for assignment in assignments:
        snippet_index = assignment.get("snippet_index")
        assignment_counts_by_index[snippet_index] += 1
        assignments_by_index[snippet_index] = assignment
    existing_concept_ids = {str(concept.get("id")) for concept in concepts if concept.get("id")}
    existing_concepts_by_id = {
        str(concept.get("id")): concept
        for concept in concepts
        if concept.get("id")
    }
    approved_concept_keys = {
        concept.get("concept_key")
        for concept in manifest_concepts
        if concept.get("concept_key")
    }
    block_reasons = Counter()
    unknown_concept_ids = []
    snippets_without_assignment = []
    by_concept_key = Counter()
    by_source_language = Counter()
    by_matched_signal = Counter()

    for index, snippet in enumerate(snippets):
        if assignment_counts_by_index[index] > 1:
            block_reasons["duplicate_assignment"] += 1
        assignment = assignments_by_index.get(index)
        if assignment is None:
            snippets_without_assignment.append(index)
            block_reasons["missing_assignment"] += 1
            continue
        concept_id = assignment.get("concept_id")
        concept_key = assignment.get("concept_key")
        if concept_id not in existing_concept_ids:
            unknown_concept_ids.append(concept_id)
            block_reasons["unknown_concept_id"] += 1
        elif _concept_is_validated(existing_concepts_by_id[concept_id]):
            block_reasons["automatically_validated_concept"] += 1
        if concept_key not in approved_concept_keys:
            block_reasons["concept_key_not_in_manifest"] += 1
        if not _concept_matches_signal(snippet, assignment):
            block_reasons["signal_concept_mismatch"] += 1
        by_concept_key[concept_key] += 1
        by_source_language[f"{snippet.get('source_type') or 'unknown'}|{snippet.get('language') or 'unknown'}"] += 1
        by_matched_signal[snippet.get("matched_signal") or "unknown"] += 1

    return {
        "passed": not block_reasons,
        "total_assignments": len(assignments),
        "block_reasons": dict(sorted(block_reasons.items())),
        "assignments_by_concept_key": dict(sorted(by_concept_key.items())),
        "assignments_by_source_type_language": dict(sorted(by_source_language.items())),
        "assignments_by_matched_signal": dict(sorted(by_matched_signal.items())),
        "unknown_concept_ids": unknown_concept_ids,
        "snippets_without_assignment": snippets_without_assignment,
        "no_database_writes": True,
    }


def _concept_matches_signal(snippet, assignment):
    metadata_reason = assignment.get("metadata_reason")
    if metadata_reason in ALLOWED_METADATA_REASONS:
        return True
    expected_concept_key = SIGNAL_TO_CONCEPT_KEY.get(_normalize_signal(snippet.get("matched_signal")))
    return assignment.get("concept_key") == expected_concept_key


def _concept_is_validated(concept):
    status = concept.get("current_status") or concept.get("review_state")
    return concept.get("validated") is True or status in VALIDATED_CONCEPT_STATUSES
