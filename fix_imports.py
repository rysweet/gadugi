#!/usr/bin/env python3
"""Script to fix import statements in test files."""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path):
    """Fix import statements in a single test file."""
    print(f"Fixing imports in: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Store original content to check if changes were made
    original_content = content
    
    # Fix claude.shared imports to shared imports
    content = re.sub(
        r'from claude\.shared\.([^\s]+) import',
        r'from shared.\1 import',
        content
    )
    
    # Fix sys.path.insert lines to include .claude directory
    if 'sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))' in content:
        content = content.replace(
            'sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))',
            'sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.claude")))'
        )
    
    # Add field import if field() is used but not imported
    if 'field(' in content and 'from dataclasses import field' not in content:
        # Find the typing import line and add field import after it
        if 'from typing import' in content:
            content = re.sub(
                r'(from typing import [^\n]+)',
                r'\1\nfrom dataclasses import field',
                content,
                count=1
            )
    
    # Only write if content changed
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Updated {file_path}")
        return True
    else:
        print(f"  - No changes needed for {file_path}")
        return False

def main():
    """Main function to process all test files."""
    test_dir = Path("tests/shared")
    
    if not test_dir.exists():
        print(f"Directory {test_dir} not found")
        return
    
    updated_count = 0
    
    for test_file in test_dir.glob("test_*.py"):
        if fix_imports_in_file(test_file):
            updated_count += 1
    
    print(f"\nFixed imports in {updated_count} files")

if __name__ == "__main__":
    main()