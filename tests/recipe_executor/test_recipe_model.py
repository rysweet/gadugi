"""Comprehensive tests for recipe_model.py."""

import pytest
from pathlib import Path
from datetime import datetime
from typing import Any

from src.recipe_executor.recipe_model import (
    ComponentType,
    RequirementPriority,
    Requirement,
    Requirements,
    ComponentDesign,
    Interface,
    Design,
    Components,
    RecipeMetadata,
    Recipe,
    BuildContext,
    GeneratedCode,
    RecipeTestSuite,
    ValidationResult,
    BuildResult,
    SingleBuildResult,
)


class TestComponentType:
    """Test ComponentType enum."""

    def test_component_types_exist(self) -> None:
        """Test that all component types are defined."""
        assert ComponentType.SERVICE.value == "service"
        assert ComponentType.AGENT.value == "agent"
        assert ComponentType.LIBRARY.value == "library"
        assert ComponentType.TOOL.value == "tool"
        assert ComponentType.CORE.value == "core"

    def test_component_type_from_string(self) -> None:
        """Test creating ComponentType from string."""
        assert ComponentType("service") == ComponentType.SERVICE
        assert ComponentType("agent") == ComponentType.AGENT


class TestRequirementPriority:
    """Test RequirementPriority enum."""

    def test_priority_levels(self) -> None:
        """Test all priority levels exist."""
        assert RequirementPriority.MUST.value == "must"
        assert RequirementPriority.SHOULD.value == "should"
        assert RequirementPriority.COULD.value == "could"
        assert RequirementPriority.WONT.value == "wont"


class TestRequirement:
    """Test Requirement dataclass."""

    def test_requirement_creation(self) -> None:
        """Test creating a requirement."""
        req = Requirement(
            id="req_1",
            description="MUST implement feature X",
            priority=RequirementPriority.MUST,
        )
        assert req.id == "req_1"
        assert req.description == "MUST implement feature X"
        assert req.priority == RequirementPriority.MUST
        assert req.validation_criteria == []
        assert req.implemented is False

    def test_requirement_with_validation_criteria(self) -> None:
        """Test requirement with validation criteria."""
        req = Requirement(
            id="req_2",
            description="SHOULD handle errors",
            priority=RequirementPriority.SHOULD,
            validation_criteria=["No unhandled exceptions", "Proper error messages"],
        )
        assert len(req.validation_criteria) == 2
        assert "No unhandled exceptions" in req.validation_criteria


class TestRequirements:
    """Test Requirements dataclass."""

    @pytest.fixture
    def sample_requirements(self) -> Requirements:
        """Create sample requirements for testing."""
        functional = [
            Requirement("req_1", "MUST parse files", RequirementPriority.MUST),
            Requirement("req_2", "SHOULD validate input", RequirementPriority.SHOULD),
        ]
        non_functional = [
            Requirement("req_3", "MUST be fast", RequirementPriority.MUST),
            Requirement("req_4", "COULD use caching", RequirementPriority.COULD),
        ]
        return Requirements(
            purpose="Test component",
            functional_requirements=functional,
            non_functional_requirements=non_functional,
            success_criteria=["All tests pass", "No errors"],
        )

    def test_get_all_requirements(self, sample_requirements: Requirements) -> None:
        """Test getting all requirements."""
        all_reqs = sample_requirements.get_all_requirements()
        assert len(all_reqs) == 4
        assert all_reqs[0].id == "req_1"
        assert all_reqs[2].id == "req_3"

    def test_get_must_requirements(self, sample_requirements: Requirements) -> None:
        """Test getting only MUST requirements."""
        must_reqs = sample_requirements.get_must_requirements()
        assert len(must_reqs) == 2
        assert all(req.priority == RequirementPriority.MUST for req in must_reqs)


class TestComponentDesign:
    """Test ComponentDesign dataclass."""

    def test_component_design_creation(self) -> None:
        """Test creating a component design."""
        design = ComponentDesign(
            name="Parser",
            description="Parses recipe files",
            class_name="RecipeParser",
            methods=["parse", "validate"],
        )
        assert design.name == "Parser"
        assert design.class_name == "RecipeParser"
        assert "parse" in design.methods
        assert design.properties == []
        assert design.code_snippet is None


class TestDesign:
    """Test Design dataclass."""

    def test_get_component_by_name(self) -> None:
        """Test finding component by name."""
        components = [
            ComponentDesign("Parser", "Parses files"),
            ComponentDesign("Generator", "Generates code"),
        ]
        design = Design(
            architecture="Layered architecture",
            components=components,
            interfaces=[],
            implementation_notes="Use Python 3.10+",
        )

        parser = design.get_component_by_name("Parser")
        assert parser is not None
        assert parser.description == "Parses files"

        missing = design.get_component_by_name("NonExistent")
        assert missing is None


class TestComponents:
    """Test Components dataclass."""

    def test_components_creation(self) -> None:
        """Test creating components metadata."""
        components = Components(
            name="test-recipe",
            version="1.0.0",
            type=ComponentType.LIBRARY,
            dependencies=["base-recipe"],
            description="Test recipe",
        )
        assert components.name == "test-recipe"
        assert components.version == "1.0.0"
        assert components.type == ComponentType.LIBRARY
        assert "base-recipe" in components.dependencies

    def test_is_self_hosting(self) -> None:
        """Test self-hosting detection."""
        components = Components(
            name="recipe-executor",
            version="1.0.0",
            type=ComponentType.CORE,
            metadata={"self_hosting": True},
        )
        assert components.is_self_hosting() is True

        regular = Components(
            name="regular",
            version="1.0.0",
            type=ComponentType.LIBRARY,
        )
        assert regular.is_self_hosting() is False

    def test_requires_bootstrap(self) -> None:
        """Test bootstrap requirement detection."""
        components = Components(
            name="recipe-executor",
            version="1.0.0",
            type=ComponentType.CORE,
            metadata={"bootstrap_required": True},
        )
        assert components.requires_bootstrap() is True


class TestRecipe:
    """Test Recipe dataclass."""

    @pytest.fixture
    def sample_recipe(self) -> Recipe:
        """Create a sample recipe for testing."""
        requirements = Requirements(
            purpose="Test",
            functional_requirements=[],
            non_functional_requirements=[],
            success_criteria=[],
        )
        design = Design(
            architecture="Simple",
            components=[],
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

    def test_recipe_creation(self, sample_recipe: Recipe) -> None:
        """Test creating a recipe."""
        assert sample_recipe.name == "test-recipe"
        assert sample_recipe.path == Path("recipes/test-recipe")
        assert sample_recipe.components.version == "1.0.0"

    def test_recipe_name_mismatch_raises_error(self) -> None:
        """Test that mismatched names raise an error."""
        requirements = Requirements("", [], [], [])
        design = Design("", [], [], "")
        components = Components("different-name", "1.0.0", ComponentType.LIBRARY)
        metadata = RecipeMetadata(datetime.now(), datetime.now())

        with pytest.raises(ValueError, match="Recipe name mismatch"):
            Recipe(
                name="test-recipe",
                path=Path("recipes/test-recipe"),
                requirements=requirements,
                design=design,
                components=components,
                metadata=metadata,
            )

    def test_get_dependencies(self, sample_recipe: Recipe) -> None:
        """Test getting recipe dependencies."""
        sample_recipe.components.dependencies = ["dep1", "dep2"]
        deps = sample_recipe.get_dependencies()
        assert len(deps) == 2
        assert "dep1" in deps
        assert "dep2" in deps

    def test_get_output_path(self, sample_recipe: Recipe) -> None:
        """Test getting output path."""
        sample_recipe.name = "test-recipe"
        path = sample_recipe.get_output_path()
        assert path == Path("src/test_recipe")

    def test_is_valid(self, sample_recipe: Recipe) -> None:
        """Test recipe validation."""
        # Empty recipe is invalid
        assert sample_recipe.is_valid() is False

        # Add requirements
        sample_recipe.requirements.functional_requirements.append(
            Requirement("req_1", "Test", RequirementPriority.MUST)
        )
        # Still invalid without components
        assert sample_recipe.is_valid() is False

        # Add component
        sample_recipe.design.components.append(ComponentDesign("Test", "Test component"))
        # Now valid
        assert sample_recipe.is_valid() is True


class TestBuildContext:
    """Test BuildContext dataclass."""

    @pytest.fixture
    def sample_recipe(self) -> Recipe:
        """Create a sample recipe for testing."""
        requirements = Requirements("", [], [], [])
        design = Design("", [], [], "")
        components = Components("test", "1.0.0", ComponentType.LIBRARY)
        metadata = RecipeMetadata(datetime.now(), datetime.now())
        return Recipe("test", Path("test"), requirements, design, components, metadata)

    def test_build_context_creation(self, sample_recipe: Recipe) -> None:
        """Test creating build context."""
        context = BuildContext(
            recipe=sample_recipe,
            dry_run=True,
            verbose=True,
        )
        assert context.recipe == sample_recipe
        assert context.dry_run is True
        assert context.verbose is True
        assert context.force_rebuild is False

    def test_dependency_management(self, sample_recipe: Recipe) -> None:
        """Test dependency get/has methods."""
        context = BuildContext(
            recipe=sample_recipe,
            dependencies={"dep1": "value1"},
        )
        assert context.has_dependency("dep1") is True
        assert context.has_dependency("dep2") is False
        assert context.get_dependency("dep1") == "value1"
        assert context.get_dependency("dep2") is None


class TestGeneratedCode:
    """Test GeneratedCode dataclass."""

    def test_generated_code_creation(self) -> None:
        """Test creating generated code."""
        code = GeneratedCode(
            recipe_name="test",
            files={"src/test.py": "print('hello')"},
        )
        assert code.recipe_name == "test"
        assert code.language == "python"
        assert "src/test.py" in code.files

    def test_add_file(self) -> None:
        """Test adding files to generated code."""
        code = GeneratedCode(recipe_name="test", files={})
        code.add_file("src/main.py", "def main(): pass")
        assert "src/main.py" in code.files
        assert code.get_file("src/main.py") == "def main(): pass"

    def test_get_file(self) -> None:
        """Test getting file content."""
        code = GeneratedCode(
            recipe_name="test",
            files={"src/test.py": "content"},
        )
        assert code.get_file("src/test.py") == "content"
        assert code.get_file("nonexistent") is None


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_creation(self) -> None:
        """Test creating validation result."""
        result = ValidationResult(
            recipe_name="test",
            passed=True,
            requirements_coverage={"req_1": True, "req_2": False},
            design_compliance={"Parser": True},
            quality_gates={"pyright": True, "ruff": True},
        )
        assert result.recipe_name == "test"
        assert result.passed is True

    def test_get_coverage_percentage(self) -> None:
        """Test calculating coverage percentage."""
        result = ValidationResult(
            recipe_name="test",
            passed=True,
            requirements_coverage={"req_1": True, "req_2": True, "req_3": False},
            design_compliance={},
            quality_gates={},
        )
        assert result.get_coverage_percentage() == pytest.approx(66.67, rel=0.01)

    def test_get_coverage_percentage_empty(self) -> None:
        """Test coverage percentage with no requirements."""
        result = ValidationResult(
            recipe_name="test",
            passed=True,
            requirements_coverage={},
            design_compliance={},
            quality_gates={},
        )
        assert result.get_coverage_percentage() == 0.0

    def test_get_failed_requirements(self) -> None:
        """Test getting failed requirements."""
        result = ValidationResult(
            recipe_name="test",
            passed=False,
            requirements_coverage={"req_1": True, "req_2": False, "req_3": False},
            design_compliance={},
            quality_gates={},
        )
        failed = result.get_failed_requirements()
        assert len(failed) == 2
        assert "req_2" in failed
        assert "req_3" in failed


class TestBuildResult:
    """Test BuildResult dataclass."""

    @pytest.fixture
    def sample_recipe(self) -> Recipe:
        """Create sample recipe."""
        requirements = Requirements("", [], [], [])
        design = Design("", [], [], "")
        components = Components("test", "1.0.0", ComponentType.LIBRARY)
        metadata = RecipeMetadata(datetime.now(), datetime.now())
        return Recipe("test", Path("test"), requirements, design, components, metadata)

    def test_get_failed_recipes(self, sample_recipe: Recipe) -> None:
        """Test getting failed recipe names."""
        results = [
            SingleBuildResult(
                recipe=sample_recipe,
                code=None,
                tests=None,
                validation=None,
                quality_result={},
                success=False,
                build_time=1.0,
            ),
            SingleBuildResult(
                recipe=sample_recipe,
                code=None,
                tests=None,
                validation=None,
                quality_result={},
                success=True,
                build_time=1.0,
            ),
        ]
        build_result = BuildResult(results=results, success=False, total_time=2.0)
        failed = build_result.get_failed_recipes()
        assert len(failed) == 1
        assert "test" in failed

    def test_get_successful_recipes(self, sample_recipe: Recipe) -> None:
        """Test getting successful recipe names."""
        results = [
            SingleBuildResult(
                recipe=sample_recipe,
                code=None,
                tests=None,
                validation=None,
                quality_result={},
                success=True,
                build_time=1.0,
            ),
        ]
        build_result = BuildResult(results=results, success=True, total_time=1.0)
        successful = build_result.get_successful_recipes()
        assert len(successful) == 1
        assert "test" in successful
