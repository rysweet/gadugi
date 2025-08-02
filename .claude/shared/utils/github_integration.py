"""
GitHub integration utilities for Gadugi multi-agent system.
Provides common GitHub operations used across multiple agents.
"""

import subprocess
import json
import time
from typing import Dict, Any, List, Optional
import logging


logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Handles GitHub operations via gh CLI."""

    def __init__(
        self, repo: Optional[str] = None, retry_config: Optional[Dict[str, Any]] = None
    ):
        self.repo = repo
        self.retry_config = retry_config or {
            "max_retries": 3,
            "initial_delay": 1,
            "backoff_factor": 2,
        }

    def _execute_gh_command(self, args: List[str]) -> Dict[str, Any]:
        """Execute gh CLI command with retry logic."""
        retries = 0
        delay = self.retry_config["initial_delay"]

        while retries < self.retry_config["max_retries"]:
            try:
                cmd = ["gh"] + args
                if self.repo:
                    cmd.extend(["--repo", self.repo])

                result = subprocess.run(cmd, capture_output=True, text=True, check=True)

                # Try to parse JSON output
                try:
                    return {
                        "success": True,
                        "data": json.loads(result.stdout) if result.stdout else None,
                        "raw_output": result.stdout,
                    }
                except json.JSONDecodeError:
                    return {"success": True, "data": None, "raw_output": result.stdout}

            except subprocess.CalledProcessError as e:
                retries += 1
                if retries >= self.retry_config["max_retries"]:
                    logger.error(f"GitHub command failed after {retries} retries: {e}")
                    return {"success": False, "error": str(e), "stderr": e.stderr}

                logger.warning(f"GitHub command failed, retrying in {delay}s...")
                time.sleep(delay)
                delay *= self.retry_config["backoff_factor"]

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a GitHub issue."""
        args = ["issue", "create", "--title", title, "--body", body]

        if labels:
            args.extend(["--label", ",".join(labels)])
        if assignees:
            args.extend(["--assignee", ",".join(assignees)])

        result = self._execute_gh_command(args + ["--json", "number,url"])

        if result["success"] and result["data"]:
            logger.info(f"Created issue #{result['data']['number']}")

        return result

    def create_pr(
        self,
        title: str,
        body: str,
        base: str = "main",
        head: Optional[str] = None,
        draft: bool = False,
    ) -> Dict[str, Any]:
        """Create a pull request."""
        args = ["pr", "create", "--title", title, "--body", body, "--base", base]

        if head:
            args.extend(["--head", head])
        if draft:
            args.append("--draft")

        args.extend(["--json", "number,url"])

        result = self._execute_gh_command(args)

        if result["success"] and result["data"]:
            logger.info(f"Created PR #{result['data']['number']}")

        return result

    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """Get issue details."""
        args = [
            "issue",
            "view",
            str(issue_number),
            "--json",
            "number,title,body,state,labels,assignees,createdAt,updatedAt",
        ]
        return self._execute_gh_command(args)

    def get_pr(self, pr_number: int) -> Dict[str, Any]:
        """Get pull request details."""
        args = [
            "pr",
            "view",
            str(pr_number),
            "--json",
            "number,title,body,state,reviews,checks,baseRef,headRef",
        ]
        return self._execute_gh_command(args)

    def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an issue."""
        args = ["issue", "edit", str(issue_number)]

        if title:
            args.extend(["--title", title])
        if body:
            args.extend(["--body", body])
        if state:
            args.extend(["--state", state])

        return self._execute_gh_command(args)

    def add_comment(self, issue_number: int, body: str) -> Dict[str, Any]:
        """Add comment to issue or PR."""
        args = ["issue", "comment", str(issue_number), "--body", body]
        return self._execute_gh_command(args)

    def list_issues(
        self, state: str = "open", labels: Optional[List[str]] = None, limit: int = 30
    ) -> Dict[str, Any]:
        """List issues with filters."""
        args = ["issue", "list", "--state", state, "--limit", str(limit)]

        if labels:
            args.extend(["--label", ",".join(labels)])

        args.extend(["--json", "number,title,state,labels,updatedAt"])
        return self._execute_gh_command(args)

    def list_prs(
        self, state: str = "open", base: Optional[str] = None, limit: int = 30
    ) -> Dict[str, Any]:
        """List pull requests with filters."""
        args = ["pr", "list", "--state", state, "--limit", str(limit)]

        if base:
            args.extend(["--base", base])

        args.extend(["--json", "number,title,state,baseRef,headRef,updatedAt"])
        return self._execute_gh_command(args)

    def create_branch(self, branch_name: str, base: str = "main") -> bool:
        """Create a new branch."""
        # First, fetch latest
        subprocess.run(["git", "fetch", "origin", base], check=True)

        # Create and checkout new branch
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name, f"origin/{base}"], check=True
            )
            logger.info(f"Created branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch: {e}")
            return False

    def push_branch(
        self, branch_name: Optional[str] = None, force: bool = False
    ) -> bool:
        """Push branch to remote."""
        args = ["git", "push", "origin"]

        if branch_name:
            args.append(branch_name)
        else:
            args.append("HEAD")

        if force:
            args.append("--force")

        args.append("--set-upstream")

        try:
            subprocess.run(args, check=True)
            logger.info(f"Pushed branch: {branch_name or 'current'}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push branch: {e}")
            return False

    def merge_pr(self, pr_number: int, merge_method: str = "squash") -> Dict[str, Any]:
        """Merge a pull request."""
        args = ["pr", "merge", str(pr_number), f"--{merge_method}", "--json", "merged"]
        return self._execute_gh_command(args)

    def close_issue(
        self, issue_number: int, reason: str = "completed"
    ) -> Dict[str, Any]:
        """Close an issue."""
        args = ["issue", "close", str(issue_number)]

        if reason:
            args.extend(["--reason", reason])

        return self._execute_gh_command(args)

    def get_workflow_runs(
        self, workflow: Optional[str] = None, limit: int = 10
    ) -> Dict[str, Any]:
        """Get workflow run information."""
        args = ["run", "list", "--limit", str(limit)]

        if workflow:
            args.extend(["--workflow", workflow])

        args.extend(["--json", "status,conclusion,databaseId,workflowName,createdAt"])
        return self._execute_gh_command(args)

    def watch_workflow_run(self, run_id: str) -> Dict[str, Any]:
        """Watch a workflow run until completion."""
        args = ["run", "watch", run_id]
        return self._execute_gh_command(args)

    def get_rate_limit(self) -> Dict[str, Any]:
        """Get API rate limit information."""
        args = ["api", "rate_limit"]
        return self._execute_gh_command(args)

    def label_issue(self, issue_number: int, labels: List[str]) -> Dict[str, Any]:
        """Add labels to an issue."""
        args = ["issue", "edit", str(issue_number), "--add-label", ",".join(labels)]
        return self._execute_gh_command(args)

    def remove_label(self, issue_number: int, labels: List[str]) -> Dict[str, Any]:
        """Remove labels from an issue."""
        args = ["issue", "edit", str(issue_number), "--remove-label", ",".join(labels)]
        return self._execute_gh_command(args)
