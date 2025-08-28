"""
Tests for PR Readiness Assessor module.

Tests the ReadinessAssessor class and related assessment functionality
including conflict analysis, CI status evaluation, and metadata checking.
"""

import pytest  # type: ignore[import]

from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add the source directories to the Python path for imports
import sys
import os

# Add pr-backlog-manager directory
pr_backlog_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    ".claude",
    "agents",
    "pr-backlog-manager",
)
sys.path.insert(0, pr_backlog_path)

# Add shared directory for interfaces
shared_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    ".claude",
    "shared",
)
sys.path.insert(0, shared_path)

# Always use stubs for readiness assessor tests
from .test_stubs import (
    ReadinessAssessor,
    ConflictAssessment,
    CIAssessment,
    ReviewAssessment,
    SyncAssessment,
    MetadataAssessment,
    ConflictComplexity,
    CIFailureType,
)


@pytest.fixture
def mock_github_ops():
    """Create mock GitHub operations."""
    mock = Mock()
    mock.get_pr_status_checks.return_value = []
    mock.get_pr_reviews.return_value = []
    mock.get_pr_comments.return_value = []
    mock.compare_commits.return_value = {"behind_by": 0, "ahead_by": 1, "commits": []}
    return mock


@pytest.fixture
def assessor(mock_github_ops):
    """Create ReadinessAssessor instance."""
    return ReadinessAssessor(mock_github_ops)


@pytest.fixture
def sample_pr_details():
    """Sample PR details for testing."""
    return {
        "number": 123,
        "title": "feat: add new feature",
        "body": "This PR adds a comprehensive new feature to the system",
        "labels": [{"name": "enhancement"}],
        "mergeable": True,
        "mergeable_state": "clean",
        "base": {"sha": "base123"},
        "head": {"sha": "head123"},
        "additions": 150,
        "deletions": 75,
        "changed_files": 8,
        "updated_at": "2024-01-01T12:00:00Z",
        "requested_reviewers": [],
        "requested_teams": [],
    }


class TestConflictAssessment:
    """Test conflict assessment functionality."""

    def test_assess_merge_conflicts_clean(self, assessor):
        """Test assessment of clean merge."""
        pr_details = {"mergeable": True, "mergeable_state": "clean"}

        assessment = assessor.assess_merge_conflicts(pr_details)

        assert assessment.has_conflicts is False
        assert assessment.complexity == ConflictComplexity.NONE
        assert assessment.auto_resolvable is True
        assert assessment.resolution_estimate == timedelta(0)
        assert assessment.is_blocking is False

    def test_assess_merge_conflicts_dirty(self, assessor):
        """Test assessment of conflicted merge."""
        pr_details = {"mergeable": False, "mergeable_state": "dirty"}

        # Mock conflict file detection
        assessor._get_conflicted_files = Mock(return_value=["file1.py", "file2.js"])

        assessment = assessor.assess_merge_conflicts(pr_details)

        assert assessment.has_conflicts is True
        assert assessment.complexity in [
            ConflictComplexity.LOW,
            ConflictComplexity.MEDIUM,
        ]
        assert len(assessment.affected_files) == 2
        assert assessment.resolution_estimate > timedelta(0)

    def test_assess_merge_conflicts_unknown(self, assessor):
        """Test assessment of unknown merge state."""
        pr_details = {"mergeable": None, "mergeable_state": "unknown"}

        assessment = assessor.assess_merge_conflicts(pr_details)

        # Should assume no conflicts for unknown state
        assert assessment.has_conflicts is False
        assert assessment.complexity == ConflictComplexity.NONE

    def test_assess_conflict_complexity(self, assessor):
        """Test conflict complexity assessment."""
        # No files - no conflicts
        assert assessor._assess_conflict_complexity([]) == ConflictComplexity.NONE

        # Few non-critical files - low complexity
        simple_files = ["src/utils.py", "src/helper.js"]
        assert (
            assessor._assess_conflict_complexity(simple_files) == ConflictComplexity.LOW
        )

        # Critical configuration files - higher complexity
        critical_files = ["package.json", "requirements.txt", "Dockerfile"]
        complexity = assessor._assess_conflict_complexity(critical_files)
        assert complexity in [ConflictComplexity.MEDIUM, ConflictComplexity.HIGH]

        # Many files - high complexity
        many_files = [f"file{i}.py" for i in range(10)]
        assert (
            assessor._assess_conflict_complexity(many_files) == ConflictComplexity.HIGH
        )

    def test_estimate_resolution_time(self, assessor):
        """Test conflict resolution time estimation."""
        # Test all complexity levels
        assert assessor._estimate_resolution_time(ConflictComplexity.NONE) == timedelta(
            0
        )
        assert assessor._estimate_resolution_time(ConflictComplexity.LOW) == timedelta(
            minutes=15
        )
        assert assessor._estimate_resolution_time(
            ConflictComplexity.MEDIUM
        ) == timedelta(minutes=45)
        assert assessor._estimate_resolution_time(ConflictComplexity.HIGH) == timedelta(
            hours=2
        )


class TestCIAssessment:
    """Test CI/CD assessment functionality."""

    def test_assess_ci_status_all_passing(
        self, assessor, mock_github_ops, sample_pr_details
    ):
        """Test CI assessment with all checks passing."""
        mock_github_ops.get_pr_status_checks.return_value = [
            {
                "state": "success",
                "context": "ci/test",
                "updated_at": "2024-01-01T12:00:00Z",
            },
            {
                "state": "success",
                "context": "ci/build",
                "updated_at": "2024-01-01T12:05:00Z",
            },
        ]

        assessment = assessor.assess_ci_status(sample_pr_details)

        assert assessment.all_passing is True
        assert len(assessment.failing_checks) == 0
        assert len(assessment.retriable_failures) == 0
        assert len(assessment.blocking_failures) == 0
        assert assessment.can_auto_retry is False  # No failures to retry
        assert assessment.last_run is not None  # type: ignore[union-attr]

    def test_assess_ci_status_with_failures(
        self, assessor, mock_github_ops, sample_pr_details
    ):
        """Test CI assessment with some failures."""
        mock_github_ops.get_pr_status_checks.return_value = [
            {
                "state": "success",
                "context": "ci/test",
                "updated_at": "2024-01-01T12:00:00Z",
            },
            {
                "state": "failure",
                "context": "ci/build",
                "description": "Build failed due to timeout",
                "updated_at": "2024-01-01T12:05:00Z",
            },
            {
                "state": "error",
                "context": "ci/lint",
                "description": "Linting errors found",
                "updated_at": "2024-01-01T12:03:00Z",
            },
        ]

        assessment = assessor.assess_ci_status(sample_pr_details)

        assert assessment.all_passing is False
        assert len(assessment.failing_checks) == 2
        assert len(assessment.retriable_failures) == 1  # Timeout is retriable
        assert len(assessment.blocking_failures) == 1  # Lint error is blocking
        assert assessment.can_auto_retry is False  # Has blocking failures

    def test_classify_ci_failure(self, assessor):
        """Test CI failure classification."""
        # Transient failure
        timeout_check = {
            "description": "Build failed due to timeout",
            "context": "ci/build",
        }
        assert assessor._classify_ci_failure(timeout_check) == CIFailureType.TRANSIENT

        # Build failure
        build_check = {"description": "Compilation error", "context": "build/compile"}
        assert assessor._classify_ci_failure(build_check) == CIFailureType.BUILD_FAILURE

        # Test failure
        test_check = {"description": "Unit tests failed", "context": "test/unit"}
        assert assessor._classify_ci_failure(test_check) == CIFailureType.TEST_FAILURE

        # Lint failure
        lint_check = {"description": "Code style violations", "context": "lint/eslint"}
        assert assessor._classify_ci_failure(lint_check) == CIFailureType.LINT_FAILURE

        # Security failure
        security_check = {
            "description": "Vulnerability detected",
            "context": "security/scan",
        }
        assert (
            assessor._classify_ci_failure(security_check)
            == CIFailureType.SECURITY_FAILURE
        )

        # Unknown failure
        unknown_check = {
            "description": "Something went wrong",
            "context": "unknown/check",
        }
        assert assessor._classify_ci_failure(unknown_check) == CIFailureType.UNKNOWN


class TestReviewAssessment:
    """Test code review assessment functionality."""

    def test_assess_review_status_complete(
        self, assessor, mock_github_ops, sample_pr_details
    ):
        """Test review assessment with complete reviews."""
        mock_github_ops.get_pr_reviews.return_value = [
            {"user": {"login": "human-reviewer"}, "state": "APPROVED"},
            {"user": {"login": "another-reviewer"}, "state": "COMMENTED"},
            {
                "user": {"login": "bot[bot]"},
                "state": "APPROVED",
            },  # Should be filtered out
        ]

        mock_github_ops.get_pr_comments.return_value = [
            {"body": "This looks good. Code-reviewer analysis complete."}
        ]

        assessment = assessor.assess_review_status(sample_pr_details)

        assert assessment.has_approved_review is True
        assert assessment.ai_review_complete is True
        assert len(assessment.requested_changes) == 0
        assert len(assessment.pending_requests) == 0
        assert assessment.is_review_complete is True
        assert assessment.review_coverage_score > 0

    def test_assess_review_status_incomplete(
        self, assessor, mock_github_ops, sample_pr_details
    ):
        """Test review assessment with incomplete reviews."""
        mock_github_ops.get_pr_reviews.return_value = [
            {"user": {"login": "human-reviewer"}, "state": "CHANGES_REQUESTED"}
        ]

        mock_github_ops.get_pr_comments.return_value = [
            {"body": "Just a regular comment"}
        ]

        # Add pending review requests
        sample_pr_details["requested_reviewers"] = [{"login": "pending-reviewer"}]
        sample_pr_details["requested_teams"] = [{"name": "team-review"}]

        assessment = assessor.assess_review_status(sample_pr_details)

        assert assessment.has_approved_review is False
        assert assessment.ai_review_complete is False
        assert len(assessment.requested_changes) == 1
        assert len(assessment.pending_requests) == 2  # One reviewer + one team
        assert assessment.is_review_complete is False

    def test_check_ai_review_completion(self, assessor, mock_github_ops):
        """Test AI review completion detection."""
        # AI review present
        mock_github_ops.get_pr_comments.return_value = [
            {"body": "Human comment about the changes"},
            {"body": "Automated review by code-reviewer: This PR looks good"},
            {"body": "Another human comment"},
        ]
        assert assessor._check_ai_review_completion(123) is True

        # No AI review
        mock_github_ops.get_pr_comments.return_value = [
            {"body": "Human comment about the changes"},
            {"body": "Another human comment"},
        ]
        assert assessor._check_ai_review_completion(123) is False

        # AI review with different indicators
        mock_github_ops.get_pr_comments.return_value = [
            {"body": "Phase 9 automated review completed successfully"}
        ]
        assert assessor._check_ai_review_completion(123) is True

    def test_calculate_review_coverage(self, assessor):
        """Test review coverage calculation."""
        pr_details = {"additions": 100, "deletions": 50, "changed_files": 5}

        # Single review
        single_review = [{"user": {"login": "reviewer1"}}]
        coverage = assessor._calculate_review_coverage(pr_details, single_review)
        assert 0 < coverage < 100

        # Multiple reviews
        multiple_reviews = [
            {"user": {"login": "reviewer1"}},
            {"user": {"login": "reviewer2"}},
            {"user": {"login": "reviewer3"}},
            {"user": {"login": "reviewer4"}},
        ]
        coverage_multiple = assessor._calculate_review_coverage(
            pr_details, multiple_reviews
        )
        assert coverage_multiple > coverage
        assert coverage_multiple <= 100

        # No reviews
        no_reviews = []
        coverage_none = assessor._calculate_review_coverage(pr_details, no_reviews)
        assert coverage_none < coverage


class TestSyncAssessment:
    """Test branch synchronization assessment functionality."""

    def test_assess_branch_sync_up_to_date(
        self, assessor, mock_github_ops, sample_pr_details
    ):
        """Test branch sync assessment for up-to-date branch."""
        mock_github_ops.compare_commits.return_value = {
            "behind_by": 0,
            "ahead_by": 3,
            "commits": [],
        }

        assessment = assessor.assess_branch_sync(sample_pr_details)

        assert assessment.is_up_to_date is True
        assert assessment.commits_behind == 0
        assert assessment.commits_ahead == 3
        assert assessment.requires_update is False
        assert assessment.is_auto_updatable is True  # No commits behind
        assert assessment.sync_complexity == "simple"

    def test_assess_branch_sync_behind(
        self, assessor, mock_github_ops, sample_pr_details
    ):
        """Test branch sync assessment for branch behind main."""
        mock_github_ops.compare_commits.return_value = {
            "behind_by": 5,
            "ahead_by": 2,
            "commits": [
                {"parents": ["parent1"]},  # Regular commit
                {"parents": ["parent1"]},  # Regular commit
                {"parents": ["parent1", "parent2"]},  # Merge commit
            ],
        }

        assessment = assessor.assess_branch_sync(sample_pr_details)

        assert assessment.is_up_to_date is False
        assert assessment.commits_behind == 5
        assert assessment.commits_ahead == 2
        assert assessment.requires_update is True
        assert (
            assessment.is_auto_updatable is False
        )  # complexity is moderate, not simple
        assert assessment.sync_complexity == "moderate"  # Has merge commit

    def test_assess_branch_sync_far_behind(
        self, assessor, mock_github_ops, sample_pr_details
    ):
        """Test branch sync assessment for branch far behind main."""
        mock_github_ops.compare_commits.return_value = {
            "behind_by": 25,
            "ahead_by": 1,
            "commits": [
                {"parents": ["p1", "p2"]} for _ in range(10)
            ],  # Many merge commits
        }

        assessment = assessor.assess_branch_sync(sample_pr_details)

        assert assessment.is_up_to_date is False
        assert assessment.commits_behind == 25
        assert assessment.requires_update is True
        assert assessment.is_auto_updatable is False  # > 10 commits behind
        assert assessment.sync_complexity == "complex"  # Many commits and merges

    def test_assess_sync_complexity(self, assessor):
        """Test sync complexity assessment."""
        # Simple sync
        simple_comparison = {
            "behind_by": 3,
            "commits": [
                {"parents": ["parent1"]},
                {"parents": ["parent2"]},
                {"parents": ["parent3"]},
            ],
        }
        assert assessor._assess_sync_complexity(simple_comparison) == "simple"

        # Moderate sync
        moderate_comparison = {
            "behind_by": 8,
            "commits": [
                {"parents": ["parent1"]},
                {"parents": ["parent1", "parent2"]},  # One merge commit
                {"parents": ["parent3"]},
            ],
        }
        assert assessor._assess_sync_complexity(moderate_comparison) == "moderate"

        # Complex sync
        complex_comparison = {
            "behind_by": 20,
            "commits": [
                {"parents": ["p1", "p2"]},
                {"parents": ["p2", "p3"]},
                {"parents": ["p3", "p4"]},
            ],
        }
        assert assessor._assess_sync_complexity(complex_comparison) == "complex"


class TestMetadataAssessment:
    """Test metadata completeness assessment functionality."""

    def test_assess_metadata_complete(self, assessor):
        """Test metadata assessment for complete metadata."""
        complete_pr = {
            "title": "feat: add new user authentication system",
            "body": "This PR implements a comprehensive user authentication system with OAuth2 support.",
            "labels": [{"name": "enhancement"}, {"name": "security"}],
        }

        assessment = assessor.assess_metadata_completeness(complete_pr)

        assert assessment.has_conventional_title is True
        assert assessment.has_description is True
        assert assessment.has_appropriate_labels is True
        assert assessment.has_linked_issues is False  # No issue references in body
        assert assessment.is_complete is True
        assert assessment.completeness_score >= 75  # Should be high

    def test_assess_metadata_incomplete(self, assessor):
        """Test metadata assessment for incomplete metadata."""
        incomplete_pr = {
            "title": "update user stuff",  # No conventional prefix
            "body": "changes",  # Too short
            "labels": [],  # No labels
        }

        assessment = assessor.assess_metadata_completeness(incomplete_pr)

        assert assessment.has_conventional_title is False
        assert assessment.has_description is False
        assert assessment.has_appropriate_labels is False
        assert assessment.is_complete is False
        assert assessment.completeness_score < 50

    def test_assess_metadata_with_issue_links(self, assessor):
        """Test metadata assessment with issue links."""
        linked_pr = {
            "title": "fix: resolve authentication bug",
            "body": "This PR fixes the authentication issue described in #123. Closes #456.",
            "labels": [{"name": "bugfix"}],
        }

        assessment = assessor.assess_metadata_completeness(linked_pr)

        assert assessment.has_linked_issues is True
        assert assessment.completeness_score == 100.0

    def test_check_linked_issues(self, assessor):
        """Test issue linking detection."""
        # Various issue reference formats
        assert assessor._check_linked_issues("Fixes #123") is True
        assert assessor._check_linked_issues("Closes #456") is True
        assert assessor._check_linked_issues("Resolves #789") is True
        assert assessor._check_linked_issues("See issue #321") is True
        assert (
            assessor._check_linked_issues("https://github.com/user/repo/issues/123")
            is True
        )

        # No issue references
        assert assessor._check_linked_issues("Just a regular description") is False
        assert assessor._check_linked_issues("") is False
        assert assessor._check_linked_issues(None) is False


class TestComprehensiveAssessment:
    """Test comprehensive assessment functionality."""

    def test_get_comprehensive_assessment_ready(
        self, assessor, mock_github_ops, sample_pr_details
    ):
        """Test comprehensive assessment for ready PR."""
        # Mock all individual assessments to return positive results
        with (
            patch.object(assessor, "assess_merge_conflicts") as mock_conflicts,
            patch.object(assessor, "assess_ci_status") as mock_ci,
            patch.object(assessor, "assess_review_status") as mock_reviews,
            patch.object(assessor, "assess_branch_sync") as mock_sync,
            patch.object(assessor, "assess_metadata_completeness") as mock_metadata,
        ):
            mock_conflicts.return_value = ConflictAssessment(
                has_conflicts=False,
                affected_files=[],
                complexity=ConflictComplexity.NONE,
                resolution_estimate=timedelta(0),
                auto_resolvable=True,
            )
            mock_ci.return_value = CIAssessment(
                all_passing=True,
                failing_checks=[],
                retriable_failures=[],
                blocking_failures=[],
                last_run=datetime.now(),
            )
            mock_reviews.return_value = ReviewAssessment(
                has_approved_review=True,
                pending_requests=[],
                requested_changes=[],
                ai_review_complete=True,
                review_coverage_score=95.0,
            )
            mock_sync.return_value = SyncAssessment(
                is_up_to_date=True,
                commits_behind=0,
                commits_ahead=2,
                last_sync=datetime.now(),
                sync_complexity="simple",
            )
            mock_metadata.return_value = MetadataAssessment(
                has_conventional_title=True,
                has_description=True,
                has_appropriate_labels=True,
                has_linked_issues=True,
                completeness_score=100.0,
            )

            result = assessor.get_comprehensive_assessment(sample_pr_details)

            assert result["pr_number"] == 123  # type: ignore[index]
            assert result["overall_score"] == 100.0  # type: ignore[index]
            assert result["is_ready"] is True  # type: ignore[index]
            assert len(result["blocking_factors"]) == 0  # type: ignore[index]
            assert len(result["recommendations"]) == 0  # type: ignore[index]

    def test_get_comprehensive_assessment_blocked(
        self, assessor, mock_github_ops, sample_pr_details
    ):
        """Test comprehensive assessment for blocked PR."""
        # Mock assessments with some failures
        with (
            patch.object(assessor, "assess_merge_conflicts") as mock_conflicts,
            patch.object(assessor, "assess_ci_status") as mock_ci,
            patch.object(assessor, "assess_review_status") as mock_reviews,
            patch.object(assessor, "assess_branch_sync") as mock_sync,
            patch.object(assessor, "assess_metadata_completeness") as mock_metadata,
        ):
            mock_conflicts.return_value = ConflictAssessment(
                has_conflicts=True,
                affected_files=["file1.py"],
                complexity=ConflictComplexity.MEDIUM,
                resolution_estimate=timedelta(minutes=30),
                auto_resolvable=False,
            )
            mock_ci.return_value = CIAssessment(
                all_passing=False,
                failing_checks=[{"context": "ci/test"}],
                retriable_failures=[],
                blocking_failures=["ci/test"],
                last_run=datetime.now(),
            )
            mock_reviews.return_value = ReviewAssessment(
                has_approved_review=False,
                pending_requests=["reviewer1"],
                requested_changes=[],
                ai_review_complete=False,
                review_coverage_score=30.0,
            )
            mock_sync.return_value = SyncAssessment(
                is_up_to_date=False,
                commits_behind=5,
                commits_ahead=2,
                last_sync=datetime.now(),
                sync_complexity="moderate",
            )
            mock_metadata.return_value = MetadataAssessment(
                has_conventional_title=False,
                has_description=True,
                has_appropriate_labels=False,
                has_linked_issues=False,
                completeness_score=40.0,
            )

            result = assessor.get_comprehensive_assessment(sample_pr_details)

            assert result["pr_number"] == 123  # type: ignore[index]
            assert result["overall_score"] < 95  # Should be below ready threshold  # type: ignore[index]
            assert result["is_ready"] is False  # type: ignore[index]
            assert len(result["blocking_factors"]) > 0  # type: ignore[index]
            assert len(result["recommendations"]) > 0  # type: ignore[index]

            # Check specific blocking factors
            blocking_factors = result["blocking_factors"]
            assert any("conflict" in factor.lower() for factor in blocking_factors)
            assert any("ci failure" in factor.lower() for factor in blocking_factors)
            assert any(
                "review incomplete" in factor.lower() for factor in blocking_factors
            )

    def test_identify_blocking_factors(self, assessor):
        """Test blocking factor identification."""
        assessments = {
            "conflicts": ConflictAssessment(
                has_conflicts=True,
                affected_files=[],
                complexity=ConflictComplexity.HIGH,
                resolution_estimate=timedelta(0),
                auto_resolvable=False,
            ),
            "ci": CIAssessment(
                all_passing=False,
                failing_checks=[{}, {}],
                retriable_failures=[],
                blocking_failures=[],
                last_run=None,
            ),
            "reviews": ReviewAssessment(
                has_approved_review=False,
                pending_requests=[],
                requested_changes=[],
                ai_review_complete=True,
                review_coverage_score=0,
            ),
            "sync": SyncAssessment(
                is_up_to_date=False,
                commits_behind=15,
                commits_ahead=0,
                last_sync=None,
                sync_complexity="complex",
            ),
            "metadata": MetadataAssessment(
                has_conventional_title=True,
                has_description=False,
                has_appropriate_labels=True,
                has_linked_issues=False,
                completeness_score=60.0,
            ),
        }

        blocking_factors = assessor._identify_blocking_factors(assessments)

        assert len(blocking_factors) == 5  # All aspects have issues
        assert any("conflict" in factor.lower() for factor in blocking_factors)
        assert any("ci failure" in factor.lower() for factor in blocking_factors)
        assert any("review incomplete" in factor.lower() for factor in blocking_factors)
        assert any("behind by 15" in factor for factor in blocking_factors)
        assert any(
            "metadata incomplete" in factor.lower() for factor in blocking_factors
        )

    def test_generate_recommendations(self, assessor):
        """Test recommendation generation."""
        assessments = {
            "conflicts": ConflictAssessment(
                has_conflicts=True,
                affected_files=[],
                complexity=ConflictComplexity.LOW,
                resolution_estimate=timedelta(0),
                auto_resolvable=True,
            ),
            "ci": CIAssessment(
                all_passing=False,
                failing_checks=[],
                retriable_failures=["test"],
                blocking_failures=[],
                last_run=None,
            ),
            "reviews": ReviewAssessment(
                has_approved_review=False,
                pending_requests=[],
                requested_changes=[],
                ai_review_complete=False,
                review_coverage_score=0,
            ),
            "sync": SyncAssessment(
                is_up_to_date=False,
                commits_behind=3,
                commits_ahead=0,
                last_sync=None,
                sync_complexity="simple",
            ),
            "metadata": MetadataAssessment(
                has_conventional_title=False,
                has_description=False,
                has_appropriate_labels=False,
                has_linked_issues=False,
                completeness_score=20.0,
            ),
        }

        recommendations = assessor._generate_recommendations(assessments)

        assert len(recommendations) >= 5
        assert any(
            "auto-resolve" in rec.lower() for rec in recommendations
        )  # Auto-resolvable conflicts
        assert any(
            "retry" in rec.lower() for rec in recommendations
        )  # Retriable CI failures
        assert any(
            "human code review" in rec.lower() for rec in recommendations
        )  # Missing human review
        assert any(
            "ai code review" in rec.lower() for rec in recommendations
        )  # Missing AI review
        assert any(
            "auto-update" in rec.lower() for rec in recommendations
        )  # Auto-updatable branch
        assert any(
            "metadata" in rec.lower() for rec in recommendations
        )  # Incomplete metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
