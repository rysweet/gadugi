import re

#!/usr/bin/env python3

"""
Fix datetime.now() errors introduced by aggressive fixing
"""

from pathlib import Path

def fix_datetime_double_reference(file_path: Path) -> bool:
    """Fix datetime.now() back to datetime.now()"""
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # Fix double datetime reference
        new_content = content.replace('datetime.now()', 'datetime.now()')
        
        if new_content != content:
            file_path.write_text(new_content, encoding='utf-8')
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def remove_unused_imports(file_path: Path) -> bool:
    """Remove truly unused imports"""
    try:
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        modified = False
        
        for i, line in enumerate(lines):
            # Remove unused Set imports
            if 'from typing import ' in line and 'Set' in line:
                # Check if Set is actually used
                if 'Set[' not in content and 'Set(' not in content:
                    # Remove Set from the import
                    new_line = re.sub(r',?\s*Set\s*,?', '', line)
                    new_line = re.sub(r'from typing import\s*,', 'from typing import', new_line)
                    new_line = re.sub(r',\s*$', '', new_line)
                    
                    if new_line != line:
                        lines[i] = new_line
                        modified = True
            
            # Remove unused Mock imports
            if 'from unittest.mock import' in line and 'Mock' in line:
                # Check if Mock is actually used
                if 'Mock(' not in content and 'Mock.' not in content:
                    # Remove Mock from the import
                    new_line = re.sub(r',?\s*Mock\s*,?', '', line)
                    new_line = re.sub(r'from unittest.mock import\s*,', 'from unittest.mock import', new_line)
                    new_line = re.sub(r',\s*$', '', new_line)
                    
                    # If the line becomes empty, remove it
                    if 'from unittest.mock import' in new_line and new_line.strip().endswith('import'):
                        new_line = ''
                    
                    if new_line != line:
                        lines[i] = new_line
                        modified = True
        
        if modified:
            file_path.write_text('\n'.join(lines), encoding='utf-8')
            return True
            
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function"""
    target_dir = Path('.')
    
    print("Fixing datetime double reference errors...")
    
    total_fixes = 0
    files_processed = 0
    
    for py_file in target_dir.rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', '.git', 'node_modules']):
            continue
        
        files_processed += 1
        file_fixes = 0
        
        try:
            if fix_datetime_double_reference(py_file):
                file_fixes += 1
                print(f"  Fixed datetime: {py_file}")
            
            if remove_unused_imports(py_file):
                file_fixes += 1
                print(f"  Removed unused imports: {py_file}")
            
            total_fixes += file_fixes
            
        except Exception as e:
            print(f"  Error processing {py_file}: {e}")
    
    print(f"\nProcessed {files_processed} files")
    print(f"Applied {total_fixes} fixes")

if __name__ == '__main__':
    main()