#!/usr/bin/env python3
"""
Fix type errors in team-coach modules.
This script will systematically fix common type errors across all team-coach files.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def fix_numpy_imports(content: str) -> str:
    """Add type ignore comment to numpy imports."""
    return content.replace(
        'import numpy as np',
        'import numpy as np  # type: ignore[import-not-found]'
    ).replace(
        'import numpy',
        'import numpy  # type: ignore[import-not-found]'
    )

def fix_matplotlib_imports(content: str) -> str:
    """Add type ignore comment to matplotlib imports."""
    return content.replace(
        'import matplotlib.pyplot',
        'import matplotlib.pyplot  # type: ignore[import-not-found]'
    ).replace(
        'from matplotlib',
        'from matplotlib  # type: ignore[import-not-found]'
    )

def fix_seaborn_imports(content: str) -> str:
    """Add type ignore comment to seaborn imports."""
    return content.replace(
        'import seaborn',
        'import seaborn  # type: ignore[import-not-found]'
    )

def fix_missing_shared_imports(content: str) -> str:
    """Fix relative imports for shared modules."""
    replacements = [
        ('from interfaces import', 'from ...shared.interfaces import'),
        ('from utils.error_handling import', 'from ...shared.utils.error_handling import'),
        ('from state_management import', 'from ...shared.state_management import'),
        ('from task_tracking import', 'from ...shared.task_tracking import'),
        ('import interfaces', 'from ...shared import interfaces'),
        ('import utils.error_handling', 'from ...shared.utils import error_handling'),
        ('import state_management', 'from ...shared import state_management'),
        ('import task_tracking', 'from ...shared import task_tracking'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    return content

def fix_optional_parameters(content: str) -> str:
    """Fix optional parameter type hints."""
    # Pattern to find function definitions with = None but without Optional
    pattern = r'(\w+):\s*(List\[[^\]]+\]|Dict\[[^\]]+\]|str|int|float|bool|Any)\s*=\s*None'
    
    def replace_with_optional(match):
        param_name = match.group(1)
        type_hint = match.group(2)
        return f'{param_name}: Optional[{type_hint}] = None'
    
    return re.sub(pattern, replace_with_optional, content)

def ensure_optional_import(content: str) -> str:
    """Ensure Optional is imported from typing."""
    if 'Optional' not in content and '= None' in content:
        # Find the typing import line
        typing_import_pattern = r'from typing import (.+)'
        match = re.search(typing_import_pattern, content)
        if match:
            imports = match.group(1)
            if 'Optional' not in imports:
                new_imports = imports.rstrip() + ', Optional'
                content = content.replace(
                    f'from typing import {imports}',
                    f'from typing import {new_imports}'
                )
    return content

def fix_type_aliases(content: str) -> str:
    """Fix type alias conflicts in team-coach modules."""
    # Fix duplicate class imports
    if 'from ..phase1.capability_assessment import' in content:
        lines = content.split('\n')
        new_lines = []
        seen_imports = set()
        
        for line in lines:
            # Check for duplicate import assignments
            if '=' in line and 'import' in line:
                import_match = re.search(r'(\w+)\s*=\s*(\w+)', line)
                if import_match:
                    alias = import_match.group(1)
                    if alias in seen_imports:
                        # Skip duplicate
                        continue
                    seen_imports.add(alias)
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    return content

def fix_datetime_optional(content: str) -> str:
    """Fix datetime optional type issues."""
    # Fix patterns like: resolved_at: datetime = None
    pattern = r'(\w+):\s*datetime\s*=\s*None'
    
    def replace_datetime(match):
        param_name = match.group(1)
        return f'{param_name}: Optional[datetime] = None'
    
    return re.sub(pattern, replace_datetime, content)

def fix_dict_type_variance(content: str) -> str:
    """Fix Dict type variance issues."""
    # Replace Dict[str, int] with Dict[str, float] where needed for compatibility
    content = content.replace(
        'durations: Dict[str, int]',
        'durations: Dict[str, float]'
    )
    return content

def fix_list_none_assignments(content: str) -> str:
    """Fix list assignments with None values."""
    # Pattern to find list comprehensions with potential None values
    pattern = r'\[([^]]*\.get\([^)]+\)[^]]*)\]'
    
    def fix_list_comp(match):
        inner = match.group(1)
        # Check if it's getting values that could be None
        if '.get(' in inner and 'for' in inner:
            # Wrap in filter to remove None values
            parts = inner.split(' for ')
            if len(parts) == 2:
                expr, iterator = parts
                return f'[{expr} for {iterator} if {expr.split()[0]} is not None]'
        return match.group(0)
    
    return re.sub(pattern, fix_list_comp, content)

def process_file(file_path: Path) -> bool:
    """Process a single file to fix type errors."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all fixes
        content = ensure_optional_import(content)
        content = fix_numpy_imports(content)
        content = fix_matplotlib_imports(content)
        content = fix_seaborn_imports(content)
        content = fix_missing_shared_imports(content)
        content = fix_optional_parameters(content)
        content = fix_type_aliases(content)
        content = fix_datetime_optional(content)
        content = fix_dict_type_variance(content)
        content = fix_list_none_assignments(content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all team-coach files."""
    team_coach_dir = Path('/home/rysweet/gadugi/.claude/agents/team-coach')
    
    if not team_coach_dir.exists():
        print(f"Directory not found: {team_coach_dir}")
        return
    
    # Find all Python files in team-coach directory
    python_files = list(team_coach_dir.glob('**/*.py'))
    
    print(f"Found {len(python_files)} Python files in team-coach directory")
    
    fixed_count = 0
    for file_path in python_files:
        if process_file(file_path):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()