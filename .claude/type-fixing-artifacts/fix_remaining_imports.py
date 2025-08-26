#!/usr/bin/env python3
"""
Fix the remaining relative import issues
"""
from pathlib import Path
import re

def fix_teamcoach_imports():
    """Fix teamcoach relative import issues"""
    teamcoach_files = list(Path('.claude/agents/teamcoach').rglob('*.py'))
    
    for file_path in teamcoach_files:
        content = file_path.read_text()
        original_content = content
        
        # For files in phase1/, phase2/, phase3/, tests/ - they need 4 dots (....shared)
        # For files directly in teamcoach/ - they need 3 dots (...shared)
        
        if '/phase1/' in str(file_path) or '/phase2/' in str(file_path) or '/phase3/' in str(file_path) or '/tests/' in str(file_path):
            # These need 4 dots to reach .claude/shared
            content = content.replace('from ...shared.', 'from ....shared.')
        elif str(file_path).endswith('teamcoach/__init__.py') or '/teamcoach/' in str(file_path):
            # Files directly in teamcoach need 3 dots
            content = content.replace('from ..shared.', 'from ...shared.')
            
        if content != original_content:
            file_path.write_text(content)
            print(f"Fixed imports in {file_path}")

def fix_black_import():
    """Fix the black import in type_safe_generator.py"""
    file_path = Path('.claude/tools/type_safe_generator.py')
    if file_path.exists():
        content = file_path.read_text()
        # Add type ignore for the black import
        if 'import black' in content and 'type: ignore' not in content:
            content = content.replace('import black', 'import black  # type: ignore[import-untyped]')
            file_path.write_text(content)
            print(f"Fixed black import in {file_path}")

def main():
    fix_teamcoach_imports()
    fix_black_import()
    print("Remaining imports fixed!")

if __name__ == "__main__":
    main()