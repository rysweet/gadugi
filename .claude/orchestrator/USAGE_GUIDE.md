# OrchestratorAgent Usage Guide

This guide provides step-by-step instructions for using the OrchestratorAgent to achieve parallel workflow execution with 3-5x speed improvements.

## Quick Start (5 Minutes)

### Step 1: Verify Prerequisites

```bash
# Check Claude CLI availability
claude --version
# Should show: Claude Code CLI version X.X.X

# Check Git version
git --version
# Should show: git version 2.25.0 or higher

# Check Python dependencies
python -c "import psutil; print('✅ psutil available')"
```

### Step 2: Analyze Your Prompts

```bash
cd .claude/orchestrator/components
python task_analyzer.py --prompts-dir ../../../prompts/ --output ../analysis.json
```

**Expected Output**:
```
🔍 Analyzing all prompt files for parallel execution opportunities...
Found 12 prompt files
✅ Analyzed: Test Coverage for Definition Node (test_coverage)
✅ Analyzed: Fix Circular Import Issue (bug_fix)
✅ Analyzed: Implement Query Builder (feature_implementation)
...
📊 Analysis complete: 12 tasks analyzed

📊 Analysis Summary:
Total tasks: 12
Parallelizable: 8
Sequential: 4
Speed improvement: 3.2x
Sequential time: 480 minutes
Parallel time: 150 minutes
```

### Step 3: Review Analysis Results

```bash
# View the generated analysis
cat ../analysis.json | jq '.execution_summary'
```

This shows you exactly which tasks can run in parallel and the expected speed improvement.

### Step 4: Execute Parallel Workflow (Manual)

For now, you can manually execute the recommended parallel groups:

```bash
# Group 1 (Parallel): Test coverage tasks
/agent:workflow-master prompts/test-definition-node.md &
/agent:workflow-master prompts/test-relationship-creator.md &
/agent:workflow-master prompts/test-documentation-linker.md &
wait

# Group 2 (Sequential): Feature implementation
/agent:workflow-master prompts/implement-query-builder.md
```

## Detailed Usage Scenarios

### Scenario 1: Test Coverage Improvement Campaign

**Situation**: You have multiple modules with low test coverage that need improvement.

**Files**:
- `prompts/test-definition-node.md` (target: definition_node.py)
- `prompts/test-relationship-creator.md` (target: relationship_creator.py)
- `prompts/test-documentation-linker.md` (target: documentation_linker.py)

**Analysis**:
```bash
python task_analyzer.py --prompts-dir ../../../prompts/
```

**Results**:
- All 3 tasks classified as `test_coverage`
- No file conflicts detected (different target files)
- Parallelizable: ✅ Yes
- Speed improvement: 3.0x (180 min → 60 min)

**Execution Strategy**:
```bash
# All three can run simultaneously
echo "Starting parallel test coverage improvement..." 
/agent:workflow-master prompts/test-definition-node.md &
/agent:workflow-master prompts/test-relationship-creator.md &  
/agent:workflow-master prompts/test-documentation-linker.md &
wait
echo "All test coverage tasks complete!"
```

### Scenario 2: Bug Fix Sprint

**Situation**: Multiple unrelated bugs need to be fixed quickly.

**Files**:
- `prompts/fix-circular-import.md` (lsp_helper.py, definition_node.py)
- `prompts/fix-memory-leak.md` (graph.py)
- `prompts/fix-ui-rendering.md` (frontend/components/)

**Analysis**:
```bash
python task_analyzer.py --prompts-dir ../../../prompts/
```

**Results**:
- All 3 tasks classified as `bug_fix`
- No file conflicts (different modules)
- Parallelizable: ✅ Yes
- Speed improvement: 3.0x (90 min → 30 min)

**Execution Strategy**:
```bash
# Parallel bug fix execution
echo "Starting parallel bug fixes..."
/agent:workflow-master prompts/fix-circular-import.md &
/agent:workflow-master prompts/fix-memory-leak.md &
/agent:workflow-master prompts/fix-ui-rendering.md &
wait
echo "All bugs fixed!"
```

### Scenario 3: Mixed Workflow with Dependencies

**Situation**: Complex workflow with some dependencies between tasks.

**Files**:
- `prompts/refactor-base-classes.md` (base classes)
- `prompts/update-derived-classes.md` (depends on base classes)
- `prompts/write-integration-tests.md` (depends on both above)
- `prompts/update-documentation.md` (independent)

**Analysis**:
```bash
python task_analyzer.py --prompts-dir ../../../prompts/
```

**Results**:
- Dependencies detected: update-derived-classes → refactor-base-classes
- write-integration-tests → both previous tasks
- update-documentation is independent
- Speed improvement: 2.0x (sequential phases required)

**Execution Strategy**:
```bash
# Phase 1: Independent tasks
echo "Phase 1: Starting base refactoring and documentation..."
/agent:workflow-master prompts/refactor-base-classes.md &
/agent:workflow-master prompts/update-documentation.md &
wait

# Phase 2: Dependent task
echo "Phase 2: Updating derived classes..."
/agent:workflow-master prompts/update-derived-classes.md

# Phase 3: Final integration
echo "Phase 3: Writing integration tests..."
/agent:workflow-master prompts/write-integration-tests.md

echo "Mixed workflow complete!"
```

## Advanced Usage Patterns

### Pattern 1: Resource-Aware Execution

Monitor system resources and adjust concurrency:

```bash
# Check system resources first
python -c "
import psutil
print(f'CPU cores: {psutil.cpu_count()}')
print(f'Available RAM: {psutil.virtual_memory().available / 1024**3:.1f}GB')
print(f'CPU usage: {psutil.cpu_percent(interval=1)}%')
"

# Adjust concurrency based on resources
# High-end system (8+ cores, 16+ GB RAM): Run 4 parallel tasks
# Mid-range system (4-8 cores, 8-16 GB RAM): Run 2-3 parallel tasks  
# Low-end system (<4 cores, <8 GB RAM): Run 1-2 parallel tasks
```

### Pattern 2: Progressive Execution

Start with high-priority tasks in parallel, then continue with others:

```bash
# Priority 1: Critical bugs (parallel)
echo "Priority 1: Critical fixes..."
/agent:workflow-master prompts/fix-critical-security-bug.md &
/agent:workflow-master prompts/fix-data-corruption-bug.md &
wait

# Priority 2: Test coverage (parallel)
echo "Priority 2: Test coverage..."
/agent:workflow-master prompts/test-module-a.md &
/agent:workflow-master prompts/test-module-b.md &
/agent:workflow-master prompts/test-module-c.md &
wait

# Priority 3: Feature enhancements (can overlap)
echo "Priority 3: Feature work..."
/agent:workflow-master prompts/implement-feature-x.md &
/agent:workflow-master prompts/implement-feature-y.md &
wait
```

### Pattern 3: Continuous Integration Workflow

Integrate with CI/CD for automated parallel execution:

```bash
#!/bin/bash
# ci-parallel-tasks.sh

set -e

echo "🔍 Analyzing tasks for parallel execution..."
cd .claude/orchestrator/components
python task_analyzer.py --prompts-dir ../../../prompts/ --output ../ci-analysis.json

# Extract parallelizable tasks
PARALLEL_TASKS=$(cat ../ci-analysis.json | jq -r '.groups[] | select(.parallelizable == true) | .tasks[].id' | head -4)

echo "🚀 Starting parallel execution of tasks: $PARALLEL_TASKS"

# Execute in parallel with proper error handling
pids=()
for task in $PARALLEL_TASKS; do
    echo "Starting task: $task"
    /agent:workflow-master "prompts/${task}.md" &
    pids+=($!)
done

# Wait for all tasks and check results
failed=0
for pid in "${pids[@]}"; do
    if ! wait "$pid"; then
        failed=$((failed + 1))
    fi
done

if [ $failed -eq 0 ]; then
    echo "✅ All parallel tasks completed successfully"
    exit 0
else
    echo "❌ $failed tasks failed"
    exit 1
fi
```

## Performance Optimization Tips

### Tip 1: Optimal Task Grouping

```bash
# Group tasks by estimated execution time for better load balancing
# Short tasks (< 30 min): Group 3-4 together
# Medium tasks (30-60 min): Group 2-3 together  
# Long tasks (> 60 min): Run individually or with one short task
```

### Tip 2: System Resource Management

```bash
# Monitor during execution
watch -n 5 "ps aux | grep -E '(claude|python)' | grep -v grep"

# Check memory usage
watch -n 5 "free -h && echo '---' && ps aux --sort=-%mem | head -10"

# Adjust if system becomes sluggish
kill -TERM <slow-task-pid>  # Gracefully stop a task if needed
```

### Tip 3: Workspace Organization

```bash
# Keep worktrees organized
ls -la .worktrees/  # Should show active parallel workspaces

# Clean up completed worktrees regularly
find .worktrees/ -type d -name "task-*" -mtime +1 -exec rm -rf {} \;
```

## Troubleshooting Common Issues

### Issue 1: "No parallelizable tasks found"

**Symptoms**: All tasks marked as sequential, no speed improvement

**Causes**:
- Tasks modify the same files
- Complex dependencies between tasks
- All tasks marked as critical complexity

**Solutions**:
```bash
# Check for file conflicts
python task_analyzer.py --prompts-dir ../../../prompts/ | grep -A 5 "conflicts"

# Review task complexity assessments
cat analysis.json | jq '.groups[].tasks[] | {id, complexity, conflicts}'

# Consider splitting large tasks into smaller independent pieces
```

### Issue 2: System slowdown during parallel execution

**Symptoms**: High CPU usage, system becomes unresponsive

**Solutions**:
```bash
# Reduce concurrency
# Instead of 4 parallel tasks, try 2:
/agent:workflow-master prompts/task1.md &
/agent:workflow-master prompts/task2.md &
wait

/agent:workflow-master prompts/task3.md &
/agent:workflow-master prompts/task4.md &
wait
```

### Issue 3: Git worktree conflicts

**Symptoms**: "worktree already exists" or similar git errors

**Solutions**:
```bash
# List and clean up existing worktrees
git worktree list
git worktree remove .worktrees/task-123  # Remove specific worktree
git worktree prune  # Remove stale worktree references

# Force cleanup if needed
rm -rf .worktrees/  # Nuclear option - removes all worktrees
```

### Issue 4: Memory issues during execution

**Symptoms**: "Out of memory" errors, swap usage high

**Solutions**:
```bash
# Monitor memory usage
watch -n 2 "free -h"

# Reduce concurrent tasks to 1-2
# Close other applications
# Consider running tasks sequentially if memory is very limited
```

## Best Practices

### 1. Pre-Execution Checklist

- [ ] Clean git working directory (`git status` should be clean)
- [ ] Sufficient disk space (check with `df -h`)
- [ ] No other intensive processes running
- [ ] Recent backup of important work
- [ ] Prompts are well-structured and tested individually

### 2. During Execution

- [ ] Monitor system resources (`top` or `htop`)
- [ ] Keep terminal output visible for progress tracking
- [ ] Don't start other intensive tasks
- [ ] Have a backup plan if execution needs to be stopped

### 3. Post-Execution

- [ ] Verify all tasks completed successfully
- [ ] Check git history for proper commits
- [ ] Run tests to ensure nothing broke
- [ ] Clean up temporary files and worktrees
- [ ] Update project documentation with results

### 4. Error Recovery

```bash
# If execution is interrupted:
# 1. Check what tasks were running
ps aux | grep claude

# 2. Check git worktree status
git worktree list

# 3. Manually complete or restart failed tasks
/agent:workflow-master prompts/failed-task.md

# 4. Clean up partial work if needed
git worktree remove .worktrees/failed-task
```

## Integration Examples

### With GitHub Actions

```yaml
# .github/workflows/parallel-tasks.yml
name: Parallel Task Execution

on:
  workflow_dispatch:
    inputs:
      task_pattern:
        description: 'Pattern for task files (e.g., test-*.md)'
        required: true
        default: 'test-*.md'

jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      parallel-groups: ${{ steps.analysis.outputs.groups }}
    steps:
      - uses: actions/checkout@v4
      - name: Analyze tasks
        id: analysis
        run: |
          cd .claude/orchestrator/components
          python task_analyzer.py --prompts-dir ../../../prompts/ --output analysis.json
          echo "groups=$(cat analysis.json | jq -c '.groups')" >> $GITHUB_OUTPUT

  execute:
    needs: analyze
    runs-on: ubuntu-latest
    strategy:
      matrix:
        group: ${{ fromJson(needs.analyze.outputs.parallel-groups) }}
    steps:
      - name: Execute task group
        run: |
          for task in ${{ matrix.group.tasks }}; do
            echo "Executing $task"
            # Execute task here
          done
```

### With Docker

```dockerfile
# Dockerfile.orchestrator
FROM python:3.12-slim

RUN apt-get update && apt-get install -y git
RUN pip install psutil

COPY .claude/orchestrator /app/orchestrator
WORKDIR /app/orchestrator

CMD ["python", "components/task_analyzer.py", "--prompts-dir", "/prompts"]
```

```bash
# Usage
docker build -t orchestrator -f Dockerfile.orchestrator .
docker run -v $(pwd)/prompts:/prompts orchestrator
```

This comprehensive usage guide should help users effectively leverage the OrchestratorAgent for parallel workflow execution with significant performance improvements.