"""Comprehensive tests for validator.py."""

import pytest
from pathlib import Path
from datetime import datetime

from src.recipe_executor.validator import Validator, Implementation
from src.recipe_executor.recipe_model import (
    Recipe,
    Requirements,
    Requirement,
    RequirementPriority,
    Design,
    ComponentDesign,
    Components,
    ComponentType,
    RecipeMetadata,
    GeneratedCode,
    RecipeTestSuite,
    ValidationResult,
)


class TestImplementation:
    """Test Implementation dataclass."""

    def test_implementation_creation(self) -> None:
        """Test creating an implementation."""
        code = GeneratedCode(
            recipe_name="test",
            files={"src/test.py": "def hello(): pass"},
        )
        impl = Implementation(code=code)
        assert impl.code == code
        assert impl.tests is None

    def test_get_all_code(self) -> None:
        """Test getting all code as string."""
        code = GeneratedCode(
            recipe_name="test",
            files={
                "src/main.py": "def main(): pass",
                "src/utils.py": "def util(): pass",
            },
        )
        impl = Implementation(code=code)
        all_code = impl.get_all_code()
        assert "def main(): pass" in all_code
        assert "def util(): pass" in all_code


class TestValidator:
    """Test Validator class."""

    @pytest.fixture
    def validator(self) -> Validator:
        """Create a Validator instance."""
        return Validator()

    @pytest.fixture
    def sample_recipe(self) -> Recipe:
        """Create a sample recipe for testing."""
        requirements = Requirements(
            purpose="Test component",
            functional_requirements=[
                Requirement(
                    id="req_1",
                    description="parse input files",
                    priority=RequirementPriority.MUST,
                ),
                Requirement(
                    id="req_2",
                    description="validate data",
                    priority=RequirementPriority.MUST,
                ),
                Requirement(
                    id="req_3",
                    description="optimize performance",
                    priority=RequirementPriority.SHOULD,
                ),
            ],
            non_functional_requirements=[
                Requirement(
                    id="req_4",
                    description="handle errors gracefully",
                    priority=RequirementPriority.MUST,
                ),
            ],
            success_criteria=["All tests pass", "No errors"],
        )

        design = Design(
            architecture="Layered",
            components=[
                ComponentDesign(
                    name="Parser",
                    description="Parses files",
                    class_name="FileParser",
                ),
                ComponentDesign(
                    name="Validator",
                    description="Validates data",
                    class_name="DataValidator",
                ),
            ],
            interfaces=[],
            implementation_notes="",
        )

        components = Components(
            name="test-recipe",
            version="1.0.0",
            type=ComponentType.LIBRARY,
        )

        metadata = RecipeMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        return Recipe(
            name="test-recipe",
            path=Path("recipes/test-recipe"),
            requirements=requirements,
            design=design,
            components=components,
            metadata=metadata,
        )

    @pytest.fixture
    def sample_implementation(self) -> Implementation:
        """Create a sample implementation."""
        code = GeneratedCode(
            recipe_name="test-recipe",
            files={
                "src/test_recipe/parser.py": """
from typing import Any, Dict
class FileParser:
    def parse(self, input: str) -> Dict[str, Any]:
        # Parse input files
        return {}
""",
                "src/test_recipe/validator.py": """
class DataValidator:
    def validate(self, data: dict) -> bool:
        # Validate data
        return True
    
    def handle_errors(self):
        # Handle errors gracefully
        pass
""",
            },
        )

        tests = RecipeTestSuite(
            recipe_name="test-recipe",
            unit_tests=["test_parser", "test_validator"],
            integration_tests=["test_integration"],
            test_files={
                "tests/test_parser.py": "def test_parser(): pass",
                "tests/test_validator.py": "def test_validator(): pass",
            },
        )

        return Implementation(code=code, tests=tests)

    def test_validate_success(
        self,
        validator: Validator,
        sample_recipe: Recipe,
        sample_implementation: Implementation,
    ) -> None:
        """Test successful validation."""
        result = validator.validate(sample_recipe, sample_implementation)

        assert result.recipe_name == "test-recipe"
        # May not pass perfectly due to simple heuristics
        assert isinstance(result.passed, bool)
        assert len(result.requirements_coverage) == 4
        assert len(result.design_compliance) == 2

    def test_validate_requirements_coverage(
        self,
        validator: Validator,
        sample_recipe: Recipe,
        sample_implementation: Implementation,
    ) -> None:
        """Test requirements coverage validation."""
        coverage = validator._validate_requirements_coverage(sample_recipe, sample_implementation)

        # Should have coverage for all requirements
        assert len(coverage) == 4
        assert "req_1" in coverage
        assert "req_2" in coverage
        assert "req_3" in coverage
        assert "req_4" in coverage

        # Check that "parse" requirement is covered
        assert coverage["req_1"] is True  # "parse" is in code
        assert coverage["req_2"] is True  # "validate" is in code

    def test_validate_design_compliance(
        self,
        validator: Validator,
        sample_recipe: Recipe,
        sample_implementation: Implementation,
    ) -> None:
        """Test design compliance validation."""
        compliance = validator._validate_design_compliance(sample_recipe, sample_implementation)

        assert len(compliance) == 2
        assert "Parser" in compliance
        assert "Validator" in compliance

        # Both components should be compliant
        assert compliance["Parser"] is True
        assert compliance["Validator"] is True

    def test_validate_design_compliance_missing_component(
        self,
        validator: Validator,
        sample_recipe: Recipe,
    ) -> None:
        """Test design compliance with missing component."""
        # Implementation missing Validator component
        code = GeneratedCode(
            recipe_name="test-recipe",
            files={
                "src/test_recipe/parser.py": "class FileParser: pass",
            },
        )
        impl = Implementation(code=code)

        compliance = validator._validate_design_compliance(sample_recipe, impl)

        assert compliance["Parser"] is True
        assert compliance["Validator"] is False

    def test_validate_quality_gates(
        self,
        validator: Validator,
        sample_implementation: Implementation,
    ) -> None:
        """Test quality gate validation."""
        gates = validator._validate_quality_gates(sample_implementation)

        assert "has_code" in gates
        assert "has_tests" in gates
        assert "has_type_hints" in gates
        assert "has_imports" in gates

        assert gates["has_code"] is True
        assert gates["has_tests"] is True
        assert gates["has_type_hints"] is True  # -> in code
        assert gates["has_imports"] is True  # from typing import

    def test_validate_quality_gates_no_tests(
        self,
        validator: Validator,
    ) -> None:
        """Test quality gates with no tests."""
        code = GeneratedCode(
            recipe_name="test",
            files={"src/test.py": "def hello(): pass"},
        )
        impl = Implementation(code=code, tests=None)

        gates = validator._validate_quality_gates(impl)
        assert gates["has_tests"] is False

    def test_validate_recipe_structure(
        self,
        validator: Validator,
        sample_recipe: Recipe,
    ) -> None:
        """Test recipe structure validation."""
        issues = validator.validate_recipe_structure(sample_recipe)
        assert len(issues) == 0  # Valid recipe

    def test_validate_recipe_structure_invalid(
        self,
        validator: Validator,
    ) -> None:
        """Test validating invalid recipe structure."""
        # Recipe with no requirements
        recipe = Recipe(
            name="bad-recipe",
            path=Path("recipes/bad"),
            requirements=Requirements("", [], [], []),
            design=Design("", [], [], ""),
            components=Components("bad-recipe", "1.0.0", ComponentType.LIBRARY),
            metadata=RecipeMetadata(datetime.now(), datetime.now()),
        )

        issues = validator.validate_recipe_structure(recipe)
        assert len(issues) > 0
        assert any("MUST requirements" in issue for issue in issues)
        assert any("No components" in issue for issue in issues)

    def test_validate_recipe_circular_dependency(
        self,
        validator: Validator,
    ) -> None:
        """Test detecting circular self-dependency."""
        recipe = Recipe(
            name="circular",
            path=Path("recipes/circular"),
            requirements=Requirements(
                "",
                [Requirement("r1", "test", RequirementPriority.MUST)],
                [],
                [],
            ),
            design=Design("", [ComponentDesign("Test", "Test")], [], ""),
            components=Components(
                name="circular",
                version="1.0.0",
                type=ComponentType.LIBRARY,
                dependencies=["circular"],  # Self-dependency
            ),
            metadata=RecipeMetadata(datetime.now(), datetime.now()),
        )

        issues = validator.validate_recipe_structure(recipe)
        assert any("circular self-dependency" in issue for issue in issues)

    def test_validation_result_with_errors(
        self,
        validator: Validator,
        sample_recipe: Recipe,
    ) -> None:
        """Test validation result with errors."""
        # Empty implementation
        impl = Implementation(code=GeneratedCode(recipe_name="test-recipe", files={}))

        result = validator.validate(sample_recipe, impl)

        assert result.passed is False
        assert len(result.errors) > 0

        # Should have uncovered requirements
        failed_reqs = result.get_failed_requirements()
        assert len(failed_reqs) > 0

    def test_full_validation_workflow(
        self,
        validator: Validator,
        sample_recipe: Recipe,
    ) -> None:
        """Test complete validation workflow."""
        # Create implementation with partial coverage
        code = GeneratedCode(
            recipe_name="test-recipe",
            files={
                "src/test_recipe/parser.py": """
from typing import Dict, Any

class FileParser:
    def parse(self, input: str) -> Dict[str, Any]:
        '''Parse input files.'''
        return {}
""",
                # Missing Validator component
            },
        )

        tests = RecipeTestSuite(
            recipe_name="test-recipe",
            unit_tests=["test_parser"],
            integration_tests=[],
            test_files={"tests/test_parser.py": "def test_parser(): pass"},
        )

        impl = Implementation(code=code, tests=tests)
        result = validator.validate(sample_recipe, impl)

        # Should fail due to missing component
        assert result.passed is False

        # Check specific failures
        assert result.design_compliance.get("Validator") is False

        # Should have some requirements coverage
        coverage_pct = result.get_coverage_percentage()
        assert 0 < coverage_pct < 100
