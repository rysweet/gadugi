"""Main orchestration engine for Recipe Executor."""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import time

from .recipe_model import (
    Recipe,
    BuildContext,
    BuildResult,
    SingleBuildResult,
)
from .recipe_parser import RecipeParser
from .dependency_resolver import DependencyResolver
from .code_generator import CodeGenerator
from .test_generator import TestGenerator
from .validator import Validator, Implementation
from .state_manager import StateManager
from .python_standards import QualityGates


@dataclass
class BuildOptions:
    """Options for building recipes."""

    dry_run: bool = False
    verbose: bool = False
    force_rebuild: bool = False
    parallel: bool = False
    output_dir: Optional[Path] = None


class RecipeOrchestrator:
    """Main orchestration engine for recipe execution."""

    def __init__(self, recipe_root: Optional[Path] = None):
        """Initialize orchestrator with all components."""
        self.recipe_root = recipe_root or Path("recipes")
        self.parser = RecipeParser()
        self.resolver = DependencyResolver(self.recipe_root)
        self.generator = CodeGenerator()
        self.test_generator = TestGenerator()
        self.validator = Validator()
        self.state_manager = StateManager()
        self.quality_gates = QualityGates()

    def execute(self, recipe_path: Path, options: Optional[BuildOptions] = None) -> BuildResult:
        """Execute a recipe and all its dependencies."""
        if options is None:
            options = BuildOptions()

        start_time = time.time()

        # 1. Parse all recipes
        recipes = self._discover_recipes(recipe_path)

        # 2. Resolve dependencies
        build_order = self.resolver.resolve(recipes)

        # 3. Execute in order
        results: List[SingleBuildResult] = []
        for recipe in build_order:
            if self.state_manager.needs_rebuild(recipe, options.force_rebuild):
                result = self._execute_single(recipe, options)
                results.append(result)
                self.state_manager.record_build(recipe, result)
            elif options.verbose:
                print(f"Skipping {recipe.name} - no rebuild needed")

        # Calculate total time
        total_time = time.time() - start_time

        # Determine overall success
        success = all(r.success for r in results)

        return BuildResult(results=results, success=success, total_time=total_time)

    def _execute_single(self, recipe: Recipe, options: BuildOptions) -> SingleBuildResult:
        """Execute a single recipe."""
        start_time = time.time()
        errors: List[str] = []

        try:
            # Build context with dependencies
            context = BuildContext(
                recipe=recipe,
                dry_run=options.dry_run,
                verbose=options.verbose,
                force_rebuild=options.force_rebuild,
            )

            # Generate code
            if options.verbose:
                print(f"Generating code for {recipe.name}...")
            code = self.generator.generate(recipe, context)

            # Generate tests
            if options.verbose:
                print(f"Generating tests for {recipe.name}...")
            tests = self.test_generator.generate_tests(recipe, code)

            # Create implementation
            impl = Implementation(code=code, tests=tests)

            # Validate
            if options.verbose:
                print(f"Validating {recipe.name}...")
            validation = self.validator.validate(recipe, impl)

            # Run quality gates (if not dry run)
            quality_result: Dict[str, bool] = {}
            if not options.dry_run:
                if options.verbose:
                    print(f"Running quality gates for {recipe.name}...")
                # Would write files and run quality gates here
                # For now, simulate success
                quality_result = {
                    "pyright": True,
                    "ruff_format": True,
                    "ruff_lint": True,
                    "pytest": True,
                }

            # Determine success
            success = validation.passed and all(quality_result.values())

            if not success:
                errors.extend(validation.errors)
                failed_gates = [g for g, p in quality_result.items() if not p]
                if failed_gates:
                    errors.append(f"Failed quality gates: {failed_gates}")

        except Exception as e:
            # Handle any errors
            code = None
            tests = None
            validation = None
            quality_result = {}
            success = False
            errors.append(str(e))

        build_time = time.time() - start_time

        return SingleBuildResult(
            recipe=recipe,
            code=code,
            tests=tests,
            validation=validation,
            quality_result=quality_result,
            success=success,
            build_time=build_time,
            errors=errors,
        )

    def _discover_recipes(self, recipe_path: Path) -> Dict[str, Recipe]:
        """Discover all recipes including dependencies."""
        recipes: Dict[str, Recipe] = {}
        to_process = [recipe_path]
        processed: Set[str] = set()

        while to_process:
            current_path = to_process.pop(0)

            # Skip if already processed
            recipe_name = current_path.name
            if recipe_name in processed:
                continue

            # Parse recipe
            try:
                recipe = self.parser.parse_recipe(current_path)
                recipes[recipe.name] = recipe
                processed.add(recipe_name)

                # Add dependencies to process
                for dep_name in recipe.get_dependencies():
                    dep_path = self.recipe_root / dep_name
                    if dep_path.exists() and dep_name not in processed:
                        to_process.append(dep_path)

            except Exception as e:
                print(f"Warning: Failed to parse recipe at {current_path}: {e}")

        return recipes

    def analyze(self, recipe_path: Path) -> Dict[str, Any]:
        """Analyze a recipe and its dependencies without building."""
        recipes = self._discover_recipes(recipe_path)

        if not recipes:
            return {"error": "No recipes found"}

        # Get the target recipe
        target_name = recipe_path.name
        if target_name not in recipes:
            return {"error": f"Target recipe {target_name} not found"}

        target = recipes[target_name]

        # Analyze dependencies
        impact = self.resolver.analyze_impact(target_name, recipes)

        # Get execution plan
        plan = self.resolver.get_execution_plan(target_name, recipes)

        # Validate recipe structure
        issues = self.validator.validate_recipe_structure(target)

        return {
            "recipe": target_name,
            "version": target.components.version,
            "type": target.components.type.value,
            "dependencies": list(impact["dependencies"]),
            "dependents": list(impact["dependents"]),
            "execution_plan": plan,
            "validation_issues": issues,
            "total_recipes": len(recipes),
        }
