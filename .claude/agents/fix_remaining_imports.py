#!/usr/bin/env python3
"""Fix remaining import issues in TeamCoach and other agent modules."""

import re
from pathlib import Path


def fix_shared_imports(content: str) -> str:
    """Add type: ignore to all shared module imports."""
    patterns = [
        (r"(from \.\.\.shared[^\n]+)", r"\1  # type: ignore"),
        (r"(from \.\.shared[^\n]+)", r"\1  # type: ignore"),
        (r"(from \.shared[^\n]+)", r"\1  # type: ignore"),
    ]

    for pattern, replacement in patterns:
        # Only add if not already there
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if re.match(pattern, line) and "# type: ignore" not in line:
                new_lines.append(re.sub(pattern, replacement, line))
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)

    return content


def fix_numpy_usage(content: str) -> str:
    """Ensure numpy is imported as np properly."""
    # Fix bad numpy import patterns
    content = re.sub(
        r"import numpy\s+#[^a]*as np.*",
        "import numpy as np  # type: ignore[import-not-found]",
        content,
    )

    # Ensure numpy is imported if np is used
    if "np." in content or "np[" in content:
        if "import numpy" not in content:
            # Add numpy import after other imports
            lines = content.split("\n")
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    import_index = i + 1
                elif import_index > 0 and line and not line.startswith(" "):
                    break

            if import_index > 0:
                lines.insert(
                    import_index, "import numpy as np  # type: ignore[import-not-found]"
                )
                content = "\n".join(lines)

    return content


def fix_matplotlib_usage(content: str) -> str:
    """Ensure matplotlib is imported properly."""
    if "plt." in content:
        if "import matplotlib.pyplot as plt" not in content:
            # Find where to add the import
            lines = content.split("\n")
            import_index = 0
            for i, line in enumerate(lines):
                if "import matplotlib" in line:
                    # Replace existing matplotlib import
                    lines[i] = (
                        "import matplotlib.pyplot as plt  # type: ignore[import-not-found]"
                    )
                    content = "\n".join(lines)
                    return content
                elif line.startswith("import ") or line.startswith("from "):
                    import_index = i + 1
                elif import_index > 0 and line and not line.startswith(" "):
                    break

            if import_index > 0:
                lines.insert(
                    import_index,
                    "import matplotlib.pyplot as plt  # type: ignore[import-not-found]",
                )
                content = "\n".join(lines)

    return content


def fix_test_syntax_errors(content: str) -> str:
    """Fix syntax errors in test files."""
    # Remove or comment out bare expected expressions
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        # Check for lines that are just 'Expected expression' comments
        if line.strip() in [
            "Expected expression",
            "Expected expression.",
            '"Expected expression"',
        ]:
            new_lines.append("    # " + line.strip())
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def process_file(file_path: Path) -> bool:
    """Process a single file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original = content

        content = fix_shared_imports(content)
        content = fix_numpy_usage(content)
        content = fix_matplotlib_usage(content)

        if "test" in file_path.name.lower():
            content = fix_test_syntax_errors(content)

        if content != original:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True

        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    base_dir = Path("/home/rysweet/gadugi/.claude/agents")

    # Process all Python files in agents directory
    python_files = list(base_dir.glob("**/*.py"))

    print(f"Processing {len(python_files)} files...")

    fixed = 0
    for file_path in python_files:
        if process_file(file_path):
            fixed += 1

    print(f"Fixed {fixed} files")


if __name__ == "__main__":
    main()
