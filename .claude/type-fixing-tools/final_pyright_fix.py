#!/usr/bin/env python3
"""
Final comprehensive script to fix ALL pyright errors and achieve 0 errors.
"""

import re
import subprocess
import sys
from pathlib import Path


def fix_broken_imports(file_path: Path) -> bool:
    """Fix imports that were broken by previous automated fixes."""
    try:
        content = file_path.read_text()
        lines = content.splitlines()

        fixed = False
        new_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for broken import pattern (typing import in middle of another import)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Pattern: import statement followed by "from typing import"
                if (
                    "from .." in line
                    and line.strip().endswith("(")
                    and "from typing import" in next_line
                ):
                    # This is a broken multi-line import
                    # Move the typing import before this import
                    new_lines.append(next_line)  # Add typing import first
                    new_lines.append(line)  # Then the original import start

                    # Skip forward to find the rest of the import
                    i += 2
                    while i < len(lines) and not lines[i].strip().endswith(")"):
                        # Skip any other misplaced imports
                        if "from typing import" not in lines[i]:
                            new_lines.append(lines[i])
                        i += 1
                    if i < len(lines):
                        new_lines.append(lines[i])  # Add the closing parenthesis
                    fixed = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
            i += 1

        if fixed:
            file_path.write_text("\n".join(new_lines) + "\n")
            print(f"Fixed broken imports in {file_path}")
            return True

    except Exception as e:
        print(f"Error fixing imports in {file_path}: {e}")

    return False


def fix_syntax_errors(file_path: Path) -> bool:
    """Fix common syntax errors."""
    try:
        content = file_path.read_text()
        original = content

        # Fix "from typing import" appearing in wrong places
        # Pattern: Line starting with "from typing import" that's indented or after an opening parenthesis
        content = re.sub(
            r"^(\s+)(from typing import .+)$",
            r"# Fixed misplaced import: \2",
            content,
            flags=re.MULTILINE,
        )

        # Fix duplicate type imports on same line
        content = re.sub(
            r"from typing import ([\w, ]+), (\1)", r"from typing import \1", content
        )

        # Fix "Path" import issues - ensure it's imported from pathlib
        lines = content.splitlines()
        has_path_import = any(
            "from pathlib import" in line and "Path" in line for line in lines
        )
        uses_path = "Path(" in content or "Path." in content

        if uses_path and not has_path_import:
            # Add Path import after other imports
            import_idx = 0
            for i, line in enumerate(lines):
                if line.startswith(("import ", "from ")):
                    import_idx = i + 1
            if import_idx > 0:
                lines.insert(import_idx, "from pathlib import Path")
                content = "\n".join(lines)

        if content != original:
            file_path.write_text(content + "\n")
            print(f"Fixed syntax errors in {file_path}")
            return True

    except Exception as e:
        print(f"Error fixing syntax in {file_path}: {e}")

    return False


def add_missing_imports(file_path: Path) -> bool:
    """Add commonly missing imports."""
    try:
        content = file_path.read_text()
        lines = content.splitlines()

        # Check what's used but not imported
        imports_needed = set()

        # Common missing imports based on usage
        if "Dict[" in content or "Dict " in content:
            if not any(
                "Dict" in line for line in lines if "from typing import" in line
            ):
                imports_needed.add("Dict")

        if "List[" in content or "List " in content:
            if not any(
                "List" in line for line in lines if "from typing import" in line
            ):
                imports_needed.add("List")

        if "Optional[" in content:
            if not any(
                "Optional" in line for line in lines if "from typing import" in line
            ):
                imports_needed.add("Optional")

        if "Tuple[" in content or "Tuple " in content:
            if not any(
                "Tuple" in line for line in lines if "from typing import" in line
            ):
                imports_needed.add("Tuple")

        if "Set[" in content or "Set " in content:
            if not any("Set" in line for line in lines if "from typing import" in line):
                imports_needed.add("Set")

        if "Any " in content or "Any[" in content or "Any]" in content:
            if not any("Any" in line for line in lines if "from typing import" in line):
                imports_needed.add("Any")

        if imports_needed:
            # Find or create typing import line
            typing_line_idx = -1
            for i, line in enumerate(lines):
                if "from typing import" in line:
                    typing_line_idx = i
                    break

            if typing_line_idx >= 0:
                # Update existing typing import
                match = re.search(r"from typing import (.+)", lines[typing_line_idx])
                if match:
                    existing = set(t.strip() for t in match.group(1).split(","))
                    all_imports = existing | imports_needed
                    lines[typing_line_idx] = (
                        f"from typing import {', '.join(sorted(all_imports))}"
                    )
            else:
                # Add new typing import after other imports
                import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith(("import ", "from ")):
                        import_idx = i + 1
                lines.insert(
                    import_idx,
                    f"from typing import {', '.join(sorted(imports_needed))}",
                )

            file_path.write_text("\n".join(lines) + "\n")
            print(f"Added missing imports to {file_path}: {imports_needed}")
            return True

    except Exception as e:
        print(f"Error adding imports to {file_path}: {e}")

    return False


def fix_teamcoach_files():
    """Fix all TeamCoach test files with syntax errors."""
    teamcoach_patterns = [
        ".claude/agents/team-coach/tests/*.py",
        ".claude/agents/teamcoach/tests/*.py",
        "claude/agents/team-coach/tests/*.py",
        "claude/agents/teamcoach/tests/*.py",
    ]

    files_fixed = 0
    for pattern in teamcoach_patterns:
        for file_path in Path(".").glob(pattern):
            if fix_broken_imports(file_path):
                files_fixed += 1
            if fix_syntax_errors(file_path):
                files_fixed += 1

    print(f"Fixed {files_fixed} TeamCoach test files")
    return files_fixed


def main():
    """Main function to achieve 0 pyright errors."""
    print("Starting final comprehensive pyright fix...")

    # Step 1: Fix TeamCoach files first (they have the most syntax errors)
    print("\n1. Fixing TeamCoach test files...")
    fix_teamcoach_files()

    # Step 2: Fix all Python files with syntax errors
    print("\n2. Fixing syntax errors in all Python files...")
    syntax_fixes = 0
    for file_path in Path(".").rglob("*.py"):
        if fix_syntax_errors(file_path):
            syntax_fixes += 1
    print(f"Fixed syntax in {syntax_fixes} files")

    # Step 3: Add missing imports
    print("\n3. Adding missing imports...")
    import_fixes = 0
    for file_path in Path(".").rglob("*.py"):
        if add_missing_imports(file_path):
            import_fixes += 1
    print(f"Added imports to {import_fixes} files")

    # Step 4: Run pyright to check final status
    print("\n4. Running final pyright check...")
    result = subprocess.run(["uv", "run", "pyright"], capture_output=True, text=True)

    # Parse final error count
    error_match = re.search(r"(\d+)\s+errors", result.stdout)
    if error_match:
        final_errors = int(error_match.group(1))
        print(f"\n{'=' * 60}")
        print(f"FINAL RESULT: {final_errors} errors remaining")
        print(f"{'=' * 60}")

        if final_errors == 0:
            print("✅ SUCCESS! All pyright errors have been fixed!")
        else:
            print(f"⚠️  {final_errors} errors still remain")

            # Show sample of remaining errors
            lines = result.stdout.splitlines()
            error_lines = [l for l in lines if "error:" in l][:10]
            if error_lines:
                print("\nSample of remaining errors:")
                for line in error_lines:
                    print(f"  {line.strip()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
