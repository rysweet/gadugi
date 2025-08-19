from typing import List

import re
import subprocess
import sys
            import json

#!/usr/bin/env python3
from ..shared.error_handling import ErrorHandler
"""
Comprehensive script to fix all pyright errors systematically.
"""

from pathlib import Path

def fix_indentation_errors(file_path: Path) -> bool:
    """Fix indentation errors caused by incorrectly inserted lines."""
    try:
        content = file_path.read_text()
        original_content = content

        # Pattern 1: Remove incorrectly inserted variable assignments in class methods
        # These are lines like "ErrorHandler = None" or "ContainerConfig = None"
        # that were incorrectly inserted and break indentation
        patterns_to_remove = [
            r"^\s+ErrorHandler = None\n",
            r"^\s+ContainerConfig = None\n",
            r"^\s+ContainerResult = None\n",
            r"^\s+ContainerManager = None\n",
            r"^\s+OrchestrationMonitor = None\n",
            r"^\s+ExecutionEngine = None\n",
        ]

        for pattern in patterns_to_remove:
            content = re.sub(pattern, "", content, flags=re.MULTILINE)

        if content != original_content:
            file_path.write_text(content)
            print(f"Fixed indentation in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def fix_unused_imports(file_path: Path) -> bool:
    """Remove unused imports from a file."""
    try:
        # Run pyright on the file to get unused imports
        result = subprocess.run(
            ["uv", "run", "pyright", str(file_path), "--outputjson"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:

            try:
                output = json.loads(result.stdout)
                diagnostics = output.get("generalDiagnostics", [])

                content = file_path.read_text()
                lines = content.splitlines()

                # Track lines to remove
                lines_to_remove = set()

                for diag in diagnostics:
                    if diag.get("rule") == "reportUnusedImport":
                        line_num = diag.get("range", {}).get("start", {}).get("line", 0)
                        lines_to_remove.add(line_num)

                if lines_to_remove:
                    # Remove lines in reverse order to maintain line numbers
                    for line_num in sorted(lines_to_remove, reverse=True):
                        if 0 <= line_num < len(lines):
                            # Check if it's an import line
                            if lines[line_num].strip().startswith(("import ", "from ")):
                                lines.pop(line_num)

                    file_path.write_text("\n".join(lines) + "\n")
                    print(
                        f"Removed {len(lines_to_remove)} unused imports from {file_path}"
                    )
                    return True

            except json.JSONDecodeError:
                pass

        return False
    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")
        return False

def fix_optional_access(file_path: Path) -> bool:
    """Add None checks for optional member access."""
    try:
        content = file_path.read_text()
        original_content = content

        # Common _patterns that need None checks
        patterns = [
            # Pattern: if obj.attr -> if obj and obj.attr
            (r"if (\w+)\.(\w+)(?!\s*is\s+None)(?!\s*==)", r"if \1 and \1.\2"),
            # Pattern: obj.method() without None check -> obj.method() if obj else None
            (
                r"^(\s*)(\w+)\.(\w+)\((.*?)\)(\s*#.*)?$",
                r"\1\2.\3(\4) if \2 else None\5",
            ),
        ]

        # Apply patterns conservatively
        # This is a simplified approach - a proper fix would need AST analysis

        return False  # For now, skip this as it needs more sophisticated handling

    except Exception as e:
        print(f"Error fixing optional access in {file_path}: {e}")
        return False

def get_all_python_files() -> List[Path]:
    """Get all Python files in the project."""
    return list(Path(".").rglob("*.py"))

def main():
    """Main function to fix all pyright errors."""
    print("Starting comprehensive pyright error fix...")

    # Step 1: Fix indentation errors in test files
    test_files = [
        Path(".claude/orchestrator/tests/test_containerized_execution.py"),
        Path(".claude/framework/tests/test_base_agent.py"),
        Path(".claude/orchestrator/tests/test_orchestrator_fixes.py"),
        Path(".claude/orchestrator/tests/test_orchestrator_integration.py"),
        Path(".claude/agents/test_solver_agent.py"),
        Path(".claude/agents/test_writer_agent.py"),
    ]

    print("\n1. Fixing indentation errors...")
    fixed_count = 0
    for file_path in test_files:
        if file_path.exists():
            if fix_indentation_errors(file_path):
                fixed_count += 1
    print(f"Fixed indentation in {fixed_count} files")

    # Step 2: Run pyright to see current state
    print("\n2. Checking current pyright status...")
    result = subprocess.run(["uv", "run", "pyright"], capture_output=True, text=True)

    # Parse error count
    error_match = re.search(r"(\d+)\s+errors", result.stdout)
    if error_match:
        error_count = int(error_match.group(1))
        print(f"Current error count: {error_count}")
    else:
        print("Could not determine error count")

    # Step 3: Fix unused imports in all files (biggest source of errors)
    print("\n3. Fixing unused imports...")
    python_files = get_all_python_files()
    fixed_imports = 0

    for file_path in python_files:
        if fix_unused_imports(file_path):
            fixed_imports += 1

    print(f"Fixed imports in {fixed_imports} files")

    # Step 4: Final pyright check
    print("\n4. Final pyright check...")
    result = subprocess.run(["uv", "run", "pyright"], capture_output=True, text=True)

    # Parse final error count
    error_match = re.search(r"(\d+)\s+errors", result.stdout)
    if error_match:
        final_error_count = int(error_match.group(1))
        print(f"Final error count: {final_error_count}")

        if final_error_count == 0:
            print("✅ SUCCESS: All pyright errors fixed!")
        else:
            print(f"⚠️  {final_error_count} errors remain. Manual intervention needed.")
            # Show a sample of remaining errors
            lines = result.stdout.splitlines()
            error_lines = [l for l in lines if "error:" in l][:10]
            if error_lines:
                print("\nSample of remaining errors:")
                for line in error_lines:
                    print(f"  {line}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
