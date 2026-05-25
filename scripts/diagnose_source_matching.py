import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

try:
    from prepare_snippet_insertion_dry_run import (
        DEFAULT_INPUT_PATH,
        fetch_source_rows,
        load_candidate_snippets,
        load_database_url,
        load_source_rows_fixture,
    )
except ModuleNotFoundError:
    from scripts.prepare_snippet_insertion_dry_run import (
        DEFAULT_INPUT_PATH,
        fetch_source_rows,
        load_candidate_snippets,
        load_database_url,
        load_source_rows_fixture,
    )


def normalize_for_diagnostic(value):
    text = "" if value is None else str(value)
    text = " ".join(text.strip().lower().split())
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(character for character in decomposed if not unicodedata.combining(character))


def summarize_snippet_sources(snippets):
    counts = Counter(
        (
            snippet.get("source_title"),
            snippet.get("source_type"),
            snippet.get("language"),
        )
        for snippet in snippets
    )
    return [
        {
            "source_title": title,
            "source_type": source_type,
            "language": language,
            "snippet_count": count,
        }
        for (title, source_type, language), count in sorted(
            counts.items(), key=lambda item: tuple("" if part is None else str(part) for part in item[0])
        )
    ]


def summarize_source_rows(source_rows):
    return [
        {
            "title": row.get("title"),
            "source_type": row.get("source_type"),
            "language": row.get("language"),
        }
        for row in sorted(
            source_rows,
            key=lambda row: (
                "" if row.get("title") is None else str(row.get("title")),
                "" if row.get("source_type") is None else str(row.get("source_type")),
                "" if row.get("language") is None else str(row.get("language")),
            ),
        )
    ]


def compare_source_matching(snippets, source_rows):
    snippet_sources = summarize_snippet_sources(snippets)
    sources = summarize_source_rows(source_rows)
    exact_source_keys = {
        (source["title"], source["source_type"], source["language"])
        for source in sources
    }
    source_diagnostic_keys = [
        {
            **source,
            "normalized_title": normalize_for_diagnostic(source["title"]),
            "normalized_source_type": normalize_for_diagnostic(source["source_type"]),
            "normalized_language": normalize_for_diagnostic(source["language"]),
        }
        for source in sources
    ]

    exact_matches = []
    exact_mismatches = []
    normalized_match_candidates = []
    for snippet_source in snippet_sources:
        snippet_key = (
            snippet_source["source_title"],
            snippet_source["source_type"],
            snippet_source["language"],
        )
        if snippet_key in exact_source_keys:
            exact_matches.append(snippet_source)
            continue

        exact_mismatches.append(snippet_source)
        snippet_title = normalize_for_diagnostic(snippet_source["source_title"])
        snippet_type = normalize_for_diagnostic(snippet_source["source_type"])
        snippet_language = normalize_for_diagnostic(snippet_source["language"])
        candidates = []
        for source in source_diagnostic_keys:
            title_matches = source["normalized_title"] == snippet_title
            type_matches = source["normalized_source_type"] == snippet_type
            language_matches = source["normalized_language"] == snippet_language
            if title_matches and type_matches:
                match_reason = "title_source_type_match"
                if not language_matches:
                    match_reason = "title_source_type_match_language_diff"
                candidates.append(
                    {
                        "source_title": source["title"],
                        "source_type": source["source_type"],
                        "language": source["language"],
                        "match_reason": match_reason,
                    }
                )
        normalized_match_candidates.append(
            {
                "snippet_source_title": snippet_source["source_title"],
                "snippet_source_type": snippet_source["source_type"],
                "snippet_language": snippet_source["language"],
                "candidate_matches": candidates,
            }
        )

    probable_causes = infer_probable_causes(exact_mismatches, normalized_match_candidates)
    return {
        "snippet_unique_sources": snippet_sources,
        "snippet_source_type_language": summarize_type_language(snippet_sources, "source_type"),
        "database_sources": sources,
        "database_source_type_language": summarize_type_language(sources, "source_type"),
        "exact_matches": exact_matches,
        "exact_mismatches": exact_mismatches,
        "normalized_match_candidates": normalized_match_candidates,
        "probable_causes": probable_causes,
        "contract": {
            "select_only": True,
            "database_writes": False,
            "prints_snippet_text": False,
        },
    }


def summarize_type_language(rows, source_type_key):
    counts = Counter(
        (row.get(source_type_key), row.get("language"))
        for row in rows
    )
    return [
        {"source_type": source_type, "language": language, "count": count}
        for (source_type, language), count in sorted(
            counts.items(), key=lambda item: tuple("" if part is None else str(part) for part in item[0])
        )
    ]


def infer_probable_causes(exact_mismatches, normalized_match_candidates):
    if not exact_mismatches:
        return ["no_mismatch_detected"]
    language_diff_count = 0
    missing_language_count = 0
    for mismatch, candidate_group in zip(exact_mismatches, normalized_match_candidates):
        candidates = candidate_group.get("candidate_matches", [])
        if any(candidate["match_reason"] == "title_source_type_match_language_diff" for candidate in candidates):
            language_diff_count += 1
            if mismatch.get("language") in (None, ""):
                missing_language_count += 1
    if language_diff_count == len(exact_mismatches) and missing_language_count == len(exact_mismatches):
        return ["snippet_language_missing_while_sources_have_language"]
    if language_diff_count:
        return ["language_mismatch_between_snippets_and_sources"]
    return ["no_normalized_candidate_match_found"]


def format_diagnostic_summary(diagnostic):
    lines = [
        "Source matching diagnostic complete.",
        "Snippet unique sources:",
    ]
    for source in diagnostic["snippet_unique_sources"]:
        lines.append(
            f"  - title={source['source_title']!r}; "
            f"source_type={source['source_type']!r}; "
            f"language={source['language']!r}; "
            f"snippet_count={source['snippet_count']}"
        )
    lines.append("Snippet source_type/language:")
    for item in diagnostic["snippet_source_type_language"]:
        lines.append(
            f"  - source_type={item['source_type']!r}; language={item['language']!r}; count={item['count']}"
        )
    lines.append("Database sources:")
    for source in diagnostic["database_sources"]:
        lines.append(
            f"  - title={source['title']!r}; "
            f"source_type={source['source_type']!r}; "
            f"language={source['language']!r}"
        )
    lines.append("Database source_type/language:")
    for item in diagnostic["database_source_type_language"]:
        lines.append(
            f"  - source_type={item['source_type']!r}; language={item['language']!r}; count={item['count']}"
        )
    lines.append(f"Exact matches: {len(diagnostic['exact_matches'])}")
    lines.append(f"Exact mismatches: {len(diagnostic['exact_mismatches'])}")
    lines.append("Normalized match candidates:")
    for group in diagnostic["normalized_match_candidates"]:
        if not group["candidate_matches"]:
            lines.append(
                f"  - snippet_title={group['snippet_source_title']!r}; "
                f"source_type={group['snippet_source_type']!r}; "
                f"language={group['snippet_language']!r}; candidates=none"
            )
            continue
        for candidate in group["candidate_matches"]:
            lines.append(
                f"  - snippet_title={group['snippet_source_title']!r}; "
                f"source_type={group['snippet_source_type']!r}; "
                f"language={group['snippet_language']!r}; "
                f"candidate_title={candidate['source_title']!r}; "
                f"candidate_language={candidate['language']!r}; "
                f"reason={candidate['match_reason']}"
            )
    lines.append("Probable causes: " + ", ".join(diagnostic["probable_causes"]))
    lines.append("No database writes: true")
    lines.append("Snippet text printed: false")
    return "\n".join(lines)


def _contains_forbidden_secret_label(output):
    return bool(re.search(r"database_url|password|token|host=", output, re.IGNORECASE))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Diagnose source matching between candidate snippets and Neon sources."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--database-url")
    parser.add_argument(
        "--sources-fixture",
        type=Path,
        help="Use local source-row fixture instead of live Neon SELECT.",
    )
    args = parser.parse_args(argv)

    try:
        snippets = load_candidate_snippets(args.input)
        if args.sources_fixture is not None:
            source_rows = load_source_rows_fixture(args.sources_fixture)
        else:
            source_rows = fetch_source_rows(args.database_url or load_database_url())
        summary = format_diagnostic_summary(compare_source_matching(snippets, source_rows))
    except Exception as exc:
        print("Source matching diagnostic failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1
    if _contains_forbidden_secret_label(summary):
        print("Source matching diagnostic failed.", file=sys.stderr)
        print("Unsafe diagnostic output detected.", file=sys.stderr)
        return 1
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
