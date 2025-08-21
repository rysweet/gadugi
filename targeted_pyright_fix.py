#!/usr/bin/env python3
"""
Targeted script to fix the most common pyright errors.
"""

import json
import re
import subprocess
from pathlib import Path


def get_pyright_diagnostics() -> Dict:
    """Get full pyright diagnostics in JSON format."""
    result = subprocess.run(
        ["uv", "run", "pyright", "--outputjson"], capture_output=True, text=True
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def fix_missing_type_imports(file_path: Path) -> bool:
    """Add missing type imports."""
    try:
        content = file_path.read_text()
        lines = content.splitlines()

        # Check if typing imports are needed
        needs_typing = False
        missing_types = set()

        # Check for undefined type variables
        if "List[" in content or "List " in content:
            missing_types.add("List")
        if "Dict[" in content or "Dict " in content:
            missing_types.add("Dict")
        if "Tuple[" in content or "Tuple " in content:
            missing_types.add("Tuple")
        if "Optional[" in content or "Optional " in content:
            missing_types.add("Optional")
        if "Any " in content or "Any[" in content:
            missing_types.add("Any")
        if "Set[" in content or "Set " in content:
            missing_types.add("Set")

        if missing_types:
            # Find existing typing import line
            typing_line_idx = -1
            for i, line in enumerate(lines):
                if line.startswith("from typing import"):
                    typing_line_idx = i
                    break

            if typing_line_idx >= 0:
                # Update existing import
                existing_imports = set()
                match = re.search(r"from typing import (.+)", lines[typing_line_idx])
                if match:
                    existing_imports = {t.strip() for t in match.group(1).split(",")}

                all_imports = existing_imports | missing_types
                lines[typing_line_idx] = (
                    f"from typing import {', '.join(sorted(all_imports))}"
                )
            else:
                # Add new typing import after other imports
                import_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith(("import ", "from ")):
                        import_idx = i + 1
                    elif (
                        import_idx > 0
                        and not line.startswith(("import ", "from ", "#"))
                        and line.strip()
                    ):
                        break

                lines.insert(
                    import_idx, f"from typing import {', '.join(sorted(missing_types))}"
                )

            file_path.write_text("\n".join(lines) + "\n")
            print(f"Fixed type imports in {file_path}")
            return True

    except Exception as e:
        print(f"Error fixing type imports in {file_path}: {e}")

    return False


def remove_unused_variables_and_imports(
    file_path: Path, diagnostics: List[Dict]
) -> bool:
    """Remove unused variables and imports from a file."""
    try:
        content = file_path.read_text()
        lines = content.splitlines()

        # Collect lines to remove or modify
        lines_to_remove = set()
        vars_to_remove = {}  # line_num -> variable_names

        for diag in diagnostics:
            rule = diag.get("rule", "")
            if rule in ["reportUnusedImport", "reportUnusedVariable"]:
                line_num = diag.get("range", {}).get("start", {}).get("line", -1)

                if rule == "reportUnusedImport":
                    lines_to_remove.add(line_num)
                elif rule == "reportUnusedVariable":
                    # Extract variable name from message
                    message = diag.get("message", "")
                    match = re.search(r'Variable "(\w+)" is not accessed', message)
                    if match:
                        var_name = match.group(1)
                        if line_num not in vars_to_remove:
                            vars_to_remove[line_num] = []
                        vars_to_remove[line_num].append(var_name)

        # Apply fixes
        modified = False

        # Remove unused imports (in reverse order)
        for line_num in sorted(lines_to_remove, reverse=True):
            if 0 <= line_num < len(lines):
                if lines[line_num].strip().startswith(("import ", "from ")):
                    lines.pop(line_num)
                    modified = True

        # Handle unused variables (comment them out or prefix with _)
        for line_num, var_names in vars_to_remove.items():
            if 0 <= line_num < len(lines):
                line = lines[line_num]
                for var_name in var_names:
                    # Prefix with underscore to indicate intentionally unused
                    line = re.sub(rf"\b{var_name}\b", f"_{var_name}", line)
                lines[line_num] = line
                modified = True

        if modified:
            file_path.write_text("\n".join(lines) + "\n")
            print(f"Fixed unused variables/imports in {file_path}")
            return True

    except Exception as e:
        print(f"Error fixing unused items in {file_path}: {e}")

    return False


def main():
    """Main function to fix targeted pyright errors."""
    print("Running targeted pyright fixes...")

    # Get full diagnostics
    print("Getting pyright diagnostics...")
    data = get_pyright_diagnostics()

    if not data:
        print("Could not get pyright diagnostics")
        return 1

    diagnostics = data.get("generalDiagnostics", [])
    print(f"Found {len(diagnostics)} diagnostics")

    # Group diagnostics by file
    file_diagnostics = {}
    for diag in diagnostics:
        file_path = diag.get("file", "")
        if file_path:
            if file_path not in file_diagnostics:
                file_diagnostics[file_path] = []
            file_diagnostics[file_path].append(diag)

    print(f"Errors found in {len(file_diagnostics)} files")

    # Fix type imports first
    print("\n1. Fixing missing type imports...")
    type_fixes = 0
    for file_path in file_diagnostics.keys():
        path = Path(file_path)
        if path.exists() and fix_missing_type_imports(path):
            type_fixes += 1
    print(f"Fixed type imports in {type_fixes} files")

    # Fix unused variables and imports
    print("\n2. Fixing unused variables and imports...")
    unused_fixes = 0
    for file_path, diags in file_diagnostics.items():
        path = Path(file_path)
        if path.exists() and remove_unused_variables_and_imports(path, diags):
            unused_fixes += 1
    print(f"Fixed unused items in {unused_fixes} files")

    # Run pyright again to check progress
    print("\n3. Checking results...")
    result = subprocess.run(["uv", "run", "pyright"], capture_output=True, text=True)

    # Parse error count
    error_match = re.search(r"(\d+)\s+errors", result.stdout)
    if error_match:
        final_errors = int(error_match.group(1))
        print(f"Errors remaining: {final_errors}")

        if final_errors == 0:
            print("✅ All pyright errors fixed!")
        else:
            # Show sample of remaining errors
            lines = result.stdout.splitlines()
            error_lines = [l for l in lines if "error:" in l][:5]
            if error_lines:
                print("\nSample of remaining errors:")
                for line in error_lines:
                    print(f"  {line.strip()}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
