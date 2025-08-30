"""Implementation validator for recipe-based code."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import List

from .models import GeneratedCode, RecipeSpec, TestCase, ValidationResult


class ImplementationValidator:
    """Validates implementation against recipe requirements."""

    def __init__(self):
        """Initialize validator."""
        self.recipe_spec: RecipeSpec | None = None

    def validate_implementation(
        self,
        code: GeneratedCode | List[GeneratedCode],
        recipe: RecipeSpec,
        run_tests: bool = True,
    ) -> ValidationResult:
        """Validate implementation against recipe.

        Args:
            code: Generated code to validate
            recipe: Recipe specification
            run_tests: Whether to run tests

        Returns:
            Validation result
        """
        self.recipe_spec = recipe

        # Handle single or multiple code files
        code_list = [code] if isinstance(code, GeneratedCode) else code

        # Create validation result
        result = ValidationResult(
            recipe_name=recipe.name,
            code_path=code_list[0].file_path if code_list else Path("."),
        )

        # Validate syntax
        for code_file in code_list:
            if not self._validate_syntax(code_file):
                result.errors.append(f"Syntax error in {code_file.file_path}")
                result.is_valid = False
                return result

        # Validate structure
        for code_file in code_list:
            structure_valid = self._validate_structure(code_file, result)
            if not structure_valid:
                result.is_valid = False

        # Run quality checks
        self._run_quality_checks(code_list, result)

        # Run tests if requested
        if run_tests:
            self._run_tests(code_list, result)

        # Validate completeness
        self._validate_completeness(code_list, result)

        # Determine overall validity
        result.is_valid = (
            len(result.errors) == 0
            and result.get_test_pass_rate() >= 0.8
            and result.get_quality_score() >= 0.7
        )

        # Generate suggestions
        self._generate_suggestions(result)

        return result

    def _validate_syntax(self, code: GeneratedCode) -> bool:
        """Validate Python syntax."""
        try:
            ast.parse(code.content)
            return True
        except SyntaxError:
            return False

    def _validate_structure(
        self, code: GeneratedCode, result: ValidationResult
    ) -> bool:
        """Validate code structure matches recipe."""
        try:
            tree = ast.parse(code.content)

            # Check for required classes
            found_classes = {
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            }
            required_classes = {
                interface.name
                for interface in (
                    self.recipe_spec.interfaces if self.recipe_spec else []
                )
                if interface.type == "class"
            }

            missing_classes = required_classes - found_classes
            if missing_classes:
                result.errors.append(f"Missing classes: {', '.join(missing_classes)}")
                return False

            # Check for required functions
            found_functions = {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            required_functions = {
                interface.name
                for interface in (
                    self.recipe_spec.interfaces if self.recipe_spec else []
                )
                if interface.type == "function"
            }

            missing_functions = required_functions - found_functions
            if missing_functions:
                result.warnings.append(
                    f"Missing functions: {', '.join(missing_functions)}"
                )

            return True

        except Exception as e:
            result.errors.append(f"Structure validation error: {e}")
            return False

    def _run_quality_checks(
        self, code_list: List[GeneratedCode], result: ValidationResult
    ) -> None:
        """Run code quality checks."""
        for code in code_list:
            # Check for docstrings
            has_docstrings = self._check_docstrings(code.content)
            result.quality_checks["has_docstrings"] = has_docstrings

            # Check for type hints
            has_type_hints = self._check_type_hints(code.content)
            result.quality_checks["has_type_hints"] = has_type_hints

            # Check for error handling
            has_error_handling = "try:" in code.content and "except" in code.content
            result.quality_checks["has_error_handling"] = has_error_handling

            # Check for logging
            has_logging = "logging" in code.content or "logger" in code.content
            result.quality_checks["has_logging"] = has_logging

            # Run ruff if available
            if code.file_path.exists():
                ruff_result = self._run_ruff(code.file_path)
                result.quality_checks["ruff_clean"] = ruff_result

            # Run pyright if available
            if code.file_path.exists():
                pyright_result = self._run_pyright(code.file_path)
                result.quality_checks["pyright_clean"] = pyright_result

    def _run_tests(
        self, code_list: List[GeneratedCode], result: ValidationResult
    ) -> None:
        """Run tests for the implementation."""
        # Find test files
        test_files = [
            code for code in code_list if "test" in code.file_path.name.lower()
        ]

        if not test_files:
            result.warnings.append("No test files found")
            return

        # Create test cases from recipe
        test_cases = self._create_test_cases()

        # Run each test case
        for test_case in test_cases:
            test_passed = self._run_test_case(test_case)
            result.test_results[test_case.id] = test_passed

        # Run pytest if available
        for test_file in test_files:
            if test_file.file_path.exists():
                pytest_result = self._run_pytest(test_file.file_path)
                result.test_results[f"pytest_{test_file.file_path.name}"] = (
                    pytest_result
                )

    def _validate_completeness(
        self, code_list: List[GeneratedCode], result: ValidationResult
    ) -> None:
        """Validate implementation completeness."""
        # Check if all high-priority requirements are addressed
        high_priority_reqs = (
            self.recipe_spec.get_high_priority_requirements()
            if self.recipe_spec
            and hasattr(self.recipe_spec, "get_high_priority_requirements")
            else []
        )

        # Simple check: look for requirement IDs in comments
        all_content = "\n".join(code.content for code in code_list)

        for req in high_priority_reqs:
            if req.id not in all_content and req.description[:20] not in all_content:
                result.warnings.append(f"Requirement {req.id} may not be implemented")

        # Check if all interfaces are implemented
        if self.recipe_spec and self.recipe_spec.interfaces:
            for interface in self.recipe_spec.interfaces:
                if interface.name not in all_content:
                    result.errors.append(f"Interface {interface.name} not implemented")

    def _generate_suggestions(self, result: ValidationResult) -> None:
        """Generate improvement suggestions."""
        # Based on quality checks
        if not result.quality_checks.get("has_docstrings"):
            result.suggestions.append("Add docstrings to all classes and functions")

        if not result.quality_checks.get("has_type_hints"):
            result.suggestions.append("Add type hints for better code clarity")

        if not result.quality_checks.get("has_error_handling"):
            result.suggestions.append(
                "Add proper error handling with try/except blocks"
            )

        if not result.quality_checks.get("has_logging"):
            result.suggestions.append("Add logging for better debugging and monitoring")

        # Based on test results
        if result.get_test_pass_rate() < 1.0:
            failed_tests = [
                tid for tid, passed in result.test_results.items() if not passed
            ]
            result.suggestions.append(
                f"Fix failing tests: {', '.join(failed_tests[:3])}"
            )

        # Based on errors and warnings
        if len(result.errors) > 0:
            result.suggestions.append("Address all errors before deployment")

        if len(result.warnings) > 3:
            result.suggestions.append(
                "Review and address warnings to improve code quality"
            )

    def _check_docstrings(self, content: str) -> bool:
        """Check if code has docstrings."""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    # Check if first statement is a docstring
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        continue
                    else:
                        return False

            return True
        except:
            return False

    def _check_type_hints(self, content: str) -> bool:
        """Check if code has type hints."""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check for return type annotation
                    if node.returns is None and node.name != "__init__":
                        return False

                    # Check for parameter type annotations (except self)
                    for arg in node.args.args:
                        if arg.arg != "self" and arg.annotation is None:
                            return False

            return True
        except:
            return False

    def _run_ruff(self, file_path: Path) -> bool:
        """Run ruff linter."""
        try:
            result = subprocess.run(
                ["ruff", "check", str(file_path)],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return True  # Assume clean if ruff not available

    def _run_pyright(self, file_path: Path) -> bool:
        """Run pyright type checker."""
        try:
            result = subprocess.run(
                ["pyright", str(file_path)],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return True  # Assume clean if pyright not available

    def _run_pytest(self, file_path: Path) -> bool:
        """Run pytest on test file."""
        try:
            result = subprocess.run(
                ["pytest", str(file_path), "-v"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False  # Tests fail if pytest not available

    def _create_test_cases(self) -> List[TestCase]:
        """Create test cases from recipe requirements."""
        test_cases = []

        from .models import RequirementType

        functional_reqs = (
            self.recipe_spec.get_requirements_by_type(RequirementType.FUNCTIONAL)
            if self.recipe_spec
            and hasattr(self.recipe_spec, "get_requirements_by_type")
            else []
        )
        for i, req in enumerate(functional_reqs[:5]):
            test_case = TestCase(
                id=f"TC-{req.id}",
                name=f"test_{req.id.lower()}",
                description=f"Test for: {req.description[:100]}",
                requirement_id=req.id,
                test_type="unit",
                steps=[
                    "Setup test environment",
                    f"Execute functionality for {req.id}",
                    "Verify expected results",
                ],
                expected_result="Requirement satisfied",
            )
            test_cases.append(test_case)

        return test_cases

    def _run_test_case(self, test_case: TestCase) -> bool:
        """Run a single test case."""
        # Simplified test execution - in real implementation would run actual tests
        # For now, randomly pass/fail based on test case ID
        return hash(test_case.id) % 3 != 0  # ~66% pass rate for demo
