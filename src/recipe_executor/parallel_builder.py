"""Parallel builder for executing independent recipes concurrently."""

from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass
import time

from .recipe_model import Recipe, SingleBuildResult


@dataclass
class ParallelBuildResult:
    """Result from parallel build execution."""

    results: Dict[str, SingleBuildResult]
    total_time: float
    parallel_groups: List[List[str]]


class ParallelRecipeBuilder:
    """Execute independent recipes in parallel for faster builds."""

    def __init__(self, max_workers: int = 4):
        """Initialize parallel builder.

        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers

    def build_parallel(
        self, recipe_groups: List[List[Recipe]], build_func: Callable[[Recipe, Any], SingleBuildResult], options: Any
    ) -> ParallelBuildResult:
        """Build recipes in parallel groups.

        Args:
            recipe_groups: Groups of recipes that can be built in parallel
            build_func: Function to build a single recipe
            options: Build options to pass to build function

        Returns:
            ParallelBuildResult with all build results
        """
        start_time = time.time()
        all_results: Dict[str, SingleBuildResult] = {}
        parallel_groups: List[List[str]] = []

        for group_idx, group in enumerate(recipe_groups):
            if options.verbose:
                print(f"\n=== Parallel Group {group_idx + 1} ===")
                print(f"Building {len(group)} recipes in parallel:")
                for recipe in group:
                    print(f"  - {recipe.name}")

            # Build this group in parallel
            group_results = self._build_group_parallel(group, build_func, options)
            all_results.update(group_results)

            # Track which recipes were built together
            parallel_groups.append([r.name for r in group])

        total_time = time.time() - start_time

        return ParallelBuildResult(
            results=all_results, total_time=total_time, parallel_groups=parallel_groups
        )

    def _build_group_parallel(
        self, recipes: List[Recipe], build_func: Callable[[Recipe, Any], SingleBuildResult], options: Any
    ) -> Dict[str, SingleBuildResult]:
        """Build a group of recipes in parallel.

        Args:
            recipes: Recipes to build in parallel
            build_func: Function to build a single recipe
            options: Build options

        Returns:
            Dictionary mapping recipe names to build results
        """
        results: Dict[str, SingleBuildResult] = {}

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(recipes))) as executor:
            # Submit all builds
            future_to_recipe: Dict[Future[SingleBuildResult], Recipe] = {
                executor.submit(build_func, recipe, options): recipe for recipe in recipes
            }

            # Collect results as they complete
            for future in as_completed(future_to_recipe):
                recipe = future_to_recipe[future]
                try:
                    result: SingleBuildResult = future.result()
                    results[recipe.name] = result

                    if options.verbose:
                        status = "✓" if result.success else "✗"
                        print(f"  {status} {recipe.name} completed in {result.build_time:.2f}s")

                except Exception as e:
                    # Build failed with exception - create a proper SingleBuildResult
                    results[recipe.name] = SingleBuildResult(
                        recipe=recipe,
                        code=None,
                        tests=None,
                        validation=None,
                        quality_result={},
                        success=False,
                        errors=[str(e)],
                        build_time=0.0
                    )

                    if options.verbose:
                        print(f"  ✗ {recipe.name} failed: {e}")

        return results

    def group_by_dependencies(
        self, recipes: List[Recipe], dependency_graph: Dict[str, List[str]]
    ) -> List[List[Recipe]]:
        """Group recipes by dependency levels for parallel execution.

        Args:
            recipes: All recipes to build
            dependency_graph: Dependency relationships

        Returns:
            List of groups, where each group can be built in parallel
        """
        # Build a map of recipe names to recipes (not used but kept for potential future use)
        # recipe_map = {r.name: r for r in recipes}

        # Track which recipes have been assigned to groups
        assigned: set[str] = set()
        groups: List[List[Recipe]] = []

        # Keep grouping until all recipes are assigned
        while len(assigned) < len(recipes):
            # Find recipes that have no unassigned dependencies
            current_group: List[Recipe] = []

            for recipe in recipes:
                if recipe.name in assigned:
                    continue

                # Check if all dependencies are already assigned
                deps = dependency_graph.get(recipe.name, [])
                if all(dep in assigned for dep in deps):
                    current_group.append(recipe)

            if not current_group:
                # Circular dependency or error - add remaining recipes
                remaining = [r for r in recipes if r.name not in assigned]
                if remaining:
                    groups.append(remaining)
                    break

            # Add this group
            groups.append(current_group)

            # Mark these recipes as assigned
            for recipe in current_group:
                assigned.add(recipe.name)

        return groups
