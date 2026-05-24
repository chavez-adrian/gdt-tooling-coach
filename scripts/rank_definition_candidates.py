"""Metadata-only scoring and ranking for definition candidate pages."""

import argparse
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "definition_candidate_pages.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "ranked_definition_candidates.json"
DEFAULT_OUTPUT_RELATIVE_PATH = Path("data/processed/ranked_definition_candidates.json")

STRONG_SIGNALS = {
    "definition",
    "definitions",
    "definiciÃ³n",
    "definiciones",
    "terminology",
    "terminologÃ­a",
    "glossary",
}
MEDIUM_SIGNALS = {
    "datum",
    "feature control frame",
    "tolerance zone",
    "MMC",
    "LMC",
    "RFS",
    "sÃ­mbolo",
    "sÃ­mbolos",
}
GENERIC_SIGNALS = {"term", "terms", "tÃ©rmino", "tÃ©rminos"}
PREFERRED_SOURCE_TYPES = {"standard", "official_standard", "norm"}
SUPPORTED_LANGUAGES = {"en", "es", "english", "spanish"}
FORBIDDEN_TEXT_KEYS = {
    "content",
    "definition",
    "definitions",
    "excerpt",
    "long_quote",
    "page_text",
    "quote",
    "sample",
    "text",
    "text_sample",
}
RANKED_REPORT_ROW_KEYS = (
    "source_title",
    "source_type",
    "language",
    "page_number",
    "matched_signals",
    "signal_count",
    "approximate_word_count",
    "candidate_score",
    "rank_within_source",
    "global_rank",
    "priority_bucket",
)


def _priority_bucket(score):
    if score >= 12:
        return "high"
    if score >= 5:
        return "medium"
    return "low"


def score_definition_candidate(candidate):
    score = candidate.get("signal_count", 0)
    word_count = candidate.get("approximate_word_count", 0)
    if 100 <= word_count <= 1600:
        score += 1
    if candidate.get("source_type") in PREFERRED_SOURCE_TYPES:
        score += 1
    if candidate.get("language") in SUPPORTED_LANGUAGES:
        score += 1
    for signal in candidate.get("matched_signals", []):
        if signal in STRONG_SIGNALS:
            score += 4
        elif signal in MEDIUM_SIGNALS:
            score += 2
        elif signal in GENERIC_SIGNALS:
            score -= 1
    safe_candidate = {
        key: value for key, value in candidate.items() if key not in FORBIDDEN_TEXT_KEYS
    }
    return {
        **safe_candidate,
        "definition_score": score,
        "priority_bucket": _priority_bucket(score),
    }


def score_definition_candidates(candidates):
    scored = [score_definition_candidate(candidate) for candidate in candidates]
    return sorted(scored, key=lambda item: item["definition_score"], reverse=True)


def build_ranked_definition_candidate_rows(candidates):
    rows = []
    source_ranks = {}
    for global_rank, candidate in enumerate(score_definition_candidates(candidates), 1):
        candidate_score = candidate["definition_score"]
        source_title = candidate.get("source_title", "")
        source_ranks[source_title] = source_ranks.get(source_title, 0) + 1
        row = {
            "source_title": candidate.get("source_title"),
            "source_type": candidate.get("source_type"),
            "language": candidate.get("language"),
            "page_number": candidate.get("page_number"),
            "matched_signals": candidate.get("matched_signals", []),
            "signal_count": candidate.get("signal_count", 0),
            "approximate_word_count": candidate.get("approximate_word_count", 0),
            "candidate_score": candidate_score,
            "rank_within_source": source_ranks[source_title],
            "global_rank": global_rank,
            "priority_bucket": candidate["priority_bucket"],
        }
        rows.append(row)
    return rows


def build_ranked_definition_candidate_report(candidates):
    rows = build_ranked_definition_candidate_rows(candidates)
    bucket_counts = {"high": 0, "medium": 0, "low": 0}
    high_counts_by_source = {}
    for row in rows:
        bucket_counts[row["priority_bucket"]] += 1
        if row["priority_bucket"] == "high":
            source_title = row.get("source_title", "")
            high_counts_by_source[source_title] = high_counts_by_source.get(source_title, 0) + 1
    top_sources = [
        {"source_title": source_title, "high_priority_candidates": count}
        for source_title, count in sorted(
            high_counts_by_source.items(), key=lambda item: (-item[1], item[0])
        )
    ]
    return {
        "summary": {
            "total_candidates": len(rows),
            "priority_buckets": bucket_counts,
            "top_sources_by_high_priority_candidates": top_sources,
        },
        "ranked_candidates": rows,
    }


def write_ranked_definition_candidate_report(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as input_file:
        candidate_report = json.load(input_file)
    report = build_ranked_definition_candidate_report(
        candidate_report.get("candidate_pages", [])
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(report, output_file, indent=2, sort_keys=True)
        output_file.write("\n")
    return report


def ranked_report_output_is_ignored(run_command=subprocess.run):
    result = run_command(
        ["git", "check-ignore", DEFAULT_OUTPUT_RELATIVE_PATH.as_posix()],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def format_console_summary(report):
    summary = report["summary"]
    buckets = summary["priority_buckets"]
    lines = [
        f"Total candidates: {summary['total_candidates']}",
        f"High: {buckets['high']}",
        f"Medium: {buckets['medium']}",
        f"Low: {buckets['low']}",
        "Top sources by high-priority candidates:",
    ]
    top_sources = summary["top_sources_by_high_priority_candidates"]
    if not top_sources:
        lines.append("  none")
    else:
        for source in top_sources:
            lines.append(
                f"  {source['source_title']}: {source['high_priority_candidates']}"
            )
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Write a metadata-only ranked definition candidate report."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args(argv)
    report = write_ranked_definition_candidate_report(args.input, args.output)
    print(format_console_summary(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
