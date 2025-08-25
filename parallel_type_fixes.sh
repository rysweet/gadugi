#!/bin/bash
# Parallel Type Safety Fixes
# Implements parallel execution as per CLAUDE.md orchestration patterns

set -e

# Base directory
BASE_DIR="/home/rysweet/gadugi"
ISSUE_311_WORKTREE="$BASE_DIR/.worktrees/issue-311"

# Create task tracking directory
TASK_DIR="$ISSUE_311_WORKTREE/.task"
mkdir -p "$TASK_DIR"

# Define tasks for parallel execution
declare -a TASKS=(
    "agents:.claude/agents"
    "services:.claude/services" 
    "orchestrator:.claude/orchestrator"
    "tests:tests"
    "shared:.claude/shared"
)

# Function to fix type errors in a directory
fix_directory_types() {
    local task_name=$1
    local directory=$2
    local task_id="fix-${task_name}"
    local log_file="$TASK_DIR/${task_id}.log"
    
    echo "[$(date)] Starting type fixes for $task_name" > "$log_file"
    
    # Change to worktree directory
    cd "$ISSUE_311_WORKTREE"
    
    # Count initial errors
    initial_errors=$(uv run pyright "$directory" 2>&1 | grep -c "error:" || true)
    echo "Initial errors in $directory: $initial_errors" >> "$log_file"
    
    # Apply fixes using Python script
    cat > "${TASK_DIR}/${task_id}_fixer.py" << 'EOF'
#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

directory = sys.argv[1]

def fix_type_annotations(content: str) -> str:
    """Add missing type annotations."""
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # Fix missing return type for __init__
        if 'def __init__(self' in line and ') -> None:' not in line and ':' in line:
            line = line.replace(':', ') -> None:')
        
        # Fix missing Optional imports
        if 'Optional[' in line and 'from typing import' in content:
            if 'Optional' not in content.split('\n')[0:20]:  # Check imports section
                # Add Optional to imports
                for i, l in enumerate(new_lines):
                    if 'from typing import' in l and 'Optional' not in l:
                        new_lines[i] = l.replace('import ', 'import Optional, ')
                        break
        
        new_lines.append(line)
    
    return '\n'.join(new_lines)

def fix_none_checks(content: str) -> str:
    """Add proper None checks."""
    # Fix patterns like obj.attr without None check
    content = re.sub(
        r'if\s+(\w+)\.(\w+)\s*:',
        r'if \1 is not None and \1.\2:',
        content
    )
    return content

def fix_dataclass_defaults(content: str) -> str:
    """Fix dataclass mutable defaults."""
    # Add field import if needed
    if '@dataclass' in content and 'field' not in content:
        content = re.sub(
            r'from dataclasses import dataclass',
            'from dataclasses import dataclass, field',
            content
        )
    
    # Fix mutable defaults
    content = re.sub(
        r'(\w+):\s*List\[.*?\]\s*=\s*\[\]',
        r'\1: List[Any] = field(default_factory=list)',
        content
    )
    content = re.sub(
        r'(\w+):\s*Dict\[.*?\]\s*=\s*\{\}',
        r'\1: Dict[Any, Any] = field(default_factory=dict)',
        content
    )
    
    return content

# Process all Python files in directory
path = Path(directory)
if path.exists():
    for py_file in path.glob('**/*.py'):
        try:
            content = py_file.read_text()
            original = content
            
            content = fix_type_annotations(content)
            content = fix_none_checks(content)
            content = fix_dataclass_defaults(content)
            
            if content != original:
                py_file.write_text(content)
                print(f"Fixed: {py_file}")
        except Exception as e:
            print(f"Error in {py_file}: {e}")
EOF
    
    # Run the fixer
    uv run python "${TASK_DIR}/${task_id}_fixer.py" "$directory" >> "$log_file" 2>&1
    
    # Count final errors
    final_errors=$(uv run pyright "$directory" 2>&1 | grep -c "error:" || true)
    echo "Final errors in $directory: $final_errors" >> "$log_file"
    echo "Reduced errors by: $((initial_errors - final_errors))" >> "$log_file"
    
    # Create completion marker
    echo "{
        \"task_id\": \"$task_id\",
        \"directory\": \"$directory\",
        \"initial_errors\": $initial_errors,
        \"final_errors\": $final_errors,
        \"reduction\": $((initial_errors - final_errors)),
        \"status\": \"completed\",
        \"timestamp\": \"$(date -Iseconds)\"
    }" > "$TASK_DIR/${task_id}.json"
    
    echo "[$(date)] Completed type fixes for $task_name" >> "$log_file"
}

# Launch parallel tasks
echo "Starting parallel type safety fixes..."
echo "Tasks to execute: ${#TASKS[@]}"

# Track PIDs for monitoring
declare -a PIDS=()

# Launch each task in background
for task in "${TASKS[@]}"; do
    IFS=':' read -r name dir <<< "$task"
    echo "Launching task: fix-$name for directory: $dir"
    
    fix_directory_types "$name" "$dir" &
    PIDS+=($!)
done

# Monitor progress
echo "Monitoring ${#PIDS[@]} parallel tasks..."

# Function to check task status
check_status() {
    local completed=0
    local running=0
    
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            ((running++))
        else
            ((completed++))
        fi
    done
    
    echo "Status: $completed completed, $running running"
}

# Wait with progress updates
while true; do
    sleep 5
    check_status
    
    # Check if all complete
    local all_done=true
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            all_done=false
            break
        fi
    done
    
    if [ "$all_done" = true ]; then
        break
    fi
done

echo "All parallel tasks completed!"

# Aggregate results
echo ""
echo "=== RESULTS SUMMARY ==="
total_initial=0
total_final=0

for task in "${TASKS[@]}"; do
    IFS=':' read -r name dir <<< "$task"
    if [ -f "$TASK_DIR/fix-${name}.json" ]; then
        initial=$(jq -r '.initial_errors' "$TASK_DIR/fix-${name}.json")
        final=$(jq -r '.final_errors' "$TASK_DIR/fix-${name}.json")
        reduction=$(jq -r '.reduction' "$TASK_DIR/fix-${name}.json")
        
        echo "$name: $initial → $final errors (reduced by $reduction)"
        
        total_initial=$((total_initial + initial))
        total_final=$((total_final + final))
    fi
done

echo ""
echo "TOTAL: $total_initial → $total_final errors"
echo "Overall reduction: $((total_initial - total_final)) errors"

# Run final pyright check
echo ""
echo "Running final pyright check..."
cd "$ISSUE_311_WORKTREE"
uv run pyright 2>&1 | tail -5