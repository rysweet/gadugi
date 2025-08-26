#!/usr/bin/env python3
"""
Fix the specific __init__ method syntax errors with double closing parentheses.
"""

import re
from pathlib import Path

def fix_init_double_parens(file_path):
    """Fix __init__ methods with double closing parentheses."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Fix patterns like: def __init__(self, task_id=None)) -> None:
        # Should be: def __init__(self, task_id=None) -> None:
        content = re.sub(
            r'def __init__\(([^)]+)\)\) -> None:',
            r'def __init__(\1) -> None:',
            content
        )
        
        # Fix patterns like: def __init__(self)) -> None:
        # Should be: def __init__(self) -> None:
        content = re.sub(
            r'def __init__\(self\)\) -> None:',
            r'def __init__(self) -> None:',
            content
        )
        
        # Fix patterns with multiple parameters and double parens
        content = re.sub(
            r'def __init__\(([^)]+), ([^)]+)\)\) -> None:',
            r'def __init__(\1, \2) -> None:',
            content
        )
        
        # Fix simple class instantiation with double parens
        content = re.sub(
            r'([A-Z][a-zA-Z0-9_]*)\(\)\)',
            r'\1()',
            content
        )
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fixed: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"✗ Error: {file_path}: {e}")
        return False

def main():
    """Fix all files with __init__ syntax errors."""
    
    # Read the list of files with syntax errors
    files_to_fix = []
    
    if Path('.task/syntax_errors_remaining.txt').exists():
        with open('.task/syntax_errors_remaining.txt', 'r') as f:
            for line in f:
                if ':' in line:
                    file_path = line.split(':')[0].strip()
                    if file_path not in files_to_fix:
                        files_to_fix.append(file_path)
    
    # Also scan for common problematic files
    additional_files = [
        './.claude/orchestrator/orchestrator_main.py',
        './.claude/orchestrator/container_manager.py',
        './.claude/orchestrator/orchestrator_cli.py',
        './.claude/orchestrator/process_registry.py',
        './.claude/agents/workflow-master-enhanced.py',
        './.claude/agents/pr-backlog-manager/core.py',
        './.claude/agents/pr-backlog-manager/delegation_coordinator.py',
        './.claude/shared/state_management.py',
        './.claude/shared/github_operations.py',
        './.claude/shared/base_classes.py',
        './.claude/shared/task_tracking.py',
    ]
    
    for file in additional_files:
        if Path(file).exists() and file not in files_to_fix:
            files_to_fix.append(file)
    
    fixed_count = 0
    for file_path in files_to_fix:
        if Path(file_path).exists():
            if fix_init_double_parens(file_path):
                fixed_count += 1
    
    print(f"\nFixed {fixed_count}/{len(files_to_fix)} files")

if __name__ == "__main__":
    main()