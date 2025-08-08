#!/usr/bin/env python3
"""Debug the orchestrator execution"""

import sys
import subprocess
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / ".claude/orchestrator"))

from components.prompt_generator import PromptGenerator, PromptContext

# Create a test task executor
worktree_path = Path(".worktrees/test-debug")
worktree_path.mkdir(parents=True, exist_ok=True)

prompt_gen = PromptGenerator()
context = PromptContext(
    task_id="test-debug",
    task_name="Test Debug Task",
    original_prompt="prompts/fix-test-workflow-manager-errors.md",
)

# Generate the workflow prompt
workflow_prompt = prompt_gen.generate_workflow_prompt(context, worktree_path)
print(f"Generated prompt: {workflow_prompt}")

# Build the claude command
claude_cmd = [
    "claude",
    "-p",
    workflow_prompt,
    "--dangerously-skip-permissions",
    "--verbose",
    "--max-turns=5",
    "--output-format=json",
]

print(f"\nCommand to run: {' '.join(claude_cmd)}")

# Try running it directly
print("\nTesting direct execution...")
try:
    result = subprocess.run(
        claude_cmd, cwd=worktree_path, capture_output=True, text=True, timeout=10
    )
    print(f"Exit code: {result.returncode}")
    print(f"Stdout length: {len(result.stdout)}")
    print(f"Stderr: {result.stderr[:500] if result.stderr else 'None'}")
    if result.stdout:
        print(f"First 500 chars of output: {result.stdout[:500]}")
except subprocess.TimeoutExpired:
    print("Command timed out after 10 seconds")
except Exception as e:
    print(f"Error: {e}")
