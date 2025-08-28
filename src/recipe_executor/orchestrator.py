"""Main orchestration engine for Recipe Executor."""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import time
import logging
from datetime import datetime

from .recipe_model import (
    Recipe,
    BuildContext,
    BuildResult,
    SingleBuildResult,
)
from .recipe_parser import RecipeParser
from .dependency_resolver import DependencyResolver
from .claude_code_generator import ClaudeCodeGenerator
from .test_generator import TestGenerator
from .validator import Validator, Implementation
from .state_manager import StateManager
from .python_standards import QualityGates
from .pattern_manager import PatternManager
from .parallel_builder import ParallelRecipeBuilder
from .component_registry import ComponentRegistry

# Configure logging
LOG_DIR = Path(".recipe_build/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"recipe_executor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Set up logger
logger = logging.getLogger("recipe_executor")
logger.setLevel(logging.DEBUG)

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# Console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(console_formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Log startup
logger.info(f"Recipe Executor started - Log file: {LOG_FILE}")


@dataclass
class BuildOptions:
    """Options for building recipes."""

    dry_run: bool = False
    verbose: bool = False
    force_rebuild: bool = False
    parallel: bool = False
    output_dir: Optional[Path] = None
    allow_self_overwrite: bool = False  # Dangerous: allows overwriting Recipe Executor itself


class RecipeOrchestrator:
    """Main orchestration engine for recipe execution."""

    def __init__(self, recipe_root: Optional[Path] = None):
        """Initialize orchestrator with all components."""
        self.recipe_root = recipe_root or Path("recipes")
        self.parser = RecipeParser()
        self.resolver = DependencyResolver(self.recipe_root)
        self.generator = ClaudeCodeGenerator()
        self.test_generator = TestGenerator()
        self.validator = Validator()
        self.state_manager = StateManager()
        self.quality_gates = QualityGates()
        self.pattern_manager = PatternManager()
        self.parallel_builder = None  # Initialized on demand

    def execute(self, recipe_path: Path, options: Optional[BuildOptions] = None) -> BuildResult:
        """Execute a recipe and all its dependencies."""
        if options is None:
            options = BuildOptions()

        print(f"🚀 Executing recipe: {recipe_path}")
        logger.info(f"Starting execution of recipe: {recipe_path}")
        if options.dry_run:
            print("DRY RUN MODE - No files will be created")
            logger.info("DRY RUN MODE enabled")

        # Check for self-overwrite protection
        if self._would_overwrite_self(recipe_path, options):
            if not options.allow_self_overwrite:
                raise ValueError(
                    "ERROR: Attempting to overwrite Recipe Executor's own source files!\n"
                    "This would destroy the running code.\n\n"
                    "Suggested solutions:\n"
                    "1. Use a different output directory: --output-dir=generated/\n"
                    "2. Use a git worktree: git worktree add .worktrees/regeneration\n"
                    "3. If you really want to overwrite (dangerous!), use --allow-self-overwrite\n"
                )
            else:
                # Double-check with user
                print("WARNING: You are about to overwrite Recipe Executor's own source files!")
                print("This is dangerous and could break the system.")
                response = input("Are you SURE you want to continue? (yes/no): ")
                if response.lower() != "yes":
                    raise ValueError("Self-overwrite cancelled by user")

        start_time = time.time()

        # 1. Parse all recipes
        recipes = self._discover_recipes(recipe_path)

        # 2. Resolve dependencies
        build_order = self.resolver.resolve(recipes)

        # 3. Execute based on parallel option
        results: List[SingleBuildResult] = []

        if options.parallel:
            # Use parallel builder for better performance
            if self.parallel_builder is None:
                self.parallel_builder = ParallelRecipeBuilder(max_workers=4)

            # Filter recipes that need rebuilding
            recipes_to_build = [
                recipe
                for recipe in build_order
                if self.state_manager.needs_rebuild(recipe, options.force_rebuild)
            ]

            if recipes_to_build:
                # Build in parallel - need to group them first
                recipe_groups = [[r] for r in recipes_to_build]  # Each in its own group for now
                parallel_result = self.parallel_builder.build_parallel(
                    recipe_groups, 
                    lambda r, opts: self._execute_single(r, opts),
                    options
                )
                results = list(parallel_result.results.values())

                # Record builds in state manager
                for result in results:
                    self.state_manager.record_build(result.recipe, result)

                if options.verbose:
                    print(
                        f"\nParallel build complete in {parallel_result.total_time:.2f}s"
                    )
        else:
            # Sequential execution (original logic)
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
            # Apply design patterns to recipe
            patterns = self.pattern_manager.get_patterns_for_recipe(recipe)
            if patterns and options.verbose:
                print(f"Applying {len(patterns)} design patterns to {recipe.name}")
                for pattern in patterns:
                    print(f"  - {pattern.name} v{pattern.version}")

            # Apply patterns to create enhanced recipe
            enhanced_recipe = (
                self.pattern_manager.apply_patterns_to_recipe(recipe, patterns)
                if patterns
                else recipe
            )

            # Build context with dependencies
            context = BuildContext(
                recipe=enhanced_recipe,
                dry_run=options.dry_run,
                verbose=options.verbose,
                force_rebuild=options.force_rebuild,
            )

            # Add pattern templates to context
            if patterns:
                pattern_templates = self.pattern_manager.get_pattern_templates(patterns)
                context.options["pattern_templates"] = pattern_templates

            # Generate code
            print(f"📚 Phase 1: Parsing {recipe.name}")
            print(
                f"   Requirements: {len(enhanced_recipe.requirements.functional_requirements)} functional, {len(enhanced_recipe.requirements.non_functional_requirements)} non-functional"
            )
            print(
                f"   Components: {len(enhanced_recipe.design.components) if enhanced_recipe.design else 0}"
            )
            logger.info(
                f"Recipe {recipe.name}: {len(enhanced_recipe.requirements.functional_requirements)} FR, {len(enhanced_recipe.requirements.non_functional_requirements)} NFR, {len(enhanced_recipe.design.components) if enhanced_recipe.design else 0} components"
            )

            print(f"🔨 Phase 2: Generating code for {recipe.name}")
            logger.info(f"Starting code generation for {recipe.name}")
            # Ensure output_dir is absolute to avoid path issues
            if options.output_dir:
                abs_output_dir = options.output_dir if options.output_dir.is_absolute() else Path.cwd() / options.output_dir
            else:
                abs_output_dir = None
            code = self.generator.generate(enhanced_recipe, context, output_dir=abs_output_dir)
            logger.info(
                f"Code generation complete for {recipe.name}: {len(code.files) if code else 0} files generated"
            )

            # Validate component completeness
            if code and recipe.name == "recipe-executor":  # Only validate for self-hosting
                registry = ComponentRegistry()
                is_complete, missing = registry.validate_completeness(code.files)
                if not is_complete:
                    logger.warning(f"Missing {len(missing)} required components for self-hosting")
                    if options.verbose:
                        print(f"⚠️  Missing components: {', '.join(missing[:5])}...")
                else:
                    logger.info("✅ All required components generated for self-hosting")

            # Generate tests
            if options.verbose:
                print(f"Generating tests for {recipe.name}...")
            tests = self.test_generator.generate_tests(enhanced_recipe)

            # Create implementation
            impl = Implementation(code=code, tests=tests)

            # Validate
            if options.verbose:
                print(f"Validating {recipe.name}...")
            validation = self.validator.validate(enhanced_recipe, impl)

            # Run quality gates (if not dry run)
            quality_result: Dict[str, bool] = {}
            if not options.dry_run:
                if options.verbose:
                    print(f"Running quality gates for {recipe.name}...")

                # Write generated files to disk
                output_dir = options.output_dir or Path.cwd()
                for filepath, content in code.files.items():
                    full_path = output_dir / filepath
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content)
                    if options.verbose:
                        print(f"  Created: {full_path}")

                # Write test files
                for filepath, content in tests.test_files.items():
                    full_path = output_dir / filepath
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content)
                    if options.verbose:
                        print(f"  Created test: {full_path}")

                # Run quality gates on the output directory
                quality_result = self.quality_gates.run_all_gates(output_dir)

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
            quality_result = {}  # type: ignore[assignment]
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
            "recipe": target.name,
            "version": target.components.version,
            "type": target.components.type.value,
            "dependencies": target.get_dependencies(),
            "dependents": list(impact["dependents"]),
            "execution_plan": plan,
            "validation_issues": issues,
            "total_recipes": len(recipes),
        }

    def _would_overwrite_self(self, recipe_path: Path, options: BuildOptions) -> bool:
        """Check if executing this recipe would overwrite Recipe Executor itself.

        Args:
            recipe_path: Path to the recipe being executed
            options: Build options

        Returns:
            True if this would overwrite Recipe Executor's own files
        """
        # Check if we're trying to regenerate the recipe-executor
        if "recipe-executor" not in str(recipe_path):
            return False

        # If output_dir is specified, check if it would overlap with our source
        if options.output_dir:
            # Resolve to absolute paths for comparison
            output_abs = options.output_dir.resolve()
            our_source = Path(__file__).parent.resolve()  # src/recipe_executor/

            # Check if output would write to our source directory
            try:
                output_abs.relative_to(our_source)
                return True  # Output is inside our source directory
            except ValueError:
                pass  # Not a subdirectory

            # Check if our source is inside the output directory
            try:
                our_source.relative_to(output_abs)
                return True  # Our source is inside output directory
            except ValueError:
                pass  # Not a subdirectory

            return False
        else:
            # No output_dir specified - would write to current directory
            # Check if current directory contains Recipe Executor source
            cwd = Path.cwd()
            our_source = Path(__file__).parent.resolve()

            # Check if we would write src/recipe_executor/ in current directory
            potential_output = cwd / "src" / "recipe_executor"
            if potential_output.resolve() == our_source:
                return True

            return False
