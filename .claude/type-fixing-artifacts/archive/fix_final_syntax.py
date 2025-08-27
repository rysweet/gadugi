#!/usr/bin/env python3
"""Fix the final 10 syntax errors."""

import re

fixes = [
    # File 1: orchestrate_complete_fix.py line 104
    {
        'file': './orchestrate_complete_fix.py',
        'line': 104,
        'fix': lambda lines: fix_line_104_orchestrate(lines)
    },
    # File 2: process_registry.py line 333
    {
        'file': './.claude/orchestrator/process_registry.py',
        'line': 333,
        'fix': lambda lines: fix_line_333_registry(lines)
    },
    # File 3: workflow-master-enhanced.py line 125
    {
        'file': './.claude/agents/workflow-master-enhanced.py',
        'line': 125,
        'fix': lambda lines: fix_line_125_workflow(lines)
    },
    # File 4: enhanced_workflow_manager.py line 103
    {
        'file': './.claude/agents/enhanced_workflow_manager.py',
        'line': 103,
        'fix': lambda lines: fix_line_103_enhanced(lines)
    },
    # File 5: pr-backlog-manager/core.py line 729
    {
        'file': './.claude/agents/pr-backlog-manager/core.py',
        'line': 729,
        'fix': lambda lines: fix_line_729_core(lines)
    },
    # File 6: delegation_coordinator.py line 765
    {
        'file': './.claude/agents/pr-backlog-manager/delegation_coordinator.py',
        'line': 765,
        'fix': lambda lines: fix_line_765_delegation(lines)
    },
    # File 7: state_management.py line 95
    {
        'file': './.claude/shared/state_management.py',
        'line': 95,
        'fix': lambda lines: fix_line_95_state(lines)
    },
    # File 8: github_operations.py line 51
    {
        'file': './.claude/shared/github_operations.py',
        'line': 51,
        'fix': lambda lines: fix_line_51_github(lines)
    },
    # File 9: task_tracking.py line 63
    {
        'file': './.claude/shared/task_tracking.py',
        'line': 63,
        'fix': lambda lines: fix_line_63_task(lines)
    }
]

def fix_line_104_orchestrate(lines):
    """Fix orchestrate_complete_fix.py line 104."""
    if len(lines) > 103 and ')' in lines[103]:
        # Remove extra closing paren
        lines[103] = lines[103].replace('))', ')')
    return lines

def fix_line_333_registry(lines):
    """Fix process_registry.py line 333."""
    if len(lines) > 332:
        # This likely has invalid syntax in a method or assignment
        # Check for common patterns
        line = lines[332]
        if '=' in line and ' if ' in line:
            # Fix conditional assignment
            lines[332] = re.sub(r'\(([^)]+)\s+if\s+([^)]+)\s+else\s+None\)\s*=', r'if \2: \1 =', line)
    return lines

def fix_line_125_workflow(lines):
    """Fix workflow-master-enhanced.py line 125."""
    if len(lines) > 124:
        # Fix unmatched bracket
        line = lines[124]
        if line.count(']') > line.count('['):
            # Remove extra closing bracket
            idx = line.rfind(']')
            if idx >= 0:
                lines[124] = line[:idx] + line[idx+1:]
    return lines

def fix_line_103_enhanced(lines):
    """Fix enhanced_workflow_manager.py line 103."""
    if len(lines) > 102:
        # Fix unexpected indent
        line = lines[102]
        # Remove leading spaces if it's incorrectly indented
        if line.startswith('        ') and not lines[101].rstrip().endswith(':'):
            lines[102] = line[4:]  # Remove 4 spaces
    return lines

def fix_line_729_core(lines):
    """Fix pr-backlog-manager/core.py line 729."""
    if len(lines) > 728:
        # Fix invalid syntax
        line = lines[728]
        # Common pattern: broken method call or assignment
        if 'if ' in line and 'else' in line:
            lines[728] = re.sub(r'\(([^)]+)\s+if\s+([^)]+)\s+else\s+([^)]+)\)', r'\1 if \2 else \3', line)
    return lines

def fix_line_765_delegation(lines):
    """Fix delegation_coordinator.py line 765."""
    if len(lines) > 764:
        # Similar fix for invalid syntax
        line = lines[764]
        if 'if ' in line and 'else' in line and '=' in line:
            lines[764] = re.sub(r'=\s*\(([^)]+)\s+if\s+([^)]+)\s+else\s+([^)]+)\)', r'= \1 if \2 else \3', line)
    return lines

def fix_line_95_state(lines):
    """Fix state_management.py line 95."""
    if len(lines) > 94:
        # Fix unmatched paren
        line = lines[94]
        if line.count(')') > line.count('('):
            idx = line.rfind(')')
            if idx >= 0:
                lines[94] = line[:idx] + line[idx+1:]
    return lines

def fix_line_51_github(lines):
    """Fix github_operations.py line 51."""
    if len(lines) > 50:
        # Fix unmatched paren
        line = lines[50]
        if line.count(')') > line.count('('):
            idx = line.rfind(')')
            if idx >= 0:
                lines[50] = line[:idx] + line[idx+1:]
    return lines

def fix_line_63_task(lines):
    """Fix task_tracking.py line 63 - broken __init__ continuation."""
    if len(lines) > 62 and len(lines) > 63:
        # Line 62 should be: def __init__(self, id: str, content: str,
        # Line 63 should be:              priority = TaskPriority.MEDIUM, title: str = None, **kwargs) -> None:
        if 'def __init__' in lines[62] and 'priority' in lines[63]:
            # Merge lines properly
            lines[62] = lines[62].rstrip() + ','
            lines[63] = '                 priority = TaskPriority.MEDIUM, title: str = None, **kwargs) -> None:'
    return lines

def fix_file(filepath, line_num, fix_func):
    """Fix a specific file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original = lines.copy()
        lines = fix_func(lines)
        
        if lines != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f"✓ Fixed {filepath}:{line_num}")
            return True
        else:
            print(f"✗ No change needed for {filepath}:{line_num}")
            return False
            
    except Exception as e:
        print(f"✗ Error fixing {filepath}:{line_num}: {e}")
        return False

def main():
    """Fix all remaining syntax errors."""
    print("Fixing final syntax errors...")
    print("=" * 50)
    
    fixed = 0
    for fix_info in fixes:
        if fix_file(fix_info['file'], fix_info['line'], fix_info['fix']):
            fixed += 1
    
    print(f"\nFixed {fixed}/{len(fixes)} files")

if __name__ == "__main__":
    main()