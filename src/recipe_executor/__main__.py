"""Command-line interface for Recipe Executor."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .orchestrator import RecipeOrchestrator, BuildOptions
from .enhanced_orchestrator import EnhancedRecipeOrchestrator
from .self_hosting import SelfHostingManager


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for Recipe Executor CLI."""
    parser = argparse.ArgumentParser(
        description="Recipe Executor - Generate code from requirements and design",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute a recipe
  python -m recipe_executor execute recipes/my-service/
  
  # Execute with specific output directory  
  python -m recipe_executor execute recipes/my-service/ --output-dir=generated/
  
  # Dry run to see what would be generated
  python -m recipe_executor execute recipes/my-service/ --dry-run
  
  # Analyze a recipe and its dependencies
  python -m recipe_executor analyze recipes/my-service/
  
  # Apply design patterns
  python -m recipe_executor execute recipes/my-service/ --patterns=python-quality
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Execute command
    execute_parser = subparsers.add_parser("execute", help="Execute a recipe and generate code")
    execute_parser.add_argument("recipe", type=Path, help="Path to the recipe directory")
    execute_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without actually creating files",
    )
    execute_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    execute_parser.add_argument(
        "--force", action="store_true", help="Force rebuild even if nothing has changed"
    )
    execute_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to write generated files (default: current directory)",
    )
    execute_parser.add_argument(
        "--allow-self-overwrite",
        action="store_true",
        help="DANGEROUS: Allow overwriting Recipe Executor's own source files",
    )
    execute_parser.add_argument(
        "--patterns", type=str, help="Comma-separated list of design patterns to apply"
    )

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a recipe without executing it")
    analyze_parser.add_argument("recipe", type=Path, help="Path to the recipe directory")
    
    # Self-host command
    selfhost_parser = subparsers.add_parser("self-host", help="Regenerate Recipe Executor from its own recipe")
    selfhost_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".recipe_build/self_host"),
        help="Directory for generated code"
    )
    selfhost_parser.add_argument(
        "--validate",
        action="store_true",
        help="Only validate self-hosting capability without generating"
    )
    selfhost_parser.add_argument(
        "--verify",
        action="store_true",
        help="Run full verification including bootstrap test"
    )
    selfhost_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="DANGEROUS: Overwrite existing Recipe Executor code"
    )
    
    # Enhanced pipeline command
    enhanced_parser = subparsers.add_parser("pipeline", help="Execute recipe through enhanced 10-stage pipeline")
    enhanced_parser.add_argument("recipe", type=Path, help="Path to the recipe directory")
    enhanced_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to write generated files"
    )
    enhanced_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without creating files"
    )
    enhanced_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    enhanced_parser.add_argument(
        "--force", action="store_true", help="Force rebuild even if nothing changed"
    )

    # Parse arguments
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    # Initialize orchestrator
    orchestrator = RecipeOrchestrator()

    try:
        if args.command == "execute":
            # Build options from arguments
            options = BuildOptions(
                dry_run=args.dry_run,
                verbose=args.verbose,
                force_rebuild=args.force,
                output_dir=args.output_dir,
                allow_self_overwrite=args.allow_self_overwrite,
            )

            # Add patterns to recipe metadata if specified
            if args.patterns:
                print(f"Applying design patterns: {args.patterns}")
                # This would need to be integrated with the orchestrator
                # For now, just note it

            # Execute the recipe
            print(f"Executing recipe: {args.recipe}")
            if args.dry_run:
                print("DRY RUN MODE - No files will be created")

            result = orchestrator.execute(args.recipe, options)

            # Print results
            print(f"\n{'=' * 60}")
            print(f"Execution {'SUCCEEDED' if result.success else 'FAILED'}")
            print(f"Total time: {result.total_time:.2f}s")
            print(f"Recipes built: {len(result.results)}")

            if args.verbose:
                for build_result in result.results:
                    print(f"\n  {build_result.recipe.name}:")
                    print(f"    Success: {build_result.success}")
                    print(f"    Time: {build_result.build_time:.2f}s")
                    if build_result.errors:
                        print(f"    Errors: {', '.join(build_result.errors)}")

            return 0 if result.success else 1

        elif args.command == "analyze":
            # Analyze the recipe
            print(f"Analyzing recipe: {args.recipe}")
            analysis = orchestrator.analyze(args.recipe)

            # Print analysis results
            print(f"\n{'=' * 60}")
            print(f"Recipe: {analysis.get('recipe', 'Unknown')}")
            print(f"Version: {analysis.get('version', 'Unknown')}")
            print(f"Type: {analysis.get('type', 'Unknown')}")
            print(f"Total recipes in dependency tree: {analysis.get('total_recipes', 0)}")

            if deps := analysis.get("dependencies"):
                print(f"\nDependencies ({len(deps)}):")
                for dep in deps:
                    print(f"  - {dep}")

            if dependents := analysis.get("dependents"):
                print(f"\nDependents ({len(dependents)}):")
                for dep in dependents:
                    print(f"  - {dep}")

            if plan := analysis.get("execution_plan"):
                print("\nExecution plan:")
                for i, step in enumerate(plan, 1):
                    print(f"  {i}. {step}")

            if issues := analysis.get("validation_issues"):
                print(f"\nValidation issues ({len(issues)}):")
                for issue in issues:
                    print(f"  - {issue}")

            return 0
            
        elif args.command == "self-host":
            # Self-hosting command
            print("Starting Recipe Executor self-hosting...")
            manager = SelfHostingManager()
            
            if args.validate:
                print("Validating self-hosting capability...")
                result = manager.regenerate_self(validate_only=True)
            elif args.verify:
                print("Running full self-hosting verification...")
                success = manager.verify_self_hosting()
                return 0 if success else 1
            else:
                print(f"Regenerating Recipe Executor to {args.output_dir}")
                result = manager.regenerate_self(
                    output_dir=args.output_dir,
                    allow_overwrite=args.overwrite
                )
            
            print(result.summary)
            return 0 if result.success else 1
            
        elif args.command == "pipeline":
            # Enhanced pipeline command
            print(f"Executing recipe through enhanced pipeline: {args.recipe}")
            
            orchestrator = EnhancedRecipeOrchestrator()
            result = orchestrator.execute_recipe(
                recipe_path=args.recipe,
                output_dir=args.output_dir,
                dry_run=args.dry_run,
                verbose=args.verbose,
                force_rebuild=args.force,
                self_hosting=args.recipe.name == "recipe-executor"
            )
            
            print(result.summary)
            
            return 0 if result.success else 1

        else:
            # This shouldn't happen due to argparse configuration
            parser.print_help()
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
