#!/usr/bin/env python3
"""
Fix mangled __init__ signatures that have multiple type annotations concatenated.
Pattern: def __init__(self, param1) -> None: type1, param2) -> None: type2)) -> None:
Should be: def __init__(self, param1: type1, param2: type2) -> None:
"""

import re
import ast
from pathlib import Path

def extract_params_from_mangled(line):
    """Extract parameters from a mangled __init__ line."""
    # Pattern to match the mangled signature
    # Example: def __init__(self, container_id) -> None: str, task_id) -> None: str)) -> None:
    
    # Try to extract all parameter names and types
    params = []
    
    # Find all patterns like "param_name) -> None: type_name"
    pattern = r'(\w+)\)\s*->\s*None:\s*(\w+)'
    matches = re.findall(pattern, line)
    
    for param_name, param_type in matches:
        params.append(f"{param_name}: {param_type}")
    
    if params:
        return f"def __init__(self, {', '.join(params)}) -> None:"
    
    return None

def fix_mangled_init_in_file(file_path):
    """Fix mangled __init__ signatures in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed = False
        new_lines = []
        
        for line in lines:
            # Check if this is a mangled __init__ line
            if 'def __init__' in line and line.count('->') > 1 and line.count('None') > 1:
                # This looks like a mangled signature
                fixed_line = extract_params_from_mangled(line)
                if fixed_line:
                    # Preserve indentation
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(' ' * indent + fixed_line + '\n')
                    fixed = True
                    print(f"  Fixed mangled __init__ in {file_path}")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        if fixed:
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        
        return False
        
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
        return False

def find_and_fix_all_mangled():
    """Find and fix all mangled __init__ signatures."""
    print("Searching for mangled __init__ signatures...")
    
    fixed_count = 0
    
    # Search all Python files
    for py_file in Path('.').rglob('*.py'):
        # Skip virtual environments
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git']):
            continue
        
        # Check if file has syntax errors
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            # No syntax error, skip
            continue
        except SyntaxError:
            # Has syntax error, check if it's a mangled __init__
            if fix_mangled_init_in_file(py_file):
                fixed_count += 1
    
    print(f"\nFixed {fixed_count} files with mangled __init__ signatures")
    return fixed_count

# Also fix other patterns
def fix_other_syntax_patterns(file_path):
    """Fix other common syntax error patterns."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Fix patterns where there's )) -> None: at the end of methods
        content = re.sub(
            r'def (\w+)\(([^)]*)\)\) -> None:',
            r'def \1(\2) -> None:',
            content
        )
        
        # Fix conditional assignments that are broken
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Fix lines with (expr if condition else None) = value
            if '=' in line and ' if ' in line and 'else None)' in line:
                # Check if it's an invalid assignment
                if re.search(r'\([^)]+\s+if\s+[^)]+\s+else\s+None\)\s*=', line):
                    # Extract components
                    match = re.search(r'(\s*)\(([^)]+)\s+if\s+([^)]+)\s+else\s+None\)\s*=\s*(.+)', line)
                    if match:
                        indent = match.group(1)
                        var = match.group(2)
                        condition = match.group(3)
                        value = match.group(4)
                        
                        # Convert to proper if statement
                        fixed_lines.append(f"{indent}if {condition}:")
                        fixed_lines.append(f"{indent}    {var} = {value}")
                        continue
            
            # Fix attribute access patterns
            line = re.sub(
                r'\(([^.]+)\.(\w+)\s+if\s+([^)]+)\s+is\s+not\s+None\s+else\s+None\)\s*=\s*(.+)',
                r'if \3 is not None: \1.\2 = \4',
                line
            )
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        if content != original:
            # Validate before saving
            try:
                ast.parse(content)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except:
                pass
        
        return False
        
    except Exception as e:
        return False

def main():
    """Main function."""
    print("🔧 Fixing Mangled Signatures and Syntax Errors")
    print("=" * 50)
    
    # First pass: fix mangled __init__ signatures
    mangled_fixed = find_and_fix_all_mangled()
    
    # Second pass: fix other syntax errors
    print("\nFixing other syntax patterns...")
    other_fixed = 0
    
    for py_file in Path('.').rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git']):
            continue
        
        try:
            with open(py_file, 'r') as f:
                ast.parse(f.read())
        except SyntaxError:
            if fix_other_syntax_patterns(py_file):
                print(f"  Fixed other patterns in {py_file}")
                other_fixed += 1
    
    print(f"\nTotal fixed: {mangled_fixed + other_fixed} files")
    
    # Check remaining syntax errors
    remaining = 0
    for py_file in Path('.').rglob('*.py'):
        if any(skip in str(py_file) for skip in ['.venv', '__pycache__', 'node_modules', '.git']):
            continue
        
        try:
            with open(py_file, 'r') as f:
                ast.parse(f.read())
        except SyntaxError:
            remaining += 1
    
    print(f"Remaining syntax errors: {remaining} files")

if __name__ == "__main__":
    main()