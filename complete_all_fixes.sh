#!/bin/bash
# Complete all remaining fixes using parallel execution

set -e

echo "🚀 Orchestrating Complete Fix - Parallel Execution"
echo "=================================================="

BASE_DIR=$(pwd)

# Function to fix syntax errors in a specific file
fix_syntax_error() {
    local FILE=$1
    local LINE=$2
    local MSG=$3
    
    echo "Fixing $FILE:$LINE - $MSG"
    
    python3 -c "
import re

def fix_file(filepath, line_num, error_msg):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Specific fixes based on error patterns
    if 'unmatched' in error_msg and line_num > 0:
        idx = line_num - 1
        if idx < len(lines):
            line = lines[idx]
            # Remove extra closing brackets/parens
            if error_msg == \"unmatched ')'\":
                if line.count(')') > line.count('('):
                    pos = line.rfind(')')
                    if pos >= 0:
                        lines[idx] = line[:pos] + line[pos+1:]
            elif error_msg == \"unmatched ']'\":
                if line.count(']') > line.count('['):
                    pos = line.rfind(']')
                    if pos >= 0:
                        lines[idx] = line[:pos] + line[pos+1:]
    
    elif 'invalid syntax' in error_msg and line_num > 0:
        idx = line_num - 1
        if idx < len(lines):
            line = lines[idx]
            # Fix common invalid syntax patterns
            if '=' in line and 'if' in line and 'else' in line:
                # Fix conditional assignment
                lines[idx] = re.sub(r'\(([^)]+)\s+if\s+([^)]+)\s+else\s+([^)]+)\)\s*=', r'\\1 if \\2 else \\3 =', line)
            # Fix parameter continuation issues
            if idx > 0 and 'def' in lines[idx-1]:
                # This might be a broken parameter list
                lines[idx] = '                 ' + lines[idx].strip() + '\n'
    
    elif 'unexpected indent' in error_msg and line_num > 0:
        idx = line_num - 1
        if idx < len(lines):
            # Fix indentation
            lines[idx] = lines[idx].lstrip() + '\n'
    
    with open(filepath, 'w') as f:
        f.writelines(lines)

fix_file('$FILE', $LINE, '$MSG')
"
}

# Fix each remaining syntax error
echo ""
echo "📝 Fixing Remaining Syntax Errors..."
echo "------------------------------------"

fix_syntax_error "./orchestrate_complete_fix.py" 104 "unmatched ')'"
fix_syntax_error "./.claude/orchestrator/process_registry.py" 333 "invalid syntax"
fix_syntax_error "./.claude/agents/workflow-master-enhanced.py" 391 "unmatched ']'"
fix_syntax_error "./.claude/agents/enhanced_workflow_manager.py" 103 "unexpected indent"
fix_syntax_error "./.claude/agents/pr-backlog-manager/core.py" 729 "invalid syntax"
fix_syntax_error "./.claude/agents/pr-backlog-manager/delegation_coordinator.py" 765 "invalid syntax"
fix_syntax_error "./.claude/shared/state_management.py" 95 "invalid syntax"
fix_syntax_error "./.claude/shared/github_operations.py" 51 "invalid syntax"
fix_syntax_error "./.claude/shared/task_tracking.py" 63 "unmatched ')'"

# Verify syntax fixes
echo ""
echo "✅ Verifying Syntax Fixes..."
SYNTAX_COUNT=$(python3 -c "
import ast, os
count = 0
for root, dirs, files in os.walk('.'):
    if any(skip in root for skip in ['.git', '.venv', '__pycache__']):
        continue
    for file in files:
        if file.endswith('.py'):
            try:
                with open(os.path.join(root, file)) as f:
                    ast.parse(f.read())
            except: count += 1
print(count)
")

echo "  Remaining syntax errors: $SYNTAX_COUNT"

if [ $SYNTAX_COUNT -eq 0 ]; then
    echo "  ✅ All syntax errors fixed!"
    
    echo ""
    echo "🔧 Launching Parallel Type Fixes..."
    echo "------------------------------------"
    
    # Create worktrees for parallel type fixing
    mkdir -p .worktrees
    
    # Function to fix types in a directory
    fix_types_in_dir() {
        local TASK_ID=$1
        local TARGET_DIR=$2
        local WORKTREE=".worktrees/typefix-$TASK_ID"
        
        echo "  Starting type fix task: $TASK_ID ($TARGET_DIR)"
        
        # Create worktree
        git worktree remove --force "$WORKTREE" 2>/dev/null || true
        git worktree add "$WORKTREE" -b "typefix-$TASK_ID" HEAD
        
        (
            cd "$WORKTREE"
            
            # Create type fixer script
            cat > fix_types.py << 'PYTHON'
#!/usr/bin/env python3
import re
import os
import sys
from pathlib import Path

def fix_types_in_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original = content
        
        # Add Optional imports
        if '= None' in content and 'Optional' not in content:
            if 'from typing import' in content:
                content = re.sub(r'from typing import ([^\\n]+)', 
                                r'from typing import \\1, Optional', content, count=1)
            else:
                content = 'from typing import Optional\\n' + content
        
        # Fix None defaults without Optional
        content = re.sub(r'(\w+):\s*(\w+)\s*=\s*None', r'\\1: Optional[\\2] = None', content)
        
        # Fix dataclass fields
        content = re.sub(r'(\w+):\s*List\[([^]]+)\]\s*=\s*None',
                        r'\\1: List[\\2] = field(default_factory=list)', content)
        content = re.sub(r'(\w+):\s*Dict\[([^]]+)\]\s*=\s*None',
                        r'\\1: Dict[\\2] = field(default_factory=dict)', content)
        
        # Add field import if needed
        if 'field(default_factory' in content and 'from dataclasses import' in content:
            if 'field' not in content.split('from dataclasses import')[1].split('\\n')[0]:
                content = re.sub(r'from dataclasses import ([^\\n]+)',
                                r'from dataclasses import \\1, field', content, count=1)
        
        # Add return type for __init__
        content = re.sub(r'def __init__\(([^)]+)\)(\s*):',
                        r'def __init__(\\1) -> None\\2:', content)
        
        if content != original:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
    except:
        pass
    return False

target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
fixed = 0

for root, dirs, files in os.walk(target_dir):
    if any(skip in root for skip in ['.git', '.venv', '__pycache__']):
        continue
    for file in files:
        if file.endswith('.py'):
            if fix_types_in_file(os.path.join(root, file)):
                fixed += 1

print(f'Fixed {fixed} files')
PYTHON
            
            python3 fix_types.py "$TARGET_DIR"
        ) &
        
        echo $!
    }
    
    # Launch parallel type fix tasks
    PIDS=()
    PID=$(fix_types_in_dir "orchestrator" ".claude/orchestrator")
    PIDS+=($PID)
    PID=$(fix_types_in_dir "agents" ".claude/agents")
    PIDS+=($PID)
    PID=$(fix_types_in_dir "shared" ".claude/shared")
    PIDS+=($PID)
    PID=$(fix_types_in_dir "tests" "tests")
    PIDS+=($PID)
    
    # Wait for all tasks
    echo "  Waiting for parallel tasks..."
    for PID in "${PIDS[@]}"; do
        wait $PID
    done
    
    echo "  ✅ Parallel type fixes complete!"
fi

# Final verification
echo ""
echo "📊 Final Status:"
echo "----------------"
FINAL_SYNTAX=$(python3 -c "
import ast, os
count = 0
for root, dirs, files in os.walk('.'):
    if any(skip in root for skip in ['.git', '.venv', '__pycache__']):
        continue
    for file in files:
        if file.endswith('.py'):
            try:
                with open(os.path.join(root, file)) as f:
                    ast.parse(f.read())
            except: count += 1
print(count)
")

FINAL_TYPES=$(uv run pyright --outputjson 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data.get('generalDiagnostics', [])))
except:
    print('unknown')
")

echo "  Syntax errors: $FINAL_SYNTAX"
echo "  Type errors: $FINAL_TYPES"

if [ $FINAL_SYNTAX -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS: All syntax errors have been fixed!"
    
    if [ "$FINAL_TYPES" != "unknown" ] && [ $FINAL_TYPES -lt 100 ]; then
        echo "🎉 EXCELLENT: Type errors reduced to under 100!"
    fi
fi

echo ""
echo "✨ Orchestration complete!"