"""
Shared instruction framework for Test Solver and Test Writer agents.
Contains common patterns, utilities, and validation logic.
"""

import os
import sys
import logging
from typing import Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))

# Define fallback classes first
@dataclass
class OperationResult:
    success: bool
    data: Any = None
    error: str = ""

@dataclass
class AgentConfig:
    agent_id: str
    name: str

try:
    from utils.error_handling import ErrorHandler
    # If successful import, override the fallback definitions if they exist there
except ImportError:
    # Use the fallback definitions already defined above
    pass


class TestStatus(Enum):
    """Test execution status."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


class SkipReason(Enum):
    """Valid reasons for skipping tests."""

    API_KEY_MISSING = "api_key_missing"
    PLATFORM_CONSTRAINT = "platform_constraint"
    UPSTREAM_BUG = "upstream_bug"
    INFRASTRUCTURE_DEPENDENCY = "infrastructure_dependency"
    RESOURCE_CONSTRAINT = "resource_constraint"
    FLAKY_TEST = "flaky_test"


@dataclass
class TestResult:
    """Test execution result with detailed information."""

    name: str
    status: TestStatus
    duration: float = 0.0
    output: str = ""
    error: str = ""
    skip_reason: Optional[SkipReason] = None
    skip_justification: str = ""


@dataclass
class TestAnalysis:
    """Test analysis result."""

    purpose: str
    requirements: List[str]
    expected_outcome: str
    dependencies: List[str]
    resources_used: List[str]
    complexity_score: int  # 1-10 scale


class SharedTestInstructions:
    """Shared instruction framework for test agents."""

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig(
            agent_id="shared_test_instructions", name="Shared Test Instructions"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_handler = ErrorHandler() if "ErrorHandler" in globals() else None

    @staticmethod
    def analyze_test_purpose(test_code: str, context: str = "") -> TestAnalysis:
        """
        Analyze the purpose and requirements of a test.

        Core instruction: Think carefully about why the test exists -
        what is the feature or function it is validating?
        """
        # Extract test name and docstring
        test_name = SharedTestInstructions._extract_test_name(test_code)
        docstring = SharedTestInstructions._extract_docstring(test_code)

        # Analyze imports and dependencies
        dependencies = SharedTestInstructions._extract_dependencies(test_code)

        # Identify resources used
        resources = SharedTestInstructions._identify_resources(test_code)

        # Determine complexity
        complexity = SharedTestInstructions._calculate_complexity(test_code)

        # Extract purpose from various sources
        purpose_sources = [docstring, test_name, context]
        purpose = SharedTestInstructions._derive_purpose(purpose_sources, test_code)

        return TestAnalysis(
            purpose=purpose,
            requirements=SharedTestInstructions._extract_requirements(
                test_code, docstring
            ),
            expected_outcome=SharedTestInstructions._derive_expected_outcome(test_code),
            dependencies=dependencies,
            resources_used=resources,
            complexity_score=complexity,
        )

    @staticmethod
    def validate_test_structure(test_code: str) -> Tuple[bool, List[str]]:
        """
        Validate test structure and setup.

        Core instruction: Think carefully about the test structure and setup.
        """
        issues = []

        # Check for proper test function naming
        if not SharedTestInstructions._has_valid_test_name(test_code):
            issues.append("Test function name should start with 'test_'")

        # Check for docstring
        if not SharedTestInstructions._has_docstring(test_code):
            issues.append("Test should have a descriptive docstring")

        # Check for setup/teardown patterns
        if SharedTestInstructions._uses_resources(test_code):
            if not SharedTestInstructions._has_cleanup(test_code):
                issues.append("Test uses resources but lacks proper cleanup")

        # Check for assertions
        if not SharedTestInstructions._has_assertions(test_code):
            issues.append("Test should have meaningful assertions")

        # Check for idempotency patterns
        if not SharedTestInstructions._appears_idempotent(test_code):
            issues.append("Test may not be idempotent - consider state isolation")

        return len(issues) == 0, issues

    @staticmethod
    def ensure_test_idempotency(test_code: str) -> str:
        """
        Ensure test is idempotent and manages dependencies.

        Core instruction: Tests must be idempotent.
        """
        lines = test_code.split("\n")
        modified_lines = []

        for line in lines:
            modified_lines.append(line)

            # Add cleanup after resource creation
            if any(
                keyword in line.lower()
                for keyword in ["tempfile", "mkdir", "create", "open"]
            ):
                if "with" not in line and "cleanup" not in line.lower():
                    indent = len(line) - len(line.lstrip())
                    cleanup_comment = (
                        " " * indent + "# TODO: Ensure proper cleanup for idempotency"
                    )
                    modified_lines.append(cleanup_comment)

        return "\n".join(modified_lines)

    @staticmethod
    def validate_dependency_management(test_code: str) -> Tuple[bool, List[str]]:
        """
        Validate test dependency management.

        Core instruction: Tests must manage their dependencies.
        """
        issues = []
        dependencies = SharedTestInstructions._extract_dependencies(test_code)

        # Check for external service dependencies
        external_deps = ["requests", "http", "api", "network", "remote"]
        has_external = any(
            dep in dep_name.lower()
            for dep_name in dependencies
            for dep in external_deps
        )

        if has_external:
            if not SharedTestInstructions._has_mocking(test_code):
                issues.append("External dependencies should be mocked for reliability")

        # Check for database dependencies
        db_deps = ["sqlite", "mysql", "postgres", "database", "db"]
        has_db = any(
            dep in dep_name.lower() for dep_name in dependencies for dep in db_deps
        )

        if has_db:
            if not SharedTestInstructions._has_transaction_rollback(test_code):
                issues.append(
                    "Database tests should use transactions or test databases"
                )

        return len(issues) == 0, issues

    @staticmethod
    def ensure_resource_cleanup(test_code: str) -> str:
        """
        Ensure proper resource cleanup.

        Core instruction: Tests must ensure cleanup of their resources.
        """
        if SharedTestInstructions._has_context_managers(test_code):
            return test_code  # Already using context managers

        # Add cleanup suggestions
        lines = test_code.split("\n")
        for i, line in enumerate(lines):
            if any(resource in line for resource in ["open(", "tempfile.", "mkdir"]):
                # Add comment suggesting context manager or cleanup
                indent = len(line) - len(line.lstrip())
                suggestion = (
                    " " * indent
                    + "# Consider using context manager or explicit cleanup"
                )
                lines.insert(i + 1, suggestion)
                break

        return "\n".join(lines)

    @staticmethod
    def recommend_shared_fixtures(
        test_code: str, existing_fixtures: List[str]
    ) -> List[str]:
        """
        Recommend shared fixtures for consistency.

        Core instruction: Tests must use shared fixtures when possible.
        """
        recommendations = []

        # Common patterns that should use fixtures
        patterns = {
            "temp_dir": ["tempfile", "mkdtemp", "temporary directory"],
            "mock_response": ["mock", "Mock()", "response"],
            "sample_data": ["test data", "example", "sample"],
            "mock_config": ["config", "configuration", "settings"],
        }

        for fixture, keywords in patterns.items():
            if fixture in existing_fixtures:
                for keyword in keywords:
                    if keyword in test_code.lower():
                        recommendations.append(
                            f"Consider using existing '{fixture}' fixture"
                        )
                        break

        return recommendations

    @staticmethod
    def validate_parallel_safety(test_code: str) -> Tuple[bool, List[str]]:
        """
        Validate test can run safely in parallel.

        Core instruction: Test fixtures must avoid creating tests that
        cannot be reliably run in parallel.
        """
        issues = []

        # Check for global state modification
        global_patterns = ["global ", "os.environ", "sys.path", "chdir", "getcwd"]
        for pattern in global_patterns:
            if pattern in test_code:
                issues.append(f"Test modifies global state: {pattern}")

        # Check for fixed port usage
        if "port=" in test_code and "random" not in test_code:
            issues.append("Test uses fixed ports - consider random port assignment")

        # Check for fixed file paths
        if "/tmp/" in test_code and "tempfile" not in test_code:
            issues.append("Test uses fixed paths - consider temporary directories")

        # Check for singleton patterns
        if "singleton" in test_code.lower():
            issues.append("Test may use singleton pattern - ensure proper isolation")

        return len(issues) == 0, issues

    @staticmethod
    def validate_skip_justification(
        skip_reason: Optional[SkipReason], justification: str
    ) -> Tuple[bool, str]:
        """
        Validate test skip justification.

        Core instruction: Do not skip tests unless in specifically permitted
        circumstances (you have instructions that it can be skipped).
        """
        if skip_reason is None:
            return True, "No skip - validation passed"

        if not justification or len(justification.strip()) < 10:
            return False, "Skip justification must be detailed and specific"

        # Validate reason is in allowed list
        if skip_reason not in SkipReason:
            return False, f"Invalid skip reason: {skip_reason}"

        # Ensure justification matches reason
        reason_keywords = {
            SkipReason.API_KEY_MISSING: ["api key", "key not", "missing key"],
            SkipReason.PLATFORM_CONSTRAINT: [
                "platform",
                "os",
                "windows",
                "linux",
                "mac",
            ],
            SkipReason.UPSTREAM_BUG: ["upstream", "bug", "issue", "broken"],
            SkipReason.INFRASTRUCTURE_DEPENDENCY: [
                "infrastructure",
                "service",
                "external",
            ],
            SkipReason.RESOURCE_CONSTRAINT: ["resource", "memory", "disk", "cpu"],
            SkipReason.FLAKY_TEST: ["flaky", "intermittent", "unreliable"],
        }

        expected_keywords = reason_keywords.get(skip_reason, [])
        has_matching_keyword = any(
            keyword in justification.lower() for keyword in expected_keywords
        )

        if not has_matching_keyword:
            return False, f"Justification doesn't match skip reason: {skip_reason}"

        return True, "Skip justification is valid"

    # Helper methods for analysis

    @staticmethod
    def _extract_test_name(test_code: str) -> str:
        """Extract test function name from code."""
        for line in test_code.split("\n"):
            if line.strip().startswith("def test_"):
                return line.split("(")[0].replace("def ", "").strip()
        return "unknown_test"

    @staticmethod
    def _extract_docstring(test_code: str) -> str:
        """Extract docstring from test function."""
        lines = test_code.split("\n")
        in_docstring = False
        docstring_lines = []

        for line in lines:
            if '"""' in line or "'''" in line:
                if in_docstring:
                    break
                in_docstring = True
                continue
            if in_docstring:
                docstring_lines.append(line.strip())

        return " ".join(docstring_lines)

    @staticmethod
    def _extract_dependencies(test_code: str) -> List[str]:
        """Extract imports and dependencies from test code."""
        dependencies = []
        for line in test_code.split("\n"):
            if line.strip().startswith(("import ", "from ")):
                dependencies.append(line.strip())
        return dependencies

    @staticmethod
    def _identify_resources(test_code: str) -> List[str]:
        """Identify resources used by the test."""
        resources = []
        resource_patterns = [
            "file",
            "tempfile",
            "socket",
            "database",
            "network",
            "process",
        ]

        for pattern in resource_patterns:
            if pattern in test_code.lower():
                resources.append(pattern)

        return resources

    @staticmethod
    def _calculate_complexity(test_code: str) -> int:
        """Calculate test complexity score (1-10)."""
        lines = len([line for line in test_code.split("\n") if line.strip()])
        assertions = test_code.count("assert")
        loops = test_code.count("for ") + test_code.count("while ")
        conditions = test_code.count("if ") + test_code.count("elif ")

        # Base complexity on various factors
        complexity = min(
            10, max(1, (lines // 10) + assertions + (loops * 2) + conditions)
        )
        return complexity

    @staticmethod
    def _derive_purpose(sources: List[str], test_code: str) -> str:
        """Derive test purpose from available sources."""
        for source in sources:
            if source and len(source) > 10:
                return source[:200]  # First 200 chars

        # Fallback to analyzing test code
        if "assert" in test_code:
            return "Test validates behavior through assertions"
        return "Test purpose needs clarification"

    @staticmethod
    def _extract_requirements(test_code: str, docstring: str) -> List[str]:
        """Extract test requirements."""
        requirements = []

        # Look for requirement keywords
        req_keywords = ["should", "must", "validates", "ensures", "checks", "tests"]
        text = f"{test_code} {docstring}".lower()

        for keyword in req_keywords:
            if keyword in text:
                requirements.append(f"Contains {keyword} requirement")

        return requirements

    @staticmethod
    def _derive_expected_outcome(test_code: str) -> str:
        """Derive expected test outcome."""
        if "assert" in test_code:
            return "Test should pass with valid assertions"
        elif "raises" in test_code:
            return "Test should raise expected exception"
        else:
            return "Test outcome unclear - needs assertions"

    @staticmethod
    def _has_valid_test_name(test_code: str) -> bool:
        """Check if test has valid naming."""
        return "def test_" in test_code

    @staticmethod
    def _has_docstring(test_code: str) -> bool:
        """Check if test has docstring."""
        return '"""' in test_code or "'''" in test_code

    @staticmethod
    def _uses_resources(test_code: str) -> bool:
        """Check if test uses external resources."""
        resource_indicators = ["open(", "tempfile", "socket", "subprocess", "requests"]
        return any(indicator in test_code for indicator in resource_indicators)

    @staticmethod
    def _has_cleanup(test_code: str) -> bool:
        """Check if test has cleanup logic."""
        cleanup_indicators = ["finally:", "close()", "cleanup", "teardown", "with "]
        return any(indicator in test_code for indicator in cleanup_indicators)

    @staticmethod
    def _has_assertions(test_code: str) -> bool:
        """Check if test has assertions."""
        return "assert" in test_code

    @staticmethod
    def _appears_idempotent(test_code: str) -> bool:
        """Check if test appears to be idempotent."""
        # Basic heuristics for idempotency
        non_idempotent_patterns = ["append", "+=", "global ", "os.environ["]
        return not any(pattern in test_code for pattern in non_idempotent_patterns)

    @staticmethod
    def _has_mocking(test_code: str) -> bool:
        """Check if test uses mocking."""
        mock_indicators = ["mock", "Mock", "patch", "MagicMock"]
        return any(indicator in test_code for indicator in mock_indicators)

    @staticmethod
    def _has_transaction_rollback(test_code: str) -> bool:
        """Check if test uses database transactions."""
        transaction_indicators = ["transaction", "rollback", "commit", "begin"]
        return any(indicator in test_code for indicator in transaction_indicators)

    @staticmethod
    def _has_context_managers(test_code: str) -> bool:
        """Check if test uses context managers."""
        return "with " in test_code
