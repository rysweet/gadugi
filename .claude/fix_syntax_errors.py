#!/usr/bin/env python3
"""Fix all syntax errors from bad lambda replacements."""

import re
from pathlib import Path


def fix_bad_lambdas(content: str) -> str:
    """Fix all bad lambda replacement patterns."""

    # Pattern 1: Fix method calls with bad lambda replacements
    pattern1 = (
        r"\((\w+)\.(\w+) if \1 is not None else lambda \*args, \*\*kwargs: None\)\("
    )
    content = re.sub(pattern1, r"\1.\2(", content)

    # Pattern 2: Fix attribute access with bad lambda replacements
    pattern2 = r"self\.\((\w+)\.(\w+) if \1 is not None else lambda \*args, \*\*kwargs: None\)\("
    content = re.sub(pattern2, r"self.\1.\2(", content)

    # Pattern 3: Fix standalone function calls
    pattern3 = r"\((\w+) if \1 is not None else lambda \*args, \*\*kwargs: None\)\("
    content = re.sub(pattern3, r"\1(", content)

    # Pattern 4: Fix chained method calls
    pattern4 = (
        r"\((\w+\.\w+) if \w+ is not None else lambda \*args, \*\*kwargs: None\)\("
    )
    content = re.sub(pattern4, r"\1(", content)

    # Pattern 5: Fix complex expressions
    pattern5 = r"\(([^)]+) if [^)]+is not None else lambda \*args, \*\*kwargs: None\)\("

    def replace_complex(match):
        expr = match.group(1)
        return f"{expr}("

    content = re.sub(pattern5, replace_complex, content)

    return content


def main():
    """Fix all files in .claude directory."""
    claude_dir = Path("/Users/ryan/src/gadugi5/gadugi/.claude")

    # Find all Python files
    python_files = list(claude_dir.rglob("*.py"))

    fixed_files = 0
    for filepath in python_files:
        try:
            content = filepath.read_text()
            original = content

            # Fix bad lambda patterns
            content = fix_bad_lambdas(content)

            # Save if changed
            if content != original:
                filepath.write_text(content)
                print(f"Fixed: {filepath.relative_to(claude_dir)}")
                fixed_files += 1

        except Exception as e:
            print(f"Error processing {filepath}: {e}")

    print(f"\nFixed {fixed_files} files")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
