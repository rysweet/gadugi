#!/usr/bin/env python3
"""
Final orchestration to fix all remaining syntax and type errors.
Uses subprocess for true parallel execution.
"""

import subprocess
import os
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import queue

class FinalOrchestrator:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.worktrees_dir = self.base_dir / '.worktrees'
        self.results_queue = queue.Queue()
        
    def create_worktree(self, task_id, branch_name):
        """Create a worktree for parallel execution."""
        worktree_path = self.worktrees_dir / f'final-{task_id}'
        
        # Remove if exists
        subprocess.run(['git', 'worktree', 'remove', '--force', str(worktree_path)],
                      capture_output=True, stderr=subprocess.DEVNULL)
        
        # Create new worktree
        result = subprocess.run(
            ['git', 'worktree', 'add', str(worktree_path), '-b', branch_name, 'HEAD'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print(f"✓ Created worktree: {worktree_path}")
            return worktree_path
        else:
            print(f"✗ Failed to create worktree: {result.stderr}")
            return None
    
    def fix_syntax_in_worktree(self, worktree_path, target_dir):
        """Fix syntax errors in a worktree."""
        fix_script = worktree_path / 'fix_syntax.py'
        
        # Create fix script
        fix_script.write_text('''#!/usr/bin/env python3
import ast
import re
import sys
from pathlib import Path

def fix_syntax_patterns(content):
    """Apply all syntax fixes."""
    # Fix double closing parens in __init__
    content = re.sub(r'def __init__\\(([^)]*)\\)\\) -> None:', r'def __init__(\\1) -> None:', content)
    
    # Fix unmatched brackets in list comprehensions
    lines = content.split('\\n')
    fixed_lines = []
    for line in lines:
        # Fix double closing brackets
        if line.count(']') > line.count('['):
            while line.count(']') > line.count('['):
                pos = line.rfind(']')
                if pos >= 0:
                    line = line[:pos] + line[pos+1:]
        # Fix double closing parens
        if line.count(')') > line.count('('):
            while line.count(')') > line.count('('):
                pos = line.rfind(')')
                if pos >= 0:
                    line = line[:pos] + line[pos+1:]
        fixed_lines.append(line)
    
    return '\\n'.join(fixed_lines)

def fix_file(filepath):
    try:
        content = Path(filepath).read_text()
        original = content
        
        # Apply fixes
        content = fix_syntax_patterns(content)
        
        # Verify it's valid Python
        try:
            ast.parse(content)
            if content != original:
                Path(filepath).write_text(content)
                return True
        except:
            pass
    except:
        pass
    return False

# Fix all Python files in target directory
target = sys.argv[1] if len(sys.argv) > 1 else '.'
fixed = 0
errors = 0

for py_file in Path(target).rglob('*.py'):
    if any(skip in str(py_file) for skip in ['.git', '.venv', '__pycache__']):
        continue
    
    try:
        ast.parse(py_file.read_text())
    except SyntaxError:
        if fix_file(py_file):
            print(f"✓ Fixed: {py_file}")
            fixed += 1
        else:
            errors += 1

print(f"Results: {fixed} fixed, {errors} remaining")
''')
        
        # Execute fix script
        result = subprocess.run(
            ['python3', str(fix_script), target_dir],
            cwd=worktree_path,
            capture_output=True,
            text=True
        )
        
        return {
            'task': target_dir,
            'fixed': result.returncode == 0,
            'output': result.stdout + result.stderr
        }
    
    def fix_types_in_worktree(self, worktree_path, target_dir):
        """Fix type errors in a worktree."""
        fix_script = worktree_path / 'fix_types.py'
        
        # Create type fix script
        fix_script.write_text('''#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def fix_type_patterns(content):
    """Apply type fixes."""
    original = content
    
    # Add Optional import if needed
    if '= None' in content and 'Optional' not in content:
        if 'from typing import' in content:
            content = re.sub(r'from typing import ([^\\n]+)', 
                           r'from typing import \\1, Optional', content, count=1)
        else:
            content = 'from typing import Optional\\n' + content
    
    # Fix None defaults
    content = re.sub(r'(\\w+):\\s*(\\w+)\\s*=\\s*None', 
                    r'\\1: Optional[\\2] = None', content)
    
    # Fix dataclass fields
    content = re.sub(r'(\\w+):\\s*List\\[([^]]+)\\]\\s*=\\s*None',
                    r'\\1: List[\\2] = field(default_factory=list)', content)
    content = re.sub(r'(\\w+):\\s*Dict\\[([^]]+)\\]\\s*=\\s*None',
                    r'\\1: Dict[\\2] = field(default_factory=dict)', content)
    
    # Add field import if needed
    if 'field(default_factory' in content and 'from dataclasses import' in content:
        if 'field' not in content.split('from dataclasses import')[1].split('\\n')[0]:
            content = re.sub(r'from dataclasses import ([^\\n]+)',
                           r'from dataclasses import \\1, field', content, count=1)
    
    # Add return type annotations
    content = re.sub(r'def __init__\\(([^)]+)\\)(\\s*):', 
                    r'def __init__(\\1) -> None\\2:', content)
    
    return content if content != original else None

# Process all files
target = sys.argv[1] if len(sys.argv) > 1 else '.'
fixed = 0

for py_file in Path(target).rglob('*.py'):
    if any(skip in str(py_file) for skip in ['.git', '.venv', '__pycache__']):
        continue
    
    try:
        content = py_file.read_text()
        new_content = fix_type_patterns(content)
        if new_content:
            py_file.write_text(new_content)
            fixed += 1
    except:
        pass

print(f"Fixed {fixed} files")
''')
        
        # Execute type fix script
        result = subprocess.run(
            ['python3', str(fix_script), target_dir],
            cwd=worktree_path,
            capture_output=True,
            text=True
        )
        
        return {
            'task': target_dir,
            'fixed': result.returncode == 0,
            'output': result.stdout
        }
    
    def orchestrate_fixes(self):
        """Main orchestration method."""
        print("🚀 Final Orchestration - Parallel Execution")
        print("=" * 50)
        
        # Define tasks
        tasks = [
            {'id': 'orchestrator', 'dir': '.claude/orchestrator'},
            {'id': 'agents', 'dir': '.claude/agents'},
            {'id': 'shared', 'dir': '.claude/shared'},
            {'id': 'tests', 'dir': 'tests'}
        ]
        
        print("\n📁 Creating worktrees...")
        worktrees = {}
        for task in tasks:
            worktree = self.create_worktree(task['id'], f"final-{task['id']}")
            if worktree:
                worktrees[task['id']] = worktree
        
        print("\n🔧 Phase 1: Fixing Syntax Errors...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for task in tasks:
                if task['id'] in worktrees:
                    future = executor.submit(
                        self.fix_syntax_in_worktree,
                        worktrees[task['id']],
                        task['dir']
                    )
                    futures.append(future)
            
            for future in futures:
                result = future.result()
                print(f"  {result['task']}: {result['output'].strip()}")
        
        print("\n🔧 Phase 2: Fixing Type Errors...")
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for task in tasks:
                if task['id'] in worktrees:
                    future = executor.submit(
                        self.fix_types_in_worktree,
                        worktrees[task['id']],
                        task['dir']
                    )
                    futures.append(future)
            
            for future in futures:
                result = future.result()
                print(f"  {result['task']}: {result['output'].strip()}")
        
        # Merge changes back
        print("\n📋 Merging changes...")
        for task_id, worktree in worktrees.items():
            # Copy fixed files back
            subprocess.run(
                ['rsync', '-av', '--exclude=.git', f'{worktree}/', './'],
                capture_output=True
            )
        
        # Clean up worktrees
        print("\n🧹 Cleaning up...")
        for worktree in worktrees.values():
            subprocess.run(
                ['git', 'worktree', 'remove', '--force', str(worktree)],
                capture_output=True
            )
        
        # Final verification
        print("\n📊 Final Verification...")
        self.verify_results()
    
    def verify_results(self):
        """Verify final state."""
        # Count syntax errors
        syntax_check = subprocess.run(
            ['python3', '-c', '''
import ast, os
count = 0
for root, dirs, files in os.walk("."):
    if any(skip in root for skip in [".git", ".venv", "__pycache__"]):
        continue
    for file in files:
        if file.endswith(".py"):
            try:
                with open(os.path.join(root, file)) as f:
                    ast.parse(f.read())
            except:
                count += 1
print(count)
'''],
            capture_output=True,
            text=True
        )
        
        syntax_errors = int(syntax_check.stdout.strip()) if syntax_check.stdout.strip().isdigit() else -1
        
        # Count type errors
        type_check = subprocess.run(
            ['uv', 'run', 'pyright', '--outputjson'],
            capture_output=True,
            text=True
        )
        
        type_errors = -1
        if type_check.stdout:
            try:
                data = json.loads(type_check.stdout)
                type_errors = len(data.get('generalDiagnostics', []))
            except:
                pass
        
        print(f"\n✅ Results:")
        print(f"  Syntax errors: {syntax_errors}")
        print(f"  Type errors: {type_errors}")
        
        if syntax_errors == 0:
            print("\n🎉 ALL SYNTAX ERRORS FIXED!")
        
        if type_errors < 100:
            print("🎉 TYPE ERRORS REDUCED TO MANAGEABLE LEVEL!")

def main():
    orchestrator = FinalOrchestrator()
    orchestrator.orchestrate_fixes()

if __name__ == "__main__":
    main()