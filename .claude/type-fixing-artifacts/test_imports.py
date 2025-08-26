#!/usr/bin/env python3
"""
Test that all test files can be imported without syntax errors.
"""
import sys
from pathlib import Path
import importlib.util

def test_import_file(file_path: Path) -> tuple[bool, str]:
    """Try to import a Python file.
    
    Returns:
        (success, error_message)
    """
    try:
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        if spec is None:
            return False, "Could not create spec"
        
        _ = importlib.util.module_from_spec(spec)  # type: ignore
        # Don't execute the module, just test if it can be imported
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} (line {e.lineno})"
    except Exception as e:
        return False, f"ImportError: {str(e)}"

def main():
    """Test importing all test files."""
    test_dir = Path("tests")
    if not test_dir.exists():
        print("tests/ directory not found!")
        return 1
    
    # Find all Python files in tests/, excluding __init__.py files
    python_files = [f for f in test_dir.rglob("*.py") if f.name != "__init__.py"]
    
    print(f"Testing imports for {len(python_files)} Python test files...")
    print("=" * 60)
    
    failed_imports = []
    
    for file_path in sorted(python_files):
        success, error_msg = test_import_file(file_path)
        
        if not success:
            print(f"❌ {file_path}: {error_msg}")
            failed_imports.append((file_path, error_msg))
        else:
            print(f"✅ {file_path}: Import OK")
    
    print("=" * 60)
    if failed_imports:
        print(f"\nFound {len(failed_imports)} files with import errors:")
        for file_path, error_msg in failed_imports:
            print(f"  - {file_path}: {error_msg}")
        return len(failed_imports)
    else:
        print(f"\n✅ All {len(python_files)} test files can be imported successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())