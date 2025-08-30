"""
Test suite for System Design Reviewer Core functionality

Tests the main reviewer implementation, PR analysis, documentation updates,
and GitHub integration.
"""

import pytest
import tempfile
import json
from unittest.mock import Mock, patch
from datetime import datetime
from pathlib import Path
import sys

# Add .claude directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / ".gadugi"))

from agents.system_design_reviewer.core import (
    SystemDesignReviewer,
    ReviewResult,
    ReviewStatus,
    SystemDesignStateManager,
)
from agents.system_design_reviewer.ast_parser import (
    ArchitecturalChange,
    ArchitecturalElement,
    ElementType,
    ChangeType,
    ImpactLevel,
)


@pytest.fixture
def mock_pr_info():
    """Mock PR information for testing"""
    return {
        "number": "123",
        "title": "Add new service architecture",
        "body": "This PR adds a new service architecture\n\nCloses #456",
        "author": {"login": "developer"},
        "baseRefName": "main",
        "headRefName": "feature/new-service",
        "changed_files": [
            "src/services/new_service.py",
            "src/services/__init__.py",
            "tests/test_new_service.py",
        ],
    }


@pytest.fixture
def sample_architectural_changes():
    """Sample architectural changes for testing"""
    return [
        ArchitecturalChange(
            change_type=ChangeType.ADDED,
            element=ArchitecturalElement(
                element_type=ElementType.CLASS,
                name="NewService",
                location="src/services/new_service.py:10",
                patterns=["singleton"],
                is_public=True,
            ),
            impact_level=ImpactLevel.HIGH,
            design_implications=["Introduces new service architecture"],
            requires_adr=True,
        ),
        ArchitecturalChange(
            change_type=ChangeType.MODIFIED,
            element=ArchitecturalElement(
                element_type=ElementType.FUNCTION,
                name="init_services",
                location="src/services/__init__.py:5",
                dependencies=["NewService"],
            ),
            impact_level=ImpactLevel.MEDIUM,
            design_implications=["Service initialization order changed"],
        ),
    ]


class TestSystemDesignReviewer:
    """Test the main System Design Reviewer class"""

    def test_initialization(self):
        """Test reviewer initialization"""
        reviewer = SystemDesignReviewer()

        assert reviewer is not None  # type: ignore[comparison-overlap]
        assert reviewer.github_ops is not None  # type: ignore[union-attr]
        assert reviewer.state_manager is not None  # type: ignore[union-attr]
        assert reviewer.error_handler is not None  # type: ignore[union-attr]
        assert reviewer.task_tracker is not None  # type: ignore[union-attr]
        assert reviewer.ast_parser_factory is not None  # type: ignore[union-attr]
        assert reviewer.documentation_manager is not None  # type: ignore[union-attr]
        assert reviewer.adr_generator is not None  # type: ignore[union-attr]

    def test_initialization_with_config(self):
        """Test reviewer initialization with custom config"""
        config = {
            "max_pr_size": 500,
            "analysis_timeout": 600,
            "enable_adr": False,
            "enable_doc_updates": False,
        }

        reviewer = SystemDesignReviewer(config)

        assert reviewer.max_pr_size == 500
        assert reviewer.analysis_timeout == 600
        assert not reviewer.enable_adr_generation
        assert not reviewer.enable_doc_updates

    @patch("subprocess.run")
    def test_get_pr_info_success(self, mock_subprocess, mock_pr_info):
        """Test successful PR information retrieval"""
        # Mock GitHub CLI response
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = json.dumps(mock_pr_info)

        reviewer = SystemDesignReviewer()

        with patch.object(
            reviewer, "_get_changed_files", return_value=mock_pr_info["changed_files"]
        ):
            result = reviewer._get_pr_info("123")

        assert result["number"] == "123"  # type: ignore[index]
        assert result["title"] == "Add new service architecture"  # type: ignore[index]
        assert "changed_files" in result
        assert len(result["changed_files"]) == 3  # type: ignore[index]

    @patch("subprocess.run")
    def test_get_pr_info_failure(self, mock_subprocess):
        """Test PR information retrieval failure"""
        # Mock GitHub CLI failure
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "PR not found"

        reviewer = SystemDesignReviewer()
        result = reviewer._get_pr_info("999")

        # The method still returns a dict with changed_files even on failure
        assert "changed_files" in result
        assert result["changed_files"] == []  # type: ignore[index]

    @patch("subprocess.run")
    def test_get_changed_files_success(self, mock_subprocess):
        """Test successful changed files retrieval"""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "file1.py\nfile2.py\nfile3.js\n"

        reviewer = SystemDesignReviewer()
        files = reviewer._get_changed_files("123")

        assert files == ["file1.py", "file2.py", "file3.js"]

    @patch("subprocess.run")
    def test_get_changed_files_failure(self, mock_subprocess):
        """Test changed files retrieval failure"""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Error"

        reviewer = SystemDesignReviewer()
        files = reviewer._get_changed_files("123")

        assert files == []

    def test_analyze_pr_changes_supported_files(self, mock_pr_info):
        """Test PR changes analysis with supported file types"""
        reviewer = SystemDesignReviewer()

        # Mock file analysis
        with patch.object(reviewer, "_analyze_file_changes") as mock_analyze:
            mock_analyze.return_value = [
                ArchitecturalChange(
                    change_type=ChangeType.ADDED,
                    element=ArchitecturalElement(
                        element_type=ElementType.CLASS,
                        name="TestClass",
                        location="test.py:1",
                    ),
                    impact_level=ImpactLevel.MEDIUM,
                )
            ]

            changes = reviewer._analyze_pr_changes("123", mock_pr_info)

            # Should analyze Python files
            assert len(changes) > 0
            assert mock_analyze.call_count >= 1

    def test_analyze_pr_changes_large_pr(self, mock_pr_info):
        """Test PR changes analysis with large PR"""
        reviewer = SystemDesignReviewer()
        reviewer.max_pr_size = 2  # Set low limit for testing

        # Mock many changed files
        large_pr_info = mock_pr_info.copy()
        large_pr_info["changed_files"] = [f"file{i}.py" for i in range(10)]

        with patch.object(reviewer, "_analyze_file_changes") as mock_analyze:
            mock_analyze.return_value = []

            reviewer._analyze_pr_changes("123", large_pr_info)

            # Should only analyze first 2 files
            assert mock_analyze.call_count == 2

    def test_assess_overall_impact_no_changes(self):
        """Test overall impact assessment with no changes"""
        reviewer = SystemDesignReviewer()
        impact = reviewer._assess_overall_impact([])

        assert impact == ImpactLevel.LOW

    def test_assess_overall_impact_critical_changes(self, sample_architectural_changes):
        """Test overall impact assessment with critical changes"""
        reviewer = SystemDesignReviewer()

        # Add critical change
        critical_change = ArchitecturalChange(
            change_type=ChangeType.REMOVED,
            element=ArchitecturalElement(
                element_type=ElementType.CLASS,
                name="CriticalService",
                location="test.py:1",
            ),
            impact_level=ImpactLevel.CRITICAL,
        )

        changes = sample_architectural_changes + [critical_change]
        impact = reviewer._assess_overall_impact(changes)

        assert impact == ImpactLevel.CRITICAL

    def test_assess_overall_impact_multiple_high(self, sample_architectural_changes):
        """Test overall impact assessment with multiple high impact changes"""
        reviewer = SystemDesignReviewer()

        # Add more high impact changes
        high_changes = [
            ArchitecturalChange(
                change_type=ChangeType.ADDED,
                element=ArchitecturalElement(
                    element_type=ElementType.CLASS,
                    name=f"HighImpactClass{i}",
                    location=f"test{i}.py:1",
                ),
                impact_level=ImpactLevel.HIGH,
            )
            for i in range(3)
        ]

        changes = sample_architectural_changes + high_changes
        impact = reviewer._assess_overall_impact(changes)

        assert impact == ImpactLevel.HIGH

    def test_generate_review_comments_low_impact(self):
        """Test review comment generation for low impact changes"""
        reviewer = SystemDesignReviewer()

        low_impact_change = ArchitecturalChange(
            change_type=ChangeType.MODIFIED,
            element=ArchitecturalElement(
                element_type=ElementType.FUNCTION,
                name="helper_function",
                location="utils.py:10",
            ),
            impact_level=ImpactLevel.LOW,
        )

        comments = reviewer._generate_review_comments([low_impact_change], ImpactLevel.LOW)

        assert len(comments) > 0
        comment_text = "\n".join(comments)
        assert "Low" in comment_text
        assert "helper_function" in comment_text

    def test_generate_review_comments_high_impact(self, sample_architectural_changes):
        """Test review comment generation for high impact changes"""
        reviewer = SystemDesignReviewer()

        comments = reviewer._generate_review_comments(
            sample_architectural_changes, ImpactLevel.HIGH
        )

        assert len(comments) > 0
        comment_text = "\n".join(comments)
        assert "High" in comment_text
        assert "NewService" in comment_text
        assert "review required" in comment_text.lower()

    def test_build_review_body_comprehensive(self, sample_architectural_changes):
        """Test comprehensive review body building"""
        reviewer = SystemDesignReviewer()

        # Add affected components to the changes for testing
        sample_architectural_changes[0].affected_components = [
            "ServiceModule",
            "InitializationModule",
        ]
        sample_architectural_changes[1].affected_components = ["ServiceRegistry"]

        review_comments = ["Test comment 1", "Test comment 2"]
        doc_updates = ["Updated ARCHITECTURE.md"]
        adrs_generated = ["ADR-001-new-service.md"]

        body = reviewer._build_review_body(
            ImpactLevel.HIGH,
            sample_architectural_changes,
            doc_updates,
            adrs_generated,
            review_comments,
        )

        assert "System Design Review Summary" in body
        assert "High" in body
        assert "Test comment 1" in body
        assert "Documentation Updates" in body
        assert "Architecture Decision Records" in body
        assert "Affected Components" in body

    def test_update_metrics(self):
        """Test metrics updating"""
        reviewer = SystemDesignReviewer()

        # Create sample result
        result = ReviewResult(
            pr_number="123",
            status=ReviewStatus.COMPLETED,
            architectural_impact=ImpactLevel.MEDIUM,
            changes_detected=[],
            documentation_updates=[],
            adrs_generated=["ADR-001.md"],
            review_comments=[],
            performance_metrics={"review_time_seconds": 30},
            timestamp=datetime.now(),
        )

        initial_count = reviewer.performance_metrics["reviews_completed"]
        reviewer._update_metrics(result)

        assert reviewer.performance_metrics["reviews_completed"] == initial_count + 1  # type: ignore[index]
        assert reviewer.performance_metrics["adrs_generated"] == 1  # type: ignore[index]
        assert reviewer.performance_metrics["average_review_time"] == 30  # type: ignore[index]

    @patch("subprocess.run")
    def test_get_file_content_at_base_success(self, mock_subprocess):
        """Test successful file content retrieval at base branch"""
        # Mock gh pr view
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout='{"baseRefName": "main"}'),  # PR info
            Mock(returncode=0, stdout="file content here"),  # git show
        ]

        reviewer = SystemDesignReviewer()
        content = reviewer._get_file_content_at_base("test.py", "123")

        assert content == "file content here"

    @patch("subprocess.run")
    def test_get_file_content_at_base_file_not_exist(self, mock_subprocess):
        """Test file content retrieval when file doesn't exist in base"""
        # Mock gh pr view success, git show failure
        mock_subprocess.side_effect = [
            Mock(returncode=0, stdout='{"baseRefName": "main"}'),
            Mock(returncode=1, stderr="file not found"),
        ]

        reviewer = SystemDesignReviewer()
        content = reviewer._get_file_content_at_base("new_file.py", "123")

        assert content is None


class TestSystemDesignStateManager:
    """Test the state manager for system design reviewer"""

    def test_initialization(self):
        """Test state manager initialization"""
        manager = SystemDesignStateManager()

        assert manager.state_dir.name == "SystemDesignReviewer"
        assert manager.task_id == "SystemDesignReviewer"

    def test_get_default_state(self):
        """Test default state structure"""
        manager = SystemDesignStateManager()
        state = manager.get_default_state()

        assert "active_reviews" in state
        assert "completed_reviews" in state
        assert "performance_metrics" in state
        assert "configuration" in state

        # Check configuration defaults
        config = state["configuration"]
        assert config["enable_adr_generation"] is True  # type: ignore[index]
        assert config["enable_doc_updates"] is True  # type: ignore[index]
        assert config["max_pr_size"] == 1000  # type: ignore[index]

    def test_save_and_load_state(self):
        """Test state saving and loading"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SystemDesignStateManager()
            manager.state_dir = Path(temp_dir)
            manager.state_file = manager.state_dir / "test_state.json"

            # Save state
            test_state = {"test_key": "test_value", "number": 42}
            success = manager.save_state(test_state)
            assert success

            # Load state
            loaded_state = manager.load_state()
            assert loaded_state["test_key"] == "test_value"  # type: ignore[index]
            assert loaded_state["number"] == 42  # type: ignore[index]
            assert "last_updated" in loaded_state
            assert "task_id" in loaded_state

    def test_save_review_result(self):
        """Test saving review results"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SystemDesignStateManager()
            manager.state_dir = Path(temp_dir)
            manager.state_file = manager.state_dir / "test_state.json"

            # Create sample result
            result = ReviewResult(
                pr_number="123",
                status=ReviewStatus.COMPLETED,
                architectural_impact=ImpactLevel.MEDIUM,
                changes_detected=[],
                documentation_updates=[],
                adrs_generated=[],
                review_comments=[],
                performance_metrics={},
                timestamp=datetime.now(),
            )

            # Save result
            success = manager.save_review_result(result)
            assert success

            # Verify it was saved
            state = manager.load_state()
            assert len(state["completed_reviews"]) == 1  # type: ignore[index]
            assert state["completed_reviews"][0]["pr_number"] == "123"  # type: ignore[index]

    def test_save_review_result_limit(self):
        """Test review result limit (keeps last 100)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = SystemDesignStateManager()
            manager.state_dir = Path(temp_dir)
            manager.state_file = manager.state_dir / "test_state.json"

            # Create initial state with many reviews
            initial_state = manager.get_default_state()
            initial_state["completed_reviews"] = [
                {"pr_number": str(i), "timestamp": datetime.now().isoformat()} for i in range(105)
            ]
            manager.save_state(initial_state)

            # Add one more review
            result = ReviewResult(
                pr_number="new",
                status=ReviewStatus.COMPLETED,
                architectural_impact=ImpactLevel.LOW,
                changes_detected=[],
                documentation_updates=[],
                adrs_generated=[],
                review_comments=[],
                performance_metrics={},
                timestamp=datetime.now(),
            )

            manager.save_review_result(result)

            # Should keep only last 100
            state = manager.load_state()
            assert len(state["completed_reviews"]) == 100  # type: ignore[index]
            assert state["completed_reviews"][-1]["pr_number"] == "new"  # type: ignore[index]


class TestReviewResult:
    """Test the ReviewResult data structure"""

    def test_review_result_creation(self):
        """Test creating a review result"""
        timestamp = datetime.now()

        result = ReviewResult(
            pr_number="123",
            status=ReviewStatus.COMPLETED,
            architectural_impact=ImpactLevel.HIGH,
            changes_detected=[],
            documentation_updates=["doc1.md"],
            adrs_generated=["adr1.md"],
            review_comments=["comment1"],
            performance_metrics={"time": 30},
            timestamp=timestamp,
        )

        assert result.pr_number == "123"
        assert result is not None  # type: ignore[comparison-overlap] and result.status == ReviewStatus.COMPLETED
        assert result.architectural_impact == ImpactLevel.HIGH
        assert len(result.documentation_updates) == 1
        assert len(result.adrs_generated) == 1
        assert len(result.review_comments) == 1
        assert result.timestamp == timestamp

    def test_review_result_to_dict(self):
        """Test converting review result to dictionary"""
        result = ReviewResult(
            pr_number="123",
            status=ReviewStatus.COMPLETED,
            architectural_impact=ImpactLevel.MEDIUM,
            changes_detected=[
                ArchitecturalChange(
                    change_type=ChangeType.ADDED,
                    element=ArchitecturalElement(
                        element_type=ElementType.CLASS,
                        name="TestClass",
                        location="test.py:1",
                    ),
                    impact_level=ImpactLevel.MEDIUM,
                )
            ],
            documentation_updates=[],
            adrs_generated=[],
            review_comments=[],
            performance_metrics={},
            timestamp=datetime.now(),
        )

        result_dict = result.to_dict()

        assert result_dict["pr_number"] == "123"  # type: ignore[index]
        assert result_dict["status"] == ReviewStatus.COMPLETED  # type: ignore[index]
        assert result_dict["architectural_impact"] == ImpactLevel.MEDIUM  # type: ignore[index]
        assert len(result_dict["changes_detected"]) == 1  # type: ignore[index]
        assert "timestamp" in result_dict

        # Check change serialization
        change_dict = result_dict["changes_detected"][0]
        assert change_dict["change_type"] == "added"  # type: ignore[index]
        assert change_dict["impact_level"] == "medium"  # type: ignore[index]
        assert change_dict["element"]["element_type"] == "class"  # type: ignore[index]
        assert change_dict["element"]["name"] == "TestClass"  # type: ignore[index]


if __name__ == "__main__":
    pytest.main([__file__])
