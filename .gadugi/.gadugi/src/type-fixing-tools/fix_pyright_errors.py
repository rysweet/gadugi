#!/usr/bin/env python3
"""
Script to automatically fix common pyright errors in the codebase.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Tuple


def get_pyright_errors(directory: str) -> List[Tuple[str, int, str]]:
    """Get all pyright errors for a directory."""
    result = subprocess.run(
        ["uv", "run", "pyright", directory], capture_output=True, text=True
    )

    errors = []
    for line in result.stderr.split("\n") + result.stdout.split("\n"):
        if "error:" in line:
            # Parse error format: /path/file.py:line:col - error: message
            match = re.match(r"(.+):(\d+):\d+ - error: (.+)", line.strip())
            if match:
                filepath, line_num, error_msg = match.groups()
                errors.append((filepath, int(line_num), error_msg))

    return errors


def fix_unused_imports(filepath: str, line_num: int, import_name: str):
    """Remove unused import from file."""
    lines = Path(filepath).read_text().splitlines()

    if line_num <= len(lines):
        line = lines[line_num - 1]

        # Handle different import patterns
        if f"import {import_name}" in line:
            # Check if it's the only import on this line
            if line.strip() == f"import {import_name}":
                # Remove the entire line
                lines.pop(line_num - 1)
            else:
                # It's part of a multi-import, need to handle carefully
                patterns = [
                    (f", {import_name}", ""),  # Middle or end of list
                    (f"{import_name}, ", ""),  # Beginning of list
                    (f"{import_name}", ""),  # Only item
                ]
                for pattern, replacement in patterns:
                    if pattern in line:
                        lines[line_num - 1] = line.replace(pattern, replacement)
                        break

        # Write back
        Path(filepath).write_text("\n".join(lines) + "\n")
        return True
    return False


def fix_possibly_unbound(filepath: str, line_num: int, var_name: str):
    """Initialize possibly unbound variables."""
    lines = Path(filepath).read_text().splitlines()

    if line_num <= len(lines):
        # Find where to initialize the variable
        # Look backwards for the start of the block
        indent_level = len(lines[line_num - 1]) - len(lines[line_num - 1].lstrip())

        # Find a good place to initialize (usually at the start of the function/block)
        for i in range(line_num - 2, -1, -1):
            line = lines[i]
            if line.strip().startswith("def ") or line.strip().startswith("try:"):
                # Found function or try block start
                # Add initialization after this line
                init_line = " " * (indent_level + 4) + f"{var_name} = None"
                lines.insert(i + 1, init_line)
                Path(filepath).write_text("\n".join(lines) + "\n")
                return True
    return False


def main():
    """Main function to fix errors."""
    directories = [
        ".claude/shared/",
        ".claude/agents/",
        ".claude/orchestrator/",
        ".claude/services/",
        ".claude/framework/",
    ]

    total_fixed = 0

    for directory in directories:
        print(f"\nProcessing {directory}...")
        errors = get_pyright_errors(directory)

        for filepath, line_num, error_msg in errors:
            fixed = False

            # Fix unused imports
            match = re.match(r'Import "(.+)" is not accessed', error_msg)
            if match:
                import_name = match.group(1)
                if fix_unused_imports(filepath, line_num, import_name):
                    print(
                        f"  Fixed unused import '{import_name}' in {filepath}:{line_num}"
                    )
                    fixed = True
                    total_fixed += 1

            # Fix possibly unbound variables
            match = re.match(r'"(.+)" is possibly unbound', error_msg)
            if match and not fixed:
                var_name = match.group(1)
                if fix_possibly_unbound(filepath, line_num, var_name):
                    print(
                        f"  Fixed possibly unbound '{var_name}' in {filepath}:{line_num}"
                    )
                    fixed = True
                    total_fixed += 1

    print(f"\n✅ Fixed {total_fixed} errors automatically")

    # Run pyright again to show remaining errors
    print("\n🔍 Running pyright to check remaining errors...")
    subprocess.run(["uv", "run", "pyright", ".claude/"], check=False)


if __name__ == "__main__":
    main()
