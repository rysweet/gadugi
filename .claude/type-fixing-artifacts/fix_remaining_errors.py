#!/usr/bin/env python3
"""Fix remaining common type errors in test files."""

import re
from pathlib import Path

def fix_common_errors(file_path: Path):
    """Fix common type errors in a single file."""
    print(f"Fixing common errors in: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Fix undefined variables by adding imports
    if '"datetime" is not defined' and 'from datetime import' not in content:
        if 'import sys' in content:
            content = content.replace(
                'import sys',
                'import sys\nfrom datetime import datetime'
            )
    
    # Fix Dict type annotation issues
    if '"Dict" is not defined' in content and 'from typing import' in content:
        # Add Dict to existing typing import
        typing_pattern = r'from typing import ([^,\n]+(?:,[^,\n]+)*)'
        match = re.search(typing_pattern, content)
        if match:
            current_imports = match.group(1)
            if 'Dict' not in current_imports:
                new_imports = current_imports.rstrip() + ', Dict'
                content = re.sub(typing_pattern, f'from typing import {new_imports}', content)
    
    # Fix unused variable errors by using underscore prefix
    content = re.sub(r'(\s+)([a-zA-Z_][a-zA-Z0-9_]*) = ([^,\n]+)  # Variable "\2" is not accessed', 
                    r'\1_\2 = \3', content)
    
    # Fix unused variables in for loops
    content = re.sub(r'for ([a-zA-Z_][a-zA-Z0-9_]*) in', r'for _\1 in', content)
    
    # Fix Optional member access issues by adding None checks
    # This is more complex, so I'll leave the current pattern
    
    # Clean up comma issues in imports
    content = re.sub(r'from typing import ,', 'from typing import', content)
    content = re.sub(r'from typing import ([^,\n]+),\s*$', r'from typing import \1', content)
    
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
    
    # Focus on the files with the most errors
    priority_files = ["test_task_tracking.py", "test_error_handling.py", "test_state_management.py"]
    
    for filename in priority_files:
        test_file = test_dir / filename
        if test_file.exists():
            if fix_common_errors(test_file):
                updated_count += 1
    
    print(f"\nFixed common errors in {updated_count} files")

if __name__ == "__main__":
    main()