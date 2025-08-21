"""Dependency resolution for Recipe Executor."""

from typing import Optional, Set, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import networkx as nx

from .recipe_model import Recipe


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected."""

    pass


class MissingDependencyError(Exception):
    """Raised when a required dependency is missing."""

    pass


@dataclass
class DependencyGraph:
    """Represents the dependency graph of recipes."""

    graph: Any = field(default_factory=lambda: nx.DiGraph())  # type: ignore[misc]  # nx.DiGraph doesn't support type parameters
    recipes: Dict[str, Recipe] = field(default_factory=lambda: {})

    def add_recipe(self, recipe: Recipe) -> None:
        """Add a recipe to the graph."""
        self.recipes[recipe.name] = recipe
        self.graph.add_node(recipe.name, recipe=recipe)

        # Add edges for dependencies
        for dep in recipe.get_dependencies():
            self.graph.add_edge(dep, recipe.name)

    def get_build_order(self) -> List[str]:
        """Get recipes in build order (topological sort)."""
        try:
            # Returns nodes in topological order (dependencies first)
            return list(nx.topological_sort(self.graph))
        except (nx.NetworkXError, nx.NetworkXUnfeasible) as e:
            # This happens when there's a cycle
            cycles = self.get_cycles()
            raise CircularDependencyError(f"Circular dependencies detected: {cycles}") from e

    def get_dependencies(self, recipe_name: str) -> Set[str]:
        """Get all dependencies of a recipe (transitive)."""
        if recipe_name not in self.graph:
            return set()

        # Get all ancestors (dependencies) of this node
        return nx.ancestors(self.graph, recipe_name)  # type: ignore[no-any-return]

    def get_dependents(self, recipe_name: str) -> Set[str]:
        """Get all recipes that depend on this one."""
        if recipe_name not in self.graph:
            return set()

        # Get all descendants (dependents) of this node
        return nx.descendants(self.graph, recipe_name)  # type: ignore[no-any-return]

    def has_cycles(self) -> bool:
        """Check if the graph has circular dependencies."""
        return not nx.is_directed_acyclic_graph(self.graph)

    def get_cycles(self) -> List[List[str]]:
        """Get all circular dependencies."""
        try:
            return list(nx.simple_cycles(self.graph))
        except nx.NetworkXError:
            return []

    def get_missing_dependencies(self) -> Set[str]:
        """Get dependencies that are referenced but not defined."""
        all_deps: Set[str] = set()
        for recipe in self.recipes.values():
            all_deps.update(recipe.get_dependencies())

        defined = set(self.recipes.keys())
        return all_deps - defined


class DependencyResolver:
    """Resolves and orders recipe dependencies."""

    def __init__(self, recipe_root: Optional[Path] = None):
        """Initialize resolver with optional recipe root directory."""
        self.recipe_root = recipe_root or Path("recipes")
        self._cache: Dict[str, Recipe] = {}

    def resolve(self, recipes: Dict[str, Recipe]) -> List[Recipe]:
        """Return recipes in build order using topological sort."""
        # Build dependency graph
        graph = self._build_dependency_graph(recipes)

        # Check for missing dependencies
        missing = graph.get_missing_dependencies()
        if missing:
            raise MissingDependencyError(f"Missing dependencies: {missing}")

        # Check for circular dependencies
        if graph.has_cycles():
            cycles = graph.get_cycles()
            raise CircularDependencyError(f"Circular dependencies detected: {cycles}")

        # Get build order
        build_order = graph.get_build_order()

        # Return recipes in build order
        return [recipes[name] for name in build_order if name in recipes]

    def resolve_single(self, recipe: Recipe, all_recipes: Dict[str, Recipe]) -> List[Recipe]:
        """Resolve dependencies for a single recipe."""
        # Get all dependencies (transitive)
        graph = self._build_dependency_graph(all_recipes)
        deps = graph.get_dependencies(recipe.name)

        # Add the recipe itself
        deps.add(recipe.name)

        # Filter to only needed recipes
        needed_recipes = {name: all_recipes[name] for name in deps if name in all_recipes}

        # Resolve order
        return self.resolve(needed_recipes)

    def _build_dependency_graph(self, recipes: Dict[str, Recipe]) -> DependencyGraph:
        """Build DAG from recipe dependencies."""
        graph = DependencyGraph()

        for recipe in recipes.values():
            graph.add_recipe(recipe)

        return graph

    def analyze_impact(
        self, recipe_name: str, all_recipes: Dict[str, Recipe]
    ) -> Dict[str, Set[str]]:
        """Analyze the impact of changing a recipe."""
        graph = self._build_dependency_graph(all_recipes)

        return {
            "dependencies": graph.get_dependencies(recipe_name),
            "dependents": graph.get_dependents(recipe_name),
            "all_affected": graph.get_dependencies(recipe_name) | graph.get_dependents(recipe_name),
        }

    def get_parallel_groups(self, recipes: List[Recipe]) -> List[List[Recipe]]:
        """Group recipes that can be built in parallel."""
        # Build dependency graph
        graph_dict: Dict[str, Recipe] = {r.name: r for r in recipes}
        graph = self._build_dependency_graph(graph_dict)

        # Group by levels (recipes with no deps, then recipes depending only on first level, etc.)
        levels: List[List[Recipe]] = []
        remaining = set(r.name for r in recipes)

        while remaining:
            # Find recipes with no dependencies in remaining set
            current_level: List[Recipe] = []
            for name in remaining:
                deps = set(graph.recipes[name].get_dependencies())
                if not deps.intersection(remaining):
                    current_level.append(graph.recipes[name])

            if not current_level:
                # This shouldn't happen if graph is acyclic
                raise CircularDependencyError("Cannot determine parallel groups")

            levels.append(current_level)
            remaining -= set(r.name for r in current_level)

        return levels

    def validate_dependencies(self, recipe: Recipe, available: Set[str]) -> List[str]:
        """Validate that a recipe's dependencies are available."""
        issues: List[str] = []

        for dep in recipe.get_dependencies():
            if dep not in available:
                issues.append(f"Missing dependency: {dep}")

        return issues

    def get_execution_plan(
        self, target: str, all_recipes: Dict[str, Recipe]
    ) -> List[Tuple[int, List[str]]]:
        """Get execution plan showing parallel execution opportunities."""
        if target not in all_recipes:
            raise ValueError(f"Target recipe not found: {target}")

        # Resolve dependencies for target
        needed = self.resolve_single(all_recipes[target], all_recipes)

        # Get parallel groups
        groups = self.get_parallel_groups(needed)

        # Convert to execution plan
        plan: List[Tuple[int, List[str]]] = []
        for i, group in enumerate(groups):
            plan.append((i, [r.name for r in group]))

        return plan
