"""
Test Writer Agent Implementation
Authors comprehensive tests for new functionality with TDD alignment.
"""

import os
import sys
import ast
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))

try:
    from utils.error_handling import CircuitBreaker
except ImportError:
    # Fallback definitions for missing imports
    from dataclasses import dataclass

    @dataclass
    class OperationResult:
        success: bool
        data: Any = None
        error: str = ""

    @dataclass
    class AgentConfig:
        agent_id: str
        name: str

    class CircuitBreaker:
        def __init__(self, failure_threshold=3, recovery_timeout=30.0):
            pass

        def __call__(self, func):
            return func


# Import shared test instructions
from shared_test_instructions import SharedTestInstructions


class TestType(Enum):
    """Types of tests to create."""

    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ERROR_HANDLING = "error_handling"


@dataclass
class CodeAnalysis:
    """Analysis of code to be tested."""

    public_methods: List[str]
    private_methods: List[str]
    classes: List[str]
    dependencies: List[str]
    edge_cases: List[str]
    complexity_score: int
    test_requirements: List[str]


@dataclass
class TestPlan:
    """Plan for creating tests."""

    test_classes: List[str]
    test_methods: List[Dict[str, Any]]
    fixtures_needed: List[str]
    setup_requirements: List[str]
    cleanup_requirements: List[str]
    coverage_targets: Dict[str, float]


@dataclass
class FixtureSpec:
    """Specification for a test fixture."""

    name: str
    purpose: str
    scope: str  # 'function', 'class', 'module', 'session'
    setup_code: str
    cleanup_code: str
    dependencies: List[str]


@dataclass
class TestSpec:
    """Specification for an individual test."""

    name: str
    purpose: str
    test_type: TestType
    coverage_areas: List[str]
    fixtures_used: List[str]
    setup_code: str
    test_code: str
    assertion_code: str
    cleanup_code: str
    documentation: str


@dataclass
class TestWriterResult:
    """Result of test writing operation."""

    module_name: str
    tests_created: List[TestSpec]
    fixtures_created: List[FixtureSpec]
    coverage_analysis: Dict[str, Any]
    tdd_alignment: Dict[str, bool]
    quality_metrics: Dict[str, bool]
    validation_results: List[str]


class TestWriterAgent:
    """
    Agent for creating comprehensive tests for new functionality.

    Follows shared test instruction framework and supports TDD practices.
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig(
            agent_id="test_writer_agent", name="Test Writer Agent"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.shared_instructions = SharedTestInstructions(config)

        # Setup error handling
        try:
            self.error_handler = ErrorHandler()
        except NameError:
            self.error_handler = None

    def create_tests(
        self,
        code_path: str,
        context: str = "",
        test_type: TestType = TestType.UNIT,
        existing_fixtures: Optional[List[str]] = None,
    ) -> TestWriterResult:
        """
        Main entry point for creating tests.

        Args:
            code_path: Path to code file to create tests for
            context: Additional context about requirements and design
            test_type: Type of tests to create
            existing_fixtures: List of existing fixtures available

        Returns:
            TestWriterResult with created tests and analysis
        """
        self.logger.info(f"Creating tests for: {code_path}")

        try:
            existing_fixtures = existing_fixtures or []

            # Phase 1: Requirements Analysis
            code_analysis = self._analyze_code_for_testing(code_path, context)
            test_scope = self._define_test_scope(code_analysis, test_type)
            tdd_context = self._analyze_tdd_context(context, code_analysis)

            # Phase 2: Test Design
            test_plan = self._design_test_structure(code_analysis, test_scope)
            fixture_plan = self._plan_fixtures(test_plan, existing_fixtures)

            # Phase 3: Test Implementation
            fixtures_created = self._create_fixtures(fixture_plan["create_new"])
            tests_created = self._create_test_methods(
                test_plan, code_analysis, tdd_context
            )

            # Phase 4: Quality Assurance
            quality_metrics = self._validate_test_quality(
                tests_created, fixtures_created
            )
            coverage_analysis = self._analyze_coverage(code_path, tests_created)

            # Phase 5: Documentation and Validation
            final_tests = self._document_tests(tests_created, code_analysis, context)
            validation_results = self._validate_complete_test_suite(final_tests)

            return TestWriterResult(
                module_name=self._extract_module_name(code_path),
                tests_created=final_tests,
                fixtures_created=fixtures_created,
                coverage_analysis=coverage_analysis,
                tdd_alignment={
                    "design_guidance_provided": tdd_context["provides_design_guidance"],
                    "interfaces_specified": tdd_context["specifies_interfaces"],
                    "behaviors_documented": tdd_context["documents_behaviors"],
                },
                quality_metrics=quality_metrics,
                validation_results=validation_results,
            )

        except Exception as e:
            self.logger.error(f"Error creating tests: {e}")
            return self._create_error_result(code_path, str(e))

    def _analyze_code_for_testing(
        self, code_path: str, context: str = ""
    ) -> CodeAnalysis:
        """Analyze code to understand testing requirements."""
        self.logger.info("Analyzing code for testing requirements...")

        try:
            with open(code_path, "r") as f:
                code_content = f.read()

            # Parse the code using AST
            tree = ast.parse(code_content)

            # Extract code elements
            public_methods = self._extract_public_methods(tree)
            private_methods = self._extract_private_methods(tree)
            classes = self._extract_classes(tree)
            dependencies = self._extract_dependencies(tree)
            edge_cases = self._identify_edge_cases(tree, code_content)
            complexity_score = self._calculate_code_complexity(tree)
            test_requirements = self._derive_test_requirements(tree, context)

            return CodeAnalysis(
                public_methods=public_methods,
                private_methods=private_methods,
                classes=classes,
                dependencies=dependencies,
                edge_cases=edge_cases,
                complexity_score=complexity_score,
                test_requirements=test_requirements,
            )

        except Exception as e:
            self.logger.error(f"Failed to analyze code: {e}")
            return CodeAnalysis([], [], [], [], [], 1, [])

    def _define_test_scope(
        self, code_analysis: CodeAnalysis, test_type: TestType
    ) -> Dict[str, List[str]]:
        """Define comprehensive test scope."""

        base_scope = {
            "functionality_tests": ["happy_path", "error_conditions", "edge_cases"],
            "integration_tests": [],
            "performance_tests": [],
            "security_tests": [],
        }

        # Adjust scope based on test type and code complexity
        if test_type == TestType.UNIT:
            base_scope["functionality_tests"].extend(
                ["boundary_conditions", "parameter_validation"]
            )

        elif test_type == TestType.INTEGRATION:
            base_scope["integration_tests"].extend(
                ["dependency_interactions", "external_services"]
            )

        elif test_type == TestType.PERFORMANCE:
            base_scope["performance_tests"].extend(
                ["response_time", "memory_usage", "throughput"]
            )

        elif test_type == TestType.SECURITY:
            base_scope["security_tests"].extend(
                ["input_validation", "access_control", "data_sanitization"]
            )

        # Add complexity-based tests
        if code_analysis.complexity_score > 5:
            base_scope["functionality_tests"].append("complex_scenarios")

        return base_scope

    def _analyze_tdd_context(
        self, context: str, code_analysis: CodeAnalysis
    ) -> Dict[str, Any]:
        """Analyze TDD context for test design guidance."""

        tdd_context = {
            "is_tdd_scenario": "tdd" in context.lower()
            or "test-driven" in context.lower(),
            "provides_design_guidance": False,
            "specifies_interfaces": False,
            "documents_behaviors": False,
            "design_requirements": [],
        }

        if tdd_context["is_tdd_scenario"]:
            # Extract design guidance from context
            if any(
                keyword in context.lower()
                for keyword in ["interface", "api", "contract"]
            ):
                tdd_context["specifies_interfaces"] = True

            if any(
                keyword in context.lower()
                for keyword in ["behavior", "should", "must", "expected"]
            ):
                tdd_context["documents_behaviors"] = True

            if any(
                keyword in context.lower()
                for keyword in ["design", "architecture", "pattern"]
            ):
                tdd_context["provides_design_guidance"] = True

        return tdd_context

    @CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    def _design_test_structure(
        self, code_analysis: CodeAnalysis, test_scope: Dict[str, List[str]]
    ) -> TestPlan:
        """Design comprehensive test structure."""
        self.logger.info("Designing test structure...")

        test_classes = []
        test_methods = []
        fixtures_needed = []
        setup_requirements = []
        cleanup_requirements = []

        # Create test class for each main class or module
        for class_name in code_analysis.classes or ["Module"]:
            test_class_name = f"Test{class_name}"
            test_classes.append(test_class_name)

            # Create test methods for each public method
            for method in code_analysis.public_methods:
                for test_category in test_scope["functionality_tests"]:
                    test_method = {
                        "class": test_class_name,
                        "name": f"test_{method}_{test_category}",
                        "purpose": f"Test {method} {test_category.replace('_', ' ')}",
                        "target_method": method,
                        "category": test_category,
                    }
                    test_methods.append(test_method)

            # Add integration tests if specified
            for integration_test in test_scope.get("integration_tests", []):
                test_method = {
                    "class": test_class_name,
                    "name": f"test_{class_name.lower()}_integration_{integration_test}",
                    "purpose": f"Test {class_name} integration {integration_test.replace('_', ' ')}",
                    "target_method": "integration",
                    "category": integration_test,
                }
                test_methods.append(test_method)

        # Determine fixtures needed
        fixtures_needed = self._determine_fixtures_needed(code_analysis, test_methods)

        # Determine setup/cleanup requirements
        setup_requirements = self._determine_setup_requirements(code_analysis)
        cleanup_requirements = self._determine_cleanup_requirements(code_analysis)

        return TestPlan(
            test_classes=test_classes,
            test_methods=test_methods,
            fixtures_needed=fixtures_needed,
            setup_requirements=setup_requirements,
            cleanup_requirements=cleanup_requirements,
            coverage_targets={"line_coverage": 90.0, "branch_coverage": 85.0},
        )

    def _plan_fixtures(
        self, test_plan: TestPlan, existing_fixtures: List[str]
    ) -> Dict[str, List[str]]:
        """Plan fixture usage and creation."""

        # Get recommendations for existing fixtures
        recommendations = self.shared_instructions.recommend_shared_fixtures(
            str(test_plan.fixtures_needed), existing_fixtures
        )

        # Determine new fixtures needed
        needed_fixtures = set(test_plan.fixtures_needed)
        available_fixtures = set(existing_fixtures)
        new_fixtures_needed = list(needed_fixtures - available_fixtures)

        return {"use_existing": recommendations, "create_new": new_fixtures_needed}

    def _create_fixtures(self, new_fixtures_needed: List[str]) -> List[FixtureSpec]:
        """Create new test fixtures."""
        fixtures = []

        for fixture_name in new_fixtures_needed:
            fixture = self._create_individual_fixture(fixture_name)
            fixtures.append(fixture)

        return fixtures

    def _create_individual_fixture(self, fixture_name: str) -> FixtureSpec:
        """Create an individual test fixture."""

        # Determine fixture purpose and scope based on name patterns
        if "temp" in fixture_name.lower() or "dir" in fixture_name.lower():
            return FixtureSpec(
                name=fixture_name,
                purpose="Provide temporary directory for file operations",
                scope="function",
                setup_code=self._generate_temp_dir_fixture_setup(),
                cleanup_code=self._generate_temp_dir_fixture_cleanup(),
                dependencies=[],
            )

        elif "mock" in fixture_name.lower():
            return FixtureSpec(
                name=fixture_name,
                purpose="Provide mock object for testing",
                scope="function",
                setup_code=self._generate_mock_fixture_setup(fixture_name),
                cleanup_code="# Mock objects cleaned up automatically",
                dependencies=[],
            )

        elif "sample" in fixture_name.lower() or "data" in fixture_name.lower():
            return FixtureSpec(
                name=fixture_name,
                purpose="Provide sample data for testing",
                scope="module",
                setup_code=self._generate_sample_data_fixture_setup(fixture_name),
                cleanup_code="# Data fixtures don't require cleanup",
                dependencies=[],
            )

        else:
            return FixtureSpec(
                name=fixture_name,
                purpose=f"Provide {fixture_name} for testing",
                scope="function",
                setup_code=f"# Setup {fixture_name}\nreturn create_{fixture_name}()",
                cleanup_code=f"# Cleanup {fixture_name}",
                dependencies=[],
            )

    def _create_test_methods(
        self,
        test_plan: TestPlan,
        code_analysis: CodeAnalysis,
        tdd_context: Dict[str, Any],
    ) -> List[TestSpec]:
        """Create individual test methods."""
        tests = []

        for test_method in test_plan.test_methods:
            test_spec = self._create_individual_test(
                test_method, code_analysis, tdd_context
            )

            # Apply shared instructions to enhance test
            enhanced_test = self._enhance_test_with_shared_instructions(test_spec)
            tests.append(enhanced_test)

        return tests

    def _create_individual_test(
        self,
        test_method: Dict[str, Any],
        code_analysis: CodeAnalysis,
        tdd_context: Dict[str, Any],
    ) -> TestSpec:
        """Create an individual test specification."""

        # Generate test code based on category
        category = test_method["category"]
        target_method = test_method["target_method"]

        if category == "happy_path":
            test_code = self._generate_happy_path_test(target_method, code_analysis)
        elif category == "error_conditions":
            test_code = self._generate_error_handling_test(target_method, code_analysis)
        elif category == "edge_cases":
            test_code = self._generate_edge_case_test(target_method, code_analysis)
        elif category == "boundary_conditions":
            test_code = self._generate_boundary_test(target_method, code_analysis)
        else:
            test_code = self._generate_generic_test(
                target_method, category, code_analysis
            )

        # Determine fixtures used
        fixtures_used = self._determine_test_fixtures(test_code, code_analysis)

        # Create comprehensive test specification
        return TestSpec(
            name=test_method["name"],
            purpose=test_method["purpose"],
            test_type=TestType.UNIT,  # Default to unit test
            coverage_areas=[category, target_method],
            fixtures_used=fixtures_used,
            setup_code=self._generate_test_setup(target_method, fixtures_used),
            test_code=test_code,
            assertion_code=self._generate_assertions(target_method, category),
            cleanup_code=self._generate_test_cleanup(fixtures_used),
            documentation=self._generate_test_documentation(
                test_method, code_analysis, tdd_context
            ),
        )

    def _enhance_test_with_shared_instructions(self, test_spec: TestSpec) -> TestSpec:
        """Apply shared instruction framework to enhance test."""

        # Combine all test code
        full_test_code = f"""
{test_spec.documentation}
def {test_spec.name}({", ".join(test_spec.fixtures_used)}):
    {test_spec.setup_code}

    {test_spec.test_code}

    {test_spec.assertion_code}

    {test_spec.cleanup_code}
"""

        # Apply shared instruction enhancements
        enhanced_code = self.shared_instructions.ensure_test_idempotency(full_test_code)
        enhanced_code = self.shared_instructions.ensure_resource_cleanup(enhanced_code)

        # Validate structure
        is_valid, issues = self.shared_instructions.validate_test_structure(
            enhanced_code
        )
        if not is_valid:
            enhanced_code = self._fix_structure_issues(enhanced_code, issues)

        # Validate dependency management
        deps_valid, dep_issues = (
            self.shared_instructions.validate_dependency_management(enhanced_code)
        )
        if not deps_valid:
            enhanced_code = self._fix_dependency_issues(enhanced_code, dep_issues)

        # Validate parallel safety
        parallel_safe, parallel_issues = (
            self.shared_instructions.validate_parallel_safety(enhanced_code)
        )
        if not parallel_safe:
            enhanced_code = self._fix_parallel_safety_issues(
                enhanced_code, parallel_issues
            )

        # Update test spec with enhanced code
        test_spec.test_code = enhanced_code
        return test_spec

    def _validate_test_quality(
        self, tests_created: List[TestSpec], fixtures_created: List[FixtureSpec]
    ) -> Dict[str, bool]:
        """Validate overall test quality."""

        quality_metrics = {
            "idempotent": True,
            "parallel_safe": True,
            "well_documented": True,
            "follows_patterns": True,
            "fixtures_appropriate": True,
        }

        # Validate each test
        for test in tests_created:
            # Check idempotency
            is_idempotent = self._check_test_idempotency(test.test_code)
            quality_metrics["idempotent"] &= is_idempotent

            # Check parallel safety
            is_parallel_safe, _ = self.shared_instructions.validate_parallel_safety(
                test.test_code
            )
            quality_metrics["parallel_safe"] &= is_parallel_safe

            # Check documentation
            has_good_docs = len(test.documentation) > 50 and '"""' in test.documentation
            quality_metrics["well_documented"] &= has_good_docs

            # Check patterns
            follows_patterns = self._check_test_patterns(test.test_code)
            quality_metrics["follows_patterns"] &= follows_patterns

        # Validate fixtures
        for fixture in fixtures_created:
            has_cleanup = (
                "cleanup" in fixture.cleanup_code.lower()
                or fixture.cleanup_code.strip() != ""
            )
            quality_metrics["fixtures_appropriate"] &= has_cleanup

        return quality_metrics

    def _analyze_coverage(
        self, code_path: str, tests_created: List[TestSpec]
    ) -> Dict[str, Any]:
        """Analyze test coverage for the code."""

        # This would typically run coverage analysis tools
        # For now, provide estimated coverage based on test count and code analysis

        return {
            "estimated_line_coverage": min(95.0, len(tests_created) * 15.0),
            "estimated_branch_coverage": min(90.0, len(tests_created) * 12.0),
            "functions_covered": [test.coverage_areas for test in tests_created],
            "coverage_gaps": self._identify_coverage_gaps(code_path, tests_created),
        }

    def _document_tests(
        self, tests_created: List[TestSpec], code_analysis: CodeAnalysis, context: str
    ) -> List[TestSpec]:
        """Add comprehensive documentation to tests."""

        for test in tests_created:
            enhanced_doc = f'''"""
{test.purpose}

This test validates:
- {test.purpose}
- Coverage areas: {", ".join(test.coverage_areas)}
- Test strategy: {self._describe_test_strategy(test)}

Requirements verified:
{self._format_test_requirements(test, code_analysis)}

Expected behavior:
- Setup: {self._describe_test_setup(test)}
- Action: {self._describe_test_action(test)}
- Verification: {self._describe_test_verification(test)}

Maintenance notes:
- Test uses fixtures: {", ".join(test.fixtures_used)}
- Idempotent: Yes
- Parallel safe: Yes
- Dependencies: {self._describe_test_dependencies(test)}
"""'''
            test.documentation = enhanced_doc

        return tests_created

    def _validate_complete_test_suite(self, tests_created: List[TestSpec]) -> List[str]:
        """Perform final validation of complete test suite."""

        validation_results = []

        # Check overall coverage
        if len(tests_created) >= 3:
            validation_results.append("✅ Adequate test coverage provided")
        else:
            validation_results.append(
                "⚠️ Limited test coverage - consider additional tests"
            )

        # Check test variety
        test_categories = set()
        for test in tests_created:
            test_categories.update(test.coverage_areas)

        if len(test_categories) >= 3:
            validation_results.append("✅ Good variety of test types")
        else:
            validation_results.append("⚠️ Limited test variety")

        # Check documentation quality
        well_documented = sum(
            1 for test in tests_created if len(test.documentation) > 100
        )
        if well_documented == len(tests_created):
            validation_results.append("✅ All tests well documented")
        else:
            validation_results.append(
                f"⚠️ {len(tests_created) - well_documented} tests need better documentation"
            )

        return validation_results

    # Code analysis helper methods

    def _extract_public_methods(self, tree: ast.AST) -> List[str]:
        """Extract public method names from AST."""
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                methods.append(node.name)
        return methods

    def _extract_private_methods(self, tree: ast.AST) -> List[str]:
        """Extract private method names from AST."""
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("_"):
                methods.append(node.name)
        return methods

    def _extract_classes(self, tree: ast.AST) -> List[str]:
        """Extract class names from AST."""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return classes

    def _extract_dependencies(self, tree: ast.AST) -> List[str]:
        """Extract import dependencies from AST."""
        dependencies = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)
        return dependencies

    def _identify_edge_cases(self, tree: ast.AST, code_content: str) -> List[str]:
        """Identify potential edge cases from code analysis."""
        edge_cases = []

        # Look for conditional statements
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                edge_cases.append("conditional_logic")
            elif isinstance(node, ast.For):
                edge_cases.append("iteration_logic")
            elif isinstance(node, ast.While):
                edge_cases.append("loop_logic")
            elif isinstance(node, ast.Try):
                edge_cases.append("exception_handling")

        # Look for common edge case patterns in code
        if "empty" in code_content.lower():
            edge_cases.append("empty_input")
        if "null" in code_content.lower() or "none" in code_content.lower():
            edge_cases.append("null_input")
        if "len(" in code_content:
            edge_cases.append("length_operations")

        return list(set(edge_cases))

    def _calculate_code_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of code."""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            if isinstance(
                node,
                (ast.If, ast.For, ast.While, ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def _derive_test_requirements(self, tree: ast.AST, context: str) -> List[str]:
        """Derive test requirements from code and context."""
        requirements = []

        # Extract from context
        if "should" in context.lower():
            requirements.append("Behavioral requirements specified")
        if "must" in context.lower():
            requirements.append("Mandatory requirements specified")

        # Extract from code structure
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("validate"):
                    requirements.append("Validation logic testing required")
                elif node.name.startswith("process"):
                    requirements.append("Processing logic testing required")

        return requirements

    # Test generation helper methods

    def _generate_happy_path_test(
        self, method_name: str, code_analysis: CodeAnalysis
    ) -> str:
        """Generate happy path test code."""
        return f"""
    # Arrange
    test_input = create_valid_input_for_{method_name}()
    expected_result = calculate_expected_result(test_input)

    # Act
    actual_result = target_object.{method_name}(test_input)

    # Assert
    assert actual_result == expected_result
    assert validate_result_properties(actual_result)
"""

    def _generate_error_handling_test(
        self, method_name: str, code_analysis: CodeAnalysis
    ) -> str:
        """Generate error handling test code."""
        return f"""
    # Arrange
    invalid_input = create_invalid_input_for_{method_name}()

    # Act & Assert
    with pytest.raises(ExpectedExceptionType) as exc_info:
        target_object.{method_name}(invalid_input)

    assert "expected error message" in str(exc_info.value)
    assert exc_info.value.args[0] is not None
"""

    def _generate_edge_case_test(
        self, method_name: str, code_analysis: CodeAnalysis
    ) -> str:
        """Generate edge case test code."""
        return f"""
    # Test various edge cases
    edge_cases = [
        (None, "null input"),
        ("", "empty string"),
        ([], "empty list"),
        (float('inf'), "infinity"),
        (-1, "negative value")
    ]

    for edge_case_input, description in edge_cases:
        try:
            result = target_object.{method_name}(edge_case_input)
            assert validate_edge_case_result(result, description)
        except ExpectedExceptionType:
            # Expected exception for this edge case
            pass
"""

    def _generate_boundary_test(
        self, method_name: str, code_analysis: CodeAnalysis
    ) -> str:
        """Generate boundary condition test code."""
        return f"""
    # Test boundary conditions
    boundaries = [
        (0, "zero boundary"),
        (1, "minimum valid"),
        (MAX_VALUE, "maximum valid"),
        (MAX_VALUE + 1, "above maximum")
    ]

    for boundary_value, description in boundaries:
        if is_valid_boundary(boundary_value):
            result = target_object.{method_name}(boundary_value)
            assert validate_boundary_result(result, description)
        else:
            with pytest.raises(ValueError):
                target_object.{method_name}(boundary_value)
"""

    def _generate_generic_test(
        self, method_name: str, category: str, code_analysis: CodeAnalysis
    ) -> str:
        """Generate generic test code."""
        return f"""
    # Test {category.replace("_", " ")} for {method_name}
    # Arrange
    test_setup = prepare_test_for_{category}()

    # Act
    result = target_object.{method_name}(test_setup.input)

    # Assert
    assert result is not None
    assert validate_{category}_result(result, test_setup.expected)
"""

    # Fixture generation helper methods

    def _generate_temp_dir_fixture_setup(self) -> str:
        """Generate temporary directory fixture setup code."""
        return """
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
"""

    def _generate_temp_dir_fixture_cleanup(self) -> str:
        """Generate temporary directory fixture cleanup code."""
        return """
    shutil.rmtree(temp_path, ignore_errors=True)
"""

    def _generate_mock_fixture_setup(self, fixture_name: str) -> str:
        """Generate mock fixture setup code."""
        return f"""
    mock_obj = Mock()
    mock_obj.configure_mock(**{fixture_name}_configuration())
    return mock_obj
"""

    def _generate_sample_data_fixture_setup(self, fixture_name: str) -> str:
        """Generate sample data fixture setup code."""
        return f"""
    return {{
        'valid_data': create_valid_{fixture_name}(),
        'invalid_data': create_invalid_{fixture_name}(),
        'edge_cases': create_edge_case_{fixture_name}()
    }}
"""

    # Utility and helper methods

    def _extract_module_name(self, code_path: str) -> str:
        """Extract module name from code path."""
        return Path(code_path).stem

    def _determine_fixtures_needed(
        self, code_analysis: CodeAnalysis, test_methods: List[Dict]
    ) -> List[str]:
        """Determine what fixtures are needed for tests."""
        fixtures = set()

        # Add common fixtures
        fixtures.add("temp_dir")

        # Add fixtures based on dependencies
        if any("mock" in dep.lower() for dep in code_analysis.dependencies):
            fixtures.add("mock_dependencies")

        if any("config" in dep.lower() for dep in code_analysis.dependencies):
            fixtures.add("test_config")

        # Add fixtures based on test methods
        for method in test_methods:
            if "data" in method["name"]:
                fixtures.add("sample_data")
            if "integration" in method["name"]:
                fixtures.add("integration_setup")

        return list(fixtures)

    def _determine_setup_requirements(self, code_analysis: CodeAnalysis) -> List[str]:
        """Determine test setup requirements."""
        requirements = []

        if code_analysis.dependencies:
            requirements.append("Mock external dependencies")

        if any("file" in dep.lower() for dep in code_analysis.dependencies):
            requirements.append("Setup temporary file system")

        if code_analysis.complexity_score > 5:
            requirements.append("Setup complex test scenarios")

        return requirements

    def _determine_cleanup_requirements(self, code_analysis: CodeAnalysis) -> List[str]:
        """Determine test cleanup requirements."""
        requirements = []

        if any("file" in dep.lower() for dep in code_analysis.dependencies):
            requirements.append("Cleanup temporary files")

        if any(
            "db" in dep.lower() or "database" in dep.lower()
            for dep in code_analysis.dependencies
        ):
            requirements.append("Cleanup database state")

        requirements.append("Reset global state")

        return requirements

    def _determine_test_fixtures(
        self, test_code: str, code_analysis: CodeAnalysis
    ) -> List[str]:
        """Determine which fixtures a test needs."""
        fixtures = []

        if "temp" in test_code.lower() or "file" in test_code.lower():
            fixtures.append("temp_dir")

        if "mock" in test_code.lower():
            fixtures.append("mock_dependencies")

        if "config" in test_code.lower():
            fixtures.append("test_config")

        if "sample" in test_code.lower() or "data" in test_code.lower():
            fixtures.append("sample_data")

        return fixtures

    def _generate_test_setup(self, method_name: str, fixtures_used: List[str]) -> str:
        """Generate test setup code."""
        if not fixtures_used:
            return (
                f"# Setup for {method_name} test\ntarget_object = create_test_target()"
            )

        return f"""
    # Setup for {method_name} test
    target_object = create_test_target()
    # Using fixtures: {", ".join(fixtures_used)}
"""

    def _generate_assertions(self, method_name: str, category: str) -> str:
        """Generate appropriate assertions for test."""
        return f"""
    # Verify {category} behavior for {method_name}
    assert result is not None
    assert validate_{category}_behavior(result)
"""

    def _generate_test_cleanup(self, fixtures_used: List[str]) -> str:
        """Generate test cleanup code."""
        if not fixtures_used:
            return "# No additional cleanup required"

        return f"""
    # Cleanup after test
    # Fixtures handle automatic cleanup: {", ".join(fixtures_used)}
"""

    def _generate_test_documentation(
        self,
        test_method: Dict[str, Any],
        code_analysis: CodeAnalysis,
        tdd_context: Dict[str, Any],
    ) -> str:
        """Generate comprehensive test documentation."""
        return f'''"""
{test_method["purpose"]}

Target: {test_method["target_method"]}
Category: {test_method["category"]}
TDD Context: {"Yes" if tdd_context["is_tdd_scenario"] else "No"}

This test ensures:
- Correct behavior under {test_method["category"]} conditions
- Proper error handling and edge cases
- Idempotent execution
- Resource cleanup

Validation Strategy:
- Setup appropriate test conditions
- Execute target functionality
- Verify expected outcomes
- Confirm side effects and state changes
"""'''

    def _check_test_idempotency(self, test_code: str) -> bool:
        """Check if test appears to be idempotent."""
        # Basic heuristics for idempotency
        non_idempotent_patterns = ["append", "+=", "global ", "os.environ["]
        return not any(pattern in test_code for pattern in non_idempotent_patterns)

    def _check_test_patterns(self, test_code: str) -> bool:
        """Check if test follows good patterns."""
        has_arrange = any(comment in test_code for comment in ["# Arrange", "# Setup"])
        has_act = any(comment in test_code for comment in ["# Act", "# Execute"])
        has_assert = any(comment in test_code for comment in ["# Assert", "# Verify"])

        return has_arrange and has_act and has_assert

    def _identify_coverage_gaps(
        self, code_path: str, tests_created: List[TestSpec]
    ) -> List[str]:
        """Identify potential coverage gaps."""
        gaps = []

        # This would typically use coverage analysis tools
        # For now, provide basic gap analysis

        covered_methods = set()
        for test in tests_created:
            covered_methods.update(test.coverage_areas)

        if len(covered_methods) < 3:
            gaps.append("Limited method coverage")

        error_tests = [test for test in tests_created if "error" in test.name]
        if len(error_tests) == 0:
            gaps.append("No error handling tests")

        edge_tests = [test for test in tests_created if "edge" in test.name]
        if len(edge_tests) == 0:
            gaps.append("No edge case tests")

        return gaps

    # Fix methods for shared instruction issues

    def _fix_structure_issues(self, test_code: str, issues: List[str]) -> str:
        """Fix test structure issues."""
        # Basic fixes for common structure issues
        if "Test should have a descriptive docstring" in issues:
            if '"""' not in test_code:
                # Add basic docstring
                lines = test_code.split("\n")
                for i, line in enumerate(lines):
                    if "def test_" in line:
                        lines.insert(i + 1, '    """Test description needed."""')
                        break
                test_code = "\n".join(lines)

        return test_code

    def _fix_dependency_issues(self, test_code: str, issues: List[str]) -> str:
        """Fix test dependency issues."""
        # Add mocking for external dependencies
        if "External dependencies should be mocked" in issues:
            # Add mock imports and setup
            if "import" not in test_code:
                test_code = "from unittest.mock import Mock, patch\n" + test_code

        return test_code

    def _fix_parallel_safety_issues(self, test_code: str, issues: List[str]) -> str:
        """Fix parallel safety issues."""
        # Replace fixed ports/paths with dynamic ones
        for issue in issues:
            if "fixed ports" in issue:
                test_code = test_code.replace("port=8080", "port=get_random_port()")
            elif "fixed paths" in issue:
                test_code = test_code.replace("/tmp/", "temp_dir / ")

        return test_code

    def _describe_test_strategy(self, test: TestSpec) -> str:
        """Describe the test strategy."""
        return f"Test {test.test_type.value} functionality using {len(test.fixtures_used)} fixtures"

    def _format_test_requirements(
        self, test: TestSpec, code_analysis: CodeAnalysis
    ) -> str:
        """Format test requirements."""
        requirements = code_analysis.test_requirements
        if not requirements:
            requirements = ["Basic functionality validation"]
        return "\n".join(f"- {req}" for req in requirements)

    def _describe_test_setup(self, test: TestSpec) -> str:
        """Describe test setup."""
        return f"Initialize test environment with {len(test.fixtures_used)} fixtures"

    def _describe_test_action(self, test: TestSpec) -> str:
        """Describe test action."""
        return f"Execute target functionality for {test.purpose}"

    def _describe_test_verification(self, test: TestSpec) -> str:
        """Describe test verification."""
        return f"Verify results and validate {', '.join(test.coverage_areas)}"

    def _describe_test_dependencies(self, test: TestSpec) -> str:
        """Describe test dependencies."""
        return f"Fixtures: {', '.join(test.fixtures_used) if test.fixtures_used else 'None'}"

    def _create_error_result(
        self, code_path: str, error_message: str
    ) -> TestWriterResult:
        """Create error result when test creation fails."""
        return TestWriterResult(
            module_name=self._extract_module_name(code_path),
            tests_created=[],
            fixtures_created=[],
            coverage_analysis={"error": error_message},
            tdd_alignment={
                "design_guidance_provided": False,
                "interfaces_specified": False,
                "behaviors_documented": False,
            },
            quality_metrics={"error": True},
            validation_results=[f"Error creating tests: {error_message}"],
        )
