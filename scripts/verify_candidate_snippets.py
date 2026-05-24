"""Local verification for the controlled candidate-snippet workflow."""


def summarize_candidate_snippet_report(report):
    return {
        "snippets_generated": len(report.get("candidate_snippets", [])),
    }
