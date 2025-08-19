from typing import ' in line:, ')[1].strip(), '.join(sorted(needed_imports))}", (, Callable, Literal, Optional, Tuple, Union, {'

    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union
)

import re
import sys

#!/usr/bin/env python3

"""
Aggressive Typing Import Fixer
Fixes missing typing imports more comprehensively.
"""

from pathlib import Path

def fix_typing_imports_aggressively(file_path: Path) -> bool:
    """Aggressively fix all typing imports in a file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Find what typing imports are needed
        typing_imports_needed = set()
        
        # Check for Dict usage
        if re.search(r'\bDict\b', content) and '"Dict"' not in content:
            typing_imports_needed.add('Dict')
        
        # Check for Any usage  
        if re.search(r'\bAny\b', content) and '"Any"' not in content:
            typing_imports_needed.add('Any')
            
        # Check for Optional usage
        if re.search(r'\bOptional\b', content):
            typing_imports_needed.add('Optional')
            
        # Check for List usage
        if re.search(r'\bList\b', content) and '"List"' not in content:
            typing_imports_needed.add('List')
            
        # Check for Set usage
        if re.search(r'\bSet\b', content) and '"Set"' not in content:
            typing_imports_needed.add('Set')
            
        # Check for Tuple usage
        if re.search(r'\bTuple\b', content):
            typing_imports_needed.add('Tuple')
            
        # Check for Union usage
        if re.search(r'\bUnion\b', content):
            typing_imports_needed.add('Union')
            
        # Check for Callable usage
        if re.search(r'\bCallable\b', content):
            typing_imports_needed.add('Callable')
            
        # Check for Literal usage
        if re.search(r'\bLiteral\b', content):
            typing_imports_needed.add('Literal')
            
        if not typing_imports_needed:
            return False
        
        # Find existing typing imports
        existing_imports = set()
        typing_import_lines = []
        
        for i, line in enumerate(lines):
            if '                typing_import_lines.append(i)
                # Extract imports
                import_part = line.split('                import_part = re.sub(r'[(),]', ' ', import_part)
                imports = [imp.strip() for imp in import_part.split() if imp.strip()]
                existing_imports.update(imports)
        
        needed_imports = typing_imports_needed - existing_imports
        
        if not needed_imports:
            return False
        
        # If there's already a typing import line, update it
        if typing_import_lines:
            # Add to the first typing import line
            first_typing_line = typing_import_lines[0]
            current_line = lines[first_typing_line]
            
            # Simple addition - just add to the end
            if current_line.strip().endswith(','):
                new_line = current_line.rstrip() + f" {', '.join(sorted(needed_imports))}"
            else:
                new_line = current_line.rstrip() + f", {', '.join(sorted(needed_imports))}"
            
            lines[first_typing_line] = new_line
        else:
            # Add a new typing import line
            # Find where to insert (after other imports)
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith(('import ', 'from ')):
                    insert_index = i + 1
                elif line.strip() == '' and i > 0 and lines[i-1].startswith(('import ', 'from ')):
                    insert_index = i
                    break
            
            new_import_line = f"            lines.insert(insert_index, new_import_line)
        
        # Write back
        new_content = '\n'.join(lines)
        if new_content != content:
            file_path.write_text(new_content, encoding='utf-8')
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def fix_datetime_usage(file_path: Path) -> bool:
    """Fix datetime.now() usage"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check if file uses datetime.now() but imports datetime
        if 'datetime.now()' in content:
            lines = content.split('\n')
            has_datetime_import = any('import datetime' in line for line in lines)
            
            if has_datetime_import:
                # Replace datetime.now() with datetime.now()
                new_content = content.replace('datetime.now()', 'datetime.now()')
                if new_content != content:
                    file_path.write_text(new_content, encoding='utf-8')
                    return True
                    
    except Exception:
        pass
    
    return False

def remove_unused_mock_imports(file_path: Path) -> bool:
    """Remove Mock imports that aren't used"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Check if Mock is imported but not used
from unittest.mock import Mock, patch, MagicMock
        if not has_mock_import:
            return False
            
        # Check usage
        uses_mock = 'Mock(' in content or 'Mock.' in content
        uses_patch = '@patch' in content or 'patch(' in content or 'with patch' in content
        uses_magic_mock = 'MagicMock(' in content or 'MagicMock.' in content
        
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
                imports = []
                if uses_mock:
                    imports.append('Mock')
                if uses_patch:
                    imports.append('patch')
                if uses_magic_mock:
                    imports.append('MagicMock')
                
                if imports:
                    if new_line != line:
                        lines[i] = new_line
                        modified = True
                else:
                    # Remove the line entirely
                    lines[i] = ''
                    modified = True
        
        if modified:
            file_path.write_text('\n'.join(lines), encoding='utf-8')
            return True
            
    except Exception:
        pass
    
    return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        target_dir = Path('.')
    
    print(f"Aggressively fixing typing imports in: {target_dir}")
    
    total_fixes = 0
    files_processed = 0
    
    for py_file in target_dir.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', '.git', 'node_modules']):
            continue
        
        files_processed += 1
        file_fixes = 0
        
        try:
            if fix_typing_imports_aggressively(py_file):
                file_fixes += 1
                print(f"  Fixed typing imports: {py_file}")
            
            if fix_datetime_usage(py_file):
                file_fixes += 1
                print(f"  Fixed datetime usage: {py_file}")
                
            if remove_unused_mock_imports(py_file):
                file_fixes += 1
                print(f"  Cleaned up mock imports: {py_file}")
            
            total_fixes += file_fixes
            
        except Exception as e:
            print(f"  Error processing {py_file}: {e}")
    
    print(f"\nProcessed {files_processed} files")
    print(f"Applied {total_fixes} fixes")

if __name__ == '__main__':
    main()