"""Local verification for the controlled candidate-snippet workflow."""

import subprocess

MAX_SNIPPET_WORDS = 80
SAFE_CONTRACT_FLAGS = {
    "neon_writes": False,
    "database_modifications": False,
    "validated_content": False,
}


def summarize_candidate_snippet_report(report):
    snippets = report.get("candidate_snippets", [])
    snippets_by_source = {}
    for snippet in snippets:
        source_title = snippet.get("source_title") or "unknown"
        snippets_by_source[source_title] = snippets_by_source.get(source_title, 0) + 1
    return {
        "snippets_generated": len(snippets),
        "snippets_by_source": dict(sorted(snippets_by_source.items())),
        "max_snippet_word_count": max(
            [snippet.get("snippet_word_count", 0) for snippet in snippets] or [0]
        ),
    }


def verify_snippet_word_limit(report):
    over_limit_indexes = [
        index
        for index, snippet in enumerate(report.get("candidate_snippets", []))
        if snippet.get("snippet_word_count", 0) > MAX_SNIPPET_WORDS
    ]
    return {
        "passed": not over_limit_indexes,
        "max_allowed_words": MAX_SNIPPET_WORDS,
        "over_limit_indexes": over_limit_indexes,
    }


def verify_review_state_fields(report):
    invalid_indexes = [
        index
        for index, snippet in enumerate(report.get("candidate_snippets", []))
        if snippet.get("extraction_type") != "literal_quote"
        or snippet.get("proposed_review_state") != "raw_import"
        or snippet.get("requires_human_review") is not True
    ]
    return {
        "passed": not invalid_indexes,
        "invalid_review_state_indexes": invalid_indexes,
    }


def verify_report_contract(report):
    contract = report.get("contract", {})
    violated_flags = [
        flag
        for flag, expected_value in SAFE_CONTRACT_FLAGS.items()
        if contract.get(flag) != expected_value
    ]
    return {
        "passed": not violated_flags,
        "violated_contract_flags": violated_flags,
    }


def _run_command_check(name, command, project_root, runner=subprocess.run):
    result = runner(command, cwd=project_root, capture_output=True, text=True)
    return {
        "name": name,
        "command": " ".join(command),
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def run_extractor_command(project_root, runner=subprocess.run):
    return _run_command_check(
        "candidate snippet extractor command",
        ["python", "scripts/extract_candidate_snippets.py"],
        project_root,
        runner=runner,
    )


def run_unittest_command(project_root, runner=subprocess.run):
    return _run_command_check(
        "unittest discovery command",
        ["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        project_root,
        runner=runner,
    )
