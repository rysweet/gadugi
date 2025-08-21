"""Comprehensive tests for dependency_resolver.py."""

import pytest
from pathlib import Path
from typing import Dict

from src.recipe_executor.dependency_resolver import (
    DependencyResolver,
    DependencyGraph,
    CircularDependencyError,
    MissingDependencyError,
)
from src.recipe_executor.recipe_model import (
    Recipe,
    Requirements,
    Design,
    Components,
    ComponentType,
    RecipeMetadata,
)
from datetime import datetime


class TestDependencyGraph:
    """Test DependencyGraph class."""

    @pytest.fixture
    def sample_recipes(self) -> Dict[str, Recipe]:
        """Create sample recipes for testing."""
        recipes = {}

        # Create base recipe with no dependencies
        recipes["base"] = self._create_recipe("base", [])

        # Create middle recipe depending on base
        recipes["middle"] = self._create_recipe("middle", ["base"])

        # Create top recipe depending on middle
        recipes["top"] = self._create_recipe("top", ["middle"])

        # Create independent recipe
        recipes["independent"] = self._create_recipe("independent", [])

        return recipes

    def _create_recipe(self, name: str, dependencies: list[str]) -> Recipe:
        """Helper to create a recipe."""
        return Recipe(
            name=name,
            path=Path(f"recipes/{name}"),
            requirements=Requirements("", [], [], []),
            design=Design("", [], [], ""),
            components=Components(
                name=name,
                version="1.0.0",
                type=ComponentType.LIBRARY,
                dependencies=dependencies,
            ),
            metadata=RecipeMetadata(datetime.now(), datetime.now()),
        )

    def test_add_recipe(self, sample_recipes: Dict[str, Recipe]) -> None:
        """Test adding recipes to graph."""
        graph = DependencyGraph()
        graph.add_recipe(sample_recipes["base"])

        assert "base" in graph.recipes
        assert graph.recipes["base"] == sample_recipes["base"]
        assert "base" in graph.graph.nodes

    def test_get_build_order(self, sample_recipes: Dict[str, Recipe]) -> None:
        """Test getting topological build order."""
        graph = DependencyGraph()
        for recipe in sample_recipes.values():
            graph.add_recipe(recipe)

        build_order = graph.get_build_order()

        # Base should come before middle
        assert build_order.index("base") < build_order.index("middle")
        # Middle should come before top
        assert build_order.index("middle") < build_order.index("top")
        # Independent can be anywhere
        assert "independent" in build_order

    def test_get_dependencies(self, sample_recipes: Dict[str, Recipe]) -> None:
        """Test getting all dependencies of a recipe."""
        graph = DependencyGraph()
        for recipe in sample_recipes.values():
            graph.add_recipe(recipe)

        # Top depends on middle and base (transitively)
        top_deps = graph.get_dependencies("top")
        assert "middle" in top_deps
        assert "base" in top_deps
        assert "independent" not in top_deps

        # Base has no dependencies
        base_deps = graph.get_dependencies("base")
        assert len(base_deps) == 0

    def test_get_dependents(self, sample_recipes: Dict[str, Recipe]) -> None:
        """Test getting recipes that depend on a given recipe."""
        graph = DependencyGraph()
        for recipe in sample_recipes.values():
            graph.add_recipe(recipe)

        # Base is depended on by middle and top (transitively)
        base_dependents = graph.get_dependents("base")
        assert "middle" in base_dependents
        assert "top" in base_dependents

        # Top has no dependents
        top_dependents = graph.get_dependents("top")
        assert len(top_dependents) == 0

    def test_circular_dependency_detection(self) -> None:
        """Test detecting circular dependencies."""
        graph = DependencyGraph()

        # Create circular dependency: A -> B -> C -> A
        recipe_a = self._create_recipe("A", ["C"])
        recipe_b = self._create_recipe("B", ["A"])
        recipe_c = self._create_recipe("C", ["B"])

        graph.add_recipe(recipe_a)
        graph.add_recipe(recipe_b)
        graph.add_recipe(recipe_c)

        assert graph.has_cycles() is True

        cycles = graph.get_cycles()
        assert len(cycles) > 0

        with pytest.raises(CircularDependencyError):
            graph.get_build_order()

    def test_no_cycles(self, sample_recipes: Dict[str, Recipe]) -> None:
        """Test that valid DAG has no cycles."""
        graph = DependencyGraph()
        for recipe in sample_recipes.values():
            graph.add_recipe(recipe)

        assert graph.has_cycles() is False
        assert len(graph.get_cycles()) == 0

    def test_get_missing_dependencies(self) -> None:
        """Test detecting missing dependencies."""
        graph = DependencyGraph()

        # Recipe that depends on non-existent recipe
        recipe = self._create_recipe("test", ["missing-dep"])
        graph.add_recipe(recipe)

        missing = graph.get_missing_dependencies()
        assert "missing-dep" in missing


class TestDependencyResolver:
    """Test DependencyResolver class."""

    @pytest.fixture
    def resolver(self) -> DependencyResolver:
        """Create a DependencyResolver instance."""
        return DependencyResolver(Path("recipes"))

    @pytest.fixture
    def sample_recipes(self) -> Dict[str, Recipe]:
        """Create sample recipes for testing."""
        recipes = {}

        # Linear dependency chain
        recipes["base"] = self._create_recipe("base", [])
        recipes["middle"] = self._create_recipe("middle", ["base"])
        recipes["top"] = self._create_recipe("top", ["middle"])

        # Parallel dependencies
        recipes["lib1"] = self._create_recipe("lib1", ["base"])
        recipes["lib2"] = self._create_recipe("lib2", ["base"])
        recipes["app"] = self._create_recipe("app", ["lib1", "lib2"])

        return recipes

    def _create_recipe(self, name: str, dependencies: list[str]) -> Recipe:
        """Helper to create a recipe."""
        return Recipe(
            name=name,
            path=Path(f"recipes/{name}"),
            requirements=Requirements("", [], [], []),
            design=Design("", [], [], ""),
            components=Components(
                name=name,
                version="1.0.0",
                type=ComponentType.LIBRARY,
                dependencies=dependencies,
            ),
            metadata=RecipeMetadata(datetime.now(), datetime.now()),
        )

    def test_resolve(self, resolver: DependencyResolver, sample_recipes: Dict[str, Recipe]) -> None:
        """Test resolving dependencies to build order."""
        build_order = resolver.resolve(sample_recipes)

        # Check order is correct
        names = [r.name for r in build_order]
        assert names.index("base") < names.index("middle")
        assert names.index("middle") < names.index("top")
        assert names.index("base") < names.index("lib1")
        assert names.index("base") < names.index("lib2")
        assert names.index("lib1") < names.index("app")
        assert names.index("lib2") < names.index("app")

    def test_resolve_with_missing_dependency(self, resolver: DependencyResolver) -> None:
        """Test resolving with missing dependencies."""
        recipes = {
            "test": self._create_recipe("test", ["missing"]),
        }

        with pytest.raises(MissingDependencyError, match="Missing dependencies"):
            resolver.resolve(recipes)

    def test_resolve_with_circular_dependency(self, resolver: DependencyResolver) -> None:
        """Test resolving with circular dependencies."""
        recipes = {
            "A": self._create_recipe("A", ["B"]),
            "B": self._create_recipe("B", ["A"]),
        }

        with pytest.raises(CircularDependencyError, match="Circular dependencies"):
            resolver.resolve(recipes)

    def test_resolve_single(
        self, resolver: DependencyResolver, sample_recipes: Dict[str, Recipe]
    ) -> None:
        """Test resolving dependencies for a single recipe."""
        target = sample_recipes["top"]
        needed = resolver.resolve_single(target, sample_recipes)

        names = [r.name for r in needed]
        # Should include top and all its dependencies
        assert "top" in names
        assert "middle" in names
        assert "base" in names
        # Should not include unrelated recipes
        assert "lib1" not in names
        assert "lib2" not in names

    def test_analyze_impact(
        self, resolver: DependencyResolver, sample_recipes: Dict[str, Recipe]
    ) -> None:
        """Test analyzing impact of changing a recipe."""
        impact = resolver.analyze_impact("base", sample_recipes)

        # Base has no dependencies
        assert len(impact["dependencies"]) == 0

        # Many recipes depend on base
        dependents = impact["dependents"]
        assert "middle" in dependents
        assert "top" in dependents
        assert "lib1" in dependents
        assert "lib2" in dependents
        assert "app" in dependents

    def test_get_parallel_groups(
        self, resolver: DependencyResolver, sample_recipes: Dict[str, Recipe]
    ) -> None:
        """Test grouping recipes for parallel execution."""
        recipes_list = list(sample_recipes.values())
        groups = resolver.get_parallel_groups(recipes_list)

        # First group should be base (no dependencies)
        assert len(groups[0]) == 1
        assert groups[0][0].name == "base"

        # Second group should have middle, lib1, lib2 (all depend only on base)
        group2_names = {r.name for r in groups[1]}
        assert "middle" in group2_names
        assert "lib1" in group2_names
        assert "lib2" in group2_names

        # Later groups have top and app
        all_names = set()
        for group in groups:
            for recipe in group:
                all_names.add(recipe.name)
        assert "top" in all_names
        assert "app" in all_names

    def test_validate_dependencies(self, resolver: DependencyResolver) -> None:
        """Test validating recipe dependencies."""
        recipe = self._create_recipe("test", ["dep1", "dep2"])

        # All dependencies available
        issues = resolver.validate_dependencies(recipe, {"dep1", "dep2", "other"})
        assert len(issues) == 0

        # Missing dependency
        issues = resolver.validate_dependencies(recipe, {"dep1"})
        assert len(issues) == 1
        assert "dep2" in issues[0]

    def test_get_execution_plan(
        self, resolver: DependencyResolver, sample_recipes: Dict[str, Recipe]
    ) -> None:
        """Test getting execution plan with parallel groups."""
        plan = resolver.get_execution_plan("app", sample_recipes)

        # Plan should be list of (level, [recipe_names])
        assert len(plan) > 0

        # First level should have base
        assert "base" in plan[0][1]

        # Check that dependencies come before dependents
        for i, (level, names) in enumerate(plan):
            if "app" in names:
                # lib1 and lib2 should be in earlier levels
                earlier_names = []
                for j in range(i):
                    earlier_names.extend(plan[j][1])
                assert "lib1" in earlier_names
                assert "lib2" in earlier_names

    def test_get_execution_plan_not_found(
        self, resolver: DependencyResolver, sample_recipes: Dict[str, Recipe]
    ) -> None:
        """Test execution plan with non-existent target."""
        with pytest.raises(ValueError, match="Target recipe not found"):
            resolver.get_execution_plan("nonexistent", sample_recipes)
