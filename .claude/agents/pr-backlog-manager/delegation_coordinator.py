"""
Delegation Coordinator for PR Backlog Manager.

Coordinates delegation of issue resolution tasks to appropriate agents
including WorkflowMaster for complex resolutions and code-reviewer for AI reviews.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DelegationType(Enum):
    """Types of delegation tasks."""

    MERGE_CONFLICT_RESOLUTION = "merge_conflict_resolution"
    CI_FAILURE_FIX = "ci_failure_fix"
    BRANCH_UPDATE = "branch_update"
    AI_CODE_REVIEW = "ai_code_review"
    METADATA_IMPROVEMENT = "metadata_improvement"


class DelegationPriority(Enum):
    """Priority levels for delegation tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DelegationStatus(Enum):
    """Status of delegation tasks."""

    PENDING = "pending"
    DELEGATED = "delegated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DelegationTask:
    """A task to be delegated to another agent."""

    task_id: str
    pr_number: int
    task_type: DelegationType
    priority: DelegationPriority
    agent_target: str
    prompt_template: str
    context: Dict[str, Any]
    created_at: datetime
    status: DelegationStatus
    retry_count: int = 0
    last_attempt: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    error_message: Optional[str] = None


class DelegationCoordinator:
    """
    Coordinates delegation of PR issue resolution tasks to appropriate agents.

    Manages the workflow of identifying issues, generating appropriate prompts,
    and delegating to specialized agents like WorkflowMaster and code-reviewer.
    """

    def __init__(self, auto_approve: bool) -> None:
        """Initialize delegation coordinator."""
        self.github_ops = github_ops
        self.auto_approve = auto_approve

        # Track active delegations
        self.active_delegations: Dict[Any, Any] = field(default_factory=dict)

        # Configuration
        self.config = {
            "max_retries": 3,
            "workflow_master_timeout": 300,  # 5 minutes
            "code_reviewer_timeout": 180,  # 3 minutes
            "enable_parallel_delegation": True,
            "auto_delegate_simple_tasks": True,
        }

        # Agent targets and their capabilities
        self.agent_capabilities = {
            "workflow-master": [
                DelegationType.MERGE_CONFLICT_RESOLUTION,
                DelegationType.CI_FAILURE_FIX,
                DelegationType.BRANCH_UPDATE,
                DelegationType.METADATA_IMPROVEMENT,
            ],
            "code-reviewer": [DelegationType.AI_CODE_REVIEW],
        }

    def delegate_issue_resolution(
        self, pr_number: int, blocking_issues: List[str], pr_context: Dict[str, Any]
    ) -> List[DelegationTask]:
        """
        Delegate resolution of blocking issues to appropriate agents.

        Args:
            pr_number: PR number requiring issue resolution
            blocking_issues: List of identified blocking issues
            pr_context: Additional context about the PR

        Returns:
            List of created delegation tasks
        """
        logger.info(
            f"Delegating issue resolution for PR #{pr_number} - {len(blocking_issues)} issues"
        )

        delegation_tasks = []

        for issue in blocking_issues:
            try:
                task = self._create_delegation_task(pr_number, issue, pr_context)
                if task:
                    delegation_tasks.append(task)
                    self.active_delegations[(task.task_id if task is not None else None)] = task

            except Exception as e:
                logger.error(
                    f"Failed to create delegation task for issue '{issue}': {e}"
                )

        # Execute delegations
        for task in delegation_tasks:
            try:
                self._execute_delegation(task)
            except Exception as e:
                logger.error(f"Failed to execute delegation {(task.task_id if task is not None else None)}: {e}")
                if task is not None:

                    task.status = DelegationStatus.FAILED
                task.error_message = str(e)

        return delegation_tasks

    def _create_delegation_task(
        self, pr_number: int, blocking_issue: str, pr_context: Dict[str, Any]
    ) -> Optional[DelegationTask]:
        """Create a delegation task for a specific blocking issue."""

        # Determine task type and priority
        task_type = self._classify_issue_type(blocking_issue)
        priority = self._assess_issue_priority(blocking_issue, pr_context)

        # Determine target agent
        agent_target = self._select_target_agent(task_type)
        if not agent_target:
            logger.warning(f"No suitable agent found for task type: {task_type}")
            return None

        # Generate prompt template
        prompt_template = self._generate_prompt_template(
            task_type, pr_number, blocking_issue, pr_context
        )

        # Create task
        task_id = f"delegation-{pr_number}-{task_type.value}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return DelegationTask(
            task_id=task_id,
            pr_number=pr_number,
            task_type=task_type,
            priority=priority,
            agent_target=agent_target,
            prompt_template=prompt_template,
            context=pr_context,
            created_at=datetime.now(),
            status=DelegationStatus.PENDING,
        )

    def _classify_issue_type(self, blocking_issue: str) -> DelegationType:
        """Classify the type of blocking issue."""
        issue_lower = blocking_issue.lower()

        if "merge conflict" in issue_lower:
            return DelegationType.MERGE_CONFLICT_RESOLUTION
        elif "ci" in issue_lower or "failing" in issue_lower:
            return DelegationType.CI_FAILURE_FIX
        elif "behind main" in issue_lower or "update" in issue_lower:
            return DelegationType.BRANCH_UPDATE
        elif "ai review" in issue_lower or "code review" in issue_lower:
            return DelegationType.AI_CODE_REVIEW
        elif (
            "metadata" in issue_lower
            or "title" in issue_lower
            or "description" in issue_lower
        ):
            return DelegationType.METADATA_IMPROVEMENT
        else:
            # Default to CI failure fix for unknown issues
            return DelegationType.CI_FAILURE_FIX

    def _assess_issue_priority(
        self, blocking_issue: str, pr_context: Dict[str, Any]
    ) -> DelegationPriority:
        """Assess priority level of the blocking issue."""
        issue_lower = blocking_issue.lower()

        # High priority issues
        if any(
            keyword in issue_lower for keyword in ["security", "critical", "urgent"]
        ):
            return DelegationPriority.CRITICAL

        # Check PR context for priority indicators
        pr_labels = pr_context.get("labels", [])
        if "priority-high" in pr_labels:
            return DelegationPriority.HIGH
        elif "priority-medium" in pr_labels:
            return DelegationPriority.MEDIUM

        # Default priority based on issue type
        if "merge conflict" in issue_lower:
            return DelegationPriority.HIGH
        elif "ci" in issue_lower:
            return DelegationPriority.MEDIUM
        else:
            return DelegationPriority.LOW

    def _select_target_agent(self, task_type: DelegationType) -> Optional[str]:
        """Select appropriate target agent for task type."""
        for agent, capabilities in self.agent_capabilities.items():
            if task_type in capabilities:
                return agent
        return None

    def _generate_prompt_template(
        self,
        task_type: DelegationType,
        pr_number: int,
        blocking_issue: str,
        pr_context: Dict[str, Any],
    ) -> str:
        """Generate appropriate prompt template for delegation."""

        base_context = f"""
# Issue Resolution for PR #{pr_number}

## Context
- Repository: {pr_context.get("repository", "Unknown")}
- PR Title: {pr_context.get("title", "N/A")}
- PR Author: {pr_context.get("author", "N/A")}
- Blocking Issue: {blocking_issue}

## Auto-Approve Context
- Auto-approve enabled: {self.auto_approve}
- GitHub Actions environment: {pr_context.get("github_actions", False)}
- Delegation timestamp: {datetime.now().isoformat()}
"""

        if task_type == DelegationType.MERGE_CONFLICT_RESOLUTION:
            return f"""{base_context}

## Objective
Resolve merge conflicts in PR #{pr_number} to enable clean merge with main branch.

## Approach
1. Checkout the PR branch locally
2. Rebase against latest main branch
3. Resolve conflicts using automated strategies where possible
4. Ensure all tests pass after resolution
5. Push resolved changes to PR branch
6. Verify mergeable status

## Success Criteria
- No merge conflicts remain
- All automated tests pass
- Code review approval maintained
- Clean git history preserved
- PR shows as mergeable in GitHub

## Safety Constraints
- Only use safe automatic conflict resolution
- Preserve all functional changes
- Do not modify core logic without explicit approval
"""

        elif task_type == DelegationType.CI_FAILURE_FIX:
            return f"""{base_context}

## Objective
Fix CI/CD failures in PR #{pr_number} to restore passing status.

## Approach
1. Analyze failing CI checks and error logs
2. Identify root causes of failures
3. Apply appropriate fixes:
   - Lint/style issues: Auto-format and fix
   - Test failures: Analyze and fix broken tests
   - Build failures: Fix compilation/dependency issues
4. Verify fixes resolve all failures
5. Ensure no new failures introduced

## Success Criteria
- All required CI checks pass
- No regression in existing functionality
- Build and test suite complete successfully
- Code quality standards maintained

## Safety Constraints
- Only make minimal necessary changes
- Preserve existing test coverage
- Do not modify test expectations without justification
"""

        elif task_type == DelegationType.BRANCH_UPDATE:
            return f"""{base_context}

## Objective
Update PR #{pr_number} branch to be current with main branch.

## Approach
1. Fetch latest changes from main branch
2. Determine update strategy (merge vs rebase)
3. Apply updates while preserving PR changes
4. Resolve any conflicts that arise
5. Verify all tests pass after update
6. Push updated branch

## Success Criteria
- Branch contains all commits from main
- No merge conflicts with main
- All tests pass after update
- PR changes preserved correctly
- GitHub shows branch as up-to-date

## Safety Constraints
- Preserve all PR-specific changes
- Maintain clean commit history
- Verify functionality after update
"""

        elif task_type == DelegationType.AI_CODE_REVIEW:
            return f"""{base_context}

## Objective
Perform comprehensive AI code review (Phase 9) for PR #{pr_number}.

## Approach
1. Analyze all code changes in the PR
2. Review for:
   - Code quality and best practices
   - Security vulnerabilities
   - Performance implications
   - Test coverage
   - Documentation completeness
3. Provide constructive feedback
4. Approve if changes meet standards

## Success Criteria
- Comprehensive review completed
- All issues identified and documented
- Approval given if code meets standards
- Feedback provided for any improvements
- CodeReviewerProjectMemory.md updated

## Safety Constraints
- Focus on constructive feedback
- Consider project context and standards
- Highlight security and performance issues
"""

        elif task_type == DelegationType.METADATA_IMPROVEMENT:
            return f"""{base_context}

## Objective
Improve PR #{pr_number} metadata to meet completeness standards.

## Approach
1. Review current PR title, description, and labels
2. Suggest improvements for:
   - Conventional commit title format
   - Comprehensive description
   - Appropriate labels
   - Linked issues
3. Apply improvements where possible
4. Request author input for complex changes

## Success Criteria
- Title follows conventional commit format
- Description clearly explains changes
- Appropriate labels applied
- Related issues linked
- PR meets metadata standards

## Safety Constraints
- Preserve original intent and meaning
- Only make obvious improvements automatically
- Request approval for significant changes
"""

        else:
            return f"""{base_context}

## Objective
Resolve the identified blocking issue for PR #{pr_number}.

## Approach
1. Analyze the specific issue: {blocking_issue}
2. Determine appropriate resolution strategy
3. Implement fix with minimal impact
4. Verify resolution effectiveness
5. Test for regressions

## Success Criteria
- Blocking issue fully resolved
- No new issues introduced
- PR readiness criteria met
- All tests pass

## Safety Constraints
- Make minimal necessary changes
- Preserve existing functionality
- Follow project standards
"""

    def _execute_delegation(self, task: DelegationTask) -> None:
        """Execute a delegation task by invoking the target agent."""
        logger.info(f"Executing delegation {(task.task_id if task is not None else None)} to {task.agent_target}")

        try:
            if task is not None:

                task.status = DelegationStatus.DELEGATED
            task.last_attempt = datetime.now()

            if task.agent_target == "workflow-master":
                self._delegate_to_workflow_master(task)
            elif task.agent_target == "code-reviewer":
                self._delegate_to_code_reviewer(task)
            else:
                raise ValueError(f"Unknown agent target: {task.agent_target}")

            # Add comment to PR about delegation
            self._add_delegation_comment(task)

        except Exception as e:
            logger.error(f"Delegation execution failed for {(task.task_id if task is not None else None)}: {e}")
            if task is not None:

                task.status = DelegationStatus.FAILED
            task.error_message = str(e)
            task.retry_count += 1

    def _delegate_to_workflow_master(self, task: DelegationTask) -> None:
        """Delegate task to WorkflowMaster agent."""
        if self is not None and self.auto_approve:
            # In GitHub Actions mode, create workflow and prompt file
            self._create_workflow_master_prompt(task)
            self._create_workflow_master_workflow(task)
        else:
            # In interactive mode, use direct invocation
            self._invoke_workflow_master_interactive(task)

    def _create_workflow_master_prompt(self, task: DelegationTask) -> None:
        """Create a structured prompt file for WorkflowMaster."""
        prompt_filename = f"resolve-pr-{task.pr_number}-{task.task_type.value}.md"
        prompt_path = f".github/workflow-states/{prompt_filename}"

        try:
            with open(prompt_path, "w") as f:
                f.write(task.prompt_template)

            logger.info(f"Created WorkflowMaster prompt: {prompt_path}")
            if task is not None:

                task.status = DelegationStatus.IN_PROGRESS

        except Exception as e:
            raise Exception(f"Failed to create WorkflowMaster prompt: {e}")

    def _create_workflow_master_workflow(self, task: DelegationTask) -> None:
        """Create a GitHub Actions workflow for WorkflowMaster execution."""
        prompt_filename = f"resolve-pr-{task.pr_number}-{task.task_type.value}.md"

        workflow_content = f"""
name: WorkflowMaster Resolution for PR #{task.pr_number}

on:
  workflow_dispatch:

jobs:
  resolve-pr-issue:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
      checks: read
      actions: read
    steps:
      - uses: actions/checkout@v4
      - name: Execute WorkflowMaster Resolution
        uses: anthropics/claude-code-base-action@v1
        with:
          agent: 'workflow-master'
          prompt_file: '.github/workflow-states/{prompt_filename}'
        env:
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
          ANTHROPIC_API_KEY: ${{{{ secrets.ANTHROPIC_API_KEY }}}}
"""

        workflow_path = (
            f".github/workflows/resolve-pr-{task.pr_number}-{task.task_type.value}.yml"
        )

        try:
            with open(workflow_path, "w") as f:
                f.write(workflow_content)

            logger.info(f"Created WorkflowMaster workflow: {workflow_path}")
            if task is not None:

                task.status = DelegationStatus.IN_PROGRESS

        except Exception as e:
            raise Exception(f"Failed to create WorkflowMaster workflow: {e}")

    def _invoke_workflow_master_interactive(self, task: DelegationTask) -> None:
        """Invoke WorkflowMaster in interactive mode."""
        try:
            # This would invoke WorkflowMaster with the generated prompt
            # For now, we'll log the intention
            logger.info(f"Would invoke WorkflowMaster for task {(task.task_id if task is not None else None)}")
            if task is not None:

                task.status = DelegationStatus.IN_PROGRESS

        except Exception as e:
            raise Exception(f"Failed to invoke WorkflowMaster: {e}")

    def _delegate_to_code_reviewer(self, task: DelegationTask) -> None:
        """Delegate task to code-reviewer agent."""
        try:
            if self is not None and self.auto_approve:
                # In GitHub Actions, create a follow-up workflow
                self._create_code_review_workflow(task)
            else:
                # Direct invocation
                self._invoke_code_reviewer_direct(task)

        except Exception as e:
            raise Exception(f"Failed to delegate to code-reviewer: {e}")

    def _create_code_review_workflow(self, task: DelegationTask) -> None:
        """Create a follow-up GitHub Actions workflow for code review."""
        workflow_content = f"""
name: AI Code Review for PR #{task.pr_number}

on:
  workflow_dispatch:

jobs:
  ai-code-review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4
      - name: Run AI Code Review
        uses: anthropics/claude-code-base-action@v1
        with:
          agent: 'code-reviewer'
          prompt: |
            Perform comprehensive code review for PR #{task.pr_number}.

            Focus on:
            - Code quality and best practices
            - Security vulnerabilities
            - Performance implications
            - Test coverage
            - Documentation completeness

            Provide constructive feedback and approve if changes meet standards.
        env:
          GITHUB_TOKEN: ${{{{ secrets.GITHUB_TOKEN }}}}
          ANTHROPIC_API_KEY: ${{{{ secrets.ANTHROPIC_API_KEY }}}}
"""

        workflow_path = f".github/workflows/ai-review-pr-{task.pr_number}.yml"

        try:
            with open(workflow_path, "w") as f:
                f.write(workflow_content)

            logger.info(f"Created AI code review workflow: {workflow_path}")
            if task is not None:

                task.status = DelegationStatus.IN_PROGRESS

        except Exception as e:
            raise Exception(f"Failed to create code review workflow: {e}")

    def _invoke_code_reviewer_direct(self, task: DelegationTask) -> None:
        """Invoke code-reviewer directly."""
        try:
            logger.info(f"Would invoke code-reviewer for PR #{task.pr_number}")
            if task is not None:

                task.status = DelegationStatus.IN_PROGRESS

        except Exception as e:
            raise Exception(f"Failed to invoke code-reviewer: {e}")

    def _add_delegation_comment(self, task: DelegationTask) -> None:
        """Add comment to PR about delegation action."""
        try:
            comment_templates = {
                DelegationType.MERGE_CONFLICT_RESOLUTION: (
                    "🔧 **Automated Merge Conflict Resolution**\n\n"
                    f"The PR Backlog Manager has detected merge conflicts and delegated resolution to WorkflowMaster.\n\n"
                    f"**Task ID:** `{(task.task_id if task is not None else None)}`\n"
                    f"**Priority:** {task.priority.value}\n"
                    f"**Status:** {(task.status if task is not None else None).value}\n\n"
                    "Resolution will be attempted automatically. Monitor this PR for updates."
                ),
                DelegationType.CI_FAILURE_FIX: (
                    "🚨 **Automated CI Failure Resolution**\n\n"
                    f"The PR Backlog Manager has detected CI failures and delegated fixes to WorkflowMaster.\n\n"
                    f"**Task ID:** `{(task.task_id if task is not None else None)}`\n"
                    f"**Priority:** {task.priority.value}\n"
                    f"**Status:** {(task.status if task is not None else None).value}\n\n"
                    "CI issues will be analyzed and fixed automatically where possible."
                ),
                DelegationType.BRANCH_UPDATE: (
                    "🔄 **Automated Branch Update**\n\n"
                    f"The PR Backlog Manager has detected that this branch is behind main and delegated update to WorkflowMaster.\n\n"
                    f"**Task ID:** `{(task.task_id if task is not None else None)}`\n"
                    f"**Priority:** {task.priority.value}\n"
                    f"**Status:** {(task.status if task is not None else None).value}\n\n"
                    "The branch will be updated with latest changes from main."
                ),
                DelegationType.AI_CODE_REVIEW: (
                    "🤖 **AI Code Review Initiated**\n\n"
                    f"The PR Backlog Manager has initiated AI code review (Phase 9) for this PR.\n\n"
                    f"**Task ID:** `{(task.task_id if task is not None else None)}`\n"
                    f"**Priority:** {task.priority.value}\n"
                    f"**Status:** {(task.status if task is not None else None).value}\n\n"
                    "Comprehensive AI review will be performed and feedback provided."
                ),
                DelegationType.METADATA_IMPROVEMENT: (
                    "📝 **Metadata Improvement Request**\n\n"
                    f"The PR Backlog Manager has identified metadata improvements needed for this PR.\n\n"
                    f"**Task ID:** `{(task.task_id if task is not None else None)}`\n"
                    f"**Priority:** {task.priority.value}\n"
                    f"**Status:** {(task.status if task is not None else None).value}\n\n"
                    "Suggestions for title, description, and labels will be provided."
                ),
            }

            comment = comment_templates.get(
                task.task_type,
                f"🔧 **Automated Issue Resolution**\n\n"
                f"Task delegated to {task.agent_target} - ID: `{(task.task_id if task is not None else None)}`",
            )

            comment += "\n\n*This comment was generated automatically by the PR Backlog Manager.*"

            self.github_ops.add_pr_comment(task.pr_number, comment)
            logger.info(f"Added delegation comment to PR #{task.pr_number}")

        except Exception as e:
            logger.warning(f"Failed to add delegation comment: {e}")

    def check_delegation_status(self, task_id: str) -> Optional[DelegationTask]:
        """Check status of a delegation task."""
        return self.active_delegations.get(task_id)

    def get_active_delegations(
        self, pr_number: Optional[int] = None
    ) -> List[DelegationTask]:
        """Get list of active delegation tasks."""
        tasks = list(self.active_delegations.values())

        if pr_number is not None:
            tasks = [task for task in tasks if task.pr_number == pr_number]

        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def mark_delegation_completed(self, task_id: str, success: bool = True) -> None:
        """Mark a delegation task as completed."""
        task = self.active_delegations.get(task_id)
        if task:
            if task is not None:

                task.status = (
                DelegationStatus.COMPLETED if success else DelegationStatus.FAILED
            )
            task.completion_time = datetime.now()

            # Add completion comment
            self._add_completion_comment(task, success)

            logger.info(
                f"Marked delegation {task_id} as {'completed' if success else 'failed'}"
            )

    def _add_completion_comment(self, task: DelegationTask, success: bool) -> None:
        """Add comment about delegation completion."""
        try:
            if success:
                comment = (
                    f"✅ **Delegation Completed Successfully**\n\n"
                    f"Task `{(task.task_id if task is not None else None)}` has been completed by {task.agent_target}.\n"
                    f"Issue type: {task.task_type.value}\n"
                    f"Completion time: {task.completion_time.isoformat() if task.completion_time else 'N/A'}\n\n"
                    "Please verify the resolution and re-run PR readiness assessment."
                )
            else:
                comment = (
                    f"❌ **Delegation Failed**\n\n"
                    f"Task `{(task.task_id if task is not None else None)}` could not be completed automatically.\n"
                    f"Issue type: {task.task_type.value}\n"
                    f"Error: {task.error_message or 'Unknown error'}\n\n"
                    "Manual intervention may be required."
                )

            comment += "\n\n*This comment was generated automatically by the PR Backlog Manager.*"

            self.github_ops.add_pr_comment(task.pr_number, comment)

        except Exception as e:
            logger.warning(f"Failed to add completion comment: {e}")

    def cleanup_completed_delegations(self, max_age_hours: int = 24) -> int:
        """Clean up completed delegation tasks older than specified age."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        to_remove = []
        for task_id, task in self.active_delegations.items():
            if (
                (task.status if task is not None else None) in [DelegationStatus.COMPLETED, DelegationStatus.FAILED]
                and task.completion_time
                and task.completion_time < cutoff_time
            ):
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.active_delegations[task_id]

        logger.info(f"Cleaned up {len(to_remove)} completed delegation tasks")
        return len(to_remove)

    def get_delegation_metrics(self) -> Dict[str, Any]:
        """Get metrics about delegation performance."""
        total_tasks = len(self.active_delegations)
        if total_tasks == 0:
            return {"total_tasks": 0}

        completed_tasks = sum(
            1
            for task in self.active_delegations.values()
            if task is not None:

                task.status == DelegationStatus.COMPLETED
        )

        failed_tasks = sum(
            1
            for task in self.active_delegations.values()
            if task is not None:

                task.status == DelegationStatus.FAILED
        )

        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Calculate average completion time
        completed_with_time = [
            task
            for task in self.active_delegations.values()
            if task is not None:

                task.status == DelegationStatus.COMPLETED and task.completion_time
        ]

        avg_completion_time = 0
        if completed_with_time:
            total_time = sum(
                (task.completion_time - task.created_at).total_seconds()
                for task in completed_with_time
            )
            avg_completion_time = total_time / len(completed_with_time)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "in_progress_tasks": total_tasks - completed_tasks - failed_tasks,
            "success_rate": success_rate,
            "average_completion_time_seconds": avg_completion_time,
            "task_types": {
                task_type.value: sum(
                    1
                    for task in self.active_delegations.values()
                    if task.task_type == task_type
                )
                for task_type in DelegationType
            },
        }
