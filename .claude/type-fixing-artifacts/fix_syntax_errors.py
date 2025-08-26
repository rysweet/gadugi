#!/usr/bin/env python3
"""Fix all syntax errors from invalid conditional assignments."""

import re
from pathlib import Path

def fix_conditional_assignment(content: str) -> str:
    """Fix invalid conditional assignment patterns."""
    # Pattern: (expr if cond else val) = something
    pattern = r'\(([\w\.]+)\s+if\s+([\w\.]+)\s+is\s+not\s+None\s+else\s+None\)\s*=\s*(.+)'
    
    def replace_func(match):
        var = match.group(1)
        cond = match.group(2)
        value = match.group(3)
        
        # Generate proper if-else block
        # Assuming this is typically for attribute assignment
        if '.' in var:
            obj, attr = var.rsplit('.', 1)
            return f"if {cond} is not None:\n            {obj}.{attr} = {value}"
        else:
            return f"if {cond} is not None:\n            {var} = {value}"
    
    # Apply the fix
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if re.search(pattern, line):
            # Get indentation
            indent = len(line) - len(line.lstrip())
            fixed = re.sub(pattern, replace_func, line.lstrip())
            # Add proper indentation
            fixed_lines = fixed.split('\n')
            new_lines.append(' ' * indent + fixed_lines[0])
            if len(fixed_lines) > 1:
                new_lines.append(' ' * indent + fixed_lines[1])
        else:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

# Fix all files with syntax errors
files_to_fix = [
    '.claude/orchestrator/process_registry.py',
    '.claude/agents/workflow-master-enhanced.py', 
    '.claude/orchestrator/tests/test_containerized_execution.py',
    '.claude/orchestrator/tests/test_orchestrator_integration.py',
    '.claude/agents/pr-backlog-manager/core.py',
    '.claude/agents/pr-backlog-manager/delegation_coordinator.py'
]

for file_path in files_to_fix:
    path = Path(file_path)
    if path.exists():
        content = path.read_text()
        fixed_content = fix_conditional_assignment(content)
        if fixed_content != content:
            path.write_text(fixed_content)
            print(f"Fixed: {file_path}")
        else:
            print(f"No changes needed: {file_path}")
    else:
        print(f"File not found: {file_path}")

print("\nVerifying all syntax errors are fixed...")
import ast
errors = []
for py_file in Path('.claude').glob('**/*.py'):
    try:
        with open(py_file) as f:
            ast.parse(f.read())
    except SyntaxError as e:
        errors.append(f'{py_file}: line {e.lineno}')

if errors:
    print(f"Still {len(errors)} syntax errors remaining")
else:
    print("✅ All syntax errors fixed!")