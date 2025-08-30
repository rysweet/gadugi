#!/usr/bin/env python3
"""
OrchestratorCLI - Command Line Interface for Orchestrator Agent

This module provides the CLI entry point that responds to `/agent:OrchestratorAgent`
invocations, parsing user input and coordinating with the main orchestrator.

Key Features:
- Parses Claude agent invocation parameters
- Validates prompt file inputs
- Integrates with OrchestratorCoordinator for execution
- Provides user-friendly output and error handling
- Supports both interactive and batch execution modes
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

# Import orchestrator components
try:
    from .orchestrator_main import (
        OrchestratorCoordinator,
        OrchestrationConfig,
        OrchestrationResult,
    )
except ImportError:
    from orchestrator_main import (
        OrchestratorCoordinator,
        OrchestrationConfig,
        OrchestrationResult,
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OrchestrationCLI:
    """
    Command-line interface for the orchestrator agent.

    This class handles parsing of user inputs and coordination with the
    main orchestrator for parallel execution.
    """

    def __init__(self, project_root: str = "."):
        """Initialize the CLI interface"""
        self.project_root = Path(project_root).resolve()
        self.prompts_dir = self.project_root / "prompts"

        # Validate environment
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

        logger.info(f"OrchestrationCLI initialized for project: {self.project_root}")

    def parse_user_input(self, user_input: str) -> List[str]:
        """
        Parse user input to extract prompt files for execution.

        Expected format:
        Execute these specific prompts in parallel:
        - test-definition-node.md
        - test-relationship-creator.md
        - test-documentation-linker.md
        """
        logger.info("Parsing user input for prompt files...")

        prompt_files = []
        lines = user_input.strip().split("\n")

        # Look for prompt file specifications
        in_prompt_list = False
        for line in lines:
            line = line.strip()

            # Detect start of prompt list
            if any(
                keyword in line.lower()
                for keyword in ["execute these", "prompts in parallel", "prompt files"]
            ):
                in_prompt_list = True
                continue

            # Skip empty lines and headers
            if not line or line.startswith("#"):
                continue

            # Parse prompt file entries
            if in_prompt_list:
                # Handle bullet points (-, *, +)
                if line.startswith(("-", "*", "+")):
                    prompt_file = line[1:].strip()
                    if prompt_file:
                        prompt_files.append(prompt_file)

                # Handle numbered lists (1., 2., etc.)
                elif line[0].isdigit() and "." in line:
                    parts = line.split(".", 1)
                    if len(parts) > 1:
                        prompt_file = parts[1].strip()
                        if prompt_file:
                            prompt_files.append(prompt_file)

                # Handle plain filenames (fallback)
                elif line.endswith(".md"):
                    prompt_files.append(line)

        # Validate prompt files
        validated_files = self._validate_prompt_files(prompt_files)

        logger.info(f"Parsed {len(validated_files)} valid prompt files from user input")
        return validated_files

    def _validate_prompt_files(self, prompt_files: List[str]) -> List[str]:
        """Validate that prompt files exist and are accessible"""
        validated_files = []

        for prompt_file in prompt_files:
            # Clean up filename
            prompt_file = prompt_file.strip()
            if not prompt_file:
                continue

            # Ensure .md extension
            if not prompt_file.endswith(".md"):
                prompt_file += ".md"

            # Check if file exists
            prompt_path = self.prompts_dir / prompt_file
            if prompt_path.exists():
                validated_files.append(prompt_file)
                logger.info(f"Validated prompt file: {prompt_file}")
            else:
                logger.warning(
                    f"Prompt file not found: {prompt_file} (path: {prompt_path})"
                )

        return validated_files

    def execute_orchestration(
        self,
        prompt_files: List[str],
        config: OrchestrationConfig = None,  # type: ignore[assignment]
    ) -> OrchestrationResult:
        """Execute orchestration with specified prompt files"""
        if not prompt_files:
            raise ValueError("No valid prompt files specified for orchestration")

        logger.info(f"Starting orchestration of {len(prompt_files)} prompt files")

        # Use default config if none provided
        if config is None:
            config = OrchestrationConfig()

        # Initialize orchestrator
        orchestrator = OrchestratorCoordinator(config, str(self.project_root))

        try:
            # Execute orchestration
            result = orchestrator.orchestrate(prompt_files)

            # Report results
            self._report_results(result)

            return result

        except KeyboardInterrupt:
            logger.info("Orchestration interrupted by user")
            orchestrator.shutdown()
            raise

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            orchestrator.shutdown()
            raise

        finally:
            # Ensure cleanup
            orchestrator.shutdown()

    def _report_results(self, result: OrchestrationResult) -> None:
        """Report orchestration results to user"""
        print("\n" + "=" * 60)
        print("ORCHESTRATION RESULTS")
        print("=" * 60)

        print(f"Orchestration ID: {result.task_id}")
        print(f"Total Tasks: {result.total_tasks}")
        print(f"Successful Tasks: {result.successful_tasks}")
        print(f"Failed Tasks: {result.failed_tasks}")
        print(f"Execution Time: {result.execution_time_seconds:.1f} seconds")

        if result.parallel_speedup:
            print(f"Parallel Speedup: {result.parallel_speedup:.1f}x")

        # Success rate
        if result.total_tasks > 0:
            success_rate = (result.successful_tasks / result.total_tasks) * 100
            print(f"Success Rate: {success_rate:.1f}%")

        # Task details
        if result.task_results:
            print("\nTask Details:")
            for task_result in result.task_results:
                status = "✅ SUCCESS" if task_result.success else "❌ FAILED"  # type: ignore
                exec_time = getattr(task_result, "execution_time", 0) or 0
                print(f"  {task_result.task_id}: {status} ({exec_time:.1f}s)")

                if not task_result.success and hasattr(task_result, "error_message"):  # type: ignore
                    error_msg = getattr(task_result, "error_message", "Unknown error")
                    print(f"    Error: {error_msg}")

        # Error summary
        if result.error_summary:
            print(f"\nError Summary: {result.error_summary}")

        print("=" * 60)

        # Log results
        if result.successful_tasks == result.total_tasks:
            logger.info("🎉 All tasks completed successfully!")
        elif result.successful_tasks > 0:
            logger.info(
                f"⚠️  Partial success: {result.successful_tasks}/{result.total_tasks} tasks"
            )
        else:
            logger.error("❌ All tasks failed")

    def run_interactive_mode(self) -> None:
        """Run in interactive mode for testing and development"""
        print("Orchestrator Agent - Interactive Mode")
        print(
            "Enter prompt files to execute in parallel (one per line, empty line to start):"
        )

        prompt_files = []
        while True:
            try:
                line = input("> ").strip()
                if not line:
                    break
                prompt_files.append(line)
            except KeyboardInterrupt:
                print("\nExiting...")
                return

        if not prompt_files:
            print("No prompt files specified")
            return

        # Validate files
        validated_files = self._validate_prompt_files(prompt_files)
        if not validated_files:
            print("No valid prompt files found")
            return

        print(f"\nExecuting {len(validated_files)} prompt files...")

        # Execute orchestration
        try:
            result = self.execute_orchestration(validated_files)

            if result.successful_tasks == result.total_tasks:
                print("\n🎉 Orchestration completed successfully!")
            else:
                print(
                    f"\n⚠️  Orchestration completed with {result.failed_tasks} failures"
                )

        except Exception as e:
            print(f"\n❌ Orchestration failed: {e}")


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Orchestrator Agent CLI - Parallel Workflow Execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python orchestrator_cli.py --interactive

  # Direct execution
  python orchestrator_cli.py test-node.md test-creator.md

  # With configuration
  python orchestrator_cli.py --max-parallel 6 --timeout 3 task1.md task2.md

  # Parse from stdin (for agent invocation)
  echo "Execute these prompts: test.md" | python orchestrator_cli.py --stdin
        """,
    )

    # Input options
    parser.add_argument(
        "prompt_files", nargs="*", help="Prompt files to execute in parallel"
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read user input from stdin (for agent invocation)",
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Run in interactive mode"
    )

    # Configuration options
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=4,
        help="Maximum number of parallel tasks (default: 4)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=12,
        help="Execution timeout in hours (default: 12)",
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--monitoring-dir",
        default=".gadugi/monitoring",
        help="Monitoring directory (default: .gadugi/monitoring)",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Disable fallback to sequential execution",
    )

    # Logging options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress output except errors"
    )

    return parser.parse_args()


def main():
    """Main entry point for orchestrator CLI"""
    args = parse_arguments()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    try:
        # Initialize CLI interface
        cli = OrchestrationCLI(args.project_root)

        # Determine input source
        prompt_files = []

        if args.interactive:
            # Interactive mode
            cli.run_interactive_mode()
            return

        elif args.stdin:
            # Read from stdin (agent invocation)
            user_input = sys.stdin.read()
            prompt_files = cli.parse_user_input(user_input)

        elif args.prompt_files:
            # Direct command line arguments
            prompt_files = args.prompt_files

        else:
            # No input specified
            print("Error: No prompt files specified. Use --help for usage information.")
            sys.exit(1)

        # Validate input
        if not prompt_files:
            print("Error: No valid prompt files found.")
            sys.exit(1)

        # Create orchestration configuration
        config = OrchestrationConfig(
            max_parallel_tasks=args.max_parallel,
            execution_timeout_hours=args.timeout,
            monitoring_dir=args.monitoring_dir,
            fallback_to_sequential=not args.no_fallback,
        )

        # Execute orchestration
        result = cli.execute_orchestration(prompt_files, config)

        # Exit with appropriate code
        if result.failed_tasks > 0:
            sys.exit(1)  # Indicate partial failure
        else:
            sys.exit(0)  # Success

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)  # Standard SIGINT exit code

    except Exception as e:
        logger.error(f"CLI execution failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
