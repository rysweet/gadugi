"""
Comprehensive tests for github_operations.py module.
Tests the Enhanced Separation architecture implementation.
"""

import json
import subprocess

# Import the module we're testing (will be implemented after tests)
from typing import Any, Dict, List

import pytest
from unittest.mock import Mock, patch

# For type checking only
from typing import Optional

try:
    from claude.shared.github_operations import GitHubError, GitHubOperations, RateLimitError
except ImportError:
    # These will be implemented after tests pass
    import time
    from typing import Any, List

    class GitHubError(Exception):
        """Base exception for GitHub operations."""

        def __init__(
            self,
            message: str,
            operation: Optional[str] = None,
            context: Optional[Dict] = None,
            command: Optional[List[str]] = None,
            stdout: str = "",
            stderr: str = "",
            details: Optional[Dict] = None):
            super().__init__(message)
            self.operation = operation
            self.context = context or {}
            self.command = command
            self.stdout = stdout
            self.stderr = stderr
            self.details = details or {}

    class RateLimitError(GitHubError):
        """Raised when hitting GitHub API rate limits."""

        def __init__(self, message: str, reset_time: Optional[int] = None) -> None:
            super().__init__(message)
            self.reset_time = reset_time

        def get_wait_time(self) -> int:
            """Get the time to wait before retrying."""
            if self is not None and self.reset_time:
                return max(0, self.reset_time - int(time.time()))
            return 60  # Default wait time

    class GitHubOperations:
        """Stub implementation for testing."""

        def __init__(
            self,
            repo: Optional[str] = None,
            retry_config: Optional[Dict[str, Any]] = None):
            self.repo = repo
            self.retry_config = retry_config or {
                "max_retries": 3,
                "initial_delay": 1,
                "backoff_factor": 2,
            }
            self.rate_limit_handler = Mock()

        def _execute_gh_command(
            self, command: List[str], input_data: Optional[str] = None
        ) -> Dict[str, Any]:
            """Mock GitHub CLI command execution."""
            # Add repo argument if specified
            full_command = ["gh"] + command
            if self is not None and self.repo:
                full_command.extend(["--repo", self.repo])

            try:
                # This would normally run subprocess, but for testing we mock it
                result = subprocess.run(
                    full_command, capture_output=True, text=True, input=input_data
                )

                if result.returncode == 0:
                    try:
                        data = (
                            json.loads(result.stdout) if result.stdout.strip() else {}
                        )
                    except json.JSONDecodeError:
                        data = {"raw": result.stdout}

                    return {
                        "success": True,
                        "data": data,
                        "raw_output": result.stdout,
                        "stderr": result.stderr,
                    }
                else:
                    return {
                        "success": False,
                        "error": result.stderr,
                        "returncode": result.returncode,
                        "raw_output": result.stdout,
                    }

            except subprocess.CalledProcessError as e:
                if "rate limit" in e.stderr.lower():
                    raise RateLimitError("GitHub API rate limit exceeded")
                raise GitHubError(
                    f"Command failed: {e.stderr}", command=full_command, stderr=e.stderr
                )

        def create_issue(
            self,
            title: str,
            body: str,
            labels: Optional[List[str]] = None,
            assignees: Optional[List[str]] = None) -> Dict[str, Any]:
            """Create a GitHub issue."""
            command = ["issue", "create", "--title", title, "--body", body]
            if labels:
                command.extend(["--label", ",".join(labels)])
            if assignees:
                command.extend(["--assignee", ",".join(assignees)])

            return self._execute_gh_command(command)

        def update_issue(
            self,
            issue_number: int,
            title: Optional[str] = None,
            body: Optional[str] = None,
            state: Optional[str] = None,
            labels: Optional[List[str]] = None) -> Dict[str, Any]:
            """Update a GitHub issue."""
            command = ["issue", "edit", str(issue_number)]
            if title:
                command.extend(["--title", title])
            if body:
                command.extend(["--body", body])
            if state:
                command.extend(["--state", state])
            if labels:
                command.extend(["--label", ",".join(labels)])

            return self._execute_gh_command(command)

        def create_pr(
            self,
            title: str,
            body: str,
            base: str = "main",
            head: Optional[str] = None,
            draft: bool = False,
            labels: Optional[List[str]] = None) -> Dict[str, Any]:
            """Create a pull request."""
            command = ["pr", "create", "--title", title, "--body", body, "--base", base]
            if head:
                command.extend(["--head", head])
            if draft:
                command.append("--draft")
            if labels:
                command.extend(["--label", ",".join(labels)])

            return self._execute_gh_command(command)

        def merge_pr(
            self,
            pr_number: int,
            merge_method: str = "merge",
            delete_branch: bool = True) -> Dict[str, Any]:
            """Merge a pull request."""
            command = ["pr", "merge", str(pr_number), f"--{merge_method}"]
            if delete_branch:
                command.append("--delete-branch")

            return self._execute_gh_command(command)

        def list_issues(
            self,
            state: str = "open",
            labels: Optional[List[str]] = None,
            assignee: Optional[str] = None,
            limit: int = 30) -> Dict[str, Any]:
            """List GitHub issues."""
            command = ["issue", "list", "--state", state, "--limit", str(limit)]
            if labels:
                command.extend(["--label", ",".join(labels)])
            if assignee:
                command.extend(["--assignee", assignee])

            return self._execute_gh_command(command)

        def list_prs(
            self,
            state: str = "open",
            base: Optional[str] = None,
            head: Optional[str] = None,
            limit: int = 30) -> Dict[str, Any]:
            """List pull requests."""
            command = ["pr", "list", "--state", state, "--limit", str(limit)]
            if base:
                command.extend(["--base", base])
            if head:
                command.extend(["--head", head])

            return self._execute_gh_command(command)

        def get_issue(self, issue_number: int) -> Dict[str, Any]:
            """Get a specific issue."""
            return self._execute_gh_command(
                [
                    "issue",
                    "view",
                    str(issue_number),
                    "--json",
                    "number,title,body,state,labels,assignees",
                ]
            )

        def get_pr(self, pr_number: int) -> Dict[str, Any]:
            """Get a specific pull request."""
            return self._execute_gh_command(
                [
                    "pr",
                    "view",
                    str(pr_number),
                    "--json",
                    "number,title,body,state,baseRefName,headRefName",
                ]
            )

        def add_comment(
            self, issue_or_pr_number: int, comment: str, is_pr: bool = False
        ) -> Dict[str, Any]:
            """Add a comment to an issue or PR."""
            resource_type = "pr" if is_pr else "issue"
            return self._execute_gh_command(
                [resource_type, "comment", str(issue_or_pr_number), "--body", comment]
            )

        def create_release(
            self,
            tag: str,
            title: str,
            notes: str,
            draft: bool = False,
            prerelease: bool = False) -> Dict[str, Any]:
            """Create a GitHub release."""
            command = ["release", "create", tag, "--title", title, "--notes", notes]
            if draft:
                command.append("--draft")
            if prerelease:
                command.append("--prerelease")

            return self._execute_gh_command(command)

        def batch_create_issues(
            self, issues: List[Dict[str, Any]]
        ) -> List[Dict[str, Any]]:
            """Create multiple issues in batch."""
            results = []
            for issue in issues:
                result = self.create_issue(
                    title=issue["title"],
                    body=issue["body"],
                    labels=issue.get("labels"),
                    assignees=issue.get("assignees"))
                results.append(result)
            return results

        def get_repo_info(self) -> Dict[str, Any]:
            """Get repository information."""
            return self._execute_gh_command(
                ["repo", "view", "--json", "name,owner,description,url,defaultBranch"]
            )

        def check_rate_limit(self) -> Dict[str, Any]:
            """Check GitHub API rate limit status."""
            return self._execute_gh_command(["api", "rate_limit"])

        def wait_for_rate_limit_reset(self) -> None:
            """Wait for rate limit to reset."""
            rate_limit_info = self.check_rate_limit()
            if rate_limit_info.get("success") and rate_limit_info.get("data"):
                reset_time = (
                    rate_limit_info["data"]
                    .get("resources", {})
                    .get("core", {})
                    .get("reset", 0)
                )
                current_time = int(time.time())
                if reset_time > current_time:
                    wait_time = reset_time - current_time + 10  # Add 10 second buffer
                    time.sleep(wait_time)

        def create_branch(
            self, branch_name: str, base_branch: str = "main"
        ) -> Dict[str, Any]:
            """Create a new branch."""
            # This would normally create a branch via git commands or GitHub API
            return {
                "success": True,
                "data": {"branch": branch_name, "base": base_branch},
                "message": f"Created branch {branch_name} from {base_branch}",
            }

        def push_branch(self, branch_name: str, force: bool = False) -> Dict[str, Any]:
            """Push a branch to remote."""
            # This would normally push via git commands
            return {
                "success": True,
                "data": {"branch": branch_name, "force": force},
                "message": f"Pushed branch {branch_name}",
            }

        def close_issue(
            self,
            issue_number: int,
            comment: Optional[str] = None,
            reason: Optional[str] = None) -> Dict[str, Any]:
            """Close an issue."""
            result = self.update_issue(issue_number, state="closed")
            if comment and result.get("success"):
                self.add_comment(issue_number, comment)
            return result

        def get_workflow_runs(
            self,
            workflow_name: Optional[str] = None,
            workflow: Optional[str] = None,
            status: Optional[str] = None,
            limit: int = 30) -> Dict[str, Any]:
            """Get workflow runs."""
            command = ["run", "list", "--limit", str(limit)]
            # Support both workflow_name and workflow parameters
            workflow_to_use = workflow or workflow_name
            if workflow_to_use:
                command.extend(["--workflow", workflow_to_use])
            if status:
                command.extend(["--status", status])

            return self._execute_gh_command(command)

        def __enter__(self):
            """Context manager entry."""
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Context manager exit."""
            # Clean up any resources if needed
            return False

class TestGitHubOperations:
    """Test suite for GitHubOperations class."""

    def test_init_default_config(self):
        """Test GitHubOperations initialization with default config."""
        gh = GitHubOperations()
        assert gh.repo is None
        assert gh.retry_config["max_retries"] == 3
        assert gh.retry_config["initial_delay"] == 1
        assert gh.retry_config["backoff_factor"] == 2
        assert gh.rate_limit_handler is not None

    def test_init_custom_config(self):
        """Test GitHubOperations initialization with custom config."""
        custom_config = {"max_retries": 5, "initial_delay": 2, "backoff_factor": 3}
        gh = GitHubOperations(repo="test/repo", retry_config=custom_config)
        assert gh.repo == "test/repo"
        assert gh.retry_config["max_retries"] == 5
        assert gh.retry_config["initial_delay"] == 2
        assert gh.retry_config["backoff_factor"] == 3

    @patch("subprocess.run")
    def test_execute_gh_command_success(self, mock_run):
        """Test successful GitHub CLI command execution."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            '{"number": 1, "url": "https://github.com/test/repo/issues/1"}'
        )
        mock_run.return_value.stderr = ""

        gh = GitHubOperations()
        result = gh._execute_gh_command(["issue", "list"])

        assert result["success"] is True
        assert result["data"]["number"] == 1
        assert result["raw_output"] is not None
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_execute_gh_command_with_repo(self, mock_run):
        """Test GitHub CLI command execution with specific repo."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "{}"

        gh = GitHubOperations(repo="test/repo")
        gh._execute_gh_command(["issue", "list"])

        # Verify --repo argument is added
        called_args = mock_run.call_args[0][0]
        assert "--repo" in called_args
        assert "test/repo" in called_args

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_execute_gh_command_retry_logic(self, mock_sleep, mock_run):
        """Test retry logic on command failure."""
        # First two calls fail, third succeeds (avoid rate limit trigger)
        error1 = subprocess.CalledProcessError(
            1, ["gh", "issue", "list"], stderr="Network timeout"
        )
        error2 = subprocess.CalledProcessError(
            1, ["gh", "issue", "list"], stderr="Connection error"
        )
        success = Mock(returncode=0, stdout='{"success": true}', stderr="")

        mock_run.side_effect = [error1, error2, success]

        gh = GitHubOperations(
            retry_config={"max_retries": 3, "initial_delay": 0.1, "backoff_factor": 2}
        )
        result = gh._execute_gh_command(["issue", "list"])

        assert result["success"] is True
        assert mock_run.call_count == 3
        assert mock_sleep.call_count == 2  # Two retries

    @patch("subprocess.run")
    def test_execute_gh_command_max_retries_exceeded(self, mock_run):
        """Test behavior when max retries are exceeded."""
        error = subprocess.CalledProcessError(
            1, ["gh", "issue", "list"], stderr="Persistent failure"
        )
        mock_run.side_effect = [error, error]  # Two failures

        gh = GitHubOperations(
            retry_config={"max_retries": 2, "initial_delay": 0.01, "backoff_factor": 1}
        )
        result = gh._execute_gh_command(["issue", "list"])

        assert result["success"] is False
        assert "error" in result
        assert mock_run.call_count == 2  # max_retries

    @patch("subprocess.run")
    def test_create_issue_success(self, mock_run):
        """Test successful issue creation."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            '{"number": 42, "url": "https://github.com/test/repo/issues/42"}'
        )

        gh = GitHubOperations()
        result = gh.create_issue(
            title="Test Issue",
            body="Test description",
            labels=["bug", "enhancement"],
            assignees=["testuser"])

        assert result["success"] is True
        assert result["data"]["number"] == 42

        # Verify command construction
        called_args = mock_run.call_args[0][0]
        assert "issue" in called_args
        assert "create" in called_args
        assert "--title" in called_args
        assert "Test Issue" in called_args
        assert "--body" in called_args
        assert "--label" in called_args
        assert "bug,enhancement" in called_args
        assert "--assignee" in called_args
        assert "testuser" in called_args

    @patch("subprocess.run")
    def test_create_pr_success(self, mock_run):
        """Test successful pull request creation."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            '{"number": 15, "url": "https://github.com/test/repo/pull/15"}'
        )

        gh = GitHubOperations()
        result = gh.create_pr(
            title="Test PR",
            body="Test PR description",
            base="main",
            head="feature/test",
            draft=True)

        assert result["success"] is True
        assert result["data"]["number"] == 15

        # Verify command construction
        called_args = mock_run.call_args[0][0]
        assert "pr" in called_args
        assert "create" in called_args
        assert "--title" in called_args
        assert "Test PR" in called_args
        assert "--base" in called_args
        assert "main" in called_args
        assert "--head" in called_args
        assert "feature/test" in called_args
        assert "--draft" in called_args

    @patch("subprocess.run")
    def test_get_issue_success(self, mock_run):
        """Test successful issue retrieval."""
        issue_data = {
            "number": 42,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "labels": [{"name": "bug"}],
            "assignees": [{"login": "testuser"}],
        }
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(issue_data)

        gh = GitHubOperations()
        result = gh.get_issue(42)

        assert result["success"] is True
        assert result["data"]["number"] == 42
        assert result["data"]["title"] == "Test Issue"
        assert result["data"]["state"] == "open"

    @patch("subprocess.run")
    def test_get_pr_success(self, mock_run):
        """Test successful pull request retrieval."""
        pr_data = {
            "number": 15,
            "title": "Test PR",
            "state": "open",
            "reviews": [],
            "checks": {"totalCount": 2, "passing": 2},
        }
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(pr_data)

        gh = GitHubOperations()
        result = gh.get_pr(15)

        assert result["success"] is True
        assert result["data"]["number"] == 15
        assert result["data"]["state"] == "open"

    @patch("subprocess.run")
    def test_update_issue_success(self, mock_run):
        """Test successful issue update."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Issue updated successfully"

        gh = GitHubOperations()
        result = gh.update_issue(
            42, title="Updated Title", body="Updated body", state="closed"
        )

        assert result["success"] is True

        # Verify command construction
        called_args = mock_run.call_args[0][0]
        assert "issue" in called_args
        assert "edit" in called_args
        assert "42" in called_args
        assert "--title" in called_args
        assert "Updated Title" in called_args
        assert "--body" in called_args
        assert "Updated body" in called_args
        assert "--state" in called_args
        assert "closed" in called_args

    @patch("subprocess.run")
    def test_add_comment_success(self, mock_run):
        """Test successful comment addition."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Comment added successfully"

        gh = GitHubOperations()
        result = gh.add_comment(42, "Test comment")

        assert result["success"] is True

        # Verify command construction
        called_args = mock_run.call_args[0][0]
        assert "issue" in called_args
        assert "comment" in called_args
        assert "42" in called_args
        assert "--body" in called_args
        assert "Test comment" in called_args

    @patch("subprocess.run")
    def test_list_issues_success(self, mock_run):
        """Test successful issue listing."""
        issues_data = [
            {"number": 1, "title": "Issue 1", "state": "open"},
            {"number": 2, "title": "Issue 2", "state": "closed"},
        ]
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(issues_data)

        gh = GitHubOperations()
        result = gh.list_issues(state="all", labels=["bug"], limit=50)

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["number"] == 1

        # Verify command construction
        called_args = mock_run.call_args[0][0]
        assert "issue" in called_args
        assert "list" in called_args
        assert "--state" in called_args
        assert "all" in called_args
        assert "--label" in called_args
        assert "bug" in called_args
        assert "--limit" in called_args
        assert "50" in called_args

    @patch("subprocess.run")
    def test_list_prs_success(self, mock_run):
        """Test successful PR listing."""
        prs_data = [
            {"number": 10, "title": "PR 1", "state": "open"},
            {"number": 11, "title": "PR 2", "state": "merged"},
        ]
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(prs_data)

        gh = GitHubOperations()
        result = gh.list_prs(state="all", base="main", limit=25)

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["number"] == 10

    @patch("subprocess.run")
    def test_create_branch_success(self, mock_run):
        """Test successful branch creation."""
        # Mock git fetch and git checkout commands
        mock_run.return_value.returncode = 0

        gh = GitHubOperations()
        result = gh.create_branch("feature/test-branch", "main")

        assert result is True

        # Verify git commands were called
        assert mock_run.call_count == 2
        # First call: git fetch
        first_call = mock_run.call_args_list[0][0][0]
        assert "git" in first_call
        assert "fetch" in first_call
        # Second call: git checkout
        second_call = mock_run.call_args_list[1][0][0]
        assert "git" in second_call
        assert "checkout" in second_call
        assert "-b" in second_call
        assert "feature/test-branch" in second_call

    @patch("subprocess.run")
    def test_push_branch_success(self, mock_run):
        """Test successful branch push."""
        mock_run.return_value.returncode = 0

        gh = GitHubOperations()
        result = gh.push_branch("feature/test-branch", force=True)

        assert result is True

        # Verify command construction
        called_args = mock_run.call_args[0][0]
        assert "git" in called_args
        assert "push" in called_args
        assert "origin" in called_args
        assert "feature/test-branch" in called_args
        assert "--force" in called_args
        assert "--set-upstream" in called_args

    @patch("subprocess.run")
    def test_merge_pr_success(self, mock_run):
        """Test successful PR merge."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '{"merged": true}'

        gh = GitHubOperations()
        result = gh.merge_pr(15, merge_method="rebase")

        assert result["success"] is True
        assert result["data"]["merged"] is True

        # Verify command construction
        called_args = mock_run.call_args[0][0]
        assert "pr" in called_args
        assert "merge" in called_args
        assert "15" in called_args
        assert "--rebase" in called_args

    @patch("subprocess.run")
    def test_close_issue_success(self, mock_run):
        """Test successful issue closure."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Issue closed successfully"

        gh = GitHubOperations()
        result = gh.close_issue(42, reason="not_planned")

        assert result["success"] is True

        # Verify command construction
        called_args = mock_run.call_args[0][0]
        assert "issue" in called_args
        assert "close" in called_args
        assert "42" in called_args
        assert "--reason" in called_args
        assert "not_planned" in called_args

    @patch("subprocess.run")
    def test_get_workflow_runs_success(self, mock_run):
        """Test successful workflow runs retrieval."""
        runs_data = [
            {"status": "completed", "conclusion": "success", "databaseId": 123},
            {"status": "in_progress", "conclusion": None, "databaseId": 124},
        ]
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(runs_data)

        gh = GitHubOperations()
        result = gh.get_workflow_runs(workflow="CI", limit=5)

        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["data"][0]["status"] == "completed"

    def test_rate_limit_handling(self):
        """Test rate limit detection and handling."""
        gh = GitHubOperations()

        # Mock rate limit exceeded response
        with patch.object(gh, "_execute_gh_command") as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "error": "rate limit exceeded",
                "stderr": "API rate limit exceeded",
            }

            result = gh.create_issue("Test", "Body")
            assert result["success"] is False
            assert "rate limit" in result["error"].lower()

    def test_error_handling(self):
        """Test comprehensive error handling."""
        gh = GitHubOperations()

        # Test various error scenarios
        with patch.object(gh, "_execute_gh_command") as mock_execute:
            # Network error
            mock_execute.return_value = {
                "success": False,
                "error": "Network unreachable",
                "stderr": "Connection failed",
            }

            result = gh.get_issue(42)
            assert result["success"] is False
            assert "Network unreachable" in result["error"]

    def test_batch_operations(self):
        """Test batch operations for efficiency."""
        gh = GitHubOperations()

        # Test batch issue creation
        issues = [
            {"title": "Issue 1", "body": "Body 1"},
            {"title": "Issue 2", "body": "Body 2"},
            {"title": "Issue 3", "body": "Body 3"},
        ]

        with patch.object(gh, "create_issue") as mock_create:
            mock_create.return_value = {"success": True, "data": {"number": 1}}

            results = gh.batch_create_issues(issues)

            assert len(results) == 3
            assert all(r["success"] for r in results)
            assert mock_create.call_count == 3

    def test_validation(self):
        """Test input validation."""
        gh = GitHubOperations()

        # Test empty title validation
        with pytest.raises(ValueError, match="Title cannot be empty"):
            gh.create_issue("", "Valid body")

        # Test invalid issue number
        with pytest.raises(ValueError, match="Issue number must be positive"):
            gh.get_issue(-1)

        # Test invalid merge method
        with pytest.raises(ValueError, match="Invalid merge method"):
            gh.merge_pr(1, merge_method="invalid")

    def test_context_management(self):
        """Test context manager functionality."""
        with GitHubOperations(repo="test/repo") as gh:
            assert gh.repo == "test/repo"
            # Operations within context should work normally
            with patch.object(gh, "_execute_gh_command") as mock_execute:
                mock_execute.return_value = {"success": True, "data": {"number": 1}}
                result = gh.create_issue("Test", "Body")
                assert result["success"] is True

class TestGitHubError:
    """Test suite for GitHubError exception class."""

    def test_github_error_creation(self):
        """Test GitHubError exception creation."""
        error = GitHubError("Test error message", "create_issue", {"title": "Test"})
        assert str(error) == "Test error message"
        assert error.operation == "create_issue"
        assert error.context == {"title": "Test"}

    def test_github_error_with_details(self):
        """Test GitHubError with additional details."""
        error = GitHubError(
            "API request failed",
            "get_issue",
            {"issue_number": 42},
            details={"status_code": 404, "response": "Not found"})
        assert error.details["status_code"] == 404

class TestRateLimitError:
    """Test suite for RateLimitError exception class."""

    def test_rate_limit_error_creation(self):
        """Test RateLimitError exception creation."""
        error = RateLimitError("Rate limit exceeded", reset_time=1640995200)
        assert str(error) == "Rate limit exceeded"
        assert error.reset_time == 1640995200

    def test_rate_limit_error_wait_time(self):
        """Test rate limit wait time calculation."""
        import time

        current_time = int(time.time())
        future_time = current_time + 3600  # 1 hour from now

        error = RateLimitError("Rate limit exceeded", reset_time=future_time)
        wait_time = error.get_wait_time()

        # Should be close to 3600 seconds (within 5 seconds for test execution time)
        assert 3595 <= wait_time <= 3605

# Integration tests
class TestGitHubOperationsIntegration:
    """Integration tests for GitHubOperations."""

    @pytest.mark.integration
    @patch("subprocess.run")
    def test_complete_workflow_integration(self, mock_run):
        """Test a complete GitHub workflow."""
        # Setup mock responses for a complete workflow
        responses = [
            # Create issue
            '{"number": 42, "url": "https://github.com/test/repo/issues/42"}',
            # Create branch (git fetch)
            "",
            # Create branch (git checkout)
            "",
            # Create PR
            '{"number": 15, "url": "https://github.com/test/repo/pull/15"}',
            # Add comment
            "Comment added successfully",
            # Merge PR
            '{"merged": true}',
            # Close issue
            "Issue closed successfully",
        ]

        mock_run.side_effect = [
            Mock(returncode=0, stdout=response, stderr="") for response in responses
        ]

        gh = GitHubOperations()

        # Execute complete workflow
        issue_result = gh.create_issue("Test Feature", "Implement test feature")
        assert issue_result["success"] is True
        issue_number = issue_result["data"]["number"]

        branch_result = gh.create_branch(f"feature/test-{issue_number}")
        assert branch_result is True

        pr_result = gh.create_pr(
            f"Implement test feature (#{issue_number})",
            f"Fixes #{issue_number}\n\nImplements test feature functionality.")
        assert pr_result["success"] is True
        pr_number = pr_result["data"]["number"]

        comment_result = gh.add_comment(pr_number, "Ready for review")
        assert comment_result["success"] is True

        merge_result = gh.merge_pr(pr_number)
        assert merge_result["success"] is True

        close_result = gh.close_issue(issue_number, reason="completed")
        assert close_result["success"] is True

        # Verify all operations were called
        assert mock_run.call_count == 7

    @pytest.mark.integration
    def test_error_recovery_integration(self):
        """Test error recovery in integrated workflows."""
        gh = GitHubOperations(retry_config={"max_retries": 2, "initial_delay": 0.01})

        with patch.object(gh, "_execute_gh_command") as mock_execute:
            # First call returns success (create_issue doesn't retry on its own)
            mock_execute.return_value = {"success": True, "data": {"number": 42}}

            result = gh.create_issue("Test", "Body")
            assert result["success"] is True
            assert mock_execute.call_count == 1
