#!/usr/bin/env python3
"""
Simple agent runner for Gadugi v0.3 orchestrator.
Runs agents in subprocess and captures output.
"""

import subprocess
import sys
from pathlib import Path


def run_agent(agent_name: str, task_description: str = "") -> dict:
    """
    Run an agent in subprocess and capture output.
    
    Args:
        agent_name: Name of the agent to run
        task_description: Optional task description to pass to agent
    
    Returns:
        Dict with stdout, stderr, returncode, and success status
    """
    
    # Special case: task-decomposer uses Python implementation for reliability
    if agent_name == "task-decomposer":
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
                "success": True
            }
        except Exception as e:
            return {
                "agent": agent_name,
                "task": task_description,
                "stdout": "",
                "stderr": f"Task decomposer error: {str(e)}",
                "returncode": -1,
                "success": False
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
            "success": False
        }
    
    # Read the agent file content
    try:
        with open(agent_file, 'r') as f:
            agent_content = f.read()
    except Exception as e:
        return {
            "agent": agent_name,
            "task": task_description,
            "stdout": "",
            "stderr": f"Could not read agent file: {e}",
            "returncode": -1,
            "success": False
        }
    
    # For minimal implementation, let's simplify and just use a basic prompt
    # Skip the agent file for now and just simulate the response
    if task_description:
        simple_prompt = f"Act as a {agent_name}. {task_description}. Respond briefly."
    else:
        simple_prompt = f"Act as a {agent_name}. Respond with a simple confirmation."
    
    try:
        # Run claude with a simple non-interactive command
        result = subprocess.run([
            "claude", "-p", simple_prompt
        ], 
        capture_output=True, 
        text=True, 
        timeout=30  # Reduced timeout
        )
        
        return {
            "agent": agent_name,
            "task": task_description,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        return {
            "agent": agent_name,
            "task": task_description,
            "stdout": "",
            "stderr": f"Agent {agent_name} timed out after 60 seconds",
            "returncode": -1,
            "success": False
        }
    
    except FileNotFoundError:
        return {
            "agent": agent_name,
            "task": task_description,
            "stdout": "",
            "stderr": "Claude command not found. Is Claude Code CLI installed?",
            "returncode": -1,
            "success": False
        }
    
    except Exception as e:
        return {
            "agent": agent_name,
            "task": task_description,
            "stdout": "",
            "stderr": f"Error running agent: {str(e)}",
            "returncode": -1,
            "success": False
        }


def main():
    """Command line interface for testing the runner."""
    if len(sys.argv) < 2:
        print("Usage: python run_agent.py <agent_name> [task_description]")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    task_description = sys.argv[2] if len(sys.argv) > 2 else ""
    
    print(f"Running agent: {agent_name}")
    if task_description:
        print(f"Task: {task_description}")
    print("-" * 50)
    
    result = run_agent(agent_name, task_description)
    
    print(f"Success: {result['success']}")
    print(f"Return code: {result['returncode']}")
    
    if result['stdout']:
        print("\n--- STDOUT ---")
        print(result['stdout'])
    
    if result['stderr']:
        print("\n--- STDERR ---")
        print(result['stderr'])


if __name__ == "__main__":
    main()