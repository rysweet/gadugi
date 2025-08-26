#!/usr/bin/env python3
"""
Check for syntax errors in all Python test files and report them.
"""
import ast
import sys
from pathlib import Path

def check_file_syntax(file_path: Path) -> tuple[bool, str]:
    """Check if a Python file has syntax errors.
    
    Returns:
        (has_error, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        ast.parse(content, filename=str(file_path))
        return False, ""
    except SyntaxError as e:
        return True, f"SyntaxError: {e.msg} (line {e.lineno}, col {e.offset})"
    except Exception as e:
        return True, f"ParseError: {str(e)}"

def main():
    """Check all test files for syntax errors."""
    test_dir = Path("tests")
    if not test_dir.exists():
        print("tests/ directory not found!")
        return 1
    
    # Find all Python files in tests/
    python_files = list(test_dir.rglob("*.py"))
    
    print(f"Checking {len(python_files)} Python test files for syntax errors...")
    print("=" * 60)
    
    error_files = []
    
    for file_path in sorted(python_files):
        has_error, error_msg = check_file_syntax(file_path)
        
        if has_error:
            print(f"❌ {file_path}: {error_msg}")
            error_files.append((file_path, error_msg))
        else:
            print(f"✅ {file_path}: OK")
    
    print("=" * 60)
    if error_files:
        print(f"\nFound {len(error_files)} files with syntax errors:")
        for file_path, error_msg in error_files:
            print(f"  - {file_path}: {error_msg}")
        return len(error_files)
    else:
        print(f"\n✅ All {len(python_files)} test files have valid syntax!")
        return 0

if __name__ == "__main__":
    sys.exit(main())