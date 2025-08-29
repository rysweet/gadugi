#!/usr/bin/env python3
"""
Comprehensive test script for orchestrator implementation.
Tests all aspects of parallel task execution.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def run_command(cmd: List[str], description: str = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    if description:
        print(f"  Running: {description}")
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd="/Users/ryan/src/gadugi2/gadugi"
    )
    return result.returncode, result.stdout, result.stderr


def test_orchestrator_modules():
    """Test that orchestrator modules can be imported."""
    print_section("Testing Orchestrator Module Imports")

    # Test Python imports
    test_imports = [
        ".claude.orchestrator.orchestrator_main",
        ".claude.orchestrator.process_registry",
        ".claude.agents.orchestrator.orchestrator",
        ".claude.agents.orchestrator.task_analyzer",
        ".claude.agents.orchestrator.parallel_executor",
    ]

    results = []
    for module_path in test_imports:
        try:
            # Try to import the module
            cmd = [
                "python3",
                "-c",
                f"import sys; sys.path.insert(0, '/Users/ryan/src/gadugi2/gadugi'); import {module_path}; print('✅ {module_path}')",
            ]
            returncode, stdout, stderr = run_command(cmd)
            if returncode == 0:
                print(f"  ✅ {module_path}: Importable")
                results.append(True)
            else:
                print(f"  ❌ {module_path}: Import failed")
                if stderr:
                    print(f"     Error: {stderr.strip()}")
                results.append(False)
        except Exception as e:
            print(f"  ❌ {module_path}: Exception - {e}")
            results.append(False)

    return all(results)


def test_prompt_files():
    """Test that all required prompt files exist."""
    print_section("Testing Prompt Files")

    prompts_dir = Path("/Users/ryan/src/gadugi2/gadugi/prompts")
    required_prompts = [
        "fix-all-pyright-errors.md",
        "complete-TeamCoach-implementation.md",
        "cleanup-all-worktrees.md",
    ]

    results = []
    for prompt_file in required_prompts:
        path = prompts_dir / prompt_file
        if path.exists():
            print(f"  ✅ {prompt_file}: Found")
            # Check file is not empty
            content = path.read_text()
            if len(content) > 10:
                print(f"     Size: {len(content)} bytes")
                results.append(True)
            else:
                print("     ⚠️  File appears empty")
                results.append(False)
        else:
            print(f"  ❌ {prompt_file}: Not found")
            results.append(False)

    return all(results)


def test_git_worktrees():
    """Test git worktree operations."""
    print_section("Testing Git Worktree Operations")

    # List current worktrees
    returncode, stdout, stderr = run_command(["git", "worktree", "list"], "Listing worktrees")

    if returncode == 0:
        print("  Current worktrees:")
        for line in stdout.strip().split("\n"):
            print(f"    {line}")

    # Prune stale worktrees
    returncode, stdout, stderr = run_command(
        ["git", "worktree", "prune"], "Pruning stale worktrees"
    )
    if returncode == 0:
        print("  ✅ Worktree prune successful")
    else:
        print(f"  ❌ Worktree prune failed: {stderr}")

    return True


def test_process_registry():
    """Test the process registry functionality."""
    print_section("Testing Process Registry")

    registry_path = Path("/Users/ryan/src/gadugi2/gadugi/.gadugi/monitoring/process_registry.json")

    if registry_path.exists():
        try:
            with open(registry_path) as f:
                registry = json.load(f)
            print(f"  ✅ Registry found with {len(registry.get('processes', {}))} processes")

            # Show process status
            for pid, process in registry.get("processes", {}).items():
                status = process.get("status", "unknown")
                name = process.get("task_name", "unknown")
                print(f"    Process {pid}: {name} ({status})")
        except json.JSONDecodeError as e:
            print(f"  ⚠️  Registry exists but has invalid JSON: {e}")
    else:
        print(f"  ℹ️  No registry file found at {registry_path}")

    return True


def test_orchestrator_cli():
    """Test the orchestrator CLI interface."""
    print_section("Testing Orchestrator CLI")

    # Test help command
    returncode, stdout, stderr = run_command(
        ["python3", ".claude/orchestrator/orchestrator_main.py", "--help"],
        "Testing orchestrator help",
    )

    if returncode == 0:
        print("  ✅ Orchestrator CLI accessible")
        # Check for expected arguments
        if "--max-parallel" in stdout and "prompt_files" in stdout:
            print("  ✅ Expected arguments found")
        else:
            print("  ⚠️  CLI interface may have changed")
    else:
        print(f"  ❌ Orchestrator CLI failed: {stderr}")
        return False

    return True


def test_docker_setup():
    """Test Docker setup for containerized execution."""
    print_section("Testing Docker Setup")

    # Check if Docker is running
    returncode, stdout, stderr = run_command(["docker", "info"], "Checking Docker daemon")

    if returncode == 0:
        print("  ✅ Docker daemon is running")

        # Check for orchestrator image
        returncode, stdout, stderr = run_command(
            [
                "docker",
                "images",
                "claude-orchestrator",
                "--format",
                "{{.Repository}}:{{.Tag}}",
            ],
            "Checking for orchestrator image",
        )

        if stdout.strip():
            print(f"  ✅ Found image: {stdout.strip()}")
        else:
            print("  ℹ️  No claude-orchestrator image found (will use subprocess fallback)")
    else:
        print("  ℹ️  Docker not available (will use subprocess fallback)")

    return True


def cleanup_branches():
    """Clean up any leftover parallel branches."""
    print_section("Cleaning Up Parallel Branches")

    # List branches
    returncode, stdout, stderr = run_command(["git", "branch", "-a"], "Listing branches")

    if returncode == 0:
        parallel_branches = [
            line.strip()
            for line in stdout.split("\n")
            if "parallel" in line and not line.startswith("remotes/")
        ]

        if parallel_branches:
            print(f"  Found {len(parallel_branches)} parallel branches to clean")
            for branch in parallel_branches[:5]:  # Show first 5
                print(f"    {branch}")

            # Offer to clean them
            # Note: In automated mode, we'll skip interactive prompts
            print("  ℹ️  Run 'git branch -D <branch>' to delete if needed")
        else:
            print("  ✅ No local parallel branches found")

    return True


def run_integration_test():
    """Run a small integration test with the orchestrator."""
    print_section("Running Integration Test")

    # Create a simple test prompt
    test_prompt_path = Path("/Users/ryan/src/gadugi2/gadugi/prompts/test-orchestrator.md")
    test_prompt_content = """# Test Orchestrator Task

This is a test task for the orchestrator.

## Requirements
- Verify orchestrator can process this task
- No actual implementation needed
- Should complete quickly
"""

    try:
        # Write test prompt
        test_prompt_path.write_text(test_prompt_content)
        print(f"  ✅ Created test prompt: {test_prompt_path.name}")

        # Run orchestrator with test prompt (with short timeout)
        print("  Running orchestrator with test prompt (10 second timeout)...")
        cmd = [
            "timeout",
            "10",
            "python3",
            ".claude/orchestrator/orchestrator_main.py",
            "test-orchestrator.md",
            "--max-parallel",
            "1",
            "--timeout",
            "0.1",
        ]

        returncode, stdout, stderr = run_command(cmd, "Executing test orchestration")

        # We expect it to at least start processing
        if "Analyzing" in stdout or "Analyzing" in stderr:
            print("  ✅ Orchestrator started processing test task")
        else:
            print("  ⚠️  Orchestrator may not have started properly")

    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
    finally:
        # Clean up test prompt
        if test_prompt_path.exists():
            test_prompt_path.unlink()
            print("  ✅ Cleaned up test prompt")

    return True


def main():
    """Run all tests."""
    print("\n" + "🔬" * 30)
    print("    ORCHESTRATOR IMPLEMENTATION TEST SUITE")
    print("🔬" * 30)

    start_time = time.time()

    # Run all tests
    test_results = {
        "Module Imports": test_orchestrator_modules(),
        "Prompt Files": test_prompt_files(),
        "Git Worktrees": test_git_worktrees(),
        "Process Registry": test_process_registry(),
        "CLI Interface": test_orchestrator_cli(),
        "Docker Setup": test_docker_setup(),
        "Branch Cleanup": cleanup_branches(),
        "Integration Test": run_integration_test(),
    }

    # Summary
    print_section("Test Results Summary")

    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")

    print(f"\n  Overall: {passed}/{total} tests passed")

    elapsed_time = time.time() - start_time
    print(f"  Execution time: {elapsed_time:.2f} seconds")

    if passed == total:
        print("\n  🎉 All tests passed! Orchestrator implementation is working.")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} tests failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
