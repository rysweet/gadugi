"""Main orchestration engine for recipe execution."""

import concurrent.futures
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .claude_code_generator import BuildContext, ClaudeCodeGenerator, GeneratedCode
from .dependency_resolver import DependencyResolver
from .quality_gates import QualityGates
from .recipe_decomposer import RecipeDecomposer
from .recipe_model import Recipe
from .recipe_parser import RecipeParser
from .recipe_validator import RecipeValidator
from .state_manager import StateManager
from .test_generator import TestGenerator
from .validator import Validator

logger = logging.getLogger(__name__)


@dataclass
class BuildOptions:
    """Options for recipe building."""
    parallel: bool = True
    force_rebuild: bool = False
    dry_run: bool = False
    verbose: bool = False
    max_workers: int = 4
    skip_tests: bool = False
    skip_validation: bool = False
    output_dir: Optional[Path] = None
    
    def get_max_workers(self) -> int:
        """Get max workers, defaulting to CPU count."""
        if self.max_workers > 0:
            return self.max_workers
        return os.cpu_count() or 4


@dataclass
class SingleBuildResult:
    """Result of building a single recipe."""
    recipe: Recipe
    code: Optional[GeneratedCode]
    validation: Optional[Any]
    quality_result: Dict[str, bool]
    success: bool
    build_time: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def get_summary(self) -> str:
        """Get build summary."""
        status = "SUCCESS" if self.success else "FAILED"
        summary = f"{self.recipe.name}: {status} ({self.build_time:.2f}s)"
        
        if self.errors:
            summary += f"\n  Errors: {len(self.errors)}"
            for error in self.errors[:3]:
                summary += f"\n    - {error[:100]}"
        
        if self.warnings:
            summary += f"\n  Warnings: {len(self.warnings)}"
        
        return summary


@dataclass
class BuildResult:
    """Overall build result."""
    results: List[SingleBuildResult]
    success: bool
    total_time: float
    parallel_groups: int = 0
    
    def get_successful_count(self) -> int:
        """Get count of successful builds."""
        return sum(1 for r in self.results if r.success)
    
    def get_failed_count(self) -> int:
        """Get count of failed builds."""
        return sum(1 for r in self.results if not r.success)
    
    def get_summary(self) -> str:
        """Get overall build summary."""
        lines = [
            f"Build {'SUCCEEDED' if self.success else 'FAILED'}",
            f"Total time: {self.total_time:.2f}s",
            f"Recipes built: {len(self.results)}",
            f"Successful: {self.get_successful_count()}",
            f"Failed: {self.get_failed_count()}"
        ]
        
        if self.parallel_groups > 0:
            lines.append(f"Parallel groups: {self.parallel_groups}")
        
        # Add individual summaries
        lines.append("\nRecipe Results:")
        for result in self.results:
            lines.append(f"  {result.get_summary()}")
        
        return '\n'.join(lines)


@dataclass
class Implementation:
    """Container for implementation code and tests."""
    code: GeneratedCode
    tests: Any  # TestSuite
    
    def get_file_count(self) -> int:
        """Get total number of files."""
        return len(self.code.get_all_files())


class RecipeOrchestrator:
    """Main orchestration engine for recipe execution with parallel support."""
    
    def __init__(self, recipe_root: Path = Path("recipes")):
        """Initialize the orchestrator.
        
        Args:
            recipe_root: Root directory for recipes
        """
        self.recipe_root = recipe_root
        self.parser = RecipeParser()
        self.validator = RecipeValidator()
        self.decomposer = RecipeDecomposer()
        self.resolver = DependencyResolver()
        self.generator = ClaudeCodeGenerator()
        self.test_generator = TestGenerator()
        self.code_validator = Validator()
        self.state_manager = StateManager()
        self.quality_gates = QualityGates()
        
        # Track built recipes for dependency injection
        self.built_recipes: Dict[str, GeneratedCode] = {}
    
    def execute(self, recipe_path: Path, options: BuildOptions) -> BuildResult:
        """Execute a recipe and all its dependencies.
        
        Args:
            recipe_path: Path to recipe to build
            options: Build options
            
        Returns:
            Overall build result
        """
        start_time = time.time()
        logger.info(f"Starting recipe execution for {recipe_path}")
        
        try:
            # 1. Parse all recipes including dependencies
            recipes = self._discover_recipes(recipe_path)
            logger.info(f"Discovered {len(recipes)} recipes to build")
            
            # 2. Validate all recipes
            if not options.skip_validation:
                self._validate_recipes(recipes)
            
            # 3. Check for complex recipes needing decomposition
            self._handle_complex_recipes(recipes)
            
            # 4. Resolve dependencies and identify parallel groups
            build_order = self.resolver.resolve(recipes)
            parallel_groups = self.resolver.get_parallel_groups(build_order)
            logger.info(f"Identified {len(parallel_groups)} parallel execution groups")
            
            # 5. Execute in parallel groups
            results = self._execute_parallel_groups(parallel_groups, options)
            
            # Calculate total time
            total_time = time.time() - start_time
            
            # Determine overall success
            success = all(r.success for r in results)
            
            build_result = BuildResult(
                results=results,
                success=success,
                total_time=total_time,
                parallel_groups=len(parallel_groups)
            )
            
            logger.info(build_result.get_summary())
            return build_result
            
        except Exception as e:
            logger.error(f"Recipe execution failed: {e}")
            # Create error result
            error_result = SingleBuildResult(
                recipe=Recipe(
                    name=recipe_path.name,
                    path=recipe_path,
                    requirements=None,
                    design=None,
                    components=None,
                    metadata=None
                ),
                code=None,
                validation=None,
                quality_result={},
                success=False,
                build_time=time.time() - start_time,
                errors=[str(e)]
            )
            
            return BuildResult(
                results=[error_result],
                success=False,
                total_time=time.time() - start_time
            )
    
    def _discover_recipes(self, recipe_path: Path) -> Dict[str, Recipe]:
        """Discover all recipes including dependencies.
        
        Args:
            recipe_path: Starting recipe path
            
        Returns:
            Dictionary of recipe name to Recipe object
        """
        recipes = {}
        to_process = [recipe_path]
        processed = set()
        
        while to_process:
            current_path = to_process.pop(0)
            
            # Skip if already processed
            if current_path in processed:
                continue
            processed.add(current_path)
            
            # Parse recipe
            try:
                recipe = self.parser.parse_recipe(current_path)
                recipes[recipe.name] = recipe
                
                # Add dependencies to process
                for dep_name in recipe.get_dependencies():
                    dep_path = self.recipe_root / dep_name
                    if dep_path.exists() and dep_path not in processed:
                        to_process.append(dep_path)
                    elif not dep_path.exists():
                        logger.warning(f"Dependency {dep_name} not found at {dep_path}")
                        
            except Exception as e:
                logger.error(f"Failed to parse recipe at {current_path}: {e}")
                raise
        
        return recipes
    
    def _validate_recipes(self, recipes: Dict[str, Recipe]):
        """Validate all recipes.
        
        Args:
            recipes: Recipes to validate
            
        Raises:
            Exception: If validation fails
        """
        for name, recipe in recipes.items():
            logger.debug(f"Validating recipe {name}")
            result = self.validator.validate(recipe)
            
            if not result.valid:
                errors = result.get_errors()
                if errors:
                    error_msg = f"Recipe {name} validation failed:\n"
                    for error in errors:
                        error_msg += f"  - {error.message}\n"
                    raise Exception(error_msg)
            
            # Log warnings
            warnings = result.get_warnings()
            for warning in warnings:
                logger.warning(f"{name}: {warning.message}")
    
    def _handle_complex_recipes(self, recipes: Dict[str, Recipe]):
        """Check and handle complex recipes that need decomposition.
        
        Args:
            recipes: Recipes to check
        """
        for name, recipe in list(recipes.items()):
            complexity = self.decomposer.evaluate_complexity(recipe)
            
            if complexity.needs_decomposition:
                logger.warning(
                    f"Recipe {name} is complex (score: {complexity.score}): "
                    f"{', '.join(complexity.reasons)}"
                )
                
                # In dry-run mode, just warn
                # In real mode, could decompose automatically
                if complexity.strategy:
                    logger.info(
                        f"Suggested decomposition: {complexity.strategy.get_description()}"
                    )
    
    def _execute_parallel_groups(self, parallel_groups, options: BuildOptions) -> List[SingleBuildResult]:
        """Execute recipe groups with parallelization.
        
        Args:
            parallel_groups: Groups of recipes that can run in parallel
            options: Build options
            
        Returns:
            List of build results
        """
        results = []
        
        for group_num, group in enumerate(parallel_groups, 1):
            logger.info(f"Executing parallel group {group_num}/{len(parallel_groups)} "
                       f"with {group.size()} recipes")
            
            if options.parallel and group.size() > 1:
                # Execute group in parallel
                group_results = self._execute_group_parallel(group.recipes, options)
            else:
                # Execute sequentially
                group_results = self._execute_group_sequential(group.recipes, options)
            
            results.extend(group_results)
            
            # Update built recipes for dependency injection
            for result in group_results:
                if result.success and result.code:
                    self.built_recipes[result.recipe.name] = result.code
        
        return results
    
    def _execute_group_parallel(self, recipes: List[Recipe], options: BuildOptions) -> List[SingleBuildResult]:
        """Execute recipes in parallel.
        
        Args:
            recipes: Recipes to execute
            options: Build options
            
        Returns:
            List of results
        """
        results = []
        max_workers = min(options.get_max_workers(), len(recipes))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all recipes for parallel execution
            futures = []
            for recipe in recipes:
                if self._should_build(recipe, options):
                    future = executor.submit(self._execute_single, recipe, options)
                    futures.append((recipe, future))
                else:
                    # Skip recipe
                    logger.info(f"Skipping {recipe.name} (no changes)")
            
            # Collect results
            for recipe, future in futures:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per recipe
                    results.append(result)
                    self.state_manager.record_build(recipe, result)
                except concurrent.futures.TimeoutError:
                    error_result = self._create_error_result(
                        recipe, 
                        Exception("Build timeout after 5 minutes")
                    )
                    results.append(error_result)
                except Exception as e:
                    error_result = self._create_error_result(recipe, e)
                    results.append(error_result)
        
        return results
    
    def _execute_group_sequential(self, recipes: List[Recipe], options: BuildOptions) -> List[SingleBuildResult]:
        """Execute recipes sequentially.
        
        Args:
            recipes: Recipes to execute
            options: Build options
            
        Returns:
            List of results
        """
        results = []
        
        for recipe in recipes:
            if self._should_build(recipe, options):
                try:
                    result = self._execute_single(recipe, options)
                    results.append(result)
                    self.state_manager.record_build(recipe, result)
                except Exception as e:
                    error_result = self._create_error_result(recipe, e)
                    results.append(error_result)
            else:
                logger.info(f"Skipping {recipe.name} (no changes)")
        
        return results
    
    def _should_build(self, recipe: Recipe, options: BuildOptions) -> bool:
        """Check if recipe should be built.
        
        Args:
            recipe: Recipe to check
            options: Build options
            
        Returns:
            True if recipe should be built
        """
        if options.force_rebuild:
            return True
        
        return self.state_manager.needs_rebuild(recipe)
    
    def _execute_single(self, recipe: Recipe, options: BuildOptions) -> SingleBuildResult:
        """Execute a single recipe following TDD approach.
        
        Args:
            recipe: Recipe to execute
            options: Build options
            
        Returns:
            Build result for this recipe
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        logger.info(f"Building recipe: {recipe.name}")
        
        try:
            # Build context with dependencies
            context = BuildContext(
                recipe=recipe,
                dependencies=self._get_built_dependencies(recipe),
                dry_run=options.dry_run,
                verbose=options.verbose,
                output_dir=options.output_dir / recipe.name if options.output_dir else None
            )
            
            # Generate code using TDD (tests first, then implementation)
            code = self.generator.generate(recipe, context)
            
            # Additional test generation if needed
            tests = None
            if not options.skip_tests:
                tests = self.test_generator.generate_tests(recipe, code)
            
            # Create implementation object
            impl = Implementation(code=code, tests=tests)
            
            # Validate against requirements
            validation = None
            if not options.skip_validation:
                validation = self.code_validator.validate(recipe, impl)
                if not validation.passed:
                    errors.extend(validation.errors)
            
            # Run quality gates if not dry run
            quality_result = {}
            if not options.dry_run and not options.skip_tests:
                quality_result = self.quality_gates.run_all_gates(impl)
                
                # Check for quality failures
                failed_gates = [k for k, v in quality_result.items() if not v]
                if failed_gates:
                    errors.extend([f"Quality gate failed: {gate}" for gate in failed_gates])
            
            # Determine success
            success = len(errors) == 0
            
            # Write files to disk if successful and not dry-run
            if success and not options.dry_run and code:
                output_dir = options.output_dir or Path(".recipe_build")
                code.write_to_disk(output_dir / recipe.name)
            
            return SingleBuildResult(
                recipe=recipe,
                code=code,
                validation=validation,
                quality_result=quality_result,
                success=success,
                build_time=time.time() - start_time,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to build {recipe.name}: {e}")
            return SingleBuildResult(
                recipe=recipe,
                code=None,
                validation=None,
                quality_result={},
                success=False,
                build_time=time.time() - start_time,
                errors=[str(e)]
            )
    
    def _get_built_dependencies(self, recipe: Recipe) -> Dict[str, GeneratedCode]:
        """Get built dependencies for a recipe.
        
        Args:
            recipe: Recipe needing dependencies
            
        Returns:
            Dictionary of dependency name to generated code
        """
        dependencies = {}
        
        for dep_name in recipe.get_dependencies():
            if dep_name in self.built_recipes:
                dependencies[dep_name] = self.built_recipes[dep_name]
            else:
                logger.warning(f"Dependency {dep_name} not available for {recipe.name}")
        
        return dependencies
    
    def _create_error_result(self, recipe: Recipe, error: Exception) -> SingleBuildResult:
        """Create an error result for a failed recipe.
        
        Args:
            recipe: Recipe that failed
            error: Exception that occurred
            
        Returns:
            Error build result
        """
        return SingleBuildResult(
            recipe=recipe,
            code=None,
            validation=None,
            quality_result={},
            success=False,
            build_time=0,
            errors=[str(error)]
        )