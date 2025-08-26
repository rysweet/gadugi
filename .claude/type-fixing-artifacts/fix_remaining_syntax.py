#!/usr/bin/env python3
"""Fix remaining syntax errors from bad conditional patterns."""

import re
from pathlib import Path

# Files with remaining errors
files_to_fix = [
    '.claude/agents/pr-backlog-manager/core.py',
    '.claude/agents/pr-backlog-manager/delegation_coordinator.py',
    '.claude/agents/workflow-master-enhanced.py',
    '.claude/orchestrator/process_registry.py',
]

for file_path in files_to_fix:
    path = Path(file_path)
    if path.exists():
        content = path.read_text()
        
        # Fix double if statements: "if if condition:"
        content = re.sub(r'\bif\s+if\s+', 'if ', content)
        
        # Fix bad assignment patterns with excessive indentation
        content = re.sub(r'(\s+)if (\w+) is not None:\n\s+(\2\.\w+ =)', r'\1if \2 is not None:\n\1    \3', content)
        
        # Fix "= =" to just "=="
        content = re.sub(r'\s+=\s+=\s+', ' == ', content)
        
        path.write_text(content)
        print(f"Fixed: {file_path}")

# Verify
import ast
errors = []
for py_file in Path('.claude').glob('**/*.py'):
    try:
        with open(py_file) as f:
            ast.parse(f.read())
    except SyntaxError as e:
        errors.append(f'{py_file}: line {e.lineno}')

if errors:
    print(f"\nStill {len(errors)} syntax errors")
    for e in errors[:5]:
        print(e)
else:
    print("\n✅ All syntax errors fixed!")
