#!/usr/bin/env python3
"""GitHub Executor - Single-purpose executor for GitHub operations.

This executor performs GitHub operations directly using gh CLI without delegating to other agents.
It follows the NO DELEGATION principle - all operations use direct subprocess calls to gh.
"""

import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any

from .base_executor import BaseExecutor


class GitHubExecutor(BaseExecutor):
    """Single-purpose executor for GitHub operations via gh CLI.

    CRITICAL: This executor MUST NOT call or delegate to other agents.
    All operations must be direct gh CLI calls only.
    """

    def __init__(self) -> None:
        """Initialize the GitHub executor."""
        self.operations_log = []

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution entry point for GitHub operations.

        Args:
            params: Dictionary containing:
                - operation: 'create_issue' | 'create_pr' | 'list_issues' | 'merge_pr' | 'close_issue'
                - title: Title for issue/PR (for create operations)
                - body: Body content for issue/PR
                - issue_number: Issue number (for close/update)
                - pr_number: PR number (for merge/update)
                - base: Base branch for PR (default: main)
                - head: Head branch for PR
                - labels: List of labels to add

        Returns:
            Dictionary with:
                - success: Boolean indicating success
                - operation: Operation performed
                - result: Operation-specific result data
                - error: Error message if failed
        """
        operation = params.get("operation")

        if not operation:
            return {"success": False, "error": "operation is required"}

        try:
            if operation == "create_issue":
                return self._create_issue(params)
            elif operation == "create_pr":
                return self._create_pr(params)
            elif operation == "list_issues":
                return self._list_issues(params)
            elif operation == "merge_pr":
                return self._merge_pr(params)
            elif operation == "close_issue":
                return self._close_issue(params)
            elif operation == "pr_status":
                return self._pr_status(params)
            elif operation == "add_labels":
                return self._add_labels(params)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        except Exception as e:
            return {"success": False, "operation": operation, "error": str(e)}

    def _create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub issue.

        Direct gh CLI execution - no agent delegation.
        """
        title = params.get("title")
        body = params.get("body", "")
        labels = params.get("labels", [])

        if not title:
            return {
                "success": False,
                "operation": "create_issue",
                "error": "title is required for creating an issue",
            }

        cmd = ["gh", "issue", "create", "--title", title]

        if body:
            cmd.extend(["--body", body])

        if labels:
            cmd.extend(["--label", ",".join(labels)])

        # Execute gh command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {
                "success": False,
                "operation": "create_issue",
                "error": result.stderr,
            }

        # Parse issue number from output
        issue_url = result.stdout.strip()
        issue_number = issue_url.split("/")[-1] if "/" in issue_url else None

        # Log the operation
        self._log_operation("create_issue", {"title": title, "number": issue_number})

        return {
            "success": True,
            "operation": "create_issue",
            "issue_number": issue_number,
            "issue_url": issue_url,
            "title": title,
        }

    def _create_pr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub pull request.

        Direct gh CLI execution - no agent delegation.
        """
        title = params.get("title")
        body = params.get("body", "")
        base = params.get("base", "main")
        head = params.get("head")
        draft = params.get("draft", False)

        if not title:
            return {
                "success": False,
                "operation": "create_pr",
                "error": "title is required for creating a PR",
            }

        cmd = ["gh", "pr", "create", "--title", title, "--base", base]

        if body:
            cmd.extend(["--body", body])

        if head:
            cmd.extend(["--head", head])

        if draft:
            cmd.append("--draft")

        # Execute gh command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {"success": False, "operation": "create_pr", "error": result.stderr}

        # Parse PR URL from output
        pr_url = result.stdout.strip()
        pr_number = pr_url.split("/")[-1] if "/" in pr_url else None

        # Log the operation
        self._log_operation("create_pr", {"title": title, "number": pr_number})

        return {
            "success": True,
            "operation": "create_pr",
            "pr_number": pr_number,
            "pr_url": pr_url,
            "title": title,
            "base": base,
            "head": head,
        }

    def _list_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List GitHub issues.

        Direct gh CLI execution - no agent delegation.
        """
        state = params.get("state", "open")  # open, closed, all
        limit = params.get("limit", 30)
        labels = params.get("labels", [])

        cmd = ["gh", "issue", "list", "--state", state, "--limit", str(limit)]

        if labels:
            cmd.extend(["--label", ",".join(labels)])

        # Add JSON output for parsing
        cmd.append("--json")
        cmd.append("number,title,state,createdAt,labels")

        # Execute gh command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {
                "success": False,
                "operation": "list_issues",
                "error": result.stderr,
            }

        # Parse JSON output
        try:
            issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            issues = []

        # Log the operation
        self._log_operation("list_issues", {"count": len(issues)})

        return {
            "success": True,
            "operation": "list_issues",
            "issues": issues,
            "count": len(issues),
        }

    def _merge_pr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a GitHub pull request.

        Direct gh CLI execution - no agent delegation.

        IMPORTANT: This should only be called after user approval.
        """
        pr_number = params.get("pr_number")
        merge_method = params.get("merge_method", "merge")  # merge, squash, rebase
        delete_branch = params.get("delete_branch", True)

        if not pr_number:
            return {
                "success": False,
                "operation": "merge_pr",
                "error": "pr_number is required for merging",
            }

        cmd = ["gh", "pr", "merge", str(pr_number)]

        # Add merge method
        if merge_method == "squash":
            cmd.append("--squash")
        elif merge_method == "rebase":
            cmd.append("--rebase")
        else:
            cmd.append("--merge")

        # Add delete branch option
        if delete_branch:
            cmd.append("--delete-branch")

        # Execute gh command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {
                "success": False,
                "operation": "merge_pr",
                "pr_number": pr_number,
                "error": result.stderr,
            }

        # Log the operation
        self._log_operation("merge_pr", {"pr_number": pr_number})

        return {
            "success": True,
            "operation": "merge_pr",
            "pr_number": pr_number,
            "message": result.stdout.strip(),
        }

    def _close_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close a GitHub issue.

        Direct gh CLI execution - no agent delegation.
        """
        issue_number = params.get("issue_number")
        comment = params.get("comment")

        if not issue_number:
            return {
                "success": False,
                "operation": "close_issue",
                "error": "issue_number is required",
            }

        # Add comment if provided
        if comment:
            comment_cmd = [
                "gh",
                "issue",
                "comment",
                str(issue_number),
                "--body",
                comment,
            ]
            subprocess.run(comment_cmd, capture_output=True, text=True)

        # Close the issue
        cmd = ["gh", "issue", "close", str(issue_number)]

        # Execute gh command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {
                "success": False,
                "operation": "close_issue",
                "issue_number": issue_number,
                "error": result.stderr,
            }

        # Log the operation
        self._log_operation("close_issue", {"issue_number": issue_number})

        return {
            "success": True,
            "operation": "close_issue",
            "issue_number": issue_number,
            "message": f"Issue #{issue_number} closed",
        }

    def _pr_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Check PR status and CI checks.

        Direct gh CLI execution - no agent delegation.
        """
        pr_number = params.get("pr_number")

        if not pr_number:
            return {
                "success": False,
                "operation": "pr_status",
                "error": "pr_number is required",
            }

        # Get PR checks status
        cmd = ["gh", "pr", "checks", str(pr_number)]

        # Execute gh command
        result = subprocess.run(cmd, capture_output=True, text=True)

        checks_passing = result.returncode == 0
        checks_output = result.stdout

        # Get PR review status
        review_cmd = [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--json",
            "state,mergeable,reviews,statusCheckRollup",
        ]

        review_result = subprocess.run(review_cmd, capture_output=True, text=True)

        pr_data = {}
        if review_result.returncode == 0:
            try:
                pr_data = json.loads(review_result.stdout)
            except json.JSONDecodeError:
                pass

        # Log the operation
        self._log_operation("pr_status", {"pr_number": pr_number})

        return {
            "success": True,
            "operation": "pr_status",
            "pr_number": pr_number,
            "checks_passing": checks_passing,
            "checks_output": checks_output,
            "pr_data": pr_data,
            "mergeable": pr_data.get("mergeable") == "MERGEABLE",
        }

    def _add_labels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add labels to an issue or PR.

        Direct gh CLI execution - no agent delegation.
        """
        item_type = params.get("type", "issue")  # issue or pr
        item_number = params.get("number")
        labels = params.get("labels", [])

        if not item_number:
            return {
                "success": False,
                "operation": "add_labels",
                "error": "number is required",
            }

        if not labels:
            return {
                "success": False,
                "operation": "add_labels",
                "error": "labels are required",
            }

        cmd = [
            "gh",
            item_type,
            "edit",
            str(item_number),
            "--add-label",
            ",".join(labels),
        ]

        # Execute gh command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return {"success": False, "operation": "add_labels", "error": result.stderr}

        # Log the operation
        self._log_operation(
            "add_labels", {"type": item_type, "number": item_number, "labels": labels}
        )

        return {
            "success": True,
            "operation": "add_labels",
            "type": item_type,
            "number": item_number,
            "labels": labels,
        }

    def _log_operation(self, operation: str, details: Dict[str, Any]):
        """Log a GitHub operation for audit purposes."""
        self.operations_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "details": details,
            }
        )

    def get_operations_log(self) -> List[Dict[str, Any]]:
        """Get the log of all GitHub operations."""
        return self.operations_log.copy()


# Single-purpose function interface for direct usage
def execute_github_operation(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a GitHub operation without creating an instance.

    This is the primary interface for CLAUDE.md orchestration.
    No agent delegation - direct gh CLI execution only.

    Args:
        params: GitHub operation parameters

    Returns:
        Operation result dictionary
    """
    executor = GitHubExecutor()
    return executor.execute(params)
