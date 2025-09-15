#!/usr/bin/env python3
"""Quick script to fix common pyright type errors."""

import subprocess
import sys
from pathlib import Path
from typing import List


def run_pyright(path: str) -> List[str]:
    """Run pyright and return errors.

    Args:
        path: Path to check with pyright

    Returns:
        List of output lines from pyright
    """
    result = subprocess.run(
        ["uv", "run", "pyright", path],
        capture_output=True,
        text=True,
    )
    return result.stdout.split("\n")


def main() -> int:
    """Main function to check pyright errors.

    Returns:
        Exit code: 0 if no errors, 1 if errors found
    """
    paths: List[str] = [
        ".claude/services/event-router/",
        ".claude/services/mcp/",
        ".claude/agents/recipe-implementation/",
    ]

    total_errors: int = 0
    for path in paths:
        if Path(path).exists():
            print(f"\nChecking {path}...")
            errors: List[str] = run_pyright(path)
            error_count: int = sum(1 for line in errors if "error:" in line)
            print(f"  Found {error_count} errors")
            total_errors += error_count

    print(f"\nTotal errors: {total_errors}")

    if total_errors == 0:
        print("✅ All code is pyright clean!")
        return 0
    else:
        print("❌ Fix the remaining type errors")
        return 1


if __name__ == "__main__":
    sys.exit(main())
