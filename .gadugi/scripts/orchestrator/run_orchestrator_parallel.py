#!/usr/bin/env python3
"""
Execute the orchestrator agent to run three tasks in parallel.

This script invokes the orchestrator to handle:
1. Fix all pyright errors
2. Complete team coach implementation
3. Clean up all worktrees
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Main execution function."""

    # Change to main repository directory
    repo_dir = Path("/Users/ryan/src/gadugi2/gadugi")
    if not repo_dir.exists():
        logger.error(f"Repository directory not found: {repo_dir}")
        return 1

    # Define the three tasks to execute in parallel
    tasks = [
        {
            "id": f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}-001",
            "name": "Fix All Pyright Errors",
            "prompt_file": "prompts/fix-all-pyright-errors.md",
            "priority": "high",
            "estimated_duration": 30,
        },
        {
            "id": f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}-002",
            "name": "Complete Team Coach Implementation",
            "prompt_file": "prompts/complete-TeamCoach-implementation.md",
            "priority": "high",
            "estimated_duration": 45,
        },
        {
            "id": f"task-{datetime.now().strftime('%Y%m%d-%H%M%S')}-003",
            "name": "Clean Up All Worktrees",
            "prompt_file": "prompts/cleanup-all-worktrees.md",
            "priority": "medium",
            "estimated_duration": 20,
        },
    ]

    logger.info("=" * 60)
    logger.info("ORCHESTRATOR PARALLEL EXECUTION")
    logger.info("=" * 60)
    logger.info(f"Tasks to execute: {len(tasks)}")
    for task in tasks:
        logger.info(f"  - {task['name']} ({task['prompt_file']})")
    logger.info("=" * 60)

    # Create orchestrator configuration
    config = {
        "tasks": tasks,
        "parallel": True,
        "max_workers": 3,
        "enable_monitoring": True,
        "checkpoint_interval": 60,
        "use_worktrees": True,
        "enforce_workflow_phases": True,
    }

    # Write config to temporary file
    config_file = repo_dir / "orchestrator_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    logger.info(f"Configuration written to: {config_file}")

    # Import and run the orchestrator directly
    sys.path.insert(0, str(repo_dir / ".gadugi" / "orchestrator"))

    try:
        from orchestrator_main import OrchestratorAgent

        # Initialize orchestrator
        orchestrator = OrchestratorAgent(
            orchestration_id=f"orch-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            config_file=str(config_file),
        )

        # Execute tasks in parallel
        logger.info("Starting parallel task execution...")
        results = orchestrator.orchestrate_parallel(tasks)

        # Report results
        logger.info("=" * 60)
        logger.info("EXECUTION RESULTS")
        logger.info("=" * 60)

        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        logger.info(f"✅ Successful: {len(successful)}/{len(tasks)}")
        logger.info(f"❌ Failed: {len(failed)}/{len(tasks)}")

        if successful:
            logger.info("\nSuccessful tasks:")
            for result in successful:
                logger.info(f"  ✅ {result['task_name']}")
                if "pr_number" in result:
                    logger.info(f"     PR: #{result['pr_number']}")

        if failed:
            logger.info("\nFailed tasks:")
            for result in failed:
                logger.info(f"  ❌ {result['task_name']}")
                if "error" in result:
                    logger.info(f"     Error: {result['error']}")

        # Calculate speedup
        if "execution_time" in results[0]:
            total_time = max(r.get("execution_time", 0) for r in results)
            sequential_estimate = sum(t["estimated_duration"] * 60 for t in tasks)
            speedup = sequential_estimate / total_time if total_time > 0 else 1
            logger.info(f"\n⚡ Speedup achieved: {speedup:.1f}x")
            logger.info(f"   Parallel time: {total_time / 60:.1f} minutes")
            logger.info(f"   Sequential estimate: {sequential_estimate / 60:.1f} minutes")

        return 0 if len(failed) == 0 else 1

    except ImportError as e:
        logger.error(f"Could not import orchestrator: {e}")
        logger.info("Falling back to CLI invocation...")

        # Fallback: Create a prompt file for manual orchestrator invocation
        prompt_content = f"""# Orchestrator Agent Invocation

Execute these specific prompts in parallel:
- {tasks[0]["prompt_file"]}
- {tasks[1]["prompt_file"]}
- {tasks[2]["prompt_file"]}

Configuration:
- Enable parallel execution: true
- Use worktrees: true
- Max workers: 3
- Enforce all workflow phases: true
"""

        prompt_file = repo_dir / "orchestrator_invocation.md"
        with open(prompt_file, "w") as f:
            f.write(prompt_content)

        logger.info(f"Created orchestrator prompt at: {prompt_file}")
        logger.info("Please run: claude -p orchestrator_invocation.md")

        return 0

    except Exception as e:
        logger.error(f"Orchestrator execution failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        if config_file.exists():
            config_file.unlink()
            logger.info("Cleaned up configuration file")


if __name__ == "__main__":
    sys.exit(main())
