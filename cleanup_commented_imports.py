import re
    import sys

#!/usr/bin/env python3
"""
Clean up all commented out imports from previous fixes.
"""

from pathlib import Path

def fix_commented_imports(file_path: Path) -> bool:
    """Uncomment imports that were mistakenly commented out."""
    try:
        content = file_path.read_text()
        original = content

        # Pattern to match commented import lines
        pattern = r"^# Fixed misplaced import: (from .+ import .+|import .+)$"

        # Replace with the uncommented version
        content = re.sub(pattern, r"\1", content, flags=re.MULTILINE)

        if content != original:
            file_path.write_text(content)
            print(f"Fixed commented imports in {file_path}")
            return True

    except Exception as e:
        print(f"Error fixing {file_path}: {e}")

    return False

def main():
    """Main function to clean up all commented imports."""
    print("Cleaning up commented imports...")

    fixed_count = 0
    for file_path in Path(".").rglob("*.py"):
        if fix_commented_imports(file_path):
            fixed_count += 1

    print(f"Fixed {fixed_count} files with commented imports")
    return 0

if __name__ == "__main__":

    sys.exit(main())
