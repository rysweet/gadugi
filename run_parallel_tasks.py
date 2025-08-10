#!/usr/bin/env python3
"""
Execute the orchestrator to run three tasks in parallel with proper path handling.
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    # Get to the main repository directory
    repo_dir = Path("/Users/ryan/src/gadugi2/gadugi")
    os.chdir(repo_dir)
    
    # Verify the prompt files exist
    prompt_files = [
        "fix-all-pyright-errors.md",
        "complete-team-coach-implementation.md", 
        "cleanup-all-worktrees.md"
    ]
    
    print("=" * 60)
    print("PARALLEL TASK ORCHESTRATION")
    print("=" * 60)
    print("Verifying prompt files...")
    
    all_exist = True
    for prompt_file in prompt_files:
        full_path = repo_dir / "prompts" / prompt_file
        if full_path.exists():
            print(f"  ✅ Found: {prompt_file}")
        else:
            print(f"  ❌ Missing: {prompt_file}")
            all_exist = False
    
    if not all_exist:
        print("ERROR: Not all prompt files found!")
        return 1
    
    print("\nCleaning up any blocking branches...")
    # Clean up branches that might block worktree creation
    branches_to_clean = [
        "feature/parallel-complete-team-coach-agent-implementation-complete-team-coach-implementation",
        "feature/parallel-clean-up-all-worktrees-cleanup-all-worktrees",
        "feature/parallel-fix-all-pyright-errors-in-v0.3-components-fix-all-pyright-errors"
    ]
    
    for branch in branches_to_clean:
        subprocess.run(["git", "branch", "-D", branch], 
                      capture_output=True, text=True)
    
    print("\nExecuting orchestrator with correct paths...")
    print("Tasks to execute in parallel:")
    print("  1. Fix all pyright errors")
    print("  2. Complete team coach implementation")
    print("  3. Clean up all worktrees")
    print("=" * 60)
    
    # Run the orchestrator with the correct command
    cmd = [
        "python3",
        ".claude/orchestrator/orchestrator_main.py",
        "fix-all-pyright-errors.md",
        "complete-team-coach-implementation.md",
        "cleanup-all-worktrees.md",
        "--max-parallel", "3",
        "--timeout", "2",
        "--project-root", str(repo_dir)
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode == 0:
        print("\n✅ Orchestrator execution completed successfully!")
    else:
        print(f"\n❌ Orchestrator execution failed with exit code: {result.returncode}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())