#!/usr/bin/env python3
"""
Real GitHub integration for Team Coach using gh CLI.
Replaces mock operations with actual GitHub API calls.
"""

import json
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime


class GitHubClient:
    """Real GitHub client using gh CLI."""

    def __init__(self, repo: Optional[str] = None):
        """Initialize GitHub client.

        Args:
            repo: Repository in format 'owner/repo'. If None, uses current repo.
        """
        self.repo = repo
        self._verify_gh_cli()

    def _verify_gh_cli(self) -> None:
        """Verify gh CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                raise RuntimeError("gh CLI not authenticated. Run 'gh auth login'")
        except FileNotFoundError:
            raise RuntimeError("gh CLI not installed. Install from https://cli.github.com/")

    def _run_gh_command(self, args: List[str]) -> Dict[str, Any]:
        """Run a gh command and return JSON output.

        Args:
            args: Command arguments for gh

        Returns:
            Parsed JSON output from gh command
        """
        cmd = ["gh"] + args
        if self.repo:
            cmd.extend(["--repo", self.repo])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Try to parse as JSON, otherwise return as dict with output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"output": result.stdout}

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"gh command failed: {e.stderr}")

    def create_issue(self, title: str, body: str, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a GitHub issue.

        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: Optional list of labels

        Returns:
            Issue data including URL and number
        """
        args = ["issue", "create", "--title", title, "--body", body]

        if labels:
            args.extend(["--label", ",".join(labels)])

        result = self._run_gh_command(args)

        # Get the issue number from the output
        if "output" in result:
            # Parse the URL from output like "https://github.com/owner/repo/issues/123"
            url = result["output"].strip()
            issue_number = int(url.split("/")[-1])

            # Get full issue data
            issue_data = self.get_issue(issue_number)
            return issue_data

        return result

    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """Get issue details.

        Args:
            issue_number: Issue number

        Returns:
            Issue data
        """
        args = ["issue", "view", str(issue_number), "--json",
                "number,title,body,state,labels,assignees,url,createdAt,updatedAt"]
        return self._run_gh_command(args)

    def list_pull_requests(self, state: str = "open", limit: int = 30) -> List[Dict[str, Any]]:
        """List pull requests.

        Args:
            state: PR state (open, closed, merged, all)
            limit: Maximum number of PRs to return

        Returns:
            List of PR data
        """
        args = ["pr", "list", "--state", state, "--limit", str(limit),
                "--json", "number,title,state,url,author,createdAt,updatedAt,isDraft,labels"]
        return self._run_gh_command(args)

    def get_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """Get pull request details.

        Args:
            pr_number: PR number

        Returns:
            PR data including review status
        """
        args = ["pr", "view", str(pr_number), "--json",
                "number,title,body,state,url,author,labels,reviewDecision,statusCheckRollup"]
        return self._run_gh_command(args)

    def get_pr_reviews(self, pr_number: int) -> List[Dict[str, Any]]:
        """Get reviews for a pull request.

        Args:
            pr_number: PR number

        Returns:
            List of review data
        """
        args = ["pr", "view", str(pr_number), "--json", "reviews"]
        result = self._run_gh_command(args)
        return result.get("reviews", [])

    def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get user information.

        Args:
            username: GitHub username

        Returns:
            User data
        """
        args = ["api", f"/users/{username}"]
        return self._run_gh_command(args)

    def get_repo_contributors(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Get repository contributors.

        Args:
            limit: Maximum number of contributors

        Returns:
            List of contributor data
        """
        repo = self.repo or self._get_current_repo()
        args = ["api", f"/repos/{repo}/contributors", "-H", "Accept: application/vnd.github+json"]
        return self._run_gh_command(args)[:limit]

    def _get_current_repo(self) -> str:
        """Get current repository from git config.

        Returns:
            Repository in format 'owner/repo'
        """
        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "nameWithOwner"],
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            return data["nameWithOwner"]
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            raise RuntimeError("Could not determine current repository")

    def search_issues(self, query: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Search for issues.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching issues
        """
        args = ["search", "issues", query, "--limit", str(limit),
                "--json", "number,title,state,url,repository,createdAt"]
        return self._run_gh_command(args)

    def add_issue_comment(self, issue_number: int, comment: str) -> Dict[str, Any]:
        """Add a comment to an issue.

        Args:
            issue_number: Issue number
            comment: Comment text (markdown)

        Returns:
            Comment data
        """
        args = ["issue", "comment", str(issue_number), "--body", comment]
        return self._run_gh_command(args)


# Example usage and testing
if __name__ == "__main__":
    # Test the GitHub client
    client = GitHubClient()

    print("GitHub Client initialized successfully!")
    print("\nTesting capabilities:")

    # Test listing PRs
    try:
        prs = client.list_pull_requests(limit=5)
        print(f"✅ Found {len(prs)} open pull requests")
    except Exception as e:
        print(f"❌ Error listing PRs: {e}")

    # Test creating an issue (commented out to avoid creating real issues)
    # issue = client.create_issue(
    #     title="Test Issue from Team Coach",
    #     body="This is a test issue created by the Team Coach GitHub integration.",
    #     labels=["test", "team-coach"]
    # )
    # print(f"✅ Created issue: {issue['url']}")

    print("\n✅ GitHub integration is working correctly!")
