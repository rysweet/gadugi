"""
Code Reviewer Engine for code analysis and review tasks.

This module provides the core engine for performing code reviews,
including issue detection, categorization, and result reporting.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class IssueCategory(Enum):
    """Categories of code review issues."""

    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    BUG = "bug"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    BEST_PRACTICE = "best_practice"


class IssueSeverity(Enum):
    """Severity levels for code review issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ReviewIssue:
    """Represents a single code review issue."""

    file_path: str
    line_number: Optional[int]
    category: IssueCategory
    severity: IssueSeverity
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary format."""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet,
        }


@dataclass
class ReviewResult:
    """Result of a code review operation."""

    success: bool
    issues: List[ReviewIssue] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None
    reviewed_files: List[str] = field(default_factory=list)

    @property
    def issue_count(self) -> int:
        """Get total number of issues found."""
        return len(self.issues)

    @property
    def critical_count(self) -> int:
        """Get number of critical issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Get number of high severity issues."""
        return sum(1 for issue in self.issues if issue.severity == IssueSeverity.HIGH)

    def get_issues_by_category(self, category: IssueCategory) -> List[ReviewIssue]:
        """Get all issues of a specific category."""
        return [issue for issue in self.issues if issue.category == category]

    def get_issues_by_severity(self, severity: IssueSeverity) -> List[ReviewIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "success": self.success,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics": self.metrics,
            "summary": self.summary,
            "reviewed_files": self.reviewed_files,
            "statistics": {
                "total_issues": self.issue_count,
                "critical_issues": self.critical_count,
                "high_issues": self.high_count,
                "issues_by_category": {
                    category.value: len(self.get_issues_by_category(category))
                    for category in IssueCategory
                },
                "issues_by_severity": {
                    severity.value: len(self.get_issues_by_severity(severity))
                    for severity in IssueSeverity
                },
            },
        }


class CodeReviewerEngine:
    """
    Engine for performing code reviews.

    This class provides the core functionality for analyzing code,
    detecting issues, and generating review results.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the code reviewer engine.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.patterns: Dict[IssueCategory, List[str]] = self._load_patterns()
        self.excluded_paths: Set[str] = set(self.config.get("excluded_paths", []))
        logger.info("CodeReviewerEngine initialized")

    def _load_patterns(self) -> Dict[IssueCategory, List[str]]:
        """Load detection patterns for various issue categories."""
        return {
            IssueCategory.SECURITY: [
                r"eval\s*\(",
                r"exec\s*\(",
                r"__import__\s*\(",
                r"os\.system\s*\(",
                r"subprocess\.\w+\(.*shell\s*=\s*True",
            ],
            IssueCategory.PERFORMANCE: [
                r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(",
                r"time\.sleep\s*\(\s*[0-9]+\s*\)",
            ],
            IssueCategory.STYLE: [
                r"^\s*except\s*:",
                r"^[^#]*\s+$",  # Trailing whitespace
            ],
            IssueCategory.BUG: [
                r"if\s+\w+\s*=\s*",  # Assignment in if statement
                r"except\s+Exception\s*:",  # Catching generic Exception
            ],
            IssueCategory.TESTING: [
                r"assert\s+True",
                r"assert\s+False",
            ],
        }

    async def review_files(self, file_paths: List[str]) -> ReviewResult:
        """
        Review a list of files for issues.

        Args:
            file_paths: List of file paths to review

        Returns:
            ReviewResult containing found issues and metrics
        """
        issues: List[ReviewIssue] = []
        reviewed_files: List[str] = []

        for file_path in file_paths:
            if self._should_skip_file(file_path):
                logger.debug(f"Skipping excluded file: {file_path}")
                continue

            try:
                path = Path(file_path)
                if not path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                file_issues = await self._review_single_file(path)
                issues.extend(file_issues)
                reviewed_files.append(file_path)

            except Exception as e:
                logger.error(f"Error reviewing file {file_path}: {e}")

        result = ReviewResult(
            success=True,
            issues=issues,
            reviewed_files=reviewed_files,
            metrics={
                "files_reviewed": len(reviewed_files),
                "total_issues": len(issues),
            },
            summary=self._generate_summary(issues, reviewed_files),
        )

        return result

    async def _review_single_file(self, file_path: Path) -> List[ReviewIssue]:
        """
        Review a single file for issues.

        Args:
            file_path: Path to the file to review

        Returns:
            List of issues found in the file
        """
        issues: List[ReviewIssue] = []

        # This is a simplified implementation
        # In production, this would use AST parsing, linting tools, etc.

        try:
            content = file_path.read_text()
            lines = content.splitlines()

            # Check for basic issues
            for line_num, line in enumerate(lines, 1):
                # Check for trailing whitespace
                if line.rstrip() != line:
                    issues.append(
                        ReviewIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            category=IssueCategory.STYLE,
                            severity=IssueSeverity.LOW,
                            message="Trailing whitespace detected",
                            suggestion="Remove trailing whitespace",
                            code_snippet=repr(line),
                        )
                    )

                # Check for TODO comments
                if "TODO" in line or "FIXME" in line:
                    issues.append(
                        ReviewIssue(
                            file_path=str(file_path),
                            line_number=line_num,
                            category=IssueCategory.DOCUMENTATION,
                            severity=IssueSeverity.INFO,
                            message="TODO/FIXME comment found",
                            suggestion="Consider addressing or creating an issue",
                            code_snippet=line.strip(),
                        )
                    )

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")

        return issues

    def _should_skip_file(self, file_path: str) -> bool:
        """Check if a file should be skipped based on exclusion rules."""
        for excluded in self.excluded_paths:
            if excluded in file_path:
                return True
        return False

    def _generate_summary(self, issues: List[ReviewIssue], reviewed_files: List[str]) -> str:
        """Generate a summary of the review results."""
        if not issues:
            return f"✅ No issues found in {len(reviewed_files)} file(s)"

        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)

        summary = f"Found {len(issues)} issue(s) in {len(reviewed_files)} file(s)\n"
        if critical_count > 0:
            summary += f"  - {critical_count} critical issue(s)\n"
        if high_count > 0:
            summary += f"  - {high_count} high severity issue(s)\n"

        return summary

    def analyze_code_quality(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze overall code quality metrics for a file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Dictionary containing quality metrics
        """
        metrics = {
            "complexity": 0,
            "maintainability": 0,
            "test_coverage": 0,
            "documentation_score": 0,
        }

        # Simplified implementation
        # In production, this would use tools like radon, pylint, etc.

        try:
            path = Path(file_path)
            if path.exists():
                content = path.read_text()
                lines = content.splitlines()

                # Basic metrics
                metrics["lines_of_code"] = len(lines)
                metrics["comment_lines"] = sum(1 for line in lines if line.strip().startswith("#"))
                metrics["blank_lines"] = sum(1 for line in lines if not line.strip())

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

        return metrics
