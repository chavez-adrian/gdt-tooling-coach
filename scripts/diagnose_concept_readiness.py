import argparse
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import psycopg

try:
    from prepare_snippet_insertion_dry_run import (
        DEFAULT_INPUT_PATH,
        load_candidate_snippets,
        load_database_url,
    )
except ModuleNotFoundError:
    from scripts.prepare_snippet_insertion_dry_run import (
        DEFAULT_INPUT_PATH,
        load_candidate_snippets,
        load_database_url,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_RELATIVE_PATH = Path("data/processed/concept_readiness_report.json")
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / DEFAULT_OUTPUT_RELATIVE_PATH
SELECT_CONCEPTS_SQL = """
SELECT id, slug, category, subcategory, current_status
FROM concepts
ORDER BY slug;
"""


def fetch_concept_rows(database_url, connect=psycopg.connect):
    with connect(database_url) as conn:
        cur = conn.cursor()
        cur.execute(SELECT_CONCEPTS_SQL)
        column_names = [column[0] for column in cur.description]
        return [dict(zip(column_names, row)) for row in cur.fetchall()]


def load_concept_rows_fixture(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_concept_readiness_report(snippets, concepts):
    concept_lookup = _concept_lookup(concepts)
    matched_signal_summary = Counter()
    source_summary = Counter()
    concepts_by_review_state = Counter()
    missing_concept_id = 0
    potential_matches = 0
    unmatched_snippets_count = 0
    candidate_label_summary = Counter()

    for concept in concepts:
        state = concept.get("review_state") or concept.get("current_status") or "unknown"
        concepts_by_review_state[state] += 1

    for snippet in snippets:
        matched_signal = snippet.get("matched_signal") or "unknown"
        source_type = snippet.get("source_type") or "unknown"
        language = snippet.get("language") or "unknown"
        page_number = snippet.get("page_number")
        matched_signal_summary[matched_signal] += 1
        source_summary[f"{source_type}|{language}"] += 1
        if not snippet.get("concept_id"):
            missing_concept_id += 1
        labels = candidate_concept_labels(snippet)
        for label in labels:
            candidate_label_summary[label] += 1
        if any(normalize_for_match(label) in concept_lookup for label in labels):
            potential_matches += 1
        else:
            unmatched_snippets_count += 1

    return {
        "total_snippets": len(snippets),
        "missing_concept_id": missing_concept_id,
        "existing_concepts_count": len(concepts),
        "concepts_by_review_state": dict(sorted(concepts_by_review_state.items())),
        "potential_existing_concept_matches": potential_matches,
        "unmatched_snippets_count": unmatched_snippets_count,
        "matched_signal_summary": dict(sorted(matched_signal_summary.items())),
        "source_summary": dict(sorted(source_summary.items())),
        "candidate_concept_label_summary": dict(sorted(candidate_label_summary.items())),
        "contract": {
            "select_only": True,
            "database_writes": False,
            "prints_text": False,
            "assigns_concept_id": False,
            "validated_content": False,
        },
    }


def candidate_concept_labels(snippet):
    signal = snippet.get("matched_signal")
    source_type = snippet.get("source_type")
    language = snippet.get("language")
    page_number = snippet.get("page_number")
    labels = []
    if signal:
        labels.append(str(signal))
    parts = [signal, source_type, language]
    if all(part not in (None, "") for part in parts):
        labels.append("-".join(str(part) for part in parts))
    if all(part not in (None, "") for part in [signal, source_type, language, page_number]):
        labels.append("-".join(str(part) for part in [signal, source_type, language, f"page-{page_number}"]))
    return labels


def write_report(report, output_path=DEFAULT_OUTPUT_PATH):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def report_path_is_ignored(run_command=subprocess.run):
    result = run_command(
        ["git", "check-ignore", DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def format_console_summary(report):
    return "\n".join(
        [
            "Concept readiness diagnostic complete.",
            f"Total snippets: {report['total_snippets']}",
            f"Missing concept_id: {report['missing_concept_id']}",
            f"Existing concepts count: {report['existing_concepts_count']}",
            f"Potential existing concept matches: {report['potential_existing_concept_matches']}",
            f"Unmatched snippets: {report['unmatched_snippets_count']}",
            f"Matched signal summary: {_format_key_counts(report['matched_signal_summary'])}",
            f"Source summary: {_format_key_counts(report['source_summary'])}",
            "No database writes: true",
            "Snippet text printed: false",
            "Concept ids assigned: false",
        ]
    )


def normalize_for_match(value):
    text = "" if value is None else str(value)
    text = " ".join(text.strip().lower().split())
    text = re.sub(r"[_\s]+", "-", text)
    decomposed = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in decomposed if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9-]+", "", text)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Diagnose concept readiness for candidate snippets without assigning concept ids."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--database-url")
    parser.add_argument("--concepts-fixture", type=Path)
    parser.add_argument("--skip-ignore-check", action="store_true")
    args = parser.parse_args(argv)

    try:
        snippets = load_candidate_snippets(args.input)
        if args.concepts_fixture is None:
            concepts = fetch_concept_rows(args.database_url or load_database_url())
        else:
            concepts = load_concept_rows_fixture(args.concepts_fixture)
        report = build_concept_readiness_report(snippets, concepts)
        write_report(report, args.output)
        if not args.skip_ignore_check and args.output == DEFAULT_OUTPUT_PATH and not report_path_is_ignored():
            raise RuntimeError(f"{DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()} is not ignored by Git")
    except Exception as exc:
        print("Concept readiness diagnostic failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(report))
    return 0


def _concept_lookup(concepts):
    keys = set()
    for concept in concepts:
        for field in ("slug", "category", "subcategory"):
            if concept.get(field):
                keys.add(normalize_for_match(concept[field]))
    return keys


def _format_key_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


if __name__ == "__main__":
    raise SystemExit(main())
