"""
Core PR Backlog Manager implementation.

Provides the main orchestration logic for automated PR backlog management
including readiness assessment, issue delegation, and labeling coordination.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Add shared modules to path for import resolution
shared_path = os.path.join(os.path.dirname(__file__), '..', '..', 'shared')
sys.path.insert(0, os.path.abspath(shared_path))

try:
    from github_operations import GitHubOperations, GitHubError, RateLimitError
    from utils.error_handling import (
        GadugiError, RetryStrategy, ErrorSeverity, 
        retry_with_backoff, CircuitBreaker
    )
    from state_management import StateManager, CheckpointManager
    from task_tracking import TaskTracker, TaskMetrics
    from interfaces import AgentConfig, OperationResult
except ImportError as e:
    logging.warning(f"Failed to import shared modules: {e}")
    # Fallback definitions for development/testing
    class GitHubOperations:
        def __init__(self, **kwargs): pass
    class StateManager:
        def __init__(self, **kwargs): pass
    class TaskTracker:
        def __init__(self, **kwargs): pass
    OperationResult = Dict[str, Any]


logger = logging.getLogger(__name__)


class PRStatus(Enum):
    """PR processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    BLOCKED = "blocked"
    FAILED = "failed"


class ReadinessCriteria(Enum):
    """PR readiness criteria."""
    NO_MERGE_CONFLICTS = "no_merge_conflicts"
    CI_PASSING = "ci_passing"
    UP_TO_DATE = "up_to_date"
    HUMAN_REVIEW_COMPLETE = "human_review_complete"
    AI_REVIEW_COMPLETE = "ai_review_complete"
    METADATA_COMPLETE = "metadata_complete"


@dataclass
class PRAssessment:
    """Comprehensive PR assessment result."""
    pr_number: int
    status: PRStatus
    criteria_met: Dict[ReadinessCriteria, bool]
    blocking_issues: List[str]
    resolution_actions: List[str]
    last_updated: datetime
    processing_time: float
    
    @property
    def is_ready(self) -> bool:
        """Check if PR meets all readiness criteria."""
        return all(self.criteria_met.values())
    
    @property
    def readiness_score(self) -> float:
        """Calculate readiness score as percentage."""
        if not self.criteria_met:
            return 0.0
        return sum(self.criteria_met.values()) / len(self.criteria_met) * 100


@dataclass
class BacklogMetrics:
    """Backlog processing metrics."""
    total_prs: int
    ready_prs: int
    blocked_prs: int
    processing_time: float
    automation_rate: float
    success_rate: float
    timestamp: datetime


class PRBacklogManager:
    """
    Core PR Backlog Manager for automated PR readiness assessment.
    
    Orchestrates the entire PR backlog management workflow including:
    - PR discovery and prioritization
    - Comprehensive readiness assessment
    - Issue resolution delegation
    - Automated labeling and notifications
    """
    
    def __init__(self, 
                 config: Optional[AgentConfig] = None,
                 auto_approve: bool = False):
        """Initialize PR Backlog Manager."""
        self.config = config or AgentConfig(
            agent_id="pr-backlog-manager",
            name="PR Backlog Manager"
        )
        self.auto_approve = auto_approve or self._detect_auto_approve_context()
        
        # Initialize shared components
        self.github_ops = GitHubOperations()
        self.state_manager = StateManager(
            workspace_dir=".github/workflow-states"
        )
        self.task_tracker = TaskTracker()
        
        # Initialize circuit breakers
        self.github_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=600.0
        )
        self.processing_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=300.0
        )
        
        # Processing state
        self.session_id = f"pr-backlog-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.metrics = BacklogMetrics(
            total_prs=0,
            ready_prs=0,
            blocked_prs=0,
            processing_time=0.0,
            automation_rate=0.0,
            success_rate=0.0,
            timestamp=datetime.now()
        )
        
        logger.info(f"Initialized PR Backlog Manager - Session: {self.session_id}")
    
    def _detect_auto_approve_context(self) -> bool:
        """Detect if running in auto-approve context (GitHub Actions)."""
        return (
            os.getenv('GITHUB_ACTIONS') == 'true' and 
            os.getenv('CLAUDE_AUTO_APPROVE') == 'true'
        )
    
    def validate_auto_approve_safety(self) -> None:
        """Validate auto-approve context is safe."""
        if not self.auto_approve:
            return
            
        if not os.getenv('GITHUB_ACTIONS'):
            raise GadugiError(
                "Auto-approve only allowed in GitHub Actions environment",
                severity=ErrorSeverity.CRITICAL
            )
        
        if not os.getenv('CLAUDE_AUTO_APPROVE'):
            raise GadugiError(
                "Auto-approve not explicitly enabled",
                severity=ErrorSeverity.CRITICAL
            )
        
        allowed_events = ['pull_request', 'schedule', 'workflow_dispatch']
        if os.getenv('GITHUB_EVENT_NAME') not in allowed_events:
            raise GadugiError(
                f"Auto-approve not allowed for event: {os.getenv('GITHUB_EVENT_NAME')}",
                severity=ErrorSeverity.HIGH
            )
    
    @retry_with_backoff(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
    def discover_prs_for_processing(self) -> List[Dict[str, Any]]:
        """
        Discover PRs requiring backlog processing.
        
        Returns list of PR objects that need evaluation.
        """
        logger.info("Discovering PRs for backlog processing...")
        
        try:
            # Get all ready_for_review PRs
            ready_prs = self.github_ops.get_prs(
                state='open',
                labels_exclude=['ready-seeking-human', 'draft']
            )
            
            # Filter for PRs needing evaluation
            candidate_prs = []
            for pr in ready_prs:
                if self._should_process_pr(pr):
                    candidate_prs.append(pr)
            
            logger.info(f"Found {len(candidate_prs)} PRs requiring evaluation")
            return self._prioritize_prs(candidate_prs)
            
        except Exception as e:
            logger.error(f"Failed to discover PRs: {e}")
            raise GadugiError(
                f"PR discovery failed: {e}",
                severity=ErrorSeverity.HIGH,
                context={'session_id': self.session_id}
            )
    
    def _should_process_pr(self, pr: Dict[str, Any]) -> bool:
        """Determine if PR should be processed."""
        # Skip draft PRs
        if pr.get('draft', False):
            return False
            
        # Skip PRs already labeled ready-seeking-human
        labels = [label['name'] for label in pr.get('labels', [])]
        if 'ready-seeking-human' in labels:
            return False
        
        # Skip very recently created PRs (give time for initial CI)
        created_at = datetime.fromisoformat(
            pr['created_at'].replace('Z', '+00:00')
        )
        if datetime.now().replace(tzinfo=created_at.tzinfo) - created_at < timedelta(minutes=5):
            return False
            
        return True
    
    def _prioritize_prs(self, prs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize PRs for processing."""
        def priority_score(pr):
            score = 0
            
            # Age factor (older PRs get higher priority)
            created_at = datetime.fromisoformat(
                pr['created_at'].replace('Z', '+00:00')
            )
            age_days = (datetime.now().replace(tzinfo=created_at.tzinfo) - created_at).days
            score += min(age_days * 10, 100)  # Cap at 100 points
            
            # Recent activity factor
            updated_at = datetime.fromisoformat(
                pr['updated_at'].replace('Z', '+00:00')
            )
            hours_since_update = (datetime.now().replace(tzinfo=updated_at.tzinfo) - updated_at).total_seconds() / 3600
            if hours_since_update < 24:
                score += 50  # Recent activity bonus
            
            # Label-based priority
            labels = [label['name'] for label in pr.get('labels', [])]
            if 'priority-high' in labels:
                score += 75
            elif 'priority-medium' in labels:
                score += 25
            
            return score
        
        return sorted(prs, key=priority_score, reverse=True)
    
    def process_single_pr(self, pr_number: int) -> PRAssessment:
        """
        Process a single PR for readiness assessment.
        
        Args:
            pr_number: PR number to process
            
        Returns:
            PRAssessment object with evaluation results
        """
        start_time = datetime.now()
        logger.info(f"Processing PR #{pr_number}...")
        
        try:
            # Validate auto-approve safety
            self.validate_auto_approve_safety()
            
            # Get PR details
            pr_details = self.github_ops.get_pr_details(pr_number)
            
            # Initialize assessment
            assessment = PRAssessment(
                pr_number=pr_number,
                status=PRStatus.PROCESSING,
                criteria_met={},
                blocking_issues=[],
                resolution_actions=[],
                last_updated=datetime.now(),
                processing_time=0.0
            )
            
            # Evaluate each readiness criterion
            assessment.criteria_met = self._evaluate_readiness_criteria(pr_details)
            
            # Identify blocking issues and resolution actions
            assessment.blocking_issues = self._identify_blocking_issues(assessment.criteria_met)
            assessment.resolution_actions = self._generate_resolution_actions(
                pr_number, assessment.blocking_issues
            )
            
            # Update status based on results
            if assessment.is_ready:
                assessment.status = PRStatus.READY
                self._apply_ready_label(pr_number)
            elif assessment.blocking_issues:
                assessment.status = PRStatus.BLOCKED
                self._delegate_issue_resolution(pr_number, assessment.resolution_actions)
            else:
                assessment.status = PRStatus.FAILED
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            assessment.processing_time = processing_time
            
            # Save assessment state
            self._save_assessment(assessment)
            
            logger.info(
                f"Completed PR #{pr_number} assessment - "
                f"Status: {assessment.status.value}, "
                f"Score: {assessment.readiness_score:.1f}%, "
                f"Time: {processing_time:.2f}s"
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to process PR #{pr_number}: {e}")
            
            return PRAssessment(
                pr_number=pr_number,
                status=PRStatus.FAILED,
                criteria_met={},
                blocking_issues=[f"Processing error: {str(e)}"],
                resolution_actions=[],
                last_updated=datetime.now(),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _evaluate_readiness_criteria(self, pr_details: Dict[str, Any]) -> Dict[ReadinessCriteria, bool]:
        """Evaluate all readiness criteria for a PR."""
        criteria_results = {}
        
        # Check merge conflicts
        criteria_results[ReadinessCriteria.NO_MERGE_CONFLICTS] = self._check_merge_conflicts(pr_details)
        
        # Check CI status
        criteria_results[ReadinessCriteria.CI_PASSING] = self._check_ci_status(pr_details)
        
        # Check branch sync
        criteria_results[ReadinessCriteria.UP_TO_DATE] = self._check_branch_sync(pr_details)
        
        # Check human review
        criteria_results[ReadinessCriteria.HUMAN_REVIEW_COMPLETE] = self._check_human_review(pr_details)
        
        # Check AI review
        criteria_results[ReadinessCriteria.AI_REVIEW_COMPLETE] = self._check_ai_review(pr_details)
        
        # Check metadata
        criteria_results[ReadinessCriteria.METADATA_COMPLETE] = self._check_metadata(pr_details)
        
        return criteria_results
    
    def _check_merge_conflicts(self, pr_details: Dict[str, Any]) -> bool:
        """Check if PR has merge conflicts."""
        try:
            mergeable = pr_details.get('mergeable')
            mergeable_state = pr_details.get('mergeable_state', '')
            
            # GitHub's mergeable can be None (still calculating), True, or False
            return mergeable is True and mergeable_state not in ['dirty', 'blocked']
        except Exception as e:
            logger.warning(f"Failed to check merge conflicts: {e}")
            return False
    
    def _check_ci_status(self, pr_details: Dict[str, Any]) -> bool:
        """Check if CI is passing."""
        try:
            # Get status checks for the PR
            checks = self.github_ops.get_pr_status_checks(pr_details['number'])
            
            # All required checks must be successful
            return all(
                check.get('state') == 'success' 
                for check in checks 
                if check.get('context', '').startswith('ci/')
            )
        except Exception as e:
            logger.warning(f"Failed to check CI status: {e}")
            return False
    
    def _check_branch_sync(self, pr_details: Dict[str, Any]) -> bool:
        """Check if branch is up to date with main."""
        try:
            base_sha = pr_details['base']['sha']
            head_sha = pr_details['head']['sha']
            
            # Use GitHub API to compare commits
            comparison = self.github_ops.compare_commits(base_sha, head_sha)
            
            # If ahead_by > 0 and behind_by = 0, branch is up to date
            return comparison.get('behind_by', 0) == 0
        except Exception as e:
            logger.warning(f"Failed to check branch sync: {e}")
            return False
    
    def _check_human_review(self, pr_details: Dict[str, Any]) -> bool:
        """Check if human review is complete."""
        try:
            reviews = self.github_ops.get_pr_reviews(pr_details['number'])
            
            # Filter for human reviews (not bots)
            human_reviews = [
                review for review in reviews 
                if not review['user']['login'].endswith('[bot]')
            ]
            
            # Check for approved reviews
            approved_reviews = [
                review for review in human_reviews
                if review['state'] == 'APPROVED'
            ]
            
            return len(approved_reviews) > 0
        except Exception as e:
            logger.warning(f"Failed to check human review: {e}")
            return False
    
    def _check_ai_review(self, pr_details: Dict[str, Any]) -> bool:
        """Check if AI review (Phase 9) is complete."""
        try:
            comments = self.github_ops.get_pr_comments(pr_details['number'])
            
            # Look for code-reviewer comments
            ai_review_comments = [
                comment for comment in comments
                if 'code-reviewer' in comment.get('body', '').lower()
            ]
            
            return len(ai_review_comments) > 0
        except Exception as e:
            logger.warning(f"Failed to check AI review: {e}")
            return False
    
    def _check_metadata(self, pr_details: Dict[str, Any]) -> bool:
        """Check if PR metadata is complete."""
        try:
            # Check title follows conventional commit format
            title = pr_details.get('title', '')
            has_conventional_title = any(
                title.lower().startswith(prefix) 
                for prefix in ['feat:', 'fix:', 'docs:', 'style:', 'refactor:', 'test:', 'chore:']
            )
            
            # Check description is not empty
            body = pr_details.get('body', '')
            has_description = bool(body and len(body.strip()) > 10)
            
            # Check for appropriate labels
            labels = [label['name'] for label in pr_details.get('labels', [])]
            has_type_label = any(
                label in labels 
                for label in ['enhancement', 'bugfix', 'documentation', 'refactor']
            )
            
            return has_conventional_title and has_description and has_type_label
        except Exception as e:
            logger.warning(f"Failed to check metadata: {e}")
            return False
    
    def _identify_blocking_issues(self, criteria_met: Dict[ReadinessCriteria, bool]) -> List[str]:
        """Identify blocking issues based on unmet criteria."""
        blocking_issues = []
        
        for criteria, is_met in criteria_met.items():
            if not is_met:
                issue_description = {
                    ReadinessCriteria.NO_MERGE_CONFLICTS: "PR has merge conflicts that need resolution",
                    ReadinessCriteria.CI_PASSING: "CI checks are failing and need to be fixed",
                    ReadinessCriteria.UP_TO_DATE: "Branch is behind main and needs to be updated",
                    ReadinessCriteria.HUMAN_REVIEW_COMPLETE: "PR needs human review approval",
                    ReadinessCriteria.AI_REVIEW_COMPLETE: "AI code review (Phase 9) not completed",
                    ReadinessCriteria.METADATA_COMPLETE: "PR metadata (title, description, labels) incomplete"
                }.get(criteria, f"Unmet criteria: {criteria.value}")
                
                blocking_issues.append(issue_description)
        
        return blocking_issues
    
    def _generate_resolution_actions(self, pr_number: int, blocking_issues: List[str]) -> List[str]:
        """Generate resolution actions for blocking issues."""
        actions = []
        
        for issue in blocking_issues:
            if "merge conflicts" in issue.lower():
                actions.append(f"Delegate merge conflict resolution to WorkflowMaster for PR #{pr_number}")
            elif "ci checks" in issue.lower():
                actions.append(f"Delegate CI failure resolution to WorkflowMaster for PR #{pr_number}")
            elif "behind main" in issue.lower():
                actions.append(f"Delegate branch update to WorkflowMaster for PR #{pr_number}")
            elif "human review" in issue.lower():
                actions.append(f"Add comment requesting human review for PR #{pr_number}")
            elif "ai code review" in issue.lower():
                actions.append(f"Invoke code-reviewer agent for PR #{pr_number}")
            elif "metadata" in issue.lower():
                actions.append(f"Add comment requesting metadata improvements for PR #{pr_number}")
        
        return actions
    
    def _apply_ready_label(self, pr_number: int) -> None:
        """Apply ready-seeking-human label to PR."""
        try:
            self.github_ops.add_pr_labels(pr_number, ['ready-seeking-human'])
            self.github_ops.add_pr_comment(
                pr_number,
                "✅ **PR Ready for Human Review**\n\n"
                "This PR has passed all automated readiness checks:\n"
                "- ✅ No merge conflicts\n"
                "- ✅ CI/CD passing\n" 
                "- ✅ Up-to-date with main\n"
                "- ✅ Code review completed\n"
                "- ✅ AI review completed\n"
                "- ✅ Metadata complete\n\n"
                "*This label was applied automatically by the PR Backlog Manager.*"
            )
            logger.info(f"Applied ready-seeking-human label to PR #{pr_number}")
        except Exception as e:
            logger.error(f"Failed to apply ready label to PR #{pr_number}: {e}")
    
    def _delegate_issue_resolution(self, pr_number: int, actions: List[str]) -> None:
        """Delegate issue resolution to appropriate agents."""
        for action in actions:
            try:
                if "WorkflowMaster" in action:
                    self._delegate_to_workflow_master(pr_number, action)
                elif "code-reviewer" in action:
                    self._invoke_code_reviewer(pr_number)
                else:
                    self._add_informational_comment(pr_number, action)
            except Exception as e:
                logger.error(f"Failed to execute action '{action}': {e}")
    
    def _delegate_to_workflow_master(self, pr_number: int, action: str) -> None:
        """Delegate complex issue resolution to WorkflowMaster."""
        # In a real implementation, this would invoke WorkflowMaster
        # For now, add a comment indicating what needs to be done
        comment = (
            f"🔧 **Automated Issue Detection**\n\n"
            f"The PR Backlog Manager has identified issues that require resolution:\n"
            f"- {action}\n\n"
            f"A WorkflowMaster will be invoked to handle this resolution.\n\n"
            f"*This comment was generated automatically by the PR Backlog Manager.*"
        )
        self.github_ops.add_pr_comment(pr_number, comment)
        logger.info(f"Delegated issue resolution to WorkflowMaster for PR #{pr_number}")
    
    def _invoke_code_reviewer(self, pr_number: int) -> None:
        """Invoke code-reviewer agent for AI review."""
        comment = (
            f"🤖 **AI Code Review Required**\n\n"
            f"This PR needs AI code review (Phase 9) to be completed.\n"
            f"The code-reviewer agent will be invoked to perform this review.\n\n"
            f"*This comment was generated automatically by the PR Backlog Manager.*"
        )
        self.github_ops.add_pr_comment(pr_number, comment)
        logger.info(f"Requested AI code review for PR #{pr_number}")
    
    def _add_informational_comment(self, pr_number: int, action: str) -> None:
        """Add informational comment for manual actions."""
        comment = (
            f"📋 **Action Required**\n\n"
            f"The PR Backlog Manager has identified an action that requires attention:\n"
            f"- {action}\n\n"
            f"*This comment was generated automatically by the PR Backlog Manager.*"
        )
        self.github_ops.add_pr_comment(pr_number, comment)
        logger.info(f"Added informational comment to PR #{pr_number}")
    
    def _save_assessment(self, assessment: PRAssessment) -> None:
        """Save assessment results to state management."""
        try:
            state_data = {
                'pr_number': assessment.pr_number,
                'status': assessment.status.value,
                'criteria_met': {k.value: v for k, v in assessment.criteria_met.items()},
                'blocking_issues': assessment.blocking_issues,
                'resolution_actions': assessment.resolution_actions,
                'last_updated': assessment.last_updated.isoformat(),
                'processing_time': assessment.processing_time,
                'readiness_score': assessment.readiness_score,
                'session_id': self.session_id
            }
            
            state_key = f"pr-assessment-{assessment.pr_number}"
            self.state_manager.save_state(state_key, state_data)
            
        except Exception as e:
            logger.warning(f"Failed to save assessment for PR #{assessment.pr_number}: {e}")
    
    def process_backlog(self) -> BacklogMetrics:
        """
        Process entire PR backlog for readiness assessment.
        
        Returns:
            BacklogMetrics with processing results
        """
        start_time = datetime.now()
        logger.info("Starting full backlog processing...")
        
        try:
            # Validate auto-approve safety
            self.validate_auto_approve_safety()
            
            # Discover PRs for processing
            prs = self.discover_prs_for_processing()
            self.metrics.total_prs = len(prs)
            
            if not prs:
                logger.info("No PRs found requiring processing")
                return self.metrics
            
            # Process each PR
            assessments = []
            for pr in prs:
                try:
                    assessment = self.process_single_pr(pr['number'])
                    assessments.append(assessment)
                    
                    # Update metrics
                    if assessment.status == PRStatus.READY:
                        self.metrics.ready_prs += 1
                    elif assessment.status == PRStatus.BLOCKED:
                        self.metrics.blocked_prs += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process PR #{pr['number']}: {e}")
                    self.metrics.blocked_prs += 1
            
            # Calculate final metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics.processing_time = processing_time
            self.metrics.automation_rate = (
                (self.metrics.ready_prs / self.metrics.total_prs * 100) 
                if self.metrics.total_prs > 0 else 0
            )
            self.metrics.success_rate = (
                ((self.metrics.ready_prs + self.metrics.blocked_prs) / self.metrics.total_prs * 100)
                if self.metrics.total_prs > 0 else 0
            )
            
            # Generate summary report
            self._generate_backlog_report(assessments)
            
            logger.info(
                f"Backlog processing complete - "
                f"Processed: {self.metrics.total_prs}, "
                f"Ready: {self.metrics.ready_prs}, "
                f"Blocked: {self.metrics.blocked_prs}, "
                f"Time: {processing_time:.2f}s"
            )
            
            return self.metrics
            
        except Exception as e:
            logger.error(f"Backlog processing failed: {e}")
            raise GadugiError(
                f"Backlog processing failed: {e}",
                severity=ErrorSeverity.HIGH,
                context={'session_id': self.session_id}
            )
    
    def _generate_backlog_report(self, assessments: List[PRAssessment]) -> None:
        """Generate summary report of backlog processing."""
        try:
            report = {
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    'total_prs': self.metrics.total_prs,
                    'ready_prs': self.metrics.ready_prs,
                    'blocked_prs': self.metrics.blocked_prs,
                    'processing_time': self.metrics.processing_time,
                    'automation_rate': self.metrics.automation_rate,
                    'success_rate': self.metrics.success_rate
                },
                'assessments': [
                    {
                        'pr_number': a.pr_number,
                        'status': a.status.value,
                        'readiness_score': a.readiness_score,
                        'blocking_issues_count': len(a.blocking_issues),
                        'processing_time': a.processing_time
                    }
                    for a in assessments
                ]
            }
            
            # Save report to state management
            self.state_manager.save_state(f"backlog-report-{self.session_id}", report)
            
            logger.info(f"Generated backlog report for session {self.session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to generate backlog report: {e}")


def main():
    """Main entry point for PR Backlog Manager."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize manager
    manager = PRBacklogManager()
    
    # Process based on context
    if len(sys.argv) > 1 and sys.argv[1].startswith('pr_'):
        # Single PR mode
        try:
            pr_number = int(sys.argv[1].split('_')[1])
            assessment = manager.process_single_pr(pr_number)
            print(f"PR #{pr_number} assessment: {assessment.status.value} "
                  f"(Score: {assessment.readiness_score:.1f}%)")
        except ValueError:
            print("Invalid PR number format. Use: pr_NUMBER")
            sys.exit(1)
    else:
        # Backlog mode
        metrics = manager.process_backlog()
        print(f"Backlog processing complete: {metrics.ready_prs}/{metrics.total_prs} PRs ready "
              f"(Automation rate: {metrics.automation_rate:.1f}%)")


if __name__ == "__main__":
    main()