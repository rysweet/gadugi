#!/bin/bash
# Parallel orchestration of syntax and type fixes using worktrees

set -e

echo "🚀 Starting Parallel Orchestration for Complete Error Fix"
echo "=================================================="

# Base directory
BASE_DIR=$(pwd)
WORKTREE_BASE="${BASE_DIR}/.worktrees"

# Create worktrees for parallel execution
echo "📁 Creating worktrees for parallel execution..."

# Function to create worktree and run fixes
create_and_fix() {
    local TASK_ID=$1
    local TARGET_DIR=$2
    local WORKTREE_PATH="${WORKTREE_BASE}/fix-${TASK_ID}"
    
    echo "[${TASK_ID}] Creating worktree..."
    
    # Remove if exists
    git worktree remove --force "${WORKTREE_PATH}" 2>/dev/null || true
    
    # Create new worktree from current branch
    git worktree add "${WORKTREE_PATH}" -b "fix-${TASK_ID}" HEAD
    
    # Create fix script in worktree
    cat > "${WORKTREE_PATH}/fix_${TASK_ID}.py" << 'PYTHON_FIX'
#!/usr/bin/env python3
import ast
import re
import os
import sys
from pathlib import Path

def fix_syntax_in_file(file_path):
    """Fix syntax errors in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Fix double closing parentheses in __init__
        content = re.sub(
            r'def __init__\(([^)]*)\)\) -> None:',
            r'def __init__(\1) -> None:',
            content
        )
        
        # Fix conditional assignments
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            if ' = ' in line and ' if ' in line and 'else None)' in line:
                if '(' in line:
                    # Fix invalid conditional assignment
                    match = re.search(r'\(([^)]+)\s+if\s+([^)]+)\s+else\s+None\)\s*=\s*(.+)', line)
                    if match:
                        indent = len(line) - len(line.lstrip())
                        fixed_lines.append(' ' * indent + f'if {match.group(2)}:')
                        fixed_lines.append(' ' * (indent + 4) + f'{match.group(1)} = {match.group(3)}')
                        continue
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Fix list comprehensions
        content = re.sub(r'\]\](\s*[,\)])', r']\1', content)
        
        # Fix trailing 's' after parens
        content = re.sub(r'\)s(\s*[,;])', r')\1', content)
        content = re.sub(r'\)s$', r')', content, flags=re.MULTILINE)
        
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
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    fixed_count = 0
    error_count = 0
    
    for root, dirs, files in os.walk(target_dir):
        if any(skip in root for skip in ['.git', '.venv', '__pycache__']):
            continue
        
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                
                # Check if has syntax error
                try:
                    with open(path, 'r') as f:
                        ast.parse(f.read())
                except SyntaxError:
                    # Try to fix
                    if fix_syntax_in_file(path):
                        print(f"✓ Fixed: {path}")
                        fixed_count += 1
                    else:
                        print(f"✗ Failed: {path}")
                        error_count += 1
    
    print(f"\nResults: Fixed {fixed_count} files, {error_count} still have errors")
    
    # Write results
    with open('.task/results.txt', 'w') as f:
        f.write(f"fixed={fixed_count}\nerrors={error_count}\n")

if __name__ == "__main__":
    main()
PYTHON_FIX
    
    chmod +x "${WORKTREE_PATH}/fix_${TASK_ID}.py"
    
    # Run the fix in background
    (
        cd "${WORKTREE_PATH}"
        mkdir -p .task
        echo "[${TASK_ID}] Starting fixes in ${TARGET_DIR}..."
        python3 "fix_${TASK_ID}.py" "${TARGET_DIR}" > ".task/output.log" 2>&1
        echo "[${TASK_ID}] Completed"
    ) &
    
    # Return PID
    echo $!
}

# Launch parallel tasks
echo "🚀 Launching parallel fix tasks..."

PIDS=()

# Task 1: Fix orchestrator files
PID=$(create_and_fix "orchestrator" ".claude/orchestrator")
PIDS+=($PID)
echo "  Task orchestrator: PID $PID"

# Task 2: Fix agent files  
PID=$(create_and_fix "agents" ".claude/agents")
PIDS+=($PID)
echo "  Task agents: PID $PID"

# Task 3: Fix shared files
PID=$(create_and_fix "shared" ".claude/shared")
PIDS+=($PID)
echo "  Task shared: PID $PID"

# Task 4: Fix test files
PID=$(create_and_fix "tests" "tests")
PIDS+=($PID)
echo "  Task tests: PID $PID"

# Monitor progress
echo ""
echo "⏳ Waiting for parallel tasks to complete..."
echo ""

# Function to check if process is running
is_running() {
    kill -0 $1 2>/dev/null
}

# Monitor loop
while true; do
    RUNNING=0
    for PID in "${PIDS[@]}"; do
        if is_running $PID; then
            RUNNING=$((RUNNING + 1))
        fi
    done
    
    if [ $RUNNING -eq 0 ]; then
        break
    fi
    
    echo -ne "\r  Active tasks: $RUNNING / ${#PIDS[@]}"
    sleep 2
done

echo -e "\n\n✅ All parallel tasks completed!"

# Aggregate results
echo ""
echo "📊 Aggregating results..."
echo "========================"

TOTAL_FIXED=0
TOTAL_ERRORS=0

for TASK in orchestrator agents shared tests; do
    WORKTREE="${WORKTREE_BASE}/fix-${TASK}"
    if [ -f "${WORKTREE}/.task/results.txt" ]; then
        source "${WORKTREE}/.task/results.txt"
        echo "  ${TASK}: Fixed ${fixed} files, ${errors} remaining"
        TOTAL_FIXED=$((TOTAL_FIXED + fixed))
        TOTAL_ERRORS=$((TOTAL_ERRORS + errors))
    fi
    
    # Merge changes back
    if [ -d "${WORKTREE}" ]; then
        echo "  Merging changes from ${TASK}..."
        cd "${WORKTREE}"
        git add -A 2>/dev/null || true
        git commit -m "fix: syntax errors in ${TASK}" 2>/dev/null || true
        
        cd "${BASE_DIR}"
        git cherry-pick "fix-${TASK}" 2>/dev/null || true
    fi
done

echo ""
echo "📈 Total Results:"
echo "  Files fixed: ${TOTAL_FIXED}"
echo "  Files with errors: ${TOTAL_ERRORS}"

# Now run pyright check
echo ""
echo "🔍 Checking remaining type errors..."
cd "${BASE_DIR}"
ERROR_COUNT=$(uv run pyright --outputjson 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('generalDiagnostics', [])))" 2>/dev/null || echo "unknown")

echo "  Type errors: ${ERROR_COUNT}"

# Clean up worktrees
echo ""
echo "🧹 Cleaning up worktrees..."
for TASK in orchestrator agents shared tests; do
    git worktree remove --force "${WORKTREE_BASE}/fix-${TASK}" 2>/dev/null || true
done

echo ""
echo "✨ Orchestration complete!"