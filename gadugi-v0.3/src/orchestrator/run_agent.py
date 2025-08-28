#!/usr/bin/env python3
"""Simple agent runner for Gadugi v0.3 orchestrator.
Runs agents in subprocess and captures output with proper path resolution.
"""

import contextlib
import os
import subprocess
import sys
from pathlib import Path


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
    # This file is at gadugi-v0.3/src/orchestrator/run_agent.py
    # So we go up 3 levels to get to gadugi-v0.3
    current_file = Path(__file__).resolve()
    base_dir = current_file.parent.parent.parent

    # Verify we found the right directory by checking for expected subdirs
    if (base_dir / "agents").exists() and (base_dir / "src").exists():
        return base_dir

    # Strategy 3: Look for gadugi-v0.3 in parent directories
    current = current_file.parent
    while current != current.parent:
        if current.name == "gadugi-v0.3" and (current / "agents").exists():
            return current
        current = current.parent

    msg = (
        "Cannot determine Gadugi base directory. "
        "Please set GADUGI_HOME environment variable or run from within gadugi-v0.3 directory."
    )
    raise RuntimeError(
        msg,
    )


# Initialize base directory and paths
GADUGI_BASE = get_gadugi_base_dir()
AGENTS_DIR = GADUGI_BASE / "agents"
SERVICES_DIR = GADUGI_BASE / "services"
SRC_DIR = GADUGI_BASE / "src"

# Add src directory to Python path for imports
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SRC_DIR / "orchestrator") not in sys.path:
    sys.path.insert(0, str(SRC_DIR / "orchestrator"))

# Import version after path setup
with contextlib.suppress(ImportError):
    from version import get_version_string


def run_agent(agent_name: str, task_description: str = "") -> dict:
    """Run an agent in subprocess and capture output.

    Args:
        agent_name: Name of the agent to run
        task_description: Optional task description to pass to agent

    Returns:
        Dict with stdout, stderr, returncode, and success status

    """
    # Special cases: agents with Python implementations for reliability
    if agent_name == "TaskDecomposer":
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
                "agent": agent_name,
                "task": task_description,
                "stdout": json.dumps(result, indent=2),
                "stderr": "",
                "returncode": 0,
                "success": True,
            }
        except Exception as e:
            return {
                "agent": agent_name,
                "task": task_description,
                "stdout": "",
                "stderr": f"Task decomposer error: {e!s}",
                "returncode": -1,
                "success": False,
            }

    # Special case: prompt-writer uses Python implementation
    if agent_name == "PromptWriter":
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
                "agent": agent_name,
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
                "agent": agent_name,
                "task": task_description,
                "stdout": "",
                "stderr": f"Prompt writer error: {e!s}",
                "returncode": -1,
                "success": False,
            }

    # Special case: code-writer uses Python implementation
    if agent_name == "CodeWriter":
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
                output = f"Code generation failed: {result.get('error', 'Unknown error')}"

            return {
                "agent": agent_name,
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
                "agent": agent_name,
                "task": task_description,
                "stdout": "",
                "stderr": f"Code writer error: {e!s}",
                "returncode": -1,
                "success": False,
            }

    # Find the agent file
    # Look relative to this script's directory
    script_dir = Path(__file__).parent
    agent_file = script_dir / ".." / ".." / "agents" / agent_name / "agent.md"

    if not agent_file.exists():
        return {
            "agent": agent_name,
            "task": task_description,
            "stdout": "",
            "stderr": f"Agent file not found: {agent_file}",
            "returncode": -1,
            "success": False,
        }

    # Read the agent file content
    try:
        with open(agent_file) as f:
            f.read()
    except Exception as e:
        return {
            "agent": agent_name,
            "task": task_description,
            "stdout": "",
            "stderr": f"Could not read agent file: {e}",
            "returncode": -1,
            "success": False,
        }

    # For minimal implementation, let's simplify and just use a basic prompt
    # Skip the agent file for now and just simulate the response
    if task_description:
        simple_prompt = f"Act as a {agent_name}. {task_description}. Respond briefly."
    else:
        simple_prompt = f"Act as a {agent_name}. Respond with a simple confirmation."

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
            "agent": agent_name,
            "task": task_description,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }

    except subprocess.TimeoutExpired:
        return {
            "agent": agent_name,
            "task": task_description,
            "stdout": "",
            "stderr": f"Agent {agent_name} timed out after 60 seconds",
            "returncode": -1,
            "success": False,
        }

    except FileNotFoundError:
        return {
            "agent": agent_name,
            "task": task_description,
            "stdout": "",
            "stderr": "Claude command not found. Is Claude Code CLI installed?",
            "returncode": -1,
            "success": False,
        }

    except Exception as e:
        return {
            "agent": agent_name,
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
    else:
        if result["stdout"]:
            pass
        if result["stderr"]:
            pass

    return result.get("returncode", 0)


if __name__ == "__main__":
    sys.exit(main())
