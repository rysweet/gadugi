#!/usr/bin/env python3
"""
CLI entry point for executing the System Design Review Agent.

This script is intended to be invoked from the GitHub Actions workflow.
It encapsulates the previous inline-Python logic so that the workflow file
remains concise and maintainable.
"""

from __future__ import annotations

import os
import subprocess
import sys
from textwrap import dedent


def _post_pr_comment(pr_number: str, body: str) -> None:
    """Post a comment to the PR via the GitHub CLI."""
    try:
        subprocess.run(
            ["gh", "pr", "comment", pr_number, "--body", body],
            check=True,
            env=os.environ,
        )
        print("Posted PR comment successfully")
    except subprocess.CalledProcessError as exc:
        print(f"Failed to post PR comment: {exc}")


def _fallback_comment() -> str:
    """Return a fallback comment when automated review is unavailable."""
    return dedent(
        """\
        ## System Design Review Summary

        **Status**: Automated review temporarily unavailable

        *Note: This notification was created by the System Design Review workflow.*

        The System Design Review Agent is currently being deployed. Manual architectural review is recommended for:

        - New classes or modules
        - Changes to public interfaces
        - Security or performance modifications
        - Integration point changes

        Once deployment is complete, automated architectural reviews will resume.
        """
    )


def _error_comment(error: Exception) -> str:
    """Return a comment body describing an unexpected error."""
    return dedent(
        f"""\
        ## System Design Review Error

        **Status**: Review failed due to technical error

        *Note: This error notification was created by the System Design Review workflow.*

        Error details:
        ```
        {error}
        ```

        Please review architectural changes manually or contact the development team.
        """
    )


def main() -> None:
    pr_number = os.getenv("PR_NUMBER")
    if not pr_number:
        print("Environment variable PR_NUMBER not set. Aborting.")
        sys.exit(1)

    # Ensure local repository modules are importable
    sys.path.insert(0, ".")

    try:
        from .claude.agents.system_design_reviewer.core import SystemDesignReviewer  # type: ignore[import]
    except ImportError as exc:
        print(f"Import error: {exc}")
        print("System Design Reviewer not available, skipping review.")
        _post_pr_comment(pr_number, _fallback_comment())
        # Graceful exit so workflow continues but marks step success.
        return

    reviewer = SystemDesignReviewer()

    try:
        print(f"Starting architectural review for PR #{pr_number}")
        result = reviewer.review_pr(pr_number)

        if result.status.value == "completed":
            summary_body = dedent(
                f"""\
                ## System Design Review Summary

                **Architectural impact**: {result.architectural_impact.value.title()}

                - Changes detected: {len(result.changes_detected)}
                - ADRs generated: {len(result.adrs_generated)}
                - Documentation updates: {len(result.documentation_updates)}

                *This review was generated automatically by the System Design Review Agent.*
                """
            )
            _post_pr_comment(pr_number, summary_body)
            print("✅ Review completed successfully")
        else:
            fail_body = (
                "## System Design Review Failed\n\n"
                "*Automated review could not be completed.*"
            )
            _post_pr_comment(pr_number, fail_body)
            print("❌ Review failed.")
            sys.exit(1)

    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error during review: {exc}")
        _post_pr_comment(pr_number, _error_comment(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
