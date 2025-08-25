"""
GitHub operations module for Enhanced Separation architecture.
Provides unified GitHub CLI operations for OrchestratorAgent and WorkflowManager.
"""

import subprocess
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


# Custom exceptions
class GitHubError(Exception):
    """Base exception for GitHub operations."""

    def __init__(self, message) -> None: str, operation) -> None: str, context) -> None: Dict[str, Any], details) -> None: Optional[Dict[str, Any]] = None)) -> None:
        super().__init__(message)
        self.operation = operation
        self.context = context
        self.details = details or {}


class RateLimitError(GitHubError):
    """Exception for rate limit exceeded errors."""

    def __init__(self, message) -> None: str, reset_time) -> None: Optional[int] = None)) -> None:
        super().__init__(message, 'rate_limit', {})
        self.reset_time = reset_time

    def get_wait_time(self) -> int:
        """Calculate seconds to wait until rate limit resets."""
        if self.reset_time is None:
            return 60  # Default 1 minute

        current_time = int(time.time())
        return max(0, self.reset_time - current_time)


logger = logging.getLogger(__name__)


class GitHubOperations:
    """
    Unified GitHub operations for the Enhanced Separation architecture.
    Reduces 29% code duplication between OrchestratorAgent and WorkflowManager.
    """

    def __init__(self, repo) -> None: Optional[str] = None, retry_config) -> None: Optional[Dict[str, Any]] = None,
                 config: Optional[Dict[str, Any]] = None, task_id: Optional[str] = None):
        """
        Initialize GitHub operations.

        Args:
            repo: Optional repository in format 'owner/name'
            retry_config: Configuration for retry behavior
            config: General configuration dictionary
            task_id: Optional task ID for traceability (format: task-YYYYMMDD-HHMMSS-XXXX)
        """
        self.repo = repo
        self.config = config or {}
        self.task_id = task_id
        self.retry_config = retry_config or {
            'max_retries': 3,
            'initial_delay': 1,
            'backoff_factor': 2
        }
        self.rate_limit_handler = self._setup_rate_limit_handler()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _setup_rate_limit_handler(self) -> Dict[str, Any]:
        """Setup rate limit handling configuration."""
        return {
            'enabled': True,
            'max_wait_time': 3600,  # 1 hour max wait
            'backoff_multiplier': 1.5
        }

    def _format_task_id_metadata(self) -> str:
        """
        Format task ID metadata for inclusion in GitHub updates.

        Returns:
            Formatted task ID string to append to body text
        """
        if not self.task_id:
            return ""

        return f"\n\n---\n**Task ID**: `{self.task_id}`"

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

    def _execute_gh_command(self, args: List[str]) -> Dict[str, Any]:
        """
        Execute GitHub CLI command with comprehensive error handling and retry logic.

        Args:
            args: Command arguments for gh CLI

        Returns:
            Dictionary with success status, data, and error information
        """
        retries = 0
        delay = self.retry_config['initial_delay']

        while retries < self.retry_config['max_retries']:
            try:
                cmd = ['gh'] + args
                if self is not None and self.repo:
                    cmd.extend(['--repo', self.repo])

                self.logger.debug(f"Executing GitHub command: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=60  # 60 second timeout
                )

                # Try to parse JSON output
                parsed_data = None
                if result.stdout.strip():
                    try:
                        parsed_data = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        # Not JSON, that's okay for some commands
                        pass

                return {
                    'success': True,
                    'data': parsed_data,
                    'raw_output': result.stdout,
                    'stderr': result.stderr
                }

            except subprocess.CalledProcessError as e:
                retries += 1

                # Check for rate limit
                if hasattr(e, 'stderr') and e.stderr and 'rate limit' in e.stderr.lower():
                    raise RateLimitError(f"GitHub API rate limit exceeded: {e.stderr}")

                if retries >= self.retry_config['max_retries']:
                    self.logger.error(f"GitHub command failed after {retries} retries: {e}")
                    return {
                        'success': False,
                        'error': str(e),
                        'stderr': getattr(e, 'stderr', ''),
                        'returncode': getattr(e, 'returncode', -1)
                    }

                self.logger.warning(f"GitHub command failed, retrying in {delay}s... (attempt {retries}/{self.retry_config['max_retries']})")
                time.sleep(delay)
                delay *= self.retry_config['backoff_factor']

            except subprocess.TimeoutExpired as e:
                self.logger.error(f"GitHub command timed out: {e}")
                return {
                    'success': False,
                    'error': 'Command timed out',
                    'timeout': True
                }
            except Exception as e:
                self.logger.error(f"Unexpected error executing GitHub command: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'unexpected': True
                }

        return {
            'success': False,
            'error': 'Max retries exceeded',
            'retries_exhausted': True
        }

    def create_issue(self, title: str, body: str, labels: Optional[List[str]] = None,
                    assignees: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a GitHub issue.

        Args:
            title: Issue title
            body: Issue description
            labels: Optional list of labels
            assignees: Optional list of assignees

        Returns:
            Result dictionary with issue information

        Raises:
            ValueError: If title is empty
        """
        if not title.strip():
            raise ValueError("Title cannot be empty")

        # Append task ID metadata to body if available
        body_with_task_id = body + self._format_task_id_metadata()

        args = ['issue', 'create', '--title', title, '--body', body_with_task_id]

        if labels:
            args.extend(['--label', ','.join(labels)])
        if assignees:
            args.extend(['--assignee', ','.join(assignees)])

        args.extend(['--json', 'number,url,id'])

        result = self._execute_gh_command(args)

        if result['success'] and result['data']:
            self.logger.info(f"Created issue #{result['data']['number']}: {title}")
            if self is not None and self.task_id:
                self.logger.debug(f"Issue created with task ID: {self.task_id}")

        return result

    def create_pr(self, title: str, body: str, base: str = 'main',
                  head: Optional[str] = None, draft: bool = False) -> Dict[str, Any]:
        """
        Create a pull request.

        Args:
            title: PR title
            body: PR description
            base: Base branch (default: main)
            head: Head branch (optional)
            draft: Whether to create as draft

        Returns:
            Result dictionary with PR information
        """
        if not title.strip():
            raise ValueError("Title cannot be empty")

        # Append task ID metadata to body if available
        body_with_task_id = body + self._format_task_id_metadata()

        args = ['pr', 'create', '--title', title, '--body', body_with_task_id, '--base', base]

        if head:
            args.extend(['--head', head])
        if draft:
            args.append('--draft')

        args.extend(['--json', 'number,url,id'])

        result = self._execute_gh_command(args)

        if result['success'] and result['data']:
            self.logger.info(f"Created PR #{result['data']['number']}: {title}")
            if self is not None and self.task_id:
                self.logger.debug(f"PR created with task ID: {self.task_id}")

        return result

    def get_issue(self, issue_number: int) -> Dict[str, Any]:
        """
        Get issue details.

        Args:
            issue_number: Issue number

        Returns:
            Result dictionary with issue information

        Raises:
            ValueError: If issue number is not positive
        """
        if issue_number <= 0:
            raise ValueError("Issue number must be positive")

        args = ['issue', 'view', str(issue_number), '--json',
                'number,title,body,state,labels,assignees,createdAt,updatedAt']

        result = self._execute_gh_command(args)

        if result['success'] and result['data']:
            self.logger.debug(f"Retrieved issue #{issue_number}")

        return result

    def get_pr(self, pr_number: int) -> Dict[str, Any]:
        """
        Get pull request details.

        Args:
            pr_number: PR number

        Returns:
            Result dictionary with PR information
        """
        if pr_number <= 0:
            raise ValueError("PR number must be positive")

        args = ['pr', 'view', str(pr_number), '--json',
                'number,title,body,state,reviews,checks,baseRef,headRef,mergeable']

        result = self._execute_gh_command(args)

        if result['success'] and result['data']:
            self.logger.debug(f"Retrieved PR #{pr_number}")

        return result

    def update_issue(self, issue_number: int, title: Optional[str] = None,
                    body: Optional[str] = None, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an issue.

        Args:
            issue_number: Issue number
            title: New title (optional)
            body: New body (optional)
            state: New state (optional)

        Returns:
            Result dictionary
        """
        if issue_number <= 0:
            raise ValueError("Issue number must be positive")

        args = ['issue', 'edit', str(issue_number)]

        if title:
            args.extend(['--title', title])
        if body:
            args.extend(['--body', body])
        if state:
            if state not in ['open', 'closed']:
                raise ValueError("State must be 'open' or 'closed'")
            args.extend(['--state', state])

        result = self._execute_gh_command(args)

        if result['success']:
            self.logger.info(f"Updated issue #{issue_number}")

        return result

    def add_comment(self, issue_number: int, body: str) -> Dict[str, Any]:
        """
        Add comment to issue or PR.

        Args:
            issue_number: Issue/PR number
            body: Comment body

        Returns:
            Result dictionary
        """
        if issue_number <= 0:
            raise ValueError("Issue number must be positive")
        if not body.strip():
            raise ValueError("Comment body cannot be empty")

        # Append task ID metadata to body if available
        body_with_task_id = body + self._format_task_id_metadata()

        args = ['issue', 'comment', str(issue_number), '--body', body_with_task_id]

        result = self._execute_gh_command(args)

        if result['success']:
            self.logger.info(f"Added comment to issue #{issue_number}")
            if self is not None and self.task_id:
                self.logger.debug(f"Comment added with task ID: {self.task_id}")

        return result

    def list_issues(self, state: str = 'open', labels: Optional[List[str]] = None,
                   limit: int = 30) -> Dict[str, Any]:
        """
        List issues with filters.

        Args:
            state: Issue state filter
            labels: Label filters
            limit: Maximum number of issues

        Returns:
            Result dictionary with issues list
        """
        if state not in ['open', 'closed', 'all']:
            raise ValueError("State must be 'open', 'closed', or 'all'")

        args = ['issue', 'list', '--state', state, '--limit', str(limit)]

        if labels:
            args.extend(['--label', ','.join(labels)])

        args.extend(['--json', 'number,title,state,labels,updatedAt,assignees'])

        result = self._execute_gh_command(args)

        if result['success'] and result['data']:
            self.logger.debug(f"Listed {len(result['data'])} issues")

        return result

    def list_prs(self, state: str = 'open', base: Optional[str] = None,
                 limit: int = 30) -> Dict[str, Any]:
        """
        List pull requests with filters.

        Args:
            state: PR state filter
            base: Base branch filter
            limit: Maximum number of PRs

        Returns:
            Result dictionary with PRs list
        """
        if state not in ['open', 'closed', 'merged', 'all']:
            raise ValueError("State must be 'open', 'closed', 'merged', or 'all'")

        args = ['pr', 'list', '--state', state, '--limit', str(limit)]

        if base:
            args.extend(['--base', base])

        args.extend(['--json', 'number,title,state,baseRef,headRef,updatedAt'])

        result = self._execute_gh_command(args)

        if result['success'] and result['data']:
            self.logger.debug(f"Listed {len(result['data'])} PRs")

        return result

    def create_branch(self, branch_name: str, base: str = 'main') -> bool:
        """
        Create a new branch.

        Args:
            branch_name: Name of new branch
            base: Base branch name

        Returns:
            True if successful, False otherwise
        """
        if not branch_name.strip():
            raise ValueError("Branch name cannot be empty")

        try:
            # First, fetch latest from remote
            subprocess.run(['git', 'fetch', 'origin', base], check=True, timeout=30)

            # Create and checkout new branch
            subprocess.run(['git', 'checkout', '-b', branch_name, f'origin/{base}'],
                          check=True, timeout=30)

            self.logger.info(f"Created branch: {branch_name}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create branch {branch_name}: {e}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout creating branch {branch_name}")
            return False

    def push_branch(self, branch_name: Optional[str] = None, force: bool = False) -> bool:
        """
        Push branch to remote.

        Args:
            branch_name: Branch name (optional, uses current if None)
            force: Whether to force push

        Returns:
            True if successful, False otherwise
        """
        args = ['git', 'push', 'origin']

        if branch_name:
            args.append(branch_name)
        else:
            args.append('HEAD')

        if force:
            args.append('--force')

        args.append('--set-upstream')

        try:
            subprocess.run(args, check=True, timeout=60)
            self.logger.info(f"Pushed branch: {branch_name or 'current'}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to push branch: {e}")
            return False
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout pushing branch")
            return False

    def merge_pr(self, pr_number: int, merge_method: str = 'squash') -> Dict[str, Any]:
        """
        Merge a pull request.

        Args:
            pr_number: PR number
            merge_method: Merge method ('squash', 'merge', 'rebase')

        Returns:
            Result dictionary
        """
        if pr_number <= 0:
            raise ValueError("PR number must be positive")

        valid_methods = ['squash', 'merge', 'rebase']
        if merge_method not in valid_methods:
            raise ValueError(f"Invalid merge method. Must be one of: {valid_methods}")

        args = ['pr', 'merge', str(pr_number), f'--{merge_method}', '--json', 'merged']

        result = self._execute_gh_command(args)

        if result['success'] and result.get('data', {}).get('merged'):
            self.logger.info(f"Merged PR #{pr_number} using {merge_method}")

        return result

    def close_issue(self, issue_number: int, reason: str = 'completed') -> Dict[str, Any]:
        """
        Close an issue.

        Args:
            issue_number: Issue number
            reason: Reason for closure

        Returns:
            Result dictionary
        """
        if issue_number <= 0:
            raise ValueError("Issue number must be positive")

        valid_reasons = ['completed', 'not_planned']
        if reason not in valid_reasons:
            raise ValueError(f"Invalid reason. Must be one of: {valid_reasons}")

        args = ['issue', 'close', str(issue_number), '--reason', reason]

        result = self._execute_gh_command(args)

        if result['success']:
            self.logger.info(f"Closed issue #{issue_number} (reason: {reason})")

        return result

    def get_workflow_runs(self, workflow: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        Get workflow run information.

        Args:
            workflow: Workflow name (optional)
            limit: Maximum number of runs

        Returns:
            Result dictionary with workflow runs
        """
        args = ['run', 'list', '--limit', str(limit)]

        if workflow:
            args.extend(['--workflow', workflow])

        args.extend(['--json', 'status,conclusion,databaseId,workflowName,createdAt'])

        result = self._execute_gh_command(args)

        if result['success'] and result['data']:
            self.logger.debug(f"Retrieved {len(result['data'])} workflow runs")

        return result

    def watch_workflow_run(self, run_id: str) -> Dict[str, Any]:
        """
        Watch a workflow run until completion.

        Args:
            run_id: Workflow run ID

        Returns:
            Result dictionary
        """
        if not run_id.strip():
            raise ValueError("Run ID cannot be empty")

        args = ['run', 'watch', run_id]

        result = self._execute_gh_command(args)

        if result['success']:
            self.logger.info(f"Watched workflow run {run_id} to completion")

        return result

    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Get API rate limit information.

        Returns:
            Result dictionary with rate limit info
        """
        args = ['api', 'rate_limit']
        return self._execute_gh_command(args)

    def label_issue(self, issue_number: int, labels: List[str]) -> Dict[str, Any]:
        """
        Add labels to an issue.

        Args:
            issue_number: Issue number
            labels: List of labels to add

        Returns:
            Result dictionary
        """
        if issue_number <= 0:
            raise ValueError("Issue number must be positive")
        if not labels:
            raise ValueError("Labels list cannot be empty")

        args = ['issue', 'edit', str(issue_number), '--add-label', ','.join(labels)]

        result = self._execute_gh_command(args)

        if result['success']:
            self.logger.info(f"Added labels {labels} to issue #{issue_number}")

        return result

    def remove_label(self, issue_number: int, labels: List[str]) -> Dict[str, Any]:
        """
        Remove labels from an issue.

        Args:
            issue_number: Issue number
            labels: List of labels to remove

        Returns:
            Result dictionary
        """
        if issue_number <= 0:
            raise ValueError("Issue number must be positive")
        if not labels:
            raise ValueError("Labels list cannot be empty")

        args = ['issue', 'edit', str(issue_number), '--remove-label', ','.join(labels)]

        result = self._execute_gh_command(args)

        if result['success']:
            self.logger.info(f"Removed labels {labels} from issue #{issue_number}")

        return result

    def batch_create_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple issues in batch.

        Args:
            issues: List of issue dictionaries with 'title' and 'body'

        Returns:
            List of result dictionaries
        """
        if not issues:
            raise ValueError("Issues list cannot be empty")

        results = []
        for issue in issues:
            if 'title' not in issue or 'body' not in issue:
                raise ValueError("Each issue must have 'title' and 'body'")

            result = self.create_issue(
                title=issue['title'],
                body=issue['body'],
                labels=issue.get('labels'),
                assignees=issue.get('assignees')
            )
            results.append(result)

        self.logger.info(f"Batch created {len(issues)} issues")
        return results

    def get_issue_status(self, issue_number: int) -> str:
        """
        Get the current status of an issue.

        Args:
            issue_number: Issue number

        Returns:
            Issue status ('open', 'closed', or 'error')
        """
        result = self.get_issue(issue_number)
        if result['success'] and result['data']:
            return result['data']['state']
        return 'error'

    def get_pr_status(self, pr_number: int) -> str:
        """
        Get the current status of a pull request.

        Args:
            pr_number: PR number

        Returns:
            PR status ('open', 'closed', 'merged', or 'error')
        """
        result = self.get_pr(pr_number)
        if result['success'] and result['data']:
            return result['data']['state']
        return 'error'

    def is_pr_mergeable(self, pr_number: int) -> bool:
        """
        Check if a PR is mergeable.

        Args:
            pr_number: PR number

        Returns:
            True if mergeable, False otherwise
        """
        result = self.get_pr(pr_number)
        if result['success'] and result['data']:
            return result['data'].get('mergeable', False)
        return False

    def get_pr_checks_status(self, pr_number: int) -> Dict[str, Any]:
        """
        Get the checks status for a PR.

        Args:
            pr_number: PR number

        Returns:
            Dictionary with checks information
        """
        result = self.get_pr(pr_number)
        if result['success'] and result['data']:
            return result['data'].get('checks', {})
        return {'totalCount': 0, 'passing': 0, 'failing': 0}

    # Method aliases for backward compatibility with tests
    def create_pull_request(self, title: str, body: str, base: str = 'main',
                          head: Optional[str] = None, draft: bool = False) -> Dict[str, Any]:
        """Alias for create_pr method."""
        return self.create_pr(title, body, base, head, draft)

    def list_pull_requests(self, state: str = 'open', base: Optional[str] = None,
                          limit: int = 30) -> Dict[str, Any]:
        """Alias for list_prs method."""
        return self.list_prs(state, base, limit)

    def batch_merge_pull_requests(self, pr_numbers: List[int], merge_method: str = 'squash') -> List[Dict[str, Any]]:
        """
        Merge multiple pull requests in batch.

        Args:
            pr_numbers: List of PR numbers to merge
            merge_method: Merge method ('merge', 'squash', 'rebase')

        Returns:
            List of result dictionaries for each PR
        """
        results = []
        for pr_number in pr_numbers:
            try:
                result = self.merge_pr(pr_number, merge_method)
                results.append(result)
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'pr_number': pr_number
                })
        return results

    def verify_pull_request_exists(self, pr_number: int) -> Dict[str, Any]:
        """
        Verify that a pull request exists.

        Args:
            pr_number: PR number to verify

        Returns:
            Dictionary with verification result
        """
        result = self.get_pr(pr_number)
        return {
            'exists': result['success'] and result.get('data') is not None,
            'pr_number': pr_number,
            'data': result.get('data', {}) if result['success'] else None
        }
