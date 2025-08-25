#!/usr/bin/env python3
"""Fix final syntax errors in list comprehensions."""

import re
from pathlib import Path

# Fix list comprehensions with wrong syntax: "if p is not None:\n    p.status"
# Should be: "if p is not None and p.status"

files_with_errors = [
    '.claude/orchestrator/process_registry.py',
    '.claude/agents/workflow-master-enhanced.py',
    '.claude/agents/pr-backlog-manager/core.py',
    '.claude/agents/pr-backlog-manager/delegation_coordinator.py',
]

for file_path in files_with_errors:
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        continue
        
    lines = path.read_text().split('\n')
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for pattern: list comprehension with "if x is not None:" on one line
        # and condition on next line
        if 'for' in line and 'if' in line and line.strip().endswith(':'):
            # This is a broken list comprehension
            # Get the next line which should have the condition
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                # Extract the condition from the next line
                condition = next_line.strip()
                
                # Fix the list comprehension
                # Remove the colon and combine with condition
                fixed_line = line.rstrip(':') + ' and ' + condition + ']'
                new_lines.append(fixed_line)
                i += 2  # Skip the next line since we combined it
                continue
        
        new_lines.append(line)
        i += 1
    
    # Write back
    path.write_text('\n'.join(new_lines))
    print(f"Fixed: {file_path}")

# Verify
import ast
errors = []
for py_file in Path('.claude').glob('**/*.py'):
    try:
        with open(py_file) as f:
            ast.parse(f.read())
    except SyntaxError as e:
        errors.append(f'{py_file}: line {e.lineno}: {e.msg}')

if errors:
    print(f"\nStill {len(errors)} syntax errors:")
    for e in errors[:10]:
        print(e)
else:
    print("\n✅ All syntax errors fixed!")