#!/usr/bin/env python3
"""Script to fix unused imports in test files."""

import re
from pathlib import Path

def remove_unused_imports(file_path: Path):
    """Remove unused imports from a file."""
    print(f"Fixing unused imports in: {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Common unused imports to remove based on pyright output
    unused_patterns = [
        # From error_handling
        (r'from typing import[^,\n]*,\s*Any[^,\n]*,\s*Dict', 'from typing import'),
        (r', Any,', ','),
        (r', Dict,', ','),
        (r', Optional', ''),
        (r'from typing import Any, Dict, Optional\n', ''),
        
        # From task_tracking  
        (r'from datetime import[^,\n]*,\s*timedelta', 'from datetime import'),
        (r', timedelta', ''),
        (r'from pathlib import Path\n', ''),
        (r'from unittest.mock import[^,\n]*MagicMock[^,\n]*,\s*', 'from unittest.mock import '),
        (r', MagicMock,', ','),
        (r', call,', ','),
        (r'from typing import[^,\n]*ClassVar[^,\n]*,\s*', 'from typing import '),
        (r', ClassVar', ''),
        
        # From workflow files
        (r'import subprocess\n', ''),
        (r'from pathlib import Path\n', ''),
        
        # Clean up comma issues
        (r'from ([^,\n]+) import ,', r'from \1 import'),
        (r'import ,', 'import'),
        (r',\s*\)', ')'),
    ]
    
    for pattern, replacement in unused_patterns:
        content = re.sub(pattern, replacement, content)
    
    # Remove empty import lines
    content = re.sub(r'\nfrom [^\n]+ import\s*\n', '\n', content)
    content = re.sub(r'\nimport\s*\n', '\n', content)
    
    # Clean up double newlines
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
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
        if remove_unused_imports(test_file):
            updated_count += 1
    
    print(f"\nFixed unused imports in {updated_count} files")

if __name__ == "__main__":
    main()