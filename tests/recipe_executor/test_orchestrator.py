"""Comprehensive tests for orchestrator.py."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time

from src.recipe_executor.orchestrator import (
    RecipeOrchestrator,
    BuildOptions,
    SingleBuildResult,
)
from src.recipe_executor.recipe_model import (
    Recipe,
    Requirements,
    Design,
    Components,
    RecipeMetadata,
    ComponentType,
    GeneratedCode,
    RecipeTestSuite,
    ValidationResult,
    BuildResult,
    Requirement,
    RequirementPriority,
    ComponentDesign,
)


class TestBuildOptions:
    """Test BuildOptions dataclass."""

    def test_default_options(self) -> None:
        """Test default build options."""
        options = BuildOptions()
        assert options.dry_run is False
        assert options.verbose is False
        assert options.force_rebuild is False
        assert options.parallel is False
        assert options.output_dir is None

    def test_custom_options(self) -> None:
        """Test custom build options."""
        options = BuildOptions(
            dry_run=True,
            verbose=True,
            force_rebuild=True,
            parallel=True,
            output_dir=Path("output"),
        )
        assert options.dry_run is True
        assert options.verbose is True
        assert options.force_rebuild is True
        assert options.parallel is True
        assert options.output_dir == Path("output")


class TestRecipeOrchestrator:
    """Test RecipeOrchestrator class."""

    @pytest.fixture
    def orchestrator(self, tmp_path: Path) -> RecipeOrchestrator:
        """Create an orchestrator instance."""
        return RecipeOrchestrator(recipe_root=tmp_path / "recipes")

    @pytest.fixture
    def sample_recipe(self, tmp_path: Path) -> Recipe:
        """Create a sample recipe for testing."""
        requirements = Requirements(
            purpose="Test component",
            functional_requirements=[
                Requirement("req_1", "parse files", RequirementPriority.MUST),
            ],
            non_functional_requirements=[],
            success_criteria=["All tests pass"],
        )

        design = Design(
            architecture="Layered",
            components=[
                ComponentDesign(
                    name="Parser",
                    description="Parses files",
                    class_name="FileParser",
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
            path=tmp_path / "recipes" / "test-recipe",
            requirements=requirements,
            design=design,
            components=components,
            metadata=metadata,
        )

    def test_orchestrator_initialization(self, tmp_path: Path) -> None:
        """Test orchestrator initialization."""
        orchestrator = RecipeOrchestrator(recipe_root=tmp_path / "recipes")
        assert orchestrator.recipe_root == tmp_path / "recipes"
        assert orchestrator.parser is not None
        assert orchestrator.resolver is not None
        assert orchestrator.generator is not None
        assert orchestrator.test_generator is not None
        assert orchestrator.validator is not None
        assert orchestrator.state_manager is not None
        assert orchestrator.quality_gates is not None

    def test_orchestrator_default_recipe_root(self) -> None:
        """Test orchestrator with default recipe root."""
        orchestrator = RecipeOrchestrator()
        assert orchestrator.recipe_root == Path("recipes")

    @patch("src.recipe_executor.orchestrator.RecipeParser")
    @patch("src.recipe_executor.orchestrator.DependencyResolver")
    def test_execute_single_recipe(
        self,
        mock_resolver_class: Mock,
        mock_parser_class: Mock,
        orchestrator: RecipeOrchestrator,
        sample_recipe: Recipe,
        tmp_path: Path,
    ) -> None:
        """Test executing a single recipe."""
        # Setup mocks
        mock_parser = Mock()
        mock_parser_class.return_value = mock_parser
        mock_parser.parse_recipe.return_value = sample_recipe

        mock_resolver = Mock()
        mock_resolver_class.return_value = mock_resolver
        mock_resolver.resolve.return_value = [sample_recipe]

        # Mock other components
        orchestrator.state_manager.needs_rebuild = Mock(return_value=True)
        orchestrator.state_manager.record_build = Mock()
        
        # Mock discovery to return the sample recipe
        with patch.object(orchestrator, "_discover_recipes", return_value={"test-recipe": sample_recipe}):
            with patch.object(orchestrator, "_execute_single") as mock_execute:
                mock_result = SingleBuildResult(
                    recipe=sample_recipe,
                    code=GeneratedCode(recipe_name="test-recipe", files={}),
                    tests=None,
                    validation=None,
                    quality_result={},
                    success=True,
                    build_time=1.0,
                )
                mock_execute.return_value = mock_result

                # Execute
                result = orchestrator.execute(
                    tmp_path / "recipes" / "test-recipe", BuildOptions()
                )

                # Verify
                assert result.success is True
                assert len(result.results) == 1
                assert result.results[0] == mock_result
                mock_execute.assert_called_once()
                orchestrator.state_manager.record_build.assert_called_once()

    def test_execute_single_recipe_implementation(
        self,
        orchestrator: RecipeOrchestrator,
        sample_recipe: Recipe,
    ) -> None:
        """Test _execute_single implementation."""
        options = BuildOptions(verbose=True, dry_run=False)

        # Mock components
        mock_code = GeneratedCode(
            recipe_name="test-recipe",
            files={"src/test.py": "def test(): pass"},
        )
        mock_tests = RecipeTestSuite(
            recipe_name="test-recipe",
            unit_tests=["test_one"],
            integration_tests=[],
            test_files={"tests/test.py": "def test_one(): pass"},
        )
        mock_validation = ValidationResult(
            recipe_name="test-recipe",
            passed=True,
            requirements_coverage={"req_1": True},
            design_compliance={"Parser": True},
            quality_gates={"has_code": True},
        )

        orchestrator.generator.generate = Mock(return_value=mock_code)
        orchestrator.test_generator.generate_tests = Mock(return_value=mock_tests)
        orchestrator.validator.validate = Mock(return_value=mock_validation)

        # Execute
        result = orchestrator._execute_single(sample_recipe, options)

        # Verify
        assert result.success is True
        assert result.recipe == sample_recipe
        assert result.code == mock_code
        assert result.tests == mock_tests
        assert result.validation == mock_validation
        assert result.quality_result["pyright"] is True
        assert result.build_time > 0
        assert len(result.errors) == 0

    def test_execute_single_recipe_with_failure(
        self,
        orchestrator: RecipeOrchestrator,
        sample_recipe: Recipe,
    ) -> None:
        """Test _execute_single with generation failure."""
        options = BuildOptions()

        # Mock generator to raise exception
        orchestrator.generator.generate = Mock(
            side_effect=Exception("Generation failed")
        )

        # Execute
        result = orchestrator._execute_single(sample_recipe, options)

        # Verify
        assert result.success is False
        assert result.code is None
        assert result.tests is None
        assert result.validation is None
        assert "Generation failed" in result.errors[0]

    def test_execute_single_recipe_validation_failure(
        self,
        orchestrator: RecipeOrchestrator,
        sample_recipe: Recipe,
    ) -> None:
        """Test _execute_single with validation failure."""
        options = BuildOptions()

        # Mock successful generation but failed validation
        mock_code = GeneratedCode(recipe_name="test-recipe", files={})
        mock_tests = RecipeTestSuite(
            recipe_name="test-recipe",
            unit_tests=[],
            integration_tests=[],
            test_files={},
        )
        mock_validation = ValidationResult(
            recipe_name="test-recipe",
            passed=False,
            requirements_coverage={"req_1": False},
            design_compliance={"Parser": False},
            quality_gates={},
            errors=["Missing requirement coverage"],
        )

        orchestrator.generator.generate = Mock(return_value=mock_code)
        orchestrator.test_generator.generate_tests = Mock(return_value=mock_tests)
        orchestrator.validator.validate = Mock(return_value=mock_validation)

        # Execute
        result = orchestrator._execute_single(sample_recipe, options)

        # Verify
        assert result.success is False
        assert "Missing requirement coverage" in result.errors

    def test_discover_recipes(
        self,
        orchestrator: RecipeOrchestrator,
        sample_recipe: Recipe,
        tmp_path: Path,
    ) -> None:
        """Test recipe discovery."""
        # Create recipe directory structure
        recipe_dir = tmp_path / "recipes" / "test-recipe"
        recipe_dir.mkdir(parents=True)

        # Mock parser
        orchestrator.parser.parse_recipe = Mock(return_value=sample_recipe)

        # Discover recipes
        recipes = orchestrator._discover_recipes(recipe_dir)

        # Verify
        assert len(recipes) == 1
        assert "test-recipe" in recipes
        assert recipes["test-recipe"] == sample_recipe

    def test_discover_recipes_with_dependencies(
        self,
        orchestrator: RecipeOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test discovering recipes with dependencies."""
        # Create recipe directory structure
        recipe1_dir = tmp_path / "recipes" / "recipe1"
        recipe2_dir = tmp_path / "recipes" / "recipe2"
        recipe1_dir.mkdir(parents=True)
        recipe2_dir.mkdir(parents=True)

        # Create recipes with dependencies
        recipe1 = Recipe(
            name="recipe1",
            path=recipe1_dir,
            requirements=Requirements("", [], [], []),
            design=Design("", [], [], ""),
            components=Components(
                "recipe1", "1.0.0", ComponentType.LIBRARY, dependencies=["recipe2"]
            ),
            metadata=RecipeMetadata(datetime.now(), datetime.now()),
        )

        recipe2 = Recipe(
            name="recipe2",
            path=recipe2_dir,
            requirements=Requirements("", [], [], []),
            design=Design("", [], [], ""),
            components=Components("recipe2", "1.0.0", ComponentType.LIBRARY),
            metadata=RecipeMetadata(datetime.now(), datetime.now()),
        )

        # Mock parser
        def parse_recipe_mock(path: Path) -> Recipe:
            if path.name == "recipe1":
                return recipe1
            elif path.name == "recipe2":
                return recipe2
            raise ValueError(f"Unknown recipe: {path}")

        orchestrator.parser.parse_recipe = Mock(side_effect=parse_recipe_mock)

        # Discover recipes
        recipes = orchestrator._discover_recipes(recipe1_dir)

        # Verify both recipes discovered
        assert len(recipes) == 2
        assert "recipe1" in recipes
        assert "recipe2" in recipes

    def test_discover_recipes_with_parse_error(
        self,
        orchestrator: RecipeOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test recipe discovery with parse error."""
        recipe_dir = tmp_path / "recipes" / "bad-recipe"
        recipe_dir.mkdir(parents=True)

        # Mock parser to raise exception
        orchestrator.parser.parse_recipe = Mock(
            side_effect=Exception("Parse error")
        )

        # Discover recipes (should handle error gracefully)
        recipes = orchestrator._discover_recipes(recipe_dir)

        # Verify empty result
        assert len(recipes) == 0

    def test_analyze_recipe(
        self,
        orchestrator: RecipeOrchestrator,
        sample_recipe: Recipe,
        tmp_path: Path,
    ) -> None:
        """Test recipe analysis."""
        recipe_path = tmp_path / "recipes" / "test-recipe"
        recipe_path.mkdir(parents=True)

        # Mock discovery
        with patch.object(
            orchestrator, "_discover_recipes", return_value={"test-recipe": sample_recipe}
        ):
            # Mock resolver methods
            orchestrator.resolver.analyze_impact = Mock(
                return_value={
                    "dependencies": set(),
                    "dependents": set(),
                }
            )
            orchestrator.resolver.get_execution_plan = Mock(
                return_value=["test-recipe"]
            )

            # Mock validator
            orchestrator.validator.validate_recipe_structure = Mock(
                return_value=[]
            )

            # Analyze
            analysis = orchestrator.analyze(recipe_path)

            # Verify
            assert analysis["recipe"] == "test-recipe"
            assert analysis["version"] == "1.0.0"
            assert analysis["type"] == "library"
            assert analysis["dependencies"] == []
            assert analysis["dependents"] == []
            assert analysis["execution_plan"] == ["test-recipe"]
            assert analysis["validation_issues"] == []
            assert analysis["total_recipes"] == 1

    def test_analyze_recipe_not_found(
        self,
        orchestrator: RecipeOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test analysis when recipe not found."""
        recipe_path = tmp_path / "recipes" / "nonexistent"

        # Mock empty discovery
        with patch.object(orchestrator, "_discover_recipes", return_value={}):
            analysis = orchestrator.analyze(recipe_path)
            assert analysis == {"error": "No recipes found"}

    def test_analyze_target_recipe_missing(
        self,
        orchestrator: RecipeOrchestrator,
        tmp_path: Path,
    ) -> None:
        """Test analysis when target recipe is missing."""
        recipe_path = tmp_path / "recipes" / "target-recipe"

        # Mock discovery with different recipe
        other_recipe = Recipe(
            name="other-recipe",
            path=tmp_path / "recipes" / "other-recipe",
            requirements=Requirements("", [], [], []),
            design=Design("", [], [], ""),
            components=Components("other-recipe", "1.0.0", ComponentType.LIBRARY),
            metadata=RecipeMetadata(datetime.now(), datetime.now()),
        )

        with patch.object(
            orchestrator, "_discover_recipes", return_value={"other-recipe": other_recipe}
        ):
            analysis = orchestrator.analyze(recipe_path)
            assert analysis == {"error": "Target recipe target-recipe not found"}

    def test_execute_with_skip_rebuild(
        self,
        orchestrator: RecipeOrchestrator,
        sample_recipe: Recipe,
        tmp_path: Path,
        capsys,
    ) -> None:
        """Test execute with skipping rebuild."""
        # Mock discovery and resolution
        with patch.object(
            orchestrator, "_discover_recipes", return_value={"test-recipe": sample_recipe}
        ):
            orchestrator.resolver.resolve = Mock(return_value=[sample_recipe])
            
            # Mock state manager to indicate no rebuild needed
            orchestrator.state_manager.needs_rebuild = Mock(return_value=False)
            
            # Execute with verbose option
            options = BuildOptions(verbose=True)
            result = orchestrator.execute(
                tmp_path / "recipes" / "test-recipe", options
            )
            
            # Verify
            assert result.success is True
            assert len(result.results) == 0  # No builds executed
            
            # Check output
            captured = capsys.readouterr()
            assert "Skipping test-recipe - no rebuild needed" in captured.out

    def test_execute_dry_run(
        self,
        orchestrator: RecipeOrchestrator,
        sample_recipe: Recipe,
        tmp_path: Path,
    ) -> None:
        """Test execute with dry run option."""
        options = BuildOptions(dry_run=True)

        # Mock components
        mock_code = GeneratedCode(recipe_name="test-recipe", files={})
        mock_tests = RecipeTestSuite(
            recipe_name="test-recipe",
            unit_tests=[],
            integration_tests=[],
            test_files={},
        )
        mock_validation = ValidationResult(
            recipe_name="test-recipe",
            passed=True,
            requirements_coverage={},
            design_compliance={},
            quality_gates={},
        )

        orchestrator.generator.generate = Mock(return_value=mock_code)
        orchestrator.test_generator.generate_tests = Mock(return_value=mock_tests)
        orchestrator.validator.validate = Mock(return_value=mock_validation)

        # Execute
        result = orchestrator._execute_single(sample_recipe, options)

        # Verify quality gates were not run (dry run)
        assert result.quality_result == {}
        assert result.success is True

    def test_build_result_aggregation(
        self,
        orchestrator: RecipeOrchestrator,
        sample_recipe: Recipe,
    ) -> None:
        """Test build result aggregation."""
        # Create multiple single results
        successful_result = SingleBuildResult(
            recipe=sample_recipe,
            code=GeneratedCode(recipe_name="test-recipe", files={}),
            tests=None,
            validation=None,
            quality_result={},
            success=True,
            build_time=1.0,
        )

        failed_recipe = Recipe(
            name="recipe2",
            path=Path("recipes/recipe2"),
            requirements=Requirements("", [], [], []),
            design=Design("", [], [], ""),
            components=Components("recipe2", "1.0.0", ComponentType.LIBRARY),
            metadata=RecipeMetadata(datetime.now(), datetime.now()),
        )

        failed_result = SingleBuildResult(
            recipe=failed_recipe,
            code=None,
            tests=None,
            validation=None,
            quality_result={},
            success=False,
            build_time=0.5,
            errors=["Build failed"],
        )

        # Create build result
        build_result = BuildResult(
            results=[successful_result, failed_result],
            success=False,
            total_time=1.5,
        )

        # Verify aggregation
        assert build_result.get_successful_recipes() == ["test-recipe"]
        assert build_result.get_failed_recipes() == ["recipe2"]
        assert build_result.success is False
        assert build_result.total_time == 1.5