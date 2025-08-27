#!/usr/bin/env python3
"""
Create a comprehensive Python script to check all Python files in the repository 
for syntax errors and report the results.
"""
import ast
import sys
from pathlib import Path

def check_all_python_files():
    """Check all Python files in the repository for syntax errors."""
    
    # Get all Python files (excluding venvs, node_modules, etc.)
    exclude_dirs = {
        '__pycache__', '.git', '.venv', 'venv', 'node_modules', 
        '.pytest_cache', 'gadugi.egg-info', '.tox'
    }
    
    python_files = []
    
    for file_path in Path(".").rglob("*.py"):
        # Skip files in excluded directories
        if any(part in exclude_dirs for part in file_path.parts):
            continue
        python_files.append(file_path)
    
    print(f"Checking {len(python_files)} Python files for syntax errors...")
    print("=" * 80)
    
    syntax_error_files = []
    total_files = len(python_files)
    valid_files = 0
    
    for file_path in sorted(python_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse the file
            ast.parse(content, filename=str(file_path))
            print(f"✅ {file_path}")
            valid_files += 1
            
        except SyntaxError as e:
            print(f"❌ {file_path}: SyntaxError - {e.msg} (line {e.lineno})")
            syntax_error_files.append((file_path, f"SyntaxError: {e.msg} (line {e.lineno})"))
            
        except UnicodeDecodeError as e:
            print(f"❌ {file_path}: UnicodeDecodeError - {e}")
            syntax_error_files.append((file_path, f"UnicodeDecodeError: {e}"))
            
        except Exception as e:
            print(f"❌ {file_path}: ParseError - {str(e)}")
            syntax_error_files.append((file_path, f"ParseError: {str(e)}"))
    
    print("=" * 80)
    print(f"\nSYNTAX ERROR SUMMARY:")
    print(f"  Total files checked: {total_files}")
    print(f"  Files with valid syntax: {valid_files}")
    print(f"  Files with syntax errors: {len(syntax_error_files)}")
    
    if syntax_error_files:
        print(f"\nFILES WITH SYNTAX ERRORS ({len(syntax_error_files)}):")
        for file_path, error_msg in syntax_error_files:
            print(f"  - {file_path}: {error_msg}")
        print(f"\n❌ SYNTAX ERRORS FOUND: {len(syntax_error_files)} files need fixing")
        return len(syntax_error_files)
    else:
        print(f"\n✅ ALL FILES HAVE VALID SYNTAX!")
        return 0

if __name__ == "__main__":
    error_count = check_all_python_files()
    sys.exit(error_count)