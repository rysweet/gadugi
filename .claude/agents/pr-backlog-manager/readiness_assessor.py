from typing import Any, Dict, List, Optional

import logging

"""
PR Readiness Assessment module.

Provides specialized assessment capabilities for evaluating PR readiness
across multiple dimensions including conflicts, CI status, reviews, and metadata.
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConflictComplexity(Enum):
    """Merge conflict complexity levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class CIFailureType(Enum):
    """Types of CI failures."""

    TRANSIENT = "transient"
    BUILD_FAILURE = "build_failure"
    TEST_FAILURE = "test_failure"
    LINT_FAILURE = "lint_failure"
    SECURITY_FAILURE = "security_failure"
    UNKNOWN = "unknown"

@dataclass
class ConflictAssessment:
    """Assessment of merge conflicts."""

    has_conflicts: bool
    affected_files: List[str]
    complexity: ConflictComplexity
    resolution_estimate: timedelta
    auto_resolvable: bool

    @property
    def is_blocking(self) -> bool:
        """Check if conflicts are blocking for automation."""
        return self.has_conflicts and self.complexity in [
            ConflictComplexity.MEDIUM,
            ConflictComplexity.HIGH,
        ]

@dataclass
class CIAssessment:
    """Assessment of CI/CD status."""

    all_passing: bool
    failing_checks: List[Dict[str, Any]]
    retriable_failures: List[str]
    blocking_failures: List[str]
    last_run: Optional[datetime]

    @property
    def can_auto_retry(self) -> bool:
        """Check if failures can be automatically retried."""
        return bool(self.retriable_failures) and not self.blocking_failures

@dataclass
class ReviewAssessment:
    """Assessment of code review status."""

    has_approved_review: bool
    pending_requests: List[str]
    requested_changes: List[Dict[str, Any]]
    ai_review_complete: bool
    review_coverage_score: float

    @property
    def is_review_complete(self) -> bool:
        """Check if review process is complete."""
        return (
            self.has_approved_review
            and not self.pending_requests
            and not self.requested_changes
            and self.ai_review_complete
        )

@dataclass
class SyncAssessment:
    """Assessment of branch synchronization."""

    is_up_to_date: bool
    commits_behind: int
    commits_ahead: int
    last_sync: Optional[datetime]
    sync_complexity: str

    @property
    def requires_update(self) -> bool:
        """Check if branch requires update."""
        return self.commits_behind > 0

    @property
    def is_auto_updatable(self) -> bool:
        """Check if branch can be automatically updated."""
        return self.commits_behind <= 10 and self.sync_complexity == "simple"

@dataclass
class MetadataAssessment:
    """Assessment of PR metadata completeness."""

    has_conventional_title: bool
    has_description: bool
    has_appropriate_labels: bool
    has_linked_issues: bool
    completeness_score: float

    @property
    def is_complete(self) -> bool:
        """Check if metadata is complete."""
        return (
            self.has_conventional_title
            and self.has_description
            and self.has_appropriate_labels
        )

class ReadinessAssessor:
    """
    Specialized PR readiness assessment engine.

    Provides detailed evaluation of PR readiness across multiple dimensions
    with actionable insights for automated resolution.
    """

    def __init__(self, github_ops):
        """Initialize readiness assessor."""
        self.github_ops = github_ops

        # Configuration for assessment thresholds
        self.config = {
            "max_auto_resolvable_conflicts": 3,
            "max_auto_updatable_commits": 10,
            "min_description_length": 20,
            "required_ci_checks": ["ci/", "build/", "test/"],
            "retriable_failure_patterns": [
                "timeout",
                "network",
                "rate limit",
                "temporary",
            ],
        }

    def assess_merge_conflicts(self, pr_details: Dict[str, Any]) -> ConflictAssessment:
        """
        Assess merge conflict status and complexity.

        Args:
            pr_details: PR details from GitHub API

        Returns:
            ConflictAssessment with detailed conflict analysis
        """
        try:
            mergeable = pr_details.get("mergeable")
            mergeable_state = pr_details.get("mergeable_state", "")

            if mergeable is True and mergeable_state == "clean":
                return ConflictAssessment(
                    has_conflicts=False,
                    affected_files=[],
                    complexity=ConflictComplexity.NONE,
                    resolution_estimate=timedelta(0),
                    auto_resolvable=True,
                )

            if mergeable is False or mergeable_state in ["dirty", "blocked"]:
                # Get detailed conflict information
                affected_files = self._get_conflicted_files(pr_details)
                complexity = self._assess_conflict_complexity(affected_files)

                return ConflictAssessment(
                    has_conflicts=True,
                    affected_files=affected_files,
                    complexity=complexity,
                    resolution_estimate=self._estimate_resolution_time(complexity),
                    auto_resolvable=complexity == ConflictComplexity.LOW,
                )

            # Unknown state (mergeable is None - still calculating)
            return ConflictAssessment(
                has_conflicts=False,  # Assume no conflicts for now
                affected_files=[],
                complexity=ConflictComplexity.NONE,
                resolution_estimate=timedelta(0),
                auto_resolvable=True,
            )

        except Exception as e:
            logger.error(f"Failed to assess merge conflicts: {e}")
            return ConflictAssessment(
                has_conflicts=True,  # Conservative assumption
                affected_files=[],
                complexity=ConflictComplexity.HIGH,
                resolution_estimate=timedelta(hours=2),
                auto_resolvable=False,
            )

    def _get_conflicted_files(self, pr_details: Dict[str, Any]) -> List[str]:
        """Get list of files with merge conflicts."""
        try:
            # In a real implementation, this would use GitHub API to get
            # detailed conflict information
            # For now, return empty list as placeholder
            return []
        except Exception:
            return []

    def _assess_conflict_complexity(
        self, affected_files: List[str]
    ) -> ConflictComplexity:
        """Assess complexity of merge conflicts."""
        if not affected_files:
            return ConflictComplexity.NONE

        # Analyze file types and count
        critical_files = [
            f
            for f in affected_files
            if any(
                pattern in f.lower()
                for pattern in [
                    "config",
                    "package.json",
                    "requirements.txt",
                    "dockerfile",
                ]
            )
        ]

        if len(affected_files) <= 2 and not critical_files:
            return ConflictComplexity.LOW
        elif len(affected_files) <= 5 and len(critical_files) <= 1:
            return ConflictComplexity.MEDIUM
        else:
            return ConflictComplexity.HIGH

    def _estimate_resolution_time(self, complexity: ConflictComplexity) -> timedelta:
        """Estimate time required to resolve conflicts."""
        time_estimates = {
            ConflictComplexity.NONE: timedelta(0),
            ConflictComplexity.LOW: timedelta(minutes=15),
            ConflictComplexity.MEDIUM: timedelta(minutes=45),
            ConflictComplexity.HIGH: timedelta(hours=2),
        }
        return time_estimates.get(complexity, timedelta(hours=2))

    def assess_ci_status(self, pr_details: Dict[str, Any]) -> CIAssessment:
        """
        Assess CI/CD status and failure types.

        Args:
            pr_details: PR details from GitHub API

        Returns:
            CIAssessment with detailed CI analysis
        """
        try:
            # Get status checks for the PR
            checks = self.github_ops.get_pr_status_checks(pr_details["number"])

            failing_checks = [
                check
                for check in checks
                if check.get("state") not in ["success", "pending"]
            ]

            # Categorize failures
            retriable_failures = []
            blocking_failures = []

            for check in failing_checks:
                failure_type = self._classify_ci_failure(check)
                if failure_type == CIFailureType.TRANSIENT:
                    retriable_failures.append(check["context"])
                else:
                    blocking_failures.append(check["context"])

            # Determine last run time
            last_run = None
            if checks:
                timestamps = [
                    check.get("updated_at")
                    for check in checks
                    if check.get("updated_at")
                ]
                if timestamps:
                    last_run = max(
                        datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        for ts in timestamps
                    )

            return CIAssessment(
                all_passing=len(failing_checks) == 0,
                failing_checks=failing_checks,
                retriable_failures=retriable_failures,
                blocking_failures=blocking_failures,
                last_run=last_run,
            )

        except Exception as e:
            logger.error(f"Failed to assess CI status: {e}")
            return CIAssessment(
                all_passing=False,
                failing_checks=[],
                retriable_failures=[],
                blocking_failures=["assessment_failed"],
                last_run=None,
            )

    def _classify_ci_failure(self, check: Dict[str, Any]) -> CIFailureType:
        """Classify type of CI failure."""
        description = check.get("description", "").lower()
        context = check.get("context", "").lower()

        # Check for transient failure patterns
        for pattern in self.config["retriable_failure_patterns"]:
            if pattern in description:
                return CIFailureType.TRANSIENT

        # Classify by context
        if "build" in context:
            return CIFailureType.BUILD_FAILURE
        elif "test" in context:
            return CIFailureType.TEST_FAILURE
        elif "lint" in context or "style" in context:
            return CIFailureType.LINT_FAILURE
        elif "security" in context or "vulnerability" in context:
            return CIFailureType.SECURITY_FAILURE
        else:
            return CIFailureType.UNKNOWN

    def assess_review_status(self, pr_details: Dict[str, Any]) -> ReviewAssessment:
        """
        Assess code review status and completeness.

        Args:
            pr_details: PR details from GitHub API

        Returns:
            ReviewAssessment with detailed review analysis
        """
        try:
            pr_number = pr_details["number"]

            # Get reviews
            reviews = self.github_ops.get_pr_reviews(pr_number)

            # Filter human reviews (exclude bots)
            human_reviews = [
                review
                for review in reviews
                if not review["user"]["login"].endswith("[bot]")
            ]

            # Check for approved reviews
            approved_reviews = [
                review for review in human_reviews if review["state"] == "APPROVED"
            ]

            # Check for requested changes
            requested_changes = [
                review
                for review in human_reviews
                if review["state"] == "CHANGES_REQUESTED"
            ]

            # Get pending review requests
            pending_requests = self._get_pending_review_requests(pr_details)

            # Check AI review completion
            ai_review_complete = self._check_ai_review_completion(pr_number)

            # Calculate review coverage score
            coverage_score = self._calculate_review_coverage(pr_details, human_reviews)

            return ReviewAssessment(
                has_approved_review=len(approved_reviews) > 0,
                pending_requests=pending_requests,
                requested_changes=requested_changes,
                ai_review_complete=ai_review_complete,
                review_coverage_score=coverage_score,
            )

        except Exception as e:
            logger.error(f"Failed to assess review status: {e}")
            return ReviewAssessment(
                has_approved_review=False,
                pending_requests=[],
                requested_changes=[],
                ai_review_complete=False,
                review_coverage_score=0.0,
            )

    def _get_pending_review_requests(self, pr_details: Dict[str, Any]) -> List[str]:
        """Get list of pending review requests."""
        try:
            requested_reviewers = pr_details.get("requested_reviewers", [])
            requested_teams = pr_details.get("requested_teams", [])

            pending = []
            pending.extend([reviewer["login"] for reviewer in requested_reviewers])
            pending.extend([team["name"] for team in requested_teams])

            return pending
        except Exception:
            return []

    def _check_ai_review_completion(self, pr_number: int) -> bool:
        """Check if AI code review (Phase 9) has been completed."""
        try:
            comments = self.github_ops.get_pr_comments(pr_number)

            # Look for code-reviewer agent comments
            ai_review_indicators = [
                "code-reviewer",
                "ai code review",
                "automated review",
                "phase 9",
            ]

            for comment in comments:
                body = comment.get("body", "").lower()
                if any(indicator in body for indicator in ai_review_indicators):
                    return True

            return False
        except Exception:
            return False

    def _calculate_review_coverage(
        self, pr_details: Dict[str, Any], reviews: List[Dict[str, Any]]
    ) -> float:
        """Calculate review coverage score based on changes and reviews."""
        try:
            # Get PR stats
            additions = pr_details.get("additions", 0)
            deletions = pr_details.get("deletions", 0)
            pr_details.get("changed_files", 0)  # Not used currently

            # Calculate change complexity
            total_changes = additions + deletions
            complexity_score = min(100, total_changes / 10)  # Normalize to 0-100

            # Calculate review depth
            review_score = 0
            if reviews:
                review_score = min(100, len(reviews) * 25)  # Up to 4 reviews = 100%

            # Combine scores
            coverage = (review_score * 0.7) + (complexity_score * 0.3)
            return min(100.0, coverage)

        except Exception:
            return 0.0

    def assess_branch_sync(self, pr_details: Dict[str, Any]) -> SyncAssessment:
        """
        Assess branch synchronization with main.

        Args:
            pr_details: PR details from GitHub API

        Returns:
            SyncAssessment with detailed sync analysis
        """
        try:
            base_sha = pr_details["base"]["sha"]
            head_sha = pr_details["head"]["sha"]

            # Compare commits
            comparison = self.github_ops.compare_commits(base_sha, head_sha)

            commits_behind = comparison.get("behind_by", 0)
            commits_ahead = comparison.get("ahead_by", 0)

            # Assess sync complexity
            complexity = self._assess_sync_complexity(comparison)

            # Check last sync time
            last_sync = self._get_last_sync_time(pr_details)

            return SyncAssessment(
                is_up_to_date=commits_behind == 0,
                commits_behind=commits_behind,
                commits_ahead=commits_ahead,
                last_sync=last_sync,
                sync_complexity=complexity,
            )

        except Exception as e:
            logger.error(f"Failed to assess branch sync: {e}")
            return SyncAssessment(
                is_up_to_date=False,
                commits_behind=999,  # Conservative assumption
                commits_ahead=0,
                last_sync=None,
                sync_complexity="complex",
            )

    def _assess_sync_complexity(self, comparison: Dict[str, Any]) -> str:
        """Assess complexity of branch synchronization."""
        try:
            behind_by = comparison.get("behind_by", 0)

            # Get commit details to assess complexity
            commits = comparison.get("commits", [])

            # Check for merge commits in base
            merge_commits = [
                commit for commit in commits if len(commit.get("parents", [])) > 1
            ]

            if behind_by <= 5 and not merge_commits:
                return "simple"
            elif behind_by <= 15 and len(merge_commits) <= 2:
                return "moderate"
            else:
                return "complex"

        except Exception:
            return "complex"

    def _get_last_sync_time(self, pr_details: Dict[str, Any]) -> Optional[datetime]:
        """Get last synchronization time with base branch."""
        try:
            # Use updated_at as proxy for last sync
            updated_at = pr_details.get("updated_at")
            if updated_at:
                return datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            return None
        except Exception:
            return None

    def assess_metadata_completeness(
        self, pr_details: Dict[str, Any]
    ) -> MetadataAssessment:
        """
        Assess PR metadata completeness and quality.

        Args:
            pr_details: PR details from GitHub API

        Returns:
            MetadataAssessment with detailed metadata analysis
        """
        try:
            title = pr_details.get("title", "")
            body = pr_details.get("body", "")
            labels = [label["name"] for label in pr_details.get("labels", [])]

            # Check conventional commit title
            conventional_prefixes = [
                "feat:",
                "fix:",
                "docs:",
                "style:",
                "refactor:",
                "test:",
                "chore:",
                "ci:",
                "build:",
                "perf:",
            ]
            has_conventional_title = any(
                title.lower().startswith(prefix) for prefix in conventional_prefixes
            )

            # Check description quality
            description_length = len(body.strip()) if body else 0
            has_description = (
                description_length >= self.config["min_description_length"]
            )

            # Check for appropriate labels
            expected_label_types = [
                "enhancement",
                "bugfix",
                "documentation",
                "refactor",
                "test",
            ]
            has_appropriate_labels = any(
                label in labels for label in expected_label_types
            )

            # Check for linked issues
            has_linked_issues = self._check_linked_issues(body)

            # Calculate completeness score
            score_components = [
                has_conventional_title,
                has_description,
                has_appropriate_labels,
                has_linked_issues,
            ]
            completeness_score = sum(score_components) / len(score_components) * 100

            return MetadataAssessment(
                has_conventional_title=has_conventional_title,
                has_description=has_description,
                has_appropriate_labels=has_appropriate_labels,
                has_linked_issues=has_linked_issues,
                completeness_score=completeness_score,
            )

        except Exception as e:
            logger.error(f"Failed to assess metadata completeness: {e}")
            return MetadataAssessment(
                has_conventional_title=False,
                has_description=False,
                has_appropriate_labels=False,
                has_linked_issues=False,
                completeness_score=0.0,
            )

    def _check_linked_issues(self, body: str) -> bool:
        """Check if PR body contains linked issues."""
        if not body:
            return False

        # Look for issue references
        issue_patterns = [
            "#",
            "closes #",
            "fixes #",
            "resolves #",
            "issue #",
            "github.com/",
            "issue/",
        ]

        body_lower = body.lower()
        return any(pattern in body_lower for pattern in issue_patterns)

    def get_comprehensive_assessment(
        self, pr_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive readiness assessment for a PR.

        Args:
            pr_details: PR details from GitHub API

        Returns:
            Dictionary with all assessment results
        """
        try:
            conflict_assessment = self.assess_merge_conflicts(pr_details)
            ci_assessment = self.assess_ci_status(pr_details)
            review_assessment = self.assess_review_status(pr_details)
            sync_assessment = self.assess_branch_sync(pr_details)
            metadata_assessment = self.assess_metadata_completeness(pr_details)

            # Calculate overall readiness score
            criteria_scores = [
                100 if not conflict_assessment.has_conflicts else 0,
                100 if ci_assessment.all_passing else 0,
                100 if review_assessment.is_review_complete else 0,
                100 if sync_assessment.is_up_to_date else 0,
                metadata_assessment.completeness_score,
            ]

            overall_score = sum(criteria_scores) / len(criteria_scores)

            return {
                "pr_number": pr_details["number"],
                "overall_score": overall_score,
                "is_ready": overall_score >= 95,  # Require 95% to be considered ready
                "assessments": {
                    "conflicts": conflict_assessment,
                    "ci": ci_assessment,
                    "reviews": review_assessment,
                    "sync": sync_assessment,
                    "metadata": metadata_assessment,
                },
                "blocking_factors": self._identify_blocking_factors(
                    {
                        "conflicts": conflict_assessment,
                        "ci": ci_assessment,
                        "reviews": review_assessment,
                        "sync": sync_assessment,
                        "metadata": metadata_assessment,
                    }
                ),
                "recommendations": self._generate_recommendations(
                    {
                        "conflicts": conflict_assessment,
                        "ci": ci_assessment,
                        "reviews": review_assessment,
                        "sync": sync_assessment,
                        "metadata": metadata_assessment,
                    }
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get comprehensive assessment: {e}")
            return {
                "pr_number": pr_details.get("number", 0),
                "overall_score": 0,
                "is_ready": False,
                "error": str(e),
            }

    def _identify_blocking_factors(self, assessments: Dict[str, Any]) -> List[str]:
        """Identify factors blocking PR readiness."""
        blocking_factors = []

        if assessments["conflicts"].has_conflicts:
            blocking_factors.append(
                f"Merge conflicts ({assessments['conflicts'].complexity.value})"
            )

        if not assessments["ci"].all_passing:
            blocking_factors.append(
                f"CI failures ({len(assessments['ci'].failing_checks)} checks)"
            )

        if not assessments["reviews"].is_review_complete:
            blocking_factors.append("Review incomplete")

        if not assessments["sync"].is_up_to_date:
            blocking_factors.append(
                f"Branch behind by {assessments['sync'].commits_behind} commits"
            )

        if not assessments["metadata"].is_complete:
            blocking_factors.append(
                f"Metadata incomplete ({assessments['metadata'].completeness_score:.0f}%)"
            )

        return blocking_factors

    def _generate_recommendations(self, assessments: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations for PR improvement."""
        recommendations = []

        conflict_assessment = assessments["conflicts"]
        if conflict_assessment.has_conflicts:
            if conflict_assessment.auto_resolvable:
                recommendations.append("Auto-resolve merge conflicts")
            else:
                recommendations.append("Manual conflict resolution required")

        ci_assessment = assessments["ci"]
        if not ci_assessment.all_passing:
            if ci_assessment.can_auto_retry:
                recommendations.append("Retry transient CI failures")
            else:
                recommendations.append("Fix CI failures manually")

        review_assessment = assessments["reviews"]
        if not review_assessment.is_review_complete:
            if not review_assessment.has_approved_review:
                recommendations.append("Request human code review")
            if not review_assessment.ai_review_complete:
                recommendations.append("Invoke AI code review (Phase 9)")

        sync_assessment = assessments["sync"]
        if not sync_assessment.is_up_to_date:
            if sync_assessment.is_auto_updatable:
                recommendations.append("Auto-update branch from main")
            else:
                recommendations.append("Manual branch update required")

        metadata_assessment = assessments["metadata"]
        if not metadata_assessment.is_complete:
            recommendations.append("Improve PR metadata (title, description, labels)")

        return recommendations
