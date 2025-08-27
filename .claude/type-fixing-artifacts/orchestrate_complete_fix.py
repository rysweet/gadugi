#!/usr/bin/env python3
"""
Orchestrate complete fix of all syntax and type errors.
Divides work, executes in parallel, and iterates until done.
"""

import ast
import os
import re
import subprocess
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from dataclasses import dataclass
import threading

@dataclass
class FileError:
    """Represents an error in a file."""
    file_path: str
    line_num: int
    error_type: str
    error_msg: str

@dataclass 
class TaskResult:
    """Result of a fix task."""
    task_id: str
    files_processed: int
    errors_fixed: int
    errors_remaining: int
    success: bool
    message: str

class SyntaxFixer:
    """Fixes syntax errors in Python files."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = ""
        self.original_content = ""
        
    def load_file(self) -> bool:
        """Load file content."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.original_content = self.content
            return True
        except Exception as e:
            print(f"Error loading {self.file_path}: {e}")
            return False
    
    def fix_syntax(self) -> bool:
        """Apply all syntax fixes."""
        if not self.load_file():
            return False
            
        # Fix patterns in order of likelihood
        self.fix_double_closing_parens()
        self.fix_conditional_assignments()
        self.fix_list_comprehensions()
        self.fix_trailing_characters()
        self.fix_malformed_ternary()
        
        # Validate and save if fixed
        if self.content != self.original_content:
            try:
                ast.parse(self.content)
                self.save_file()
                return True
            except SyntaxError:
                # If still broken, try line-by-line fixes
                return self.fix_line_by_line()
        
        return False
    
    def fix_double_closing_parens(self):
        """Fix double closing parentheses."""
        # Fix __init__ methods with double parens
        self.content = re.sub(
            r'def __init__\(([^)]*)\)\) -> None:',
            r'def __init__(\1) -> None:',
            self.content
        )
        
        # Fix other methods with double parens
        self.content = re.sub(
            r'def (\w+)\(([^)]*)\)\) ->',
            r'def \1(\2) ->',
            self.content
        )
        
    def fix_conditional_assignments(self):
        """Fix invalid conditional assignments."""
        # Fix pattern: (expr if condition else None) = value
        lines = self.content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Check for invalid conditional assignment
            if ' = ' in line and ('(if ' in line or ' if ' in line) and 'else None)' in line:
                # Extract parts
                match = re.match(r'^(\s*)(.+?)\s*=\s*(.+)$', line)
                if match:
                    indent = match.group(1)
                    left = match.group(2)
                    right = match.group(3)
                    
                    # Check if left side is a conditional expression
                    if '(' in left and ' if ' in left and 'else None)' in left:
                        # Extract the actual variable and condition
                        var_match = re.match(r'\((.+?)\s+if\s+(.+?)\s+else\s+None\)', left)
                        if var_match:
                            var = var_match.group(1)
                            condition = var_match.group(2)
                            # Convert to proper if statement
                            fixed_lines.append(f"{indent}if {condition}:")
                            fixed_lines.append(f"{indent}    {var} = {right}")
                            continue
            
            fixed_lines.append(line)
        
        self.content = '\n'.join(fixed_lines)
    
    def fix_list_comprehensions(self):
        """Fix malformed list comprehensions."""
        # Fix double closing brackets
        self.content = re.sub(r'\]\](\s*[,\)])', r']\1', self.content)
        
        # Fix list comprehensions with syntax errors
        self.content = re.sub(
            r'\[([^]]+)\s+if\s+([^]]+):\s+([^]]+)\]\]',
            r'[\1 for \1 in items if \2]',
            self.content
        )
    
    def fix_trailing_characters(self):
        """Fix trailing 's' or other characters."""
        lines = self.content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Remove trailing 's' after closing parens
            line = re.sub(r'\)s(\s*[,;])', r')\1', line)
            line = re.sub(r'\)s$', r')', line)
            fixed_lines.append(line)
        
        self.content = '\n'.join(fixed_lines)
    
    def fix_malformed_ternary(self):
        """Fix malformed ternary operators."""
        # Fix patterns where ternary is used incorrectly
        self.content = re.sub(
            r'=\s*\(([^)]+)\s+if\s+([^)]+)\s+else\s+None\)\s*=',
            r'= \1 if \2 else None',
            self.content
        )
    
    def fix_line_by_line(self) -> bool:
        """Try to fix file line by line."""
        lines = self.content.split('\n')
        
        # Try to identify and fix specific line with error
        try:
            ast.parse(self.content)
            return True  # Already valid
        except SyntaxError as e:
            if e.lineno and e.lineno <= len(lines):
                line_idx = e.lineno - 1
                line = lines[line_idx]
                
                # Apply specific fixes based on error message
                if "unmatched ')'" in str(e.msg):
                    # Count parentheses and remove extra closing ones
                    open_count = line.count('(')
                    close_count = line.count(')')
                    if close_count > open_count:
                        # Remove rightmost closing paren
                        idx = line.rfind(')')
                        if idx >= 0:
                            lines[line_idx] = line[:idx] + line[idx+1:]
                
                elif "unmatched ']'" in str(e.msg):
                    # Similar for brackets
                    open_count = line.count('[')
                    close_count = line.count(']')
                    if close_count > open_count:
                        idx = line.rfind(']')
                        if idx >= 0:
                            lines[line_idx] = line[:idx] + line[idx+1:]
                
                self.content = '\n'.join(lines)
                
                # Verify fix
                try:
                    ast.parse(self.content)
                    self.save_file()
                    return True
                except:
                    return False
        
        return False
    
    def save_file(self):
        """Save fixed content to file."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(self.content)

class TypeFixer:
    """Fixes type errors in Python files."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def fix_types(self) -> bool:
        """Fix type errors in file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original = content
            
            # Fix common type patterns
            content = self.fix_optional_types(content)
            content = self.fix_dataclass_fields(content)
            content = self.fix_type_annotations(content)
            content = self.fix_none_checks(content)
            
            if content != original:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
                
        except Exception as e:
            print(f"Error fixing types in {self.file_path}: {e}")
        
        return False
    
    def fix_optional_types(self, content: str) -> str:
        """Add Optional types where needed."""
        # Add Optional import if missing
        if 'Optional' not in content and '= None' in content:
            if 'from typing import' in content:
                content = re.sub(
                    r'from typing import ([^\\n]+)',
                    r'from typing import \1, Optional',
                    content,
                    count=1
                )
            else:
                content = "from typing import Optional\n" + content
        
        # Fix function parameters with None defaults
        content = re.sub(
            r'def (\w+)\(([^)]*?)(\w+):\s*(\w+)\s*=\s*None',
            r'def \1(\2\3: Optional[\4] = None',
            content
        )
        
        return content
    
    def fix_dataclass_fields(self, content: str) -> str:
        """Fix dataclass field initialization."""
        # Fix list/dict fields initialized with None
        content = re.sub(
            r'(\w+):\s*List\[([^\]]+)\]\s*=\s*None',
            r'\1: List[\2] = field(default_factory=list)',
            content
        )
        
        content = re.sub(
            r'(\w+):\s*Dict\[([^\]]+)\]\s*=\s*None',
            r'\1: Dict[\2] = field(default_factory=dict)',
            content
        )
        
        # Add field import if needed
        if 'field(default_factory' in content and 'from dataclasses import' in content:
            if 'field' not in content.split('from dataclasses import')[1].split('\n')[0]:
                content = re.sub(
                    r'from dataclasses import ([^\\n]+)',
                    r'from dataclasses import \1, field',
                    content,
                    count=1
                )
        
        return content
    
    def fix_type_annotations(self, content: str) -> str:
        """Add missing type annotations."""
        # Add return type annotations for __init__
        content = re.sub(
            r'def __init__\(self([^)]*)\)(\s*):',
            r'def __init__(self\1) -> None\2:',
            content
        )
        
        # Add Any type for untyped parameters
        content = re.sub(
            r'def (\w+)\(([^)]*?)(\w+)(?!:)(?=,|\))',
            r'def \1(\2\3: Any',
            content
        )
        
        return content
    
    def fix_none_checks(self, content: str) -> str:
        """Fix None checking patterns."""
        # Fix attribute access on potentially None objects
        content = re.sub(
            r'(\w+)\.(\w+)\s*if\s+\1\s+else\s+None',
            r'\1.\2 if \1 is not None else None',
            content
        )
        
        return content

class OrchestrationEngine:
    """Main orchestration engine for parallel execution."""
    
    def __init__(self):
        self.syntax_errors: List[FileError] = []
        self.type_errors: List[FileError] = []
        self.results: List[TaskResult] = []
        self.lock = threading.Lock()
        
    def scan_syntax_errors(self) -> List[FileError]:
        """Scan for all syntax errors."""
        errors = []
        
        for root, _, files in os.walk('.'):
            # Skip virtual environments and git
            if any(skip in root for skip in ['.git', '.venv', '__pycache__', 'node_modules']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            ast.parse(f.read())
                    except SyntaxError as e:
                        errors.append(FileError(
                            file_path=path,
                            line_num=e.lineno or 0,
                            error_type='syntax',
                            error_msg=str(e.msg)
                        ))
        
        self.syntax_errors = errors
        return errors
    
    def group_errors_by_directory(self, errors: List[FileError]) -> Dict[str, List[FileError]]:
        """Group errors by parent directory for parallel processing."""
        groups = {}
        
        for error in errors:
            # Get parent directory
            parent = str(Path(error.file_path).parent)
            if parent not in groups:
                groups[parent] = []
            groups[parent].append(error)
        
        return groups
    
    def fix_syntax_group(self, group_id: str, errors: List[FileError]) -> TaskResult:
        """Fix a group of syntax errors."""
        fixed = 0
        remaining = 0
        
        for error in errors:
            fixer = SyntaxFixer(error.file_path)
            if fixer.fix_syntax():
                fixed += 1
                print(f"✓ Fixed syntax in {error.file_path}")
            else:
                remaining += 1
                print(f"✗ Could not fix {error.file_path}")
        
        return TaskResult(
            task_id=group_id,
            files_processed=len(errors),
            errors_fixed=fixed,
            errors_remaining=remaining,
            success=remaining == 0,
            message=f"Fixed {fixed}/{len(errors)} syntax errors in {group_id}"
        )
    
    def fix_type_errors_parallel(self) -> int:
        """Fix type errors in parallel after syntax is fixed."""
        # Get all Python files
        py_files = []
        for root, _, files in os.walk('.'):
            if any(skip in root for skip in ['.git', '.venv', '__pycache__']):
                continue
            for file in files:
                if file.endswith('.py'):
                    py_files.append(os.path.join(root, file))
        
        fixed_count = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            
            for file_path in py_files:
                future = executor.submit(self.fix_single_file_types, file_path)
                futures.append(future)
            
            for future in as_completed(futures):
                if future.result():
                    fixed_count += 1
        
        return fixed_count
    
    def fix_single_file_types(self, file_path: str) -> bool:
        """Fix types in a single file."""
        fixer = TypeFixer(file_path)
        return fixer.fix_types()
    
    def run_orchestration(self):
        """Main orchestration loop."""
        iteration = 0
        max_iterations = 10
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"ITERATION {iteration}")
            print(f"{'='*60}")
            
            # Step 1: Scan for syntax errors
            print("\n📊 Scanning for syntax errors...")
            syntax_errors = self.scan_syntax_errors()
            
            if not syntax_errors:
                print("✅ No syntax errors found!")
                
                # Step 2: Run pyright to get type error count
                print("\n📊 Checking type errors...")
                type_error_count = self.get_type_error_count()
                
                if type_error_count == 0:
                    print("🎉 ALL ERRORS FIXED! Zero syntax and type errors!")
                    break
                
                print(f"Found {type_error_count} type errors")
                
                # Step 3: Fix type errors in parallel
                print("\n🔧 Fixing type errors in parallel...")
                fixed = self.fix_type_errors_parallel()
                print(f"Modified {fixed} files for type fixes")
                
                # Continue to next iteration
                continue
            
            print(f"Found {len(syntax_errors)} files with syntax errors")
            
            # Group errors by directory
            error_groups = self.group_errors_by_directory(syntax_errors)
            print(f"Grouped into {len(error_groups)} parallel tasks")
            
            # Fix syntax errors in parallel
            print("\n🔧 Fixing syntax errors in parallel...")
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {}
                
                for group_id, errors in error_groups.items():
                    future = executor.submit(self.fix_syntax_group, group_id, errors)
                    futures[future] = group_id
                
                for future in as_completed(futures):
                    result = future.result()
                    self.results.append(result)
                    print(f"  {result.message}")
            
            # Check if we made progress
            remaining_syntax = sum(r.errors_remaining for r in self.results if r.task_id in error_groups)
            if remaining_syntax == len(syntax_errors):
                print("\n⚠️ No progress made in this iteration, stopping")
                break
        
        # Final summary
        self.print_summary()
    
    def get_type_error_count(self) -> int:
        """Get current pyright error count."""
        try:
            result = subprocess.run(
                ['uv', 'run', 'pyright', '--outputjson'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 or result.stdout:
                data = json.loads(result.stdout)
                return len(data.get('generalDiagnostics', []))
        except Exception as e:
            print(f"Error running pyright: {e}")
        
        return -1
    
    def print_summary(self):
        """Print final summary."""
        print("\n" + "="*60)
        print("ORCHESTRATION COMPLETE")
        print("="*60)
        
        # Count final errors
        final_syntax = len(self.scan_syntax_errors())
        final_types = self.get_type_error_count()
        
        print(f"\n📊 Final Status:")
        print(f"  Syntax errors: {final_syntax}")
        print(f"  Type errors: {final_types}")
        
        if final_syntax == 0 and final_types == 0:
            print("\n🎉 SUCCESS! All errors have been fixed!")
        elif final_syntax == 0:
            print(f"\n✅ All syntax errors fixed! {final_types} type errors remain")
        else:
            print(f"\n⚠️ {final_syntax} syntax errors and {final_types} type errors remain")

def main():
    """Main entry point."""
    print("🚀 Starting Complete Error Fix Orchestration")
    print("This will run in parallel and iterate until all errors are fixed")
    
    engine = OrchestrationEngine()
    engine.run_orchestration()

if __name__ == "__main__":
    main()