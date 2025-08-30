#!/usr/bin/env python3
"""Simple agent runner for Gadugi v0.3 orchestrator.
Runs agents in subprocess and captures output with proper path resolution.
"""

import os
import subprocess
import sys
from pathlib import Path
import re


def camel_to_kebab(name: str) -> str:
    """Convert CamelCase to kebab-case.

    Args:
        name: CamelCase string like "CodeReviewer"

    Returns:
        kebab-case string like "code-reviewer"
    """
    # Insert hyphens before uppercase letters that follow lowercase letters
    s1 = re.sub("([a-z0-9])([A-Z])", r"\1-\2", name)
    return s1.lower()


def kebab_to_camel(name: str) -> str:
    """Convert kebab-case to CamelCase.

    Args:
        name: kebab-case string like "code-reviewer"

    Returns:
        CamelCase string like "CodeReviewer"
    """
    components = name.split("-")
    return "".join(word.capitalize() for word in components)


# Agent name mapping - kebab-case to CamelCase
AGENT_NAME_MAPPING = {
    # Explicitly map known agents for backward compatibility
    "agent-updater": "AgentUpdater",
    "claude-settings-update": "ClaudeSettingsUpdate",
    "code-executor": "CodeExecutor",
    "code-review-response": "CodeReviewResponse",
    "code-reviewer": "CodeReviewer",
    "event-router-manager": "EventRouterManager",
    "event-router-service-manager": "EventRouterServiceManager",
    "execution-monitor": "ExecutionMonitor",
    "gadugi-coordinator": "GadugiCoordinator",
    "github-executor": "GitHubExecutor",
    "llm-proxy-agent": "LlmProxyAgent",
    "memory-manager": "MemoryManager",
    "memory-service-manager": "MemoryServiceManager",
    "neo4j-service-manager": "Neo4jServiceManager",
    "orchestrator-agent": "OrchestratorAgent",
    "pr-backlog-manager": "PrBacklogManager",
    "program-manager": "ProgramManager",
    "prompt-writer": "PromptWriter",
    "readme-agent": "ReadmeAgent",
    "recipe-executor": "RecipeExecutor",
    "system-design-reviewer": "SystemDesignReviewer",
    "task-analyzer": "TaskAnalyzer",
    "task-bounds-eval": "TaskBoundsEval",
    "task-decomposer": "TaskDecomposer",
    "task-research-agent": "TaskResearchAgent",
    "team-coach": "TeamCoach",
    "teamcoach-agent": "TeamcoachAgent",
    "test-executor": "TestExecutor",
    "test-solver": "TestSolver",
    "test-writer": "TestWriter",
    "type-fix-agent": "TypeFixAgent",
    "workflow-manager": "WorkflowManager",
    "workflow-manager-phase9-enforcement": "WorkflowManagerPhase9Enforcement",
    "workflow-manager-simplified": "WorkflowManagerSimplified",
    "workflow-phase-reflection": "WorkflowPhaseReflection",
    "worktree-executor": "WorktreeExecutor",
    "worktree-manager": "WorktreeManager",
    "xpia-defense-agent": "XpiaDefenseAgent",
}

# Reverse mapping - CamelCase to kebab-case
CAMEL_TO_KEBAB_MAPPING = {v: k for k, v in AGENT_NAME_MAPPING.items()}


def normalize_agent_name(agent_name: str) -> str:
    """Normalize agent name to CamelCase format.

    Args:
        agent_name: Agent name in any format

    Returns:
        CamelCase agent name
    """
    # If already in mapping, use it
    if agent_name in AGENT_NAME_MAPPING:
        return AGENT_NAME_MAPPING[agent_name]

    # If already CamelCase and exists, use as-is
    if agent_name[0].isupper() and "-" not in agent_name:
        return agent_name

    # Convert kebab-case to CamelCase
    if "-" in agent_name:
        return kebab_to_camel(agent_name)

    # Default: assume it's already correct
    return agent_name


def get_gadugi_base_dir() -> Path:
    """Get the Gadugi base directory using multiple strategies.

    Returns:
        Path to the Gadugi v0.3 base directory

    Raises:
        RuntimeError: If base directory cannot be determined
    """
    # Strategy 1: Use GADUGI_HOME environment variable if set
    if "GADUGI_HOME" in os.environ:
        base_dir = Path(os.environ["GADUGI_HOME"])
        if base_dir.exists():
            return base_dir

    # Strategy 2: Auto-detect from this file's location
    # This file is at gadugi/.claude/engines/run_agent.py
    # So we go up 2 levels to get to gadugi root
    current_file = Path(__file__).resolve()
    base_dir = current_file.parent.parent.parent

    # Verify we found the right directory by checking for expected subdirs
    if (base_dir / ".claude" / "agents").exists():
        return base_dir

    # Strategy 3: Look for gadugi-v0.3 in parent directories
    current = current_file.parent
    while current != current.parent:
        if current.name == "gadugi-v0.3" and (current / "agents").exists():
            return current
        current = current.parent

    raise RuntimeError(
        "Cannot determine Gadugi base directory. "
        "Please set GADUGI_HOME environment variable or run from within gadugi-v0.3 directory."
    )


# Initialize base directory and paths
GADUGI_BASE = get_gadugi_base_dir()
AGENTS_DIR = GADUGI_BASE / ".claude" / "agents"
SERVICES_DIR = GADUGI_BASE / ".claude" / "services"
SRC_DIR = GADUGI_BASE

# Add src directory to Python path for imports
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SRC_DIR / "orchestrator") not in sys.path:
    sys.path.insert(0, str(SRC_DIR / "orchestrator"))

# Import version after path setup
try:
    from version import get_version_string  # type: ignore[import]

    print(
        f"{get_version_string()} initialized with base: {GADUGI_BASE}", file=sys.stderr
    )
except ImportError:
    print(f"Gadugi v0.3 initialized with base: {GADUGI_BASE}", file=sys.stderr)


def run_agent(agent_name: str, task_description: str = "") -> dict:
    """Run an agent in subprocess and capture output.

    Args:
        agent_name: Name of the agent to run (supports both CamelCase and kebab-case)
        task_description: Optional task description to pass to agent

    Returns:
        Dict with stdout, stderr, returncode, and success status

    """
    # Normalize agent name to CamelCase for consistency
    normalized_name = normalize_agent_name(agent_name)
    original_name = agent_name  # Keep original for error messages
    # Special cases: agents with Python implementations for reliability
    if normalized_name == "TaskDecomposer":
        try:
            import json
            import sys

            # Add current directory to path for import
            script_dir = Path(__file__).parent
            if str(script_dir) not in sys.path:
                sys.path.insert(0, str(script_dir))

            from simple_decomposer import decompose_task

            result = decompose_task(task_description or "Generic task")
            return {
                "agent": normalized_name,
                "task": task_description,
                "stdout": json.dumps(result, indent=2),
                "stderr": "",
                "returncode": 0,
                "success": True,
            }
        except Exception as e:
            return {
                "agent": normalized_name,
                "task": task_description,
                "stdout": "",
                "stderr": f"Task decomposer error: {e!s}",
                "returncode": -1,
                "success": False,
            }

    # Special case: PromptWriter uses Python implementation
    if normalized_name == "PromptWriter":
        try:
            import json
            import sys

            # Add current directory to path for import
            script_dir = Path(__file__).parent
            if str(script_dir) not in sys.path:
                sys.path.insert(0, str(script_dir))

            from prompt_writer_engine import generate_prompt_for_task

            result = generate_prompt_for_task(
                task_description or "Generic development task",
            )
            return {
                "agent": normalized_name,
                "task": task_description,
                "stdout": result["markdown"],
                "stderr": "",
                "returncode": 0,
                "success": True,
                "metadata": {
                    "suggested_filename": result["suggested_filename"],
                    "prompt_data": result["prompt_data"],
                },
            }
        except Exception as e:
            return {
                "agent": normalized_name,
                "task": task_description,
                "stdout": "",
                "stderr": f"Prompt writer error: {e!s}",
                "returncode": -1,
                "success": False,
            }

    # Special case: code-writer uses Python implementation
    if normalized_name == "CodeWriter":
        try:
            import json
            import sys

            # Add current directory to path for import
            script_dir = Path(__file__).parent
            if str(script_dir) not in sys.path:
                sys.path.insert(0, str(script_dir))

            from code_writer_engine import generate_code_for_task

            result = generate_code_for_task(
                task_description or "Generic code generation task",
            )

            # Format output for orchestrator consumption
            if result["success"]:
                # Create a summary of generated files
                files_summary = []
                for file_info in result["files"]:
                    files_summary.append(
                        f"📁 {file_info['filename']}: {file_info['description']}",
                    )

                output = "Code Generation Results:\n"
                output += f"Task: {result['task']}\n"
                output += f"Language: {result['metadata']['language']}\n"
                output += "Files Generated:\n" + "\n".join(files_summary)

                if result["dependencies"]:
                    output += f"\nDependencies: {', '.join(result['dependencies'])}"

                if result["integration_notes"]:
                    output += f"\nIntegration: {result['integration_notes']}"
            else:
                output = (
                    f"Code generation failed: {result.get('error', 'Unknown error')}"
                )

            return {
                "agent": normalized_name,
                "task": task_description,
                "stdout": output,
                "stderr": "" if result["success"] else result.get("error", ""),
                "returncode": 0 if result["success"] else -1,
                "success": result["success"],
                "metadata": {
                    "code_result": result,
                    "language": result.get("metadata", {}).get("language", "unknown"),
                    "code_type": result.get("metadata", {}).get("code_type", "unknown"),
                },
            }
        except Exception as e:
            return {
                "agent": normalized_name,
                "task": task_description,
                "stdout": "",
                "stderr": f"Code writer error: {e!s}",
                "returncode": -1,
                "success": False,
            }

    # Find the agent file - try multiple resolution strategies
    agents_base_dir = AGENTS_DIR

    # Strategy 1: Try CamelCase .md file directly
    agent_file = agents_base_dir / f"{normalized_name}.md"

    if not agent_file.exists():
        # Strategy 2: Try kebab-case directory structure
        kebab_name = camel_to_kebab(normalized_name)
        agent_file = agents_base_dir / kebab_name / "agent.md"

        if not agent_file.exists():
            # Strategy 3: Try original name as directory
            agent_file = agents_base_dir / original_name / "agent.md"

            if not agent_file.exists():
                # Strategy 4: Try normalized name as directory
                agent_file = agents_base_dir / normalized_name / "agent.md"

                if not agent_file.exists():
                    return {
                        "agent": normalized_name,
                        "task": task_description,
                        "stdout": "",
                        "stderr": f"Agent file not found. Tried: {normalized_name}.md, {kebab_name}/agent.md, {original_name}/agent.md, {normalized_name}/agent.md",
                        "returncode": -1,
                        "success": False,
                    }

    # Read the agent file content
    try:
        with open(agent_file) as f:
            f.read()
    except Exception as e:
        return {
            "agent": normalized_name,
            "task": task_description,
            "stdout": "",
            "stderr": f"Could not read agent file: {e}",
            "returncode": -1,
            "success": False,
        }

    # For minimal implementation, let's simplify and just use a basic prompt
    # Skip the agent file for now and just simulate the response
    if task_description:
        simple_prompt = (
            f"Act as a {normalized_name}. {task_description}. Respond briefly."
        )
    else:
        simple_prompt = (
            f"Act as a {normalized_name}. Respond with a simple confirmation."
        )

    try:
        # Run claude with a simple non-interactive command
        result = subprocess.run(
            ["claude", "-p", simple_prompt],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,  # Reduced timeout
        )

        return {
            "agent": normalized_name,
            "task": task_description,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }

    except subprocess.TimeoutExpired:
        return {
            "agent": normalized_name,
            "task": task_description,
            "stdout": "",
            "stderr": f"Agent {normalized_name} timed out after 30 seconds",
            "returncode": -1,
            "success": False,
        }

    except FileNotFoundError:
        return {
            "agent": normalized_name,
            "task": task_description,
            "stdout": "",
            "stderr": "Claude command not found. Is Claude Code CLI installed?",
            "returncode": -1,
            "success": False,
        }

    except Exception as e:
        return {
            "agent": normalized_name,
            "task": task_description,
            "stdout": "",
            "stderr": f"Error running agent: {e!s}",
            "returncode": -1,
            "success": False,
        }


def main():
    """Command line interface for testing the runner."""
    import argparse

    # Get available agents
    available_agents = []
    if AGENTS_DIR.exists():
        available_agents = sorted([d.name for d in AGENTS_DIR.iterdir() if d.is_dir()])

    parser = argparse.ArgumentParser(
        description="Run a Gadugi v0.3 agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Environment:
  GADUGI_HOME={GADUGI_BASE}

Available agents:
  {', '.join(available_agents) if available_agents else 'No agents found'}

Examples:
  gadugi-orchestrator orchestrator --task "Build an API"
  gadugi-orchestrator TaskDecomposer --task "Create authentication"
  export GADUGI_HOME=/path/to/gadugi-v0.3 && gadugi-orchestrator TestAgent
        """,
    )

    parser.add_argument("agent", help="Name of the agent to run")
    parser.add_argument("--task", help="Task description", default="")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = run_agent(args.agent, args.task)

    if args.json:
        import json

        print(json.dumps(result, indent=2))
    else:
        if result["stdout"]:
            print(result["stdout"])
        if result["stderr"]:
            print(result["stderr"], file=sys.stderr)

    return result.get("returncode", 0)


if __name__ == "__main__":
    sys.exit(main())
