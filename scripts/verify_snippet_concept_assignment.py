from collections import Counter


def verify_assignment_draft(snippets, assignment_draft, concepts, manifest_concepts):
    assignments = assignment_draft.get("assignments", [])
    assignments_by_index = {assignment.get("snippet_index"): assignment for assignment in assignments}
    existing_concept_ids = {str(concept.get("id")) for concept in concepts if concept.get("id")}
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
        if concept_key not in approved_concept_keys:
            block_reasons["concept_key_not_in_manifest"] += 1
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
