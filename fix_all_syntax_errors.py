#!/usr/bin/env python3
"""
Comprehensive syntax error fixer for all Python files.
Identifies and fixes common syntax patterns that cause errors.
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Tuple

def find_syntax_errors() -> List[Tuple[str, int, str]]:
    """Find all files with syntax errors."""
    errors = []
    
    for root, dirs, files in os.walk('.'):
        # Skip version control and virtual environment directories
        if any(skip in root for skip in ['.git', '.venv', '__pycache__', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        ast.parse(content)
                except SyntaxError as e:
                    errors.append((path, e.lineno or 0, e.msg or 'Unknown error'))
    
    return errors

def fix_unmatched_parenthesis(content: str, line_num: int) -> str:
    """Fix unmatched parenthesis errors."""
    lines = content.split('\n')
    
    if line_num > 0 and line_num <= len(lines):
        line_idx = line_num - 1
        line = lines[line_idx]
        
        # Pattern 1: Extra closing parenthesis at end of line
        if line.rstrip().endswith('))') and line.count('(') < line.count(')'):
            lines[line_idx] = line.rstrip()[:-1]
            return '\n'.join(lines)
        
        # Pattern 2: Extra closing parenthesis in middle of expression
        if line.count(')') > line.count('('):
            # Find and remove the first unmatched closing parenthesis
            open_count = 0
            new_line = []
            removed = False
            
            for char in line:
                if char == '(':
                    open_count += 1
                    new_line.append(char)
                elif char == ')':
                    if open_count > 0:
                        open_count -= 1
                        new_line.append(char)
                    elif not removed:
                        # Skip this unmatched closing parenthesis
                        removed = True
                    else:
                        new_line.append(char)
                else:
                    new_line.append(char)
            
            if removed:
                lines[line_idx] = ''.join(new_line)
                return '\n'.join(lines)
    
    return content

def fix_file_syntax(file_path: str) -> bool:
    """Fix syntax errors in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Try to parse and identify the specific error
        try:
            ast.parse(content)
            return True  # No syntax error
        except SyntaxError as e:
            if "unmatched ')'" in str(e.msg):
                content = fix_unmatched_parenthesis(content, e.lineno or 0)
            else:
                # For other syntax errors, try common fixes
                
                # Fix malformed list comprehensions with extra brackets
                content = re.sub(
                    r'\[\s*([a-zA-Z_]\w*)\s+for\s+([a-zA-Z_]\w*)\s+in\s+([a-zA-Z_]\w*(?:\.\w+)*(?:\([^)]*\))?)\s+if\s+([^]]+)\]\]',
                    r'[\1 for \2 in \3 if \4]',
                    content
                )
                
                # Fix conditional assignments with improper parenthesis
                content = re.sub(
                    r'\(([^)]+)\s+if\s+([^)]+)\s+else\s+None\)\s*=\s*([^;]+)',
                    r'if \2:\n    \1 = \3',
                    content
                )
        
        # Verify the fix worked
        try:
            ast.parse(content)
            
            # Only write if content changed and is now valid
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ Fixed: {file_path}")
                return True
            return True
            
        except SyntaxError:
            # If still has errors, try line-by-line analysis
            lines = content.split('\n')
            fixed_lines = []
            
            for i, line in enumerate(lines):
                # Remove trailing 's' character that was mistakenly added
                if line.rstrip().endswith(')s'):
                    line = line.rstrip()[:-1]
                
                # Fix double closing brackets in list comprehensions
                line = re.sub(r'\]\]$', ']', line)
                
                # Fix conditional expressions used as assignment targets
                if '= None) =' in line or 'else None) =' in line:
                    # This is likely a broken conditional assignment
                    parts = line.split('=')
                    if len(parts) >= 3:
                        # Reconstruct as proper if statement
                        var_part = parts[0].strip()
                        if '(' in var_part:
                            var_name = var_part.split('(')[0].strip()
                            condition = var_part.split('if')[1].split('else')[0].strip() if 'if' in var_part else ''
                            value = parts[-1].strip()
                            if condition:
                                line = f"    if {condition}:\n        {var_name} = {value}"
                
                fixed_lines.append(line)
            
            content = '\n'.join(fixed_lines)
            
            # Final verification
            try:
                ast.parse(content)
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✓ Fixed: {file_path}")
                    return True
            except:
                print(f"✗ Could not fix: {file_path}")
                return False
                
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False
    
    return True

def main():
    """Main function to fix all syntax errors."""
    print("Scanning for syntax errors...")
    errors = find_syntax_errors()
    
    if not errors:
        print("No syntax errors found!")
        return
    
    print(f"\nFound {len(errors)} files with syntax errors")
    print("=" * 60)
    
    fixed = 0
    failed = []
    
    for file_path, line_num, error_msg in errors:
        print(f"\nProcessing: {file_path}:{line_num}")
        print(f"  Error: {error_msg}")
        
        if fix_file_syntax(file_path):
            fixed += 1
        else:
            failed.append((file_path, line_num, error_msg))
    
    print("\n" + "=" * 60)
    print(f"Results: Fixed {fixed}/{len(errors)} files")
    
    if failed:
        print(f"\nFailed to fix {len(failed)} files:")
        for file_path, line_num, error_msg in failed[:10]:
            print(f"  - {file_path}:{line_num} - {error_msg}")
        
        # Save failed files for manual inspection
        with open('.task/syntax_errors_remaining.txt', 'w') as f:
            for file_path, line_num, error_msg in failed:
                f.write(f"{file_path}:{line_num}: {error_msg}\n")
        print(f"\nSaved remaining errors to .task/syntax_errors_remaining.txt")

if __name__ == "__main__":
    main()