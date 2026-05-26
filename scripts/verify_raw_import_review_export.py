import argparse
import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_PATH = PROJECT_ROOT / "data" / "processed" / "raw_import_review_export.csv"
EXPECTED_ROWS = 100


def load_review_export(path=DEFAULT_EXPORT_PATH):
    with Path(path).open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def verify_review_export(
    rows,
    export_path=DEFAULT_EXPORT_PATH,
    expected_rows=EXPECTED_ROWS,
    check_ignore_func=None,
):
    check_ignore_func = check_ignore_func or export_is_ignored
    fingerprints = [row.get("import_fingerprint", "") for row in rows]
    duplicate_fingerprints = sorted(
        fingerprint
        for fingerprint, count in Counter(fingerprints).items()
        if fingerprint and count > 1
    )
    result = {
        "export_exists": Path(export_path).exists(),
        "rows": len(rows),
        "expected_rows": expected_rows,
        "all_raw_import": all(row.get("review_status") == "raw_import" for row in rows),
        "all_require_human_review": all(
            _bool_text(row.get("requires_human_review")) is True for row in rows
        ),
        "none_validated": all(_bool_text(row.get("validated")) is False for row in rows),
        "duplicate_import_fingerprints": duplicate_fingerprints,
        "git_ignored": check_ignore_func(export_path),
        "concepts_included": dict(sorted(Counter(row.get("concept_key", "") for row in rows).items())),
        "sources_included": dict(
            sorted(
                Counter(
                    f"{row.get('source_title', '')}|{row.get('source_type', '')}|{row.get('language', '')}"
                    for row in rows
                ).items()
            )
        ),
        "definition_text_printed": False,
    }
    result["passed"] = (
        result["export_exists"]
        and result["rows"] == expected_rows
        and result["all_raw_import"]
        and result["all_require_human_review"]
        and result["none_validated"]
        and not result["duplicate_import_fingerprints"]
        and result["git_ignored"]
    )
    return result


def export_is_ignored(path):
    relative_path = Path(path)
    if relative_path.is_absolute():
        try:
            relative_path = relative_path.relative_to(PROJECT_ROOT)
        except ValueError:
            pass
    result = subprocess.run(
        ["git", "check-ignore", str(relative_path).replace("\\", "/")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def format_console_summary(result):
    return "\n".join(
        [
            "Raw import review export verification complete.",
            f"Passed: {str(result['passed']).lower()}",
            f"Export exists: {str(result['export_exists']).lower()}",
            f"Rows: {result['rows']}",
            f"Expected rows: {result['expected_rows']}",
            f"All raw_import: {str(result['all_raw_import']).lower()}",
            f"All require human review: {str(result['all_require_human_review']).lower()}",
            f"None validated: {str(result['none_validated']).lower()}",
            f"Duplicate import fingerprints: {_format_list(result['duplicate_import_fingerprints'])}",
            f"Git ignored: {str(result['git_ignored']).lower()}",
            f"Concepts included: {_format_key_counts(result['concepts_included'])}",
            f"Sources included: {_format_key_counts(result['sources_included'])}",
            "Definition text printed: false",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify local raw_import review export safety and shape."
    )
    parser.add_argument("--export", type=Path, default=DEFAULT_EXPORT_PATH)
    parser.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS)
    args = parser.parse_args(argv)

    try:
        rows = load_review_export(args.export)
        result = verify_review_export(rows, args.export, args.expected_rows)
    except Exception as exc:
        print("Raw import review export verification failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(result))
    return 0 if result["passed"] else 1


def _bool_text(value):
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def _format_key_counts(counts):
    if not counts:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in counts.items())


def _format_list(values):
    return "none" if not values else ", ".join(values)


if __name__ == "__main__":
    raise SystemExit(main())
