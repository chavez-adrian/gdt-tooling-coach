from scripts.insert_seed_concepts import build_insertion_plan


def verify_seed_gate(manifest_concepts, existing_concepts):
    default_plan = build_insertion_plan(
        manifest_concepts,
        existing_concepts,
        execute=False,
    )
    return {
        "default_dry_run_verified": (
            default_plan["mode"] == "dry-run"
            and default_plan["database_writes_attempted"] is False
            and default_plan["execute_requested"] is False
        ),
        "default_mode": default_plan["mode"],
        "default_database_writes_attempted": default_plan["database_writes_attempted"],
        "default_execute_requested": default_plan["execute_requested"],
        "ready_to_insert": default_plan["ready_to_insert"],
        "blocked_concepts": default_plan["blocked_concepts"],
    }
