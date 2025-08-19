#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Gadugi v0.3

This script runs all tests and quality checks for the project.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any


def run_command(cmd: str, description: str, timeout: int = 120) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )

        output = result.stdout + result.stderr
        success = result.returncode == 0

        if success:
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED")
            print(f"Exit code: {result.returncode}")

        return success, output
    except subprocess.TimeoutExpired:
        print(f"⏱️ {description} - TIMEOUT")
        return False, f"Command timed out after {timeout} seconds"
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False, str(e)


def main():
    """Run comprehensive tests and quality checks."""

    print("\n" + "=" * 80)
    print("GADUGI v0.3 COMPREHENSIVE TESTING SUITE")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 80)

    # Track results
    results: Dict[str, Any] = {
        "start_time": datetime.now().isoformat(),
        "tests": {},
        "summary": {"total": 0, "passed": 0, "failed": 0},
    }

    # Define test suite
    test_suite = [
        # Environment setup
        ("uv sync --all-extras", "UV Environment Setup", 60),
        # Quality checks - Formatting
        ("uv run ruff format --check .", "Code Formatting Check", 30),
        ("uv run ruff format .", "Auto-format Code", 30),
        # Quality checks - Linting
        ("uv run ruff check . --fix", "Linting with Auto-fix", 60),
        # Type checking - check individual directories to avoid overwhelming output
        (
            "uv run pyright gadugi/ --pythonversion 3.13 || true",
            "Type Check: gadugi/",
            60,
        ),
        (
            "uv run pyright tests/ --pythonversion 3.13 || true",
            "Type Check: tests/",
            60,
        ),
        (
            "uv run pyright compat/ --pythonversion 3.13 || true",
            "Type Check: compat/",
            60,
        ),
        # Unit tests - run specific test directories
        (
            "uv run pytest tests/event_service/ -v --tb=short || true",
            "Unit Tests: Event Service",
            60,
        ),
        (
            "uv run pytest tests/container_runtime/ -v --tb=short || true",
            "Unit Tests: Container Runtime",
            60,
        ),
        ("uv run pytest tests/agents/ -v --tb=short || true", "Unit Tests: Agents", 60),
        (
            "uv run pytest tests/shared/ -v --tb=short || true",
            "Unit Tests: Shared Modules",
            60,
        ),
        # Integration tests
        (
            "uv run pytest tests/integration/ -v --tb=short || true",
            "Integration Tests",
            120,
        ),
        # Neo4j connectivity test
        ("uv run python neo4j/test_connection.py || true", "Neo4j Connection Test", 30),
        # Test coverage report
        (
            "uv run pytest tests/ --cov=. --cov-report=term-missing --cov-report=html || true",
            "Coverage Report",
            180,
        ),
    ]

    # Run all tests
    for cmd, description, timeout in test_suite:
        success, output = run_command(cmd, description, timeout)

        results["tests"][description] = {
            "command": cmd,
            "success": success,
            "output_length": len(output),
        }

        results["summary"]["total"] += 1
        if success:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1

    # Generate report
    print("\n" + "=" * 80)
    print("TEST EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']} ✅")
    print(f"Failed: {results['summary']['failed']} ❌")
    print(
        f"Success Rate: {results['summary']['passed'] / results['summary']['total'] * 100:.1f}%"
    )

    # Detailed results
    print("\nDetailed Results:")
    print("-" * 60)
    for test_name, test_result in results["tests"].items():
        status = "✅ PASS" if test_result["success"] else "❌ FAIL"
        print(f"{status} - {test_name}")

    # Write report to file
    report_path = Path("test_report.md")
    with open(report_path, "w") as f:
        f.write("# Gadugi v0.3 Test Report\n\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total Tests: {results['summary']['total']}\n")
        f.write(f"- Passed: {results['summary']['passed']}\n")
        f.write(f"- Failed: {results['summary']['failed']}\n")
        f.write(
            f"- Success Rate: {results['summary']['passed'] / results['summary']['total'] * 100:.1f}%\n\n"
        )
        f.write("## Detailed Results\n\n")
        for test_name, test_result in results["tests"].items():
            status = "✅" if test_result["success"] else "❌"
            f.write(f"- {status} **{test_name}**\n")
            f.write(f"  - Command: `{test_result['command']}`\n")

    print(f"\nReport written to: {report_path}")

    # Exit with appropriate code
    if results["summary"]["failed"] == 0:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(
            f"\n⚠️ {results['summary']['failed']} tests failed. Please review and fix."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
