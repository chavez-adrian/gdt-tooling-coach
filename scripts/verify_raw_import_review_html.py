import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    from build_raw_import_review_html import ALLOWED_REVIEW_DECISIONS, DEFAULT_HTML_PATH
except ModuleNotFoundError:
    from scripts.build_raw_import_review_html import ALLOWED_REVIEW_DECISIONS, DEFAULT_HTML_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROWS = 100


def verify_review_html(path=DEFAULT_HTML_PATH, expected_rows=EXPECTED_ROWS, check_ignore_func=None):
    path = Path(path)
    check_ignore_func = check_ignore_func or html_is_ignored
    html = path.read_text(encoding="utf-8") if path.exists() else ""
    result = {
        "html_exists": path.exists(),
        "git_ignored": check_ignore_func(path),
        "definition_id_entries": len(re.findall(r'data-definition-id="[^"]+"', html)),
        "expected_rows": expected_rows,
        "allowed_decisions_present": all(
            f'value="{decision}"' in html for decision in ALLOWED_REVIEW_DECISIONS
        ),
        "no_external_urls": "http://" not in html and "https://" not in html,
    }
    result["passed"] = (
        result["html_exists"]
        and result["git_ignored"]
        and result["definition_id_entries"] == expected_rows
        and result["allowed_decisions_present"]
        and result["no_external_urls"]
    )
    return result


def html_is_ignored(path):
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
            "Raw import review HTML verification complete.",
            f"Passed: {str(result['passed']).lower()}",
            f"HTML exists: {str(result['html_exists']).lower()}",
            f"Git ignored: {str(result['git_ignored']).lower()}",
            f"Definition id entries: {result['definition_id_entries']}",
            f"Expected rows: {result['expected_rows']}",
            f"Allowed decisions present: {str(result['allowed_decisions_present']).lower()}",
            f"No external URLs: {str(result['no_external_urls']).lower()}",
        ]
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify local raw_import review HTML.")
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_PATH)
    parser.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS)
    args = parser.parse_args(argv)

    try:
        result = verify_review_html(args.html, args.expected_rows)
    except Exception as exc:
        print("Raw import review HTML verification failed.", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print(format_console_summary(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
