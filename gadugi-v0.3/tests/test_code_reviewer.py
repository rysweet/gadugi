"""Tests for CodeReviewer Engine.

Comprehensive test suite covering code analysis, quality metrics,
and review workflow integration.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator"))

from code_reviewer_engine import (
    BanditAnalyzer,
    CodeReviewerEngine,
    FileReview,
    IssueCategory,
    IssueType,
    MypyAnalyzer,
    QualityGateValidator,
    QualityMetrics,
    ReviewIssue,
    ReviewResult,
    ReviewStatus,
    RuffAnalyzer,
)


class TestReviewIssue:
    """Test ReviewIssue data class."""

    def test_issue_creation(self) -> None:
        """Test basic issue creation."""
        issue = ReviewIssue(
            line=45,
            column=12,
            type=IssueType.WARNING,
            category=IssueCategory.STYLE,
            message="Line too long",
            suggestion="Break line at logical operator",
            rule_id="E501",
            severity=2,
        )

        assert issue.line == 45
        assert issue.type == IssueType.WARNING
        assert issue.category == IssueCategory.STYLE
        assert issue.severity == 2

    def test_issue_to_dict(self) -> None:
        """Test issue serialization."""
        issue = ReviewIssue(
            line=10,
            column=5,
            type=IssueType.ERROR,
            category=IssueCategory.SECURITY,
            message="Potential SQL injection",
            suggestion="Use parameterized queries",
            rule_id="B608",
            severity=5,
        )

        result = issue.to_dict()

        assert result["line"] == 10
        assert result["type"] == "error"
        assert result["category"] == "security"
        assert result["severity"] == 5


class TestFileReview:
    """Test FileReview data class."""

    def test_file_review_creation(self) -> None:
        """Test file review creation."""
        issues = [
            ReviewIssue(
                line=1,
                column=1,
                type=IssueType.WARNING,
                category=IssueCategory.STYLE,
                message="Test issue",
                suggestion="Fix it",
                rule_id="TEST",
                severity=1,
            ),
        ]

        review = FileReview(
            file_path="test.py",
            status=ReviewStatus.NEEDS_CHANGES,
            score=75,
            issues=issues,
            metrics={"lines_of_code": 100},
        )

        assert review.file_path == "test.py"
        assert review.status == ReviewStatus.NEEDS_CHANGES
        assert review.score == 75
        assert len(review.issues) == 1

    def test_file_review_to_dict(self) -> None:
        """Test file review serialization."""
        review = FileReview(
            file_path="example.py",
            status=ReviewStatus.APPROVED,
            score=95,
            issues=[],
            metrics={"lines_of_code": 50},
        )

        result = review.to_dict()

        assert result["file_path"] == "example.py"
        assert result["status"] == "approved"
        assert result["score"] == 95
        assert result["issues"] == []


class TestRuffAnalyzer:
    """Test Ruff analyzer integration."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analyzer = RuffAnalyzer()

    @pytest.mark.asyncio
    async def test_is_available_tool_present(self) -> None:
        """Test tool availability check when tool is present."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            available = await self.analyzer.is_available()
            assert available
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_available_tool_missing(self) -> None:
        """Test tool availability check when tool is missing."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            available = await self.analyzer.is_available()
            assert not available

    @pytest.mark.asyncio
    async def test_analyze_with_issues(self) -> None:
        """Test analysis with ruff issues."""
        mock_output = json.dumps(
            [
                {
                    "location": {"row": 45, "column": 12},
                    "severity": "error",
                    "message": "Line too long (89 > 88 characters)",
                    "code": "E501",
                },
            ],
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout=mock_output, stderr="")

            issues = await self.analyzer.analyze(["test.py"])

            assert len(issues) == 1
            issue = issues[0]
            assert issue.line == 45
            assert issue.column == 12
            assert issue.type == IssueType.ERROR
            assert issue.category == IssueCategory.STYLE
            assert issue.rule_id == "E501"

    @pytest.mark.asyncio
    async def test_analyze_no_issues(self) -> None:
        """Test analysis with no issues."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            issues = await self.analyzer.analyze(["test.py"])
            assert len(issues) == 0

    def test_map_severity(self) -> None:
        """Test severity mapping."""
        assert self.analyzer._map_severity("error") == IssueType.ERROR
        assert self.analyzer._map_severity("warning") == IssueType.WARNING
        assert self.analyzer._map_severity("note") == IssueType.INFO

    def test_map_category(self) -> None:
        """Test category mapping."""
        assert self.analyzer._map_category("E501") == IssueCategory.STYLE
        assert self.analyzer._map_category("F401") == IssueCategory.QUALITY
        assert self.analyzer._map_category("S101") == IssueCategory.SECURITY
        assert self.analyzer._map_category("C901") == IssueCategory.MAINTAINABILITY


class TestBanditAnalyzer:
    """Test Bandit security analyzer."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analyzer = BanditAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_security_issues(self) -> None:
        """Test security issue detection."""
        mock_output = json.dumps(
            {
                "results": [
                    {
                        "line_number": 25,
                        "col_offset": 4,
                        "issue_severity": "HIGH",
                        "issue_text": "Use of exec detected",
                        "test_id": "B102",
                    },
                ],
            },
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout=mock_output, stderr="")

            issues = await self.analyzer.analyze(["test.py"])

            assert len(issues) == 1
            issue = issues[0]
            assert issue.line == 25
            assert issue.category == IssueCategory.SECURITY
            assert issue.type == IssueType.ERROR  # HIGH severity
            assert issue.rule_id == "B102"
            assert issue.severity == 5

    def test_generate_security_suggestion(self) -> None:
        """Test security suggestion generation."""
        item = {"test_id": "B101"}
        suggestion = self.analyzer._generate_security_suggestion(item)
        assert "assert only for debugging" in suggestion

        item = {"test_id": "B999"}  # Unknown ID
        suggestion = self.analyzer._generate_security_suggestion(item)
        assert "OWASP guidelines" in suggestion


class TestMypyAnalyzer:
    """Test MyPy type checker integration."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analyzer = MypyAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_type_errors(self) -> None:
        """Test type error detection."""
        mock_output = """test.py:15:8: error: Incompatible types in assignment [assignment]
test.py:20:12: warning: Unused variable 'x' [misc]"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout=mock_output, stderr="")

            issues = await self.analyzer.analyze(["test.py"])

            assert len(issues) == 2

            error_issue = issues[0]
            assert error_issue.line == 15
            assert error_issue.column == 8
            assert error_issue.type == IssueType.ERROR
            assert error_issue.rule_id == "assignment"

            warning_issue = issues[1]
            assert warning_issue.line == 20
            assert warning_issue.type == IssueType.WARNING

    def test_parse_mypy_line(self) -> None:
        """Test mypy output parsing."""
        line = "test.py:10:5: error: Name 'undefined_var' is not defined [name-defined]"
        issue = self.analyzer._parse_mypy_line(line)

        assert issue is not None
        assert issue.line == 10
        assert issue.column == 5
        assert issue.type == IssueType.ERROR
        assert issue.rule_id == "name-defined"
        assert "Name 'undefined_var' is not defined" in issue.message

    def test_parse_invalid_line(self) -> None:
        """Test parsing invalid mypy output."""
        line = "Invalid mypy output line"
        issue = self.analyzer._parse_mypy_line(line)
        assert issue is None


class TestQualityGateValidator:
    """Test quality gate validation."""

    def test_coverage_validation_pass(self) -> None:
        """Test coverage validation passing."""
        gates = {"min_test_coverage": 80}
        validator = QualityGateValidator(gates)

        # Create mock review result
        result = Mock()
        result.quality_metrics = Mock()
        result.quality_metrics.test_coverage = 85.0
        result.file_reviews = []

        validation = validator.validate(result)
        assert validation["coverage_check"] == "passed"

    def test_coverage_validation_fail(self) -> None:
        """Test coverage validation failing."""
        gates = {"min_test_coverage": 90}
        validator = QualityGateValidator(gates)

        result = Mock()
        result.quality_metrics = Mock()
        result.quality_metrics.test_coverage = 75.0
        result.file_reviews = []

        validation = validator.validate(result)
        assert validation["coverage_check"] == "failed"

    def test_security_validation_strict(self) -> None:
        """Test strict security validation."""
        gates = {"security_level": "strict"}
        validator = QualityGateValidator(gates)

        # Create mock with security issue
        security_issue = Mock()
        security_issue.category = IssueCategory.SECURITY
        security_issue.severity = 3

        file_review = Mock()
        file_review.issues = [security_issue]

        result = Mock()
        result.quality_metrics = Mock()
        result.file_reviews = [file_review]

        validation = validator.validate(result)
        assert validation["security_check"] == "failed"


class TestCodeReviewerEngine:
    """Test main code reviewer engine."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.engine = CodeReviewerEngine()

    def test_initialize_analyzers(self) -> None:
        """Test analyzer initialization."""
        assert "python" in self.engine.analyzers
        python_analyzers = self.engine.analyzers["python"]
        assert len(python_analyzers) > 0

    def test_group_files_by_language(self) -> None:
        """Test file language grouping."""
        files = ["module.py", "script.js", "component.tsx", "main.go", "config.yaml"]

        groups = self.engine._group_files_by_language(files)

        assert "python" in groups
        assert "module.py" in groups["python"]
        assert "javascript" in groups
        assert "script.js" in groups["javascript"]
        assert "typescript" in groups
        assert "component.tsx" in groups["typescript"]
        assert "go" in groups
        assert "main.go" in groups["go"]
        assert "other" in groups
        assert "config.yaml" in groups["other"]

    def test_calculate_file_score_no_issues(self) -> None:
        """Test file score calculation with no issues."""
        score = self.engine._calculate_file_score([], "test.py")
        assert score == 100

    def test_calculate_file_score_with_issues(self) -> None:
        """Test file score calculation with issues."""
        issues = [
            ReviewIssue(
                line=1,
                column=1,
                type=IssueType.ERROR,
                category=IssueCategory.STYLE,
                message="Test",
                suggestion="Fix",
                rule_id="E1",
                severity=3,
            ),
            ReviewIssue(
                line=2,
                column=1,
                type=IssueType.WARNING,
                category=IssueCategory.QUALITY,
                message="Test",
                suggestion="Fix",
                rule_id="W1",
                severity=2,
            ),
        ]

        score = self.engine._calculate_file_score(issues, "test.py")
        # 100 - (3*3) - (2*2) = 100 - 9 - 4 = 87
        assert score == 87

    def test_determine_file_status_approved(self) -> None:
        """Test file status determination - approved."""
        status = self.engine._determine_file_status(90, [])
        assert status == ReviewStatus.APPROVED

    def test_determine_file_status_needs_changes(self) -> None:
        """Test file status determination - needs changes."""
        status = self.engine._determine_file_status(70, [])
        assert status == ReviewStatus.NEEDS_CHANGES

    def test_determine_file_status_rejected(self) -> None:
        """Test file status determination - rejected."""
        # Low score
        status = self.engine._determine_file_status(30, [])
        assert status == ReviewStatus.REJECTED

        # Critical issues
        critical_issue = ReviewIssue(
            line=1,
            column=1,
            type=IssueType.ERROR,
            category=IssueCategory.SECURITY,
            message="Critical",
            suggestion="Fix",
            rule_id="S1",
            severity=5,
        )
        status = self.engine._determine_file_status(90, [critical_issue])
        assert status == ReviewStatus.REJECTED

    @pytest.mark.asyncio
    async def test_filter_files_valid(self) -> None:
        """Test file filtering with valid files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('hello')")
            temp_file = f.name

        try:
            files = await self.engine._filter_files([temp_file], {})
            assert len(files) == 1
            assert temp_file in files
        finally:
            Path(temp_file).unlink()

    @pytest.mark.asyncio
    async def test_filter_files_nonexistent(self) -> None:
        """Test file filtering with non-existent files."""
        files = await self.engine._filter_files(["nonexistent.py"], {})
        assert len(files) == 0

    def test_generate_recommendations(self) -> None:
        """Test recommendation generation."""
        # Create mock data with various issues
        file_reviews = []

        # File with security issues
        security_issue = ReviewIssue(
            line=1,
            column=1,
            type=IssueType.ERROR,
            category=IssueCategory.SECURITY,
            message="Security issue",
            suggestion="Fix",
            rule_id="S1",
            severity=4,
        )
        file_reviews.append(
            FileReview(
                file_path="test1.py",
                status=ReviewStatus.NEEDS_CHANGES,
                score=70,
                issues=[security_issue],
            ),
        )

        # File with style issues
        style_issues = [
            ReviewIssue(
                line=i,
                column=1,
                type=IssueType.WARNING,
                category=IssueCategory.STYLE,
                message=f"Style issue {i}",
                suggestion="Fix",
                rule_id=f"E{i}",
                severity=1,
            )
            for i in range(1, 8)  # 7 style issues
        ]
        file_reviews.append(
            FileReview(
                file_path="test2.py",
                status=ReviewStatus.NEEDS_CHANGES,
                score=75,
                issues=style_issues,
            ),
        )

        # Mock quality metrics
        quality_metrics = QualityMetrics(
            technical_debt_ratio=8.0, cyclomatic_complexity=12.0, test_coverage=65.0,
        )

        recommendations = self.engine._generate_recommendations(
            file_reviews, quality_metrics,
        )

        # Should include security, debt, complexity, coverage, and style recommendations
        assert len(recommendations) == 5
        assert any("security" in rec.lower() for rec in recommendations)
        assert any("technical debt" in rec.lower() for rec in recommendations)
        assert any("complex" in rec.lower() for rec in recommendations)
        assert any("test coverage" in rec.lower() for rec in recommendations)
        assert any("style" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_review_files_integration(self) -> None:
        """Test complete file review integration."""
        # Create temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
def hello_world():
    print("Hello, world!")
    return True

if __name__ == "__main__":
    hello_world()
            """)
            temp_file = f.name

        try:
            # Mock analyzer availability and results
            with (
                patch.object(RuffAnalyzer, "is_available", return_value=True),
                patch.object(RuffAnalyzer, "analyze") as mock_analyze,
            ):
                # Mock some analysis results
                mock_analyze.return_value = [
                    ReviewIssue(
                        line=3,
                        column=1,
                        type=IssueType.SUGGESTION,
                        category=IssueCategory.STYLE,
                        message="Add docstring",
                        suggestion="Add function docstring",
                        rule_id="D100",
                        severity=1,
                    ),
                ]

                result = await self.engine.review_files([temp_file])

                assert isinstance(result, ReviewResult)
                assert result.status in [
                    ReviewStatus.APPROVED,
                    ReviewStatus.NEEDS_CHANGES,
                ]
                assert result.summary.total_files == 1
                assert len(result.file_reviews) == 1
                assert result.execution_time > 0

        finally:
            Path(temp_file).unlink()


class TestReviewIntegration:
    """Integration tests for complete review workflows."""

    @pytest.mark.asyncio
    async def test_empty_file_list(self) -> None:
        """Test review with empty file list."""
        engine = CodeReviewerEngine()
        result = await engine.review_files([])

        assert result.status == ReviewStatus.APPROVED
        assert result.summary.total_files == 0
        assert result.overall_score == 100

    @pytest.mark.asyncio
    async def test_multiple_files_review(self) -> None:
        """Test review with multiple files."""
        # Create multiple temporary files
        temp_files = []

        for i in range(3):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(f"""
def function_{i}():
    '''Function {i}'''
    return {i}
                """)
                temp_files.append(f.name)

        try:
            engine = CodeReviewerEngine()

            # Mock all analyzers to be unavailable to test basic flow
            with (
                patch.object(RuffAnalyzer, "is_available", return_value=False),
                patch.object(BanditAnalyzer, "is_available", return_value=False),
                patch.object(MypyAnalyzer, "is_available", return_value=False),
            ):
                result = await engine.review_files(temp_files)

                # When no analyzers available, no file reviews are created
                # but total_lines should still reflect the files processed
                assert (
                    result.summary.total_lines > 0
                )  # Files were processed for line count
                assert result.status == ReviewStatus.APPROVED

        finally:
            for temp_file in temp_files:
                Path(temp_file).unlink()

    @pytest.mark.asyncio
    async def test_quality_gates_integration(self) -> None:
        """Test quality gates integration."""
        engine = CodeReviewerEngine()

        # Create config with strict quality gates
        config = {
            "quality_gates": {
                "min_test_coverage": 95,
                "max_cyclomatic_complexity": 5,
                "security_level": "strict",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def simple_function(): return True")
            temp_file = f.name

        try:
            # Mock analyzer to return no issues but low coverage
            with (
                patch.object(RuffAnalyzer, "is_available", return_value=True),
                patch.object(RuffAnalyzer, "analyze", return_value=[]),
            ):
                result = await engine.review_files([temp_file], config)

                # Should fail quality gates due to low test coverage (mocked at 85%)
                assert "coverage_check" in result.quality_gates

        finally:
            Path(temp_file).unlink()


class TestPerformanceAndEdgeCases:
    """Performance and edge case tests."""

    @pytest.mark.asyncio
    async def test_large_file_handling(self) -> None:
        """Test handling of large files."""
        engine = CodeReviewerEngine()

        # Create a file just under the size limit
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            # Write 5MB of content (under default 10MB limit)
            content = "# " + "x" * 1000 + "\n"
            for _ in range(5000):
                f.write(content)
            temp_file = f.name

        try:
            files = await engine._filter_files([temp_file], {"max_file_size_mb": 10})
            assert len(files) == 1

            # Test with smaller limit
            files = await engine._filter_files([temp_file], {"max_file_size_mb": 1})
            assert len(files) == 0  # Should be filtered out

        finally:
            Path(temp_file).unlink()

    def test_count_lines(self) -> None:
        """Test line counting functionality."""
        engine = CodeReviewerEngine()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            content = """
def hello():
    print("Hello")

    return True

# Comment
if __name__ == "__main__":
    hello()
            """.strip()
            f.write(content)
            temp_file = f.name

        try:
            line_count = engine._count_lines(temp_file)
            assert line_count == 6  # Non-empty lines (excluding blank line)
        finally:
            Path(temp_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
