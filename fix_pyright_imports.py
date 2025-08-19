

import os
import re
import sys

#!/usr/bin/env python3

"""
Systematic Pyright Import Fixer
Fixes the most common import-related pyright errors.
"""

from pathlib import Path

def fix_mock_imports(file_path: Path) -> bool:
    """Fix missing unittest.mock imports"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # Check if file uses Mock, patch, MagicMock, AsyncMock
    uses_mock = any(pattern in content for pattern in [
        'Mock(', 'patch(', 'MagicMock(', 'AsyncMock(',
        '@patch', 'with patch', 'Mock.', 'MagicMock.',
        '"Mock"', '"patch"', '"MagicMock"', '"AsyncMock"'
    ])
    
    if not uses_mock:
        return False
    
    # Check if unittest.mock import already exists
    has_mock_import = (
from unittest.mock import Mock, patch, MagicMock
        'import unittest.mock' in content
    )
    
    if has_mock_import:
        return False
    
    # Find the right place to add the import
    lines = content.split('\n')
    insert_index = 0
    
    # Find imports section
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_index = i
        elif line.strip() == '' and i > 0 and (
            lines[i-1].startswith('import ') or lines[i-1].startswith('from ')
        ):
            insert_index = i
            break
    
    # Determine what to import
    mock_imports = []
    if any(p in content for p in ['Mock(', 'Mock.', '"Mock"']):
        mock_imports.append('Mock')
    if any(p in content for p in ['patch(', '@patch', 'with patch', '"patch"']):
        mock_imports.append('patch')
    if any(p in content for p in ['MagicMock(', 'MagicMock.', '"MagicMock"']):
        mock_imports.append('MagicMock')
    if any(p in content for p in ['AsyncMock(', 'AsyncMock.', '"AsyncMock"']):
        mock_imports.append('AsyncMock')
    
    if mock_imports:
        lines.insert(insert_index, import_line)
        
        file_path.write_text('\n'.join(lines), encoding='utf-8')
        return True
    
    return False

def fix_datetime_imports(file_path: Path) -> bool:
    """Fix missing datetime imports"""
    content = file_path.read_text(encoding='utf-8')
    
    # Check if file uses datetime but doesn't import it
    uses_datetime = (
        'datetime.' in content or 
        'datetime(' in content or
        '"datetime"' in content
    )
    
    has_datetime_import = (
        'import datetime' in content or
        'from datetime import' in content
    )
    
    if not uses_datetime or has_datetime_import:
        return False
    
    lines = content.split('\n')
    
    # Find imports section
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_index = i + 1
    
    lines.insert(insert_index, 'import datetime')
    file_path.write_text('\n'.join(lines), encoding='utf-8')
    return True

def fix_typing_imports(file_path: Path) -> bool:
    """Fix missing typing imports"""
    content = file_path.read_text(encoding='utf-8')
    
    # Check what typing imports are needed
    typing_needs = set()
    
    if 'Dict[' in content or 'Dict,' in content:
        typing_needs.add('Dict')
    if 'List[' in content or 'List,' in content:
        typing_needs.add('List')
    if 'Optional[' in content:
        typing_needs.add('Optional')
    if 'Set[' in content or 'Set,' in content:
        typing_needs.add('Set')
    if 'Tuple[' in content:
        typing_needs.add('Tuple')
    if 'Any' in content and '"Any"' not in content:
        typing_needs.add('Any')
    
    if not typing_needs:
        return False
    
    # Check existing typing imports
    existing_typing_imports = set()
    lines = content.split('\n')
    
    for line in lines:
        if '            # Extract imported names
            import_part = line.split('            # Handle parentheses and multiple lines
            import_part = import_part.strip('()')
            imports = [imp.strip() for imp in import_part.split(',')]
            existing_typing_imports.update(imports)
    
    needed_imports = typing_needs - existing_typing_imports
    
    if not needed_imports:
        return False
    
    # Find where to add typing imports
    typing_import_line = None
    for i, line in enumerate(lines):
        if '            typing_import_line = i
            break
    
    if typing_import_line is not None:
        # Update existing typing import
        current_line = lines[typing_import_line]
        if '(' in current_line:
            # Multi-line import
            # Find the end of the import
            end_line = typing_import_line
            for j in range(typing_import_line, len(lines)):
                if ')' in lines[j]:
                    end_line = j
                    break
            
            # Insert before the closing parenthesis
            before_paren = lines[end_line].replace(')', f", {', '.join(needed_imports)})")
            lines[end_line] = before_paren
        else:
            # Single line import
            lines[typing_import_line] = current_line.rstrip() + f", {', '.join(needed_imports)}"
    else:
        # Add new typing import
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_index = i + 1
        
        lines.insert(insert_index, f"    
    file_path.write_text('\n'.join(lines), encoding='utf-8')
    return True

def remove_unused_imports(file_path: Path) -> bool:
    """Remove unused imports that pyright complains about"""
    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    modified = False
    
    # Common unused imports to remove
    unused_patterns = [
        r'        r'import.*\bSet\b.*',  # Remove Set imports
    ]
    
    new_lines = []
    for line in lines:
        should_remove = False
        for pattern in unused_patterns:
            if re.search(pattern, line):
                # Check if Set is actually used in the file
                if 'Set' in pattern and 'Set[' not in content and 'Set(' not in content:
                    should_remove = True
                    break
        
        if not should_remove:
            new_lines.append(line)
        else:
            modified = True
    
    if modified:
        file_path.write_text('\n'.join(new_lines), encoding='utf-8')
    
    return modified

def fix_syntax_errors(file_path: Path) -> bool:
    """Fix basic syntax errors"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # Fix common syntax issues
    content = re.sub(r';\s*\n', '\n', content)  # Remove trailing semicolons
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Remove excessive blank lines
    
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return True
    
    return False

def main():
    """Main function to fix pyright errors"""
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        target_dir = Path('.')
    
    print(f"Fixing pyright import errors in: {target_dir}")
    
    total_fixes = 0
    files_processed = 0
    
    for py_file in target_dir.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', '.git', 'node_modules']):
            continue
        
        files_processed += 1
        file_fixes = 0
        
        try:
            if fix_mock_imports(py_file):
                file_fixes += 1
                print(f"  Fixed Mock imports in: {py_file}")
            
            if fix_datetime_imports(py_file):
                file_fixes += 1
                print(f"  Fixed datetime imports in: {py_file}")
            
            if fix_typing_imports(py_file):
                file_fixes += 1
                print(f"  Fixed typing imports in: {py_file}")
            
            if remove_unused_imports(py_file):
                file_fixes += 1
                print(f"  Removed unused imports in: {py_file}")
            
            if fix_syntax_errors(py_file):
                file_fixes += 1
                print(f"  Fixed syntax errors in: {py_file}")
            
            total_fixes += file_fixes
            
        except Exception as e:
            print(f"  Error processing {py_file}: {e}")
    
    print(f"\nProcessed {files_processed} files")
    print(f"Applied {total_fixes} fixes")
    
    return total_fixes

if __name__ == '__main__':
    main()