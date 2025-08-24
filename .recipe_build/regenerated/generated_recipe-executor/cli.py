#!/usr/bin/env python3
"""Recipe Executor CLI - Self-hosting build system."""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.orchestrator import BuildOptions, RecipeOrchestrator


def setup_logging(verbose: bool):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s' if verbose else '%(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[logging.StreamHandler()]
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Recipe Executor - Self-hosting build system for AI-powered code generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build a single recipe
  recipe-executor build path/to/recipe
  
  # Build with dependencies
  recipe-executor build path/to/recipe --parallel
  
  # Force rebuild
  recipe-executor build path/to/recipe --force
  
  # Dry run to see what would be built
  recipe-executor build path/to/recipe --dry-run
  
  # Validate recipes without building
  recipe-executor validate path/to/recipe
  
  # Check recipe complexity
  recipe-executor complexity path/to/recipe
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build a recipe and its dependencies')
    build_parser.add_argument('recipe', type=Path, help='Path to recipe directory')
    build_parser.add_argument('--parallel', action='store_true', help='Build in parallel where possible')
    build_parser.add_argument('--force', action='store_true', help='Force rebuild even if up to date')
    build_parser.add_argument('--dry-run', action='store_true', help='Show what would be built without building')
    build_parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    build_parser.add_argument('--skip-validation', action='store_true', help='Skip validation checks')
    build_parser.add_argument('--output-dir', type=Path, help='Output directory for generated code')
    build_parser.add_argument('--max-workers', type=int, default=4, help='Maximum parallel workers')
    build_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate recipe structure')
    validate_parser.add_argument('recipe', type=Path, help='Path to recipe directory')
    validate_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Complexity command
    complexity_parser = subparsers.add_parser('complexity', help='Analyze recipe complexity')
    complexity_parser.add_argument('recipe', type=Path, help='Path to recipe directory')
    complexity_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Clean command
    clean_parser = subparsers.add_parser('clean', help='Clean build state and artifacts')
    clean_parser.add_argument('--all', action='store_true', help='Clean all state')
    clean_parser.add_argument('--recipe', type=str, help='Clean specific recipe')
    
    # Self-test command
    selftest_parser = subparsers.add_parser('selftest', help='Run self-hosting test')
    selftest_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set up logging
    setup_logging(args.verbose if hasattr(args, 'verbose') else False)
    
    # Execute command
    if args.command == 'build':
        return build_command(args)
    elif args.command == 'validate':
        return validate_command(args)
    elif args.command == 'complexity':
        return complexity_command(args)
    elif args.command == 'clean':
        return clean_command(args)
    elif args.command == 'selftest':
        return selftest_command(args)
    else:
        parser.print_help()
        return 1


def build_command(args):
    """Execute build command."""
    if not args.recipe.exists():
        print(f"Error: Recipe directory not found: {args.recipe}")
        return 1
    
    # Create build options
    options = BuildOptions(
        parallel=args.parallel,
        force_rebuild=args.force,
        dry_run=args.dry_run,
        verbose=args.verbose,
        max_workers=args.max_workers,
        skip_tests=args.skip_tests,
        skip_validation=args.skip_validation,
        output_dir=args.output_dir
    )
    
    # Create orchestrator
    orchestrator = RecipeOrchestrator()
    
    try:
        # Execute build
        result = orchestrator.execute(args.recipe, options)
        
        # Print summary
        print("\n" + "=" * 60)
        print(result.get_summary())
        print("=" * 60)
        
        return 0 if result.success else 1
        
    except Exception as e:
        print(f"Build failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def validate_command(args):
    """Execute validate command."""
    if not args.recipe.exists():
        print(f"Error: Recipe directory not found: {args.recipe}")
        return 1
    
    from src.recipe_parser import RecipeParser
    from src.recipe_validator import RecipeValidator
    
    try:
        # Parse recipe
        parser = RecipeParser()
        recipe = parser.parse_recipe(args.recipe)
        
        print(f"Validating recipe: {recipe.name}")
        print(recipe.to_summary())
        print("\n" + "=" * 60)
        
        # Validate recipe
        validator = RecipeValidator()
        result = validator.validate(recipe)
        
        if result.valid:
            print("✓ Recipe is valid")
        else:
            print("✗ Recipe has validation issues:")
            
            # Print errors
            for issue in result.get_errors():
                print(f"  ERROR [{issue.location}]: {issue.message}")
                if issue.suggestion:
                    print(f"    Suggestion: {issue.suggestion}")
            
            # Print warnings
            for issue in result.get_warnings():
                print(f"  WARNING [{issue.location}]: {issue.message}")
                if issue.suggestion:
                    print(f"    Suggestion: {issue.suggestion}")
        
        return 0 if result.valid else 1
        
    except Exception as e:
        print(f"Validation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def complexity_command(args):
    """Execute complexity analysis command."""
    if not args.recipe.exists():
        print(f"Error: Recipe directory not found: {args.recipe}")
        return 1
    
    from src.recipe_parser import RecipeParser
    from src.recipe_decomposer import RecipeDecomposer
    
    try:
        # Parse recipe
        parser = RecipeParser()
        recipe = parser.parse_recipe(args.recipe)
        
        print(f"Analyzing complexity for: {recipe.name}")
        print("=" * 60)
        
        # Analyze complexity
        decomposer = RecipeDecomposer()
        result = decomposer.evaluate_complexity(recipe)
        
        print(f"Complexity Score: {result.score}/10 ({result.get_severity()})")
        print(f"Needs Decomposition: {'Yes' if result.needs_decomposition else 'No'}")
        
        if result.reasons:
            print("\nComplexity Factors:")
            for reason in result.reasons:
                print(f"  - {reason}")
        
        if result.functional_areas:
            print(f"\nFunctional Areas: {len(result.functional_areas)}")
            for area in result.functional_areas:
                print(f"  - {area.name}: {area.get_requirement_count()} requirements, "
                      f"{area.get_component_count()} components")
        
        if result.strategy:
            print(f"\nSuggested Strategy: {result.strategy.get_description()}")
            print(f"Estimated Sub-recipes: {result.strategy.estimated_sub_recipes}")
            if result.strategy.suggested_splits:
                print("Suggested Splits:")
                for split in result.strategy.suggested_splits:
                    print(f"  - {split}")
        
        return 0
        
    except Exception as e:
        print(f"Complexity analysis failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def clean_command(args):
    """Execute clean command."""
    from src.state_manager import StateManager
    
    state_manager = StateManager()
    
    if args.all:
        print("Cleaning all build state and artifacts...")
        state_manager.clear_state()
        print("✓ All state cleared")
    elif args.recipe:
        print(f"Cleaning state for recipe: {args.recipe}")
        state_manager.clear_state(args.recipe)
        print(f"✓ State cleared for {args.recipe}")
    else:
        # Show statistics
        stats = state_manager.get_statistics()
        print("Build State Statistics:")
        print(f"  Total cached: {stats['total_cached']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Cache size: {stats['cache_size_mb']} MB")
        print("\nUse --all to clean all state or --recipe NAME to clean specific recipe")
    
    return 0


def selftest_command(args):
    """Execute self-hosting test."""
    print("Running Recipe Executor Self-Hosting Test")
    print("=" * 60)
    
    # Path to recipe-executor's own recipe
    recipe_path = Path(__file__).parent / "recipes" / "recipe-executor"
    
    if not recipe_path.exists():
        print(f"Error: Recipe executor recipe not found at {recipe_path}")
        print("Creating self-hosting recipe...")
        
        # Create minimal self-hosting recipe
        recipe_path.mkdir(parents=True, exist_ok=True)
        
        # Create requirements.md
        (recipe_path / "requirements.md").write_text("""# Recipe Executor Requirements

## Purpose
Self-hosting build system for AI-powered code generation.

## Functional Requirements
- MUST parse recipe files
- MUST validate recipes
- MUST generate code using Claude CLI
- MUST support TDD approach
- MUST handle dependencies

## Success Criteria
- Self-regeneration test passes
- All quality gates pass
""")
        
        # Create design.md
        (recipe_path / "design.md").write_text("""# Recipe Executor Design

## Architecture
Multi-stage pipeline with validation, generation, and quality checks.

## Components
- **RecipeParser**: Parse recipe files
- **RecipeValidator**: Validate structure
- **ClaudeCodeGenerator**: Generate code
- **RecipeOrchestrator**: Coordinate execution

## Language
Python
""")
        
        # Create components.json
        import json
        components = {
            "name": "recipe-executor",
            "version": "1.0.0",
            "type": "CORE",
            "dependencies": [],
            "description": "Self-hosting recipe executor",
            "metadata": {"self_hosting": True}
        }
        with open(recipe_path / "components.json", 'w') as f:
            json.dump(components, f, indent=2)
    
    # Run self-test
    print(f"Building recipe executor from: {recipe_path}")
    
    # Create build options
    options = BuildOptions(
        parallel=False,
        force_rebuild=True,
        dry_run=False,
        verbose=args.verbose,
        skip_tests=False,
        skip_validation=False,
        output_dir=Path(".recipe_build/selftest")
    )
    
    # Create orchestrator
    orchestrator = RecipeOrchestrator()
    
    try:
        # Execute build
        result = orchestrator.execute(recipe_path, options)
        
        if result.success:
            print("\n✓ SELF-HOSTING TEST PASSED")
            print("Recipe Executor successfully regenerated itself!")
        else:
            print("\n✗ SELF-HOSTING TEST FAILED")
            print("Recipe Executor could not regenerate itself")
        
        # Print summary
        print("\n" + "=" * 60)
        print(result.get_summary())
        print("=" * 60)
        
        return 0 if result.success else 1
        
    except Exception as e:
        print(f"Self-test failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())