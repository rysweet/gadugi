#!/usr/bin/env python3
"""
Systematically fix all pyright errors in the .claude directory.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any


def run_pyright(path: str) -> List[str]:
    """Run pyright and return list of errors."""
    result = subprocess.run(
        ["uv", "run", "pyright", path], capture_output=True, text=True
    )
    errors = []
    for line in result.stdout.split("\n"):
        if "error:" in line:
            errors.append(line)
    return errors


def fix_unused_imports(file_path: Path) -> bool:
    """Remove unused imports from a file."""
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Common unused imports to remove
    patterns = [
        r"^from typing import .*\bSet\b.*$",  # Unused Set import
        r"^import Set\s*$",
    ]

    for pattern in patterns:
        # Check if this is truly unused (not referenced in the file)
        if re.search(pattern, content, re.MULTILINE):
            # Extract the import
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                import_line = match.group(0)
                # Check if Set is used in the file (excluding the import line itself)
                temp_content = content.replace(import_line, "")
                if "Set[" not in temp_content and "Set(" not in temp_content:
                    # Remove just 'Set' from the import
                    if "from typing import" in import_line:
                        # Parse the imports
                        imports = re.search(r"from typing import (.+)", import_line)
                        if imports:
                            import_list = [
                                i.strip() for i in imports.group(1).split(",")
                            ]
                            if "Set" in import_list:
                                import_list.remove("Set")
                                if import_list:
                                    new_import = (
                                        f"from typing import {', '.join(import_list)}"
                                    )
                                    content = content.replace(import_line, new_import)
                                else:
                                    # Remove the entire line if Set was the only import
                                    content = content.replace(import_line + "\n", "")

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_undefined_variables(file_path: Path) -> bool:
    """Fix undefined variable errors."""
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Fix common undefined variables
    fixes = {
        "tempfile": "import tempfile",
        "AgentConfig": "from ..shared.types import AgentConfig",
        "ErrorHandler": "from ..shared.error_handling import ErrorHandler",
    }

    for var, import_stmt in fixes.items():
        if f'"{var}" is not defined' in content or f"'{var}' is not defined" in content:
            # Add the import if not already present
            if import_stmt not in content:
                # Add after other imports
                lines = content.split("\n")
                import_index = 0
                for i, line in enumerate(lines):
                    if line.startswith("import ") or line.startswith("from "):
                        import_index = i + 1
                lines.insert(import_index, import_stmt)
                content = "\n".join(lines)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_syntax_errors(file_path: Path) -> bool:
    """Fix syntax errors in files."""
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Fix unclosed parentheses
    lines = content.split("\n")
    fixed_lines = []
    open_parens = 0

    for i, line in enumerate(lines):
        # Count parentheses
        open_parens += line.count("(") - line.count(")")

        # If we have unclosed parens and the next line starts with 'from' or 'import'
        if open_parens > 0 and i + 1 < len(lines):
            next_line = lines[i + 1]
            if next_line.strip().startswith(("from ", "import ")):
                # Close the parentheses
                line = line.rstrip() + ")" * open_parens
                open_parens = 0

        fixed_lines.append(line)

    content = "\n".join(fixed_lines)

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_parameter_mismatches(file_path: Path) -> bool:
    """Fix parameter mismatch errors in test files."""
    if not file_path.exists():
        return False

    content = file_path.read_text()
    original = content

    # Fix AgentPerformance parameter issues
    if "AgentPerformance" in content:
        # Replace named parameters with positional or fix the class definition
        content = re.sub(
            r"AgentPerformance\(\s*agent_id=([^,]+),\s*success_rate=([^,]+),\s*average_execution_time=([^,]+),\s*total_tasks=([^,]+),\s*successful_tasks=([^,]+),\s*failed_tasks=([^,]+),\s*error_count=([^,]+),\s*error_types=([^)]+)\)",
            r"AgentPerformance(\1, \2, \3, \4, \5, \6, \7, \8)",
            content,
        )

    if content != original:
        file_path.write_text(content)
        return True
    return False


def fix_file(file_path: Path) -> int:
    """Fix all issues in a single file. Returns number of fixes applied."""
    fixes_applied = 0

    if fix_unused_imports(file_path):
        fixes_applied += 1
        print(f"  Fixed unused imports in {file_path.name}")

    if fix_undefined_variables(file_path):
        fixes_applied += 1
        print(f"  Fixed undefined variables in {file_path.name}")

    if fix_syntax_errors(file_path):
        fixes_applied += 1
        print(f"  Fixed syntax errors in {file_path.name}")

    if fix_parameter_mismatches(file_path):
        fixes_applied += 1
        print(f"  Fixed parameter mismatches in {file_path.name}")

    return fixes_applied


def main():
    """Main execution function."""
    claude_dir = Path(".claude")

    print("Starting systematic pyright error fixes...")

    # Get initial error count
    initial_errors = run_pyright(".claude")
    initial_count = len(initial_errors)
    print(f"Initial error count: {initial_count}")

    # Process all Python files
    total_fixes = 0
    for py_file in claude_dir.rglob("*.py"):
        fixes = fix_file(py_file)
        if fixes > 0:
            total_fixes += fixes
            print(f"Fixed {fixes} issues in {py_file.relative_to(claude_dir)}")

    # Get final error count
    final_errors = run_pyright(".claude")
    final_count = len(final_errors)
    print(f"\nFinal error count: {final_count}")
    print(f"Errors fixed: {initial_count - final_count}")
    print(f"Total fixes applied: {total_fixes}")

    if final_count > 0:
        print("\nRemaining errors (first 10):")
        for error in final_errors[:10]:
            print(f"  {error}")


if __name__ == "__main__":
    main()
