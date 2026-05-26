SIGNAL_TO_CONCEPT_KEY = {
    "datum": "datum",
    "feature control frame": "feature_control_frame",
    "tolerance zone": "tolerance_zone",
    "mmc": "maximum_material_condition",
    "lmc": "least_material_condition",
    "rfs": "regardless_of_feature_size",
}


def build_assignment_draft(snippets, concepts):
    concept_ids_by_key = {
        concept["slug"]: concept["id"]
        for concept in concepts
    }
    assignments = []
    ready_to_insert = 0
    missing_concept_id = 0
    for index, snippet in enumerate(snippets):
        concept_key = _concept_key_for_signal(snippet.get("matched_signal"))
        concept_id = concept_ids_by_key.get(concept_key)
        if concept_id:
            ready_to_insert += 1
        else:
            missing_concept_id += 1
        assignments.append(
            {
                "snippet_index": index,
                "matched_signal": snippet.get("matched_signal"),
                "metadata_reason": None,
                "concept_key": concept_key,
                "concept_id": concept_id,
                "confidence": "high" if concept_id else "none",
                "status": "ready_to_insert" if concept_id else "blocked",
                "reason_codes": [] if concept_id else ["missing_concept_id"],
                "audit_notes": [
                    "matched_signal normalized to approved concept_key",
                    "concept_id resolved from existing concepts metadata",
                ]
                if concept_id
                else ["concept_id not found in existing concepts metadata"],
            }
        )
    return {
        "total_snippets": len(snippets),
        "ready_to_insert": ready_to_insert,
        "blocked_snippets": len(snippets) - ready_to_insert,
        "missing_concept_id": missing_concept_id,
        "assignments": assignments,
        "contract": {
            "database_writes": False,
            "database_modifications": False,
            "snippet_content_saved": False,
            "concept_ids_assigned_in_database": False,
        },
    }


def _concept_key_for_signal(signal):
    normalized_signal = " ".join(str(signal or "").strip().lower().split())
    return SIGNAL_TO_CONCEPT_KEY.get(normalized_signal, normalized_signal)
