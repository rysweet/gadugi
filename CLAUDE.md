# AI Assistant Instructions

This file combines generic Claude Code best practices with project-specific instructions for the Gadugi repository.

⚠️ **FIRST ACTION**: Check and update @.github/Memory.md ! ⚠️
⚠️ **NEW**: Memory.md now syncs with GitHub Issues via MemoryManagerAgent! ⚠️

⚠️ **SECOND ACTION**: When working on Claude agents or instructions, read https://docs.anthropic.com/en/docs/claude-code/memory ! ⚠️

---

## CRITICAL: Orchestration-First Development

**ALL development tasks MUST follow the orchestration workflow defined here.**

### Core Orchestration Workflow

For complex or multiple tasks:
1. **Task Analysis**: Decompose work into discrete tasks
2. **Dependency Detection**: Identify which tasks can run in parallel
3. **Worktree Isolation**: Create separate worktrees for each task
4. **Parallel Execution**: Execute independent tasks simultaneously
5. **Progress Monitoring**: Track all tasks to completion
6. **Result Aggregation**: Collect and report results

### Implementation Approach

#### For Single Tasks
- Follow the 11-phase workflow directly
- Create a single worktree and execute phases sequentially
- No external agent delegation needed

#### For Multiple Tasks
- Analyze dependencies using the patterns below
- Create worktrees for each independent task
- Execute tasks in parallel using subprocess management
- Monitor completion using process tracking

---

## CRITICAL: Development Guidelines - MANDATORY

⚠️ **YOU MUST FOLLOW THE GUIDELINES IN @.claude/Guidelines.md** ⚠️

Key principles you MUST follow:
- **Zero BS Principle**: NO false claims of completion. If it's not implemented, say so.
- **Recipe-Driven Development**: Requirements → Design → Implementation → Tests → Review
- **Quality Gates**: All code MUST pass pyright, ruff, pytest before claiming completion
- **Review Requirements**: Design review, code review, system review for EVERY component
- **Dependency Order**: Build foundations first, no building on stubs

Read @.claude/Guidelines.md for complete requirements.

---

## 11-Phase Workflow (MANDATORY for ALL Changes)

Every code change MUST go through these phases IN ORDER:

### Phase 1: Initial Setup
- Acknowledge the task requirements
- Identify affected components
- Check current branch status
- Review existing code structure

### Phase 2: Issue Creation
```bash
gh issue create --title "[Type]: Brief description" \
  --body "## Objective\n[What needs to be done]\n\n## Requirements\n[Specific requirements]\n\n## Success Criteria\n[How to verify completion]"
```

### Phase 3: Branch and Worktree Management
```bash
# Create worktree for isolation
ISSUE_NUMBER="[number]"
BRANCH_NAME="feature/issue-${ISSUE_NUMBER}-[description]"
WORKTREE_DIR=".worktrees/issue-${ISSUE_NUMBER}"

# Clean up if exists
git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true

# Create new worktree
git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" origin/main
cd "$WORKTREE_DIR"
```

### Phase 4: Research and Planning
- Analyze the codebase for the task
- Identify dependencies and impacts
- Create implementation plan
- Document approach in issue comments

### Phase 5: Implementation
- Write code following project standards
- Use atomic commits with clear messages
- Follow the Guidelines.md principles
- Implement complete functionality (no stubs)

### Phase 6: Testing (MANDATORY Quality Gates)
```bash
# For UV projects (recommended)
if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
    uv sync --all-extras
    uv run pytest tests/ -v
    uv run ruff check .
    uv run ruff format .
    uv run pyright
    uv run pre-commit run --all-files
else
    # Standard Python projects
    pytest tests/ -v
    ruff check .
    ruff format .
    pyright
    pre-commit run --all-files
fi
```

ALL tests MUST pass before proceeding to Phase 7.

### Phase 7: Documentation
- Update relevant documentation
- Add/update docstrings
- Update README if needed
- Document in Memory.md

### Phase 8: Pull Request Creation
```bash
# Push branch
git push -u origin "$BRANCH_NAME"

# Create PR
gh pr create --base main \
  --title "[Type]: Brief description (#${ISSUE_NUMBER})" \
  --body "## Summary\n[What this PR does]\n\n## Changes\n[List of changes]\n\n## Testing\n[How it was tested]\n\nCloses #${ISSUE_NUMBER}"
```

### Phase 9: Code Review
- Request review via GitHub
- Address review feedback
- Ensure all CI checks pass

### Phase 10: Review Response
- Implement requested changes
- Re-test after changes
- Update PR with responses

### Phase 11: Merge and Cleanup
```bash
# After approval and merge
cd ../..
git worktree remove "$WORKTREE_DIR"
git branch -d "$BRANCH_NAME"
```

---

## NEW: Simplified Executor Architecture (V0.3)

### Overview
Gadugi V0.3 uses simplified single-purpose executors located in `.claude/executors/`. These executors follow the NO DELEGATION principle - they cannot call other agents, only direct tools.

### Available Executors

#### 1. Code Executor
Handles all file operations:
```python
# Write a new file
from .claude.executors import execute
result = execute('code', {
    'action': 'write',
    'file_path': 'src/example.py',
    'content': 'print("Hello, World!")'
})

# Read a file
result = execute('code', {
    'action': 'read',
    'file_path': 'src/example.py'
})

# Edit a file
result = execute('code', {
    'action': 'edit',
    'file_path': 'src/example.py',
    'old_content': 'print("Hello, World!")',
    'new_content': 'print("Hello, Gadugi!")'
})
```

#### 2. Test Executor
Runs tests with automatic framework detection:
```python
# Run pytest (automatically detects UV projects)
result = execute('test', {
    'test_framework': 'pytest',
    'test_path': 'tests/',
    'options': {
        'verbose': True,
        'coverage': True,
        'coverage_path': 'src'
    }
})

# Run unittest
result = execute('test', {
    'test_framework': 'unittest',
    'test_path': 'tests/'
})

# Run Jest for JavaScript
result = execute('test', {
    'test_framework': 'jest',
    'test_path': 'tests/',
    'working_dir': './frontend'
})
```

#### 3. GitHub Executor
Manages GitHub operations via gh CLI:
```python
# Create an issue
result = execute('github', {
    'operation': 'create_issue',
    'title': 'Fix bug in parser',
    'body': 'The parser fails on...',
    'labels': ['bug', 'parser']
})

# Create a PR
result = execute('github', {
    'operation': 'create_pr',
    'title': 'Fix: Parser bug (#123)',
    'body': 'This PR fixes...',
    'base': 'main',
    'head': 'fix/parser-bug'
})

# Check PR status
result = execute('github', {
    'operation': 'pr_status',
    'pr_number': 123
})

# IMPORTANT: Never auto-merge! Always wait for user approval
# Only merge when user explicitly says to:
if user_approved:
    result = execute('github', {
        'operation': 'merge_pr',
        'pr_number': 123,
        'delete_branch': True
    })
```

#### 4. Worktree Executor
Manages git worktrees for isolated development:
```python
# Create a worktree
result = execute('worktree', {
    'operation': 'create',
    'task_id': '123',
    'branch_name': 'feature/task-123',
    'base_branch': 'main'
})

# List worktrees
result = execute('worktree', {
    'operation': 'list'
})

# Check worktree status
result = execute('worktree', {
    'operation': 'status',
    'task_id': '123'
})

# Remove worktree
result = execute('worktree', {
    'operation': 'remove',
    'task_id': '123'
})

# Cleanup old worktrees
result = execute('worktree', {
    'operation': 'cleanup',
    'max_age_days': 7,
    'dry_run': False
})
```

### Orchestration Patterns

#### Single Task Execution
For a single task, orchestrate executors directly:
```python
# 1. Create worktree
worktree_result = execute('worktree', {
    'operation': 'create',
    'task_id': '123',
    'branch_name': 'fix/bug-123'
})

# 2. Write code in worktree
code_result = execute('code', {
    'action': 'write',
    'file_path': f"{worktree_result['worktree_path']}/fix.py",
    'content': '...'
})

# 3. Run tests
test_result = execute('test', {
    'test_framework': 'pytest',
    'test_path': 'tests/',
    'working_dir': worktree_result['worktree_path']
})

# 4. Create PR if tests pass
if test_result['success']:
    pr_result = execute('github', {
        'operation': 'create_pr',
        'title': 'Fix bug #123',
        'body': 'Tests passing, ready for review'
    })
```

#### Parallel Task Execution
For multiple independent tasks, use subprocess or threading:
```python
import subprocess
import json
from pathlib import Path

def execute_task_in_worktree(task_id, task_description):
    """Execute a task in its own worktree."""
    # Create worktree
    worktree = execute('worktree', {
        'operation': 'create',
        'task_id': task_id
    })
    
    # Execute task-specific operations
    # ... code writing, testing, etc ...
    
    return results

# Execute multiple tasks in parallel
tasks = [
    {'id': '123', 'desc': 'Fix parser bug'},
    {'id': '124', 'desc': 'Add logging'},
    {'id': '125', 'desc': 'Update docs'}
]

# Use threading or asyncio for parallel execution
import concurrent.futures
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(execute_task_in_worktree, t['id'], t['desc']) for t in tasks]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
```

### Important Principles

1. **NO DELEGATION**: Executors never call other agents or executors
2. **SINGLE PURPOSE**: Each executor has exactly one responsibility
3. **DIRECT TOOLS**: Executors use only subprocess, file I/O, etc.
4. **STRUCTURED RESULTS**: All executors return consistent result dicts
5. **ERROR HANDLING**: All executors handle and report errors gracefully

### Migration Notes

When migrating from old agent patterns:
- Replace agent delegation chains with direct executor calls
- Use CLAUDE.md orchestration instead of WorkflowManager
- Call executors sequentially or in parallel as needed
- Results from one executor can be passed to another

---

## Task Analysis and Dependency Detection

### Identifying Independent Tasks
Tasks can run in PARALLEL when:
- They modify different files
- They have no shared dependencies  
- They work on separate features
- They have no import relationships

### Detecting Dependencies
Tasks must run SEQUENTIALLY when:
- One task's output is another's input
- They modify the same files
- They share state or configuration
- One creates structure another uses

### Dependency Analysis Implementation

Use this approach to detect task dependencies:

```bash
# 1. Extract files affected by each task
for task in tasks; do
    # Use grep/git to identify files the task will modify
    git grep -l "pattern" > task_files.txt
done

# 2. Check for overlaps
# If tasks modify the same files, they must run sequentially
# If tasks modify different files, they can run in parallel
```

**Key Patterns**:
- Tasks modifying the same module → Sequential
- Tasks in different directories → Parallel  
- Tasks with import dependencies → Sequential
- Independent bug fixes → Parallel

---

## Parallel Execution Guidelines

### When to Execute in Parallel
1. Multiple independent bug fixes
2. Separate feature implementations
3. Documentation updates for different components
4. Test additions for different modules

### How to Execute Parallel Tasks
1. **Create separate worktrees** for each task
2. **Use subprocess or threading** for parallel execution
3. **Monitor progress** of each task
4. **Aggregate results** after completion

### Parallel Execution Implementation

#### Using Shell Scripts (Recommended)
```bash
#!/bin/bash
# Execute multiple tasks in parallel

# Create worktrees and launch tasks
for task in "$@"; do
    (
        WORKTREE=".worktrees/task-${task}"
        BRANCH="feature/task-${task}"
        
        # Create isolated worktree
        git worktree add "$WORKTREE" -b "$BRANCH" origin/main
        
        # Execute task in worktree
        cd "$WORKTREE"
        # Run the 11-phase workflow for this task
        # Phase 1-11 implementation...
    ) &
    
    # Store PID for monitoring
    echo $! >> .task_pids
done

# Wait for all tasks to complete
while read pid; do
    wait $pid
done < .task_pids
```

#### Using Python (When Needed)
```python
#!/usr/bin/env python3
import subprocess
import asyncio
from pathlib import Path

async def execute_task(task_id, task_description):
    """Execute a single task in its own worktree."""
    worktree = Path(f".worktrees/task-{task_id}")
    branch = f"feature/task-{task_id}"
    
    # Create worktree
    await asyncio.create_subprocess_exec(
        "git", "worktree", "add", str(worktree), "-b", branch, "origin/main"
    )
    
    # Execute 11-phase workflow
    # Implementation continues...
    
async def execute_parallel(tasks):
    """Execute multiple tasks in parallel."""
    tasks_list = [execute_task(t['id'], t['desc']) for t in tasks]
    results = await asyncio.gather(*tasks_list)
    return results
```

### Progress Monitoring and Execution Tracking

#### Real-time Progress Monitoring
```bash
#!/bin/bash
# Monitor parallel task execution

monitor_tasks() {
    while true; do
        clear
        echo "=== Task Execution Status ==="
        echo "Time: $(date)"
        echo ""
        
        # Check each worktree for status
        for worktree in .worktrees/task-*/; do
            if [[ -f "$worktree/.task/state.json" ]]; then
                TASK_ID=$(jq -r '.task_id' "$worktree/.task/state.json")
                STATUS=$(jq -r '.status' "$worktree/.task/state.json")
                PHASE=$(jq -r '.phase' "$worktree/.task/state.json")
                echo "Task: $TASK_ID - Status: $STATUS - Phase: $PHASE/11"
            fi
        done
        
        # Check if all tasks complete
        INCOMPLETE=$(find .worktrees/task-*/.task/state.json -exec jq -r '.status' {} \; | grep -v "complete" | wc -l)
        if [[ $INCOMPLETE -eq 0 ]]; then
            echo ""
            echo "✅ All tasks completed!"
            break
        fi
        
        sleep 5
    done
}
```

#### Process Registry Pattern
```python
#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from datetime import datetime

class ProcessRegistry:
    """Track and manage parallel task processes."""
    
    def __init__(self):
        self.registry_file = Path(".task_registry.json")
        self.processes = {}
    
    def register_task(self, task_id, pid, worktree):
        """Register a new task process."""
        self.processes[task_id] = {
            "pid": pid,
            "worktree": str(worktree),
            "started": datetime.now().isoformat(),
            "status": "running"
        }
        self.save()
    
    def check_status(self, task_id):
        """Check if task process is still running."""
        if task_id in self.processes:
            pid = self.processes[task_id]["pid"]
            try:
                # Check if process exists
                subprocess.run(["kill", "-0", str(pid)], check=True, capture_output=True)
                return "running"
            except subprocess.CalledProcessError:
                self.processes[task_id]["status"] = "completed"
                self.save()
                return "completed"
        return "unknown"
    
    def save(self):
        """Persist registry to disk."""
        with open(self.registry_file, 'w') as f:
            json.dump(self.processes, f, indent=2)
```

### State Management and Recovery

#### Task State Tracking
```bash
# Create state file for each task
STATE_FILE=".worktrees/task-${TASK_ID}/.task/state.json"

echo '{
  "task_id": "'${TASK_ID}'",
  "status": "in_progress",
  "phase": 1,
  "started": "'$(date -Iseconds)'"
}' > "$STATE_FILE"

# Update state as task progresses
jq '.phase = 6 | .status = "testing"' "$STATE_FILE" > tmp && mv tmp "$STATE_FILE"
```

#### Error Recovery
If a task fails:
1. Check the state file to identify failure point
2. Fix the issue in the worktree
3. Resume from the failed phase
4. Update state to reflect recovery

#### Result Aggregation
```bash
#!/bin/bash
# Aggregate results from all completed tasks

aggregate_results() {
    RESULTS_FILE="parallel_execution_results.json"
    echo '{"tasks": [], "summary": {}}' > "$RESULTS_FILE"
    
    for worktree in .worktrees/task-*/; do
        if [[ -f "$worktree/.task/state.json" ]]; then
            TASK_RESULT=$(cat "$worktree/.task/state.json")
            
            # Add to results
            jq --argjson task "$TASK_RESULT" '.tasks += [$task]' "$RESULTS_FILE" > tmp
            mv tmp "$RESULTS_FILE"
        fi
    done
    
    # Generate summary
    TOTAL=$(jq '.tasks | length' "$RESULTS_FILE")
    COMPLETED=$(jq '[.tasks[] | select(.status == "complete")] | length' "$RESULTS_FILE")
    
    jq --arg total "$TOTAL" --arg completed "$COMPLETED" \
       '.summary = {total: $total, completed: $completed}' "$RESULTS_FILE" > tmp
    mv tmp "$RESULTS_FILE"
    
    echo "Results aggregated to $RESULTS_FILE"
}

### Emergency Procedures (Critical Production Issues)

⚠️ **EMERGENCY HOTFIX EXCEPTION** ⚠️

For **CRITICAL PRODUCTION ISSUES** requiring immediate fixes (security vulnerabilities, system downtime, data corruption), you may bypass the normal workflow:

**Emergency Criteria** (ALL must be true):
- Production system is down or compromised
- Issue poses immediate security risk or data loss
- Fix is simple and well-understood (< 10 lines of code)
- No time for full workflow due to business impact

**Emergency Procedure**:
1. **Document the emergency**: Create issue with `emergency` label
2. **Work directly on main branch** (exception to normal branching)
3. **Make minimal, focused changes only**
4. **Commit with clear emergency attribution**:
   ```bash
   git commit -m "EMERGENCY: fix critical [issue description]

   Emergency hotfix bypassing normal workflow
   due to production impact. Full workflow to follow.

   Fixes: [issue-number]"
   ```
5. **Immediately create follow-up issue** for proper workflow implementation
6. **Return to orchestrator requirement** for all subsequent changes

**Post-Emergency Actions**:
- Conduct immediate post-mortem
- Implement proper tests via standard workflow
- Update documentation to prevent recurrence
- Review emergency decision in next team meeting

**Important**: Emergency exception should be used < 1% of the time. If used frequently, reassess development practices.

---

## Generic Claude Code Instructions

@claude-generic-instructions.md

## Project-Specific Instructions

Note: Project-specific instructions are integrated directly into this file above.

---

## Worktree Lifecycle Management

**IMPORTANT**: Create and manage worktrees for isolated development environments.

### When to Use Worktrees

Use worktrees for:
- Working on individual issues that require code changes
- Isolating development work from the main repository
- Preventing conflicts when multiple issues are being worked on
- Creating clean environments for testing and validation

### Worktree Lifecycle

1. **Creation Phase**:
   ```bash
   # Create a new git worktree for an issue
   ISSUE_NUMBER="123"
   BRANCH_NAME="feature/issue-${ISSUE_NUMBER}-description"
   WORKTREE_DIR=".worktrees/issue-${ISSUE_NUMBER}"
   
   # Remove if exists, then create
   git worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true
   git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" origin/main
   
   # Initialize task metadata
   mkdir -p "$WORKTREE_DIR/.task"
   echo '{"issue": '${ISSUE_NUMBER}', "created": "'$(date -Iseconds)'"}' > "$WORKTREE_DIR/.task/metadata.json"
   ```

2. **Development Phase**:
   - Navigate to worktree: `cd .worktrees/issue-[number]/`
   - All development happens in isolated environment
   - Changes don't affect main repository or other worktrees
   - Commit changes regularly with descriptive messages

3. **PR Creation Phase**:
   - Push branch from within worktree
   - Create PR using `gh pr create` from worktree directory
   - Reference issue number in PR description

4. **Cleanup Phase**:
   - After PR is merged, remove worktree:
     ```bash
     git worktree remove .worktrees/issue-[number]/
     ```
   - Delete remote branch if not auto-deleted

### Worktree Best Practices

1. **One Issue, One Worktree**: Each issue gets its own isolated worktree
2. **Clean State**: Always start worktrees from latest main
3. **Regular Commits**: Commit progress frequently within worktree
4. **Task Metadata**: Use `.task/` directory for tracking progress
5. **Proper Cleanup**: Remove worktrees after PR merge to save space

### Example Workflow

```bash
# 1. Create worktree for issue 44
ISSUE_NUMBER="44"
BRANCH_NAME="docs/issue-44-worktree-lifecycle"
WORKTREE_DIR=".worktrees/issue-44"

git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" origin/main

# 2. Navigate to worktree
cd .worktrees/issue-44/

# 3. Make changes
# ... edit files ...

# 4. Commit changes
git add .
git commit -m "docs: add worktree lifecycle documentation

- Document when to use worktrees
- Add lifecycle phases
- Include best practices
- Provide example workflow"

# 5. Push and create PR
git push -u origin docs/issue-44-worktree-lifecycle
gh pr create --base main --title "docs: add worktree lifecycle documentation" \
  --body "Closes #44

Added comprehensive documentation for worktree lifecycle management."

# 6. After merge, cleanup
cd ../..
git worktree remove .worktrees/issue-44/
```

### Worktree Management Patterns

#### Automatic Branch Naming
```bash
# Derive branch type from issue title
get_branch_type() {
    case "$1" in
        *fix*|*bug*) echo "fix" ;;
        *feat*|*add*) echo "feature" ;;
        *docs*) echo "docs" ;;
        *test*) echo "test" ;;
        *) echo "feature" ;;
    esac
}

BRANCH_TYPE=$(get_branch_type "$ISSUE_TITLE")
BRANCH_NAME="${BRANCH_TYPE}/issue-${ISSUE_NUMBER}-${ISSUE_SLUG}"
```

#### Task Metadata Management
```bash
# Initialize comprehensive task metadata
cat > "$WORKTREE_DIR/.task/metadata.json" << EOF
{
  "issue_number": ${ISSUE_NUMBER},
  "branch": "${BRANCH_NAME}",
  "created": "$(date -Iseconds)",
  "phases_completed": [],
  "current_phase": 1
}
EOF
```

#### Parallel Work Coordination
When executing multiple tasks:
1. Create worktrees for each task
2. Track PIDs for process monitoring
3. Aggregate results after completion
4. Clean up all worktrees when done

Use worktrees whenever working on issues to maintain clean, isolated development environments.

## UV Virtual Environment Setup for Agents

**CRITICAL**: All agents working in worktrees on UV Python projects MUST properly set up virtual environments.

### UV Project Detection

Agents must detect UV projects by checking for both:
- `pyproject.toml` file
- `uv.lock` file

### Required UV Setup in Worktrees

When agents create or work in worktrees for UV projects, they MUST:

1. **Always run UV sync after entering worktree**:
   ```bash
   cd .worktrees/task-*/
   uv sync --all-extras
   ```

2. **Use `uv run` prefix for all Python commands**:
   ```bash
   # Correct UV usage
   uv run python script.py
   uv run pytest tests/
   uv run ruff check .
   uv run black .

   # NEVER run directly (will fail in UV projects)
   python script.py     # ❌ Wrong
   pytest tests/        # ❌ Wrong
   ```

### UV Setup Script for Agents

All agents should use the shared UV setup script: `.claude/scripts/setup-uv-env.sh`

#### Basic Usage for Agents:
```bash
# Set up UV environment in current worktree
source .claude/scripts/setup-uv-env.sh
setup_uv_environment "$(pwd)" "--all-extras"

# Check if environment is healthy
check_uv_environment "$(pwd)"

# Run commands with UV
uv_run "$(pwd)" pytest tests/
uv_run_python "$(pwd)" script.py
```

#### Agent Integration Pattern:
```bash
# In agent scripts - always check for UV project first
if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
    echo "UV project detected - setting up virtual environment"
    source .claude/scripts/setup-uv-env.sh

    if setup_uv_environment "$(pwd)" "--all-extras"; then
        echo "UV environment ready"
        # Use uv_run for all subsequent Python commands
        uv_run_pytest "$(pwd)" tests/
    else
        echo "Failed to set up UV environment"
        exit 1
    fi
else
    echo "Not a UV project - using standard Python setup"
    # Standard Python setup for non-UV projects
fi
```

### Agent-Specific UV Requirements

#### WorktreeManager Agent
- MUST run `uv sync --all-extras` in `setup_worktree_environment()` function
- Should detect UV projects and set up virtual environment automatically
- Must update environment setup documentation

#### WorkflowManager Agent
- MUST check for UV project when starting any workflow
- MUST use `uv run` prefix for all Python commands in UV projects
- Should validate UV environment before running tests or scripts

#### OrchestratorAgent
- MUST coordinate UV setup across all parallel worktrees
- Should pass UV project status to sub-agents
- Must ensure consistent UV environment setup across all workers

### UV Environment Commands Reference

| Task | UV Command | Notes |
|------|------------|-------|
| Setup environment | `uv sync --all-extras` | Run once per worktree |
| Run Python script | `uv run python script.py` | Always use uv run |
| Run tests | `uv run pytest tests/` | Never run pytest directly |
| Format code | `uv run ruff format .` | UV manages tool versions |
| Lint code | `uv run ruff check .` | Consistent tool versions |
| Add dependency | `uv add package` | Updates pyproject.toml |
| Add dev dependency | `uv add --group dev package` | For development tools |

### Troubleshooting UV Issues

#### "Module not found" errors in agents:
```bash
# Always check if you're using uv run
uv run python script.py  # ✅ Correct
python script.py         # ❌ Wrong - will fail

# Ensure environment is synced
uv sync --all-extras
```

#### "uv: command not found" in worktrees:
```bash
# Check UV installation
which uv
uv --version

# Install UV if missing
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Virtual environment not found:
```bash
# Re-run setup
uv sync --all-extras

# Check environment health
source .claude/scripts/setup-uv-env.sh
check_uv_environment "$(pwd)"
```

### UV Environment Validation

Agents should validate UV environments before executing Python code:

```bash
# Validation checklist for agents
validate_uv_environment() {
    local worktree_path="$1"
    cd "$worktree_path"

    # Check UV project files
    if [[ ! -f "pyproject.toml" || ! -f "uv.lock" ]]; then
        echo "Not a UV project"
        return 1
    fi

    # Check UV installation
    if ! command -v uv &> /dev/null; then
        echo "UV not installed"
        return 1
    fi

    # Check virtual environment
    if [[ ! -d ".venv" ]]; then
        echo "Virtual environment not found - running uv sync"
        uv sync --all-extras
    fi

    # Test Python access
    if ! uv run python -c "import sys; print('Python ready')"; then
        echo "UV environment not working"
        return 1
    fi

    return 0
}
```

## Testing and Quality Assurance Requirements for Agents

All agents working in development workflows MUST follow these testing and quality assurance requirements. This is a mandatory part of all workflow phases, especially Phase 6 (Testing).

### Mandatory Testing Commands by Project Type

#### For UV Python Projects (Recommended - Most Projects)

All agents MUST detect UV projects and use the appropriate commands:

```bash
# Detection: Check for both pyproject.toml and uv.lock
if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
    echo "UV project detected"

    # 1. Setup UV environment (required in all worktrees)
    uv sync --all-extras

    # 2. Run tests (MANDATORY - must pass to continue workflow)
    uv run pytest tests/ -v
    uv run pytest tests/ --cov=. --cov-report=html  # With coverage

    # 3. Run linting and formatting (MANDATORY)
    uv run ruff check .                    # Linting
    uv run ruff format .                   # Formatting

    # 4. Type checking (if configured)
    uv run mypy . --ignore-missing-imports  # Optional but recommended

    # 5. Pre-commit hooks (MANDATORY before PR creation)
    uv run pre-commit install             # One-time setup
    uv run pre-commit run --all-files     # MUST pass before PR
fi
```

#### For Standard Python Projects (Legacy)

```bash
# For non-UV projects (discouraged but supported)
if [[ ! -f "uv.lock" ]]; then
    echo "Standard Python project"

    # Activate virtual environment if available
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi

    # Run tests (MANDATORY)
    pytest tests/ -v
    pytest tests/ --cov=. --cov-report=html

    # Run linting and formatting (MANDATORY)
    ruff check .
    ruff format .

    # Pre-commit hooks (MANDATORY)
    pre-commit run --all-files  # Standard Python projects don't use 'uv run' prefix
fi
```

### Agent Testing Responsibilities by Phase

#### Phase 6: Testing Phase (ALL AGENTS MUST IMPLEMENT)

Every agent that executes workflows MUST implement these mandatory checks:

```bash
# Phase 6 Testing Implementation for Agents
execute_phase_6_testing() {
    local worktree_path="$1"
    cd "$worktree_path" || exit 1

    echo "🧪 PHASE 6: MANDATORY TESTING STARTED"

    # Step 1: Environment validation
    if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
        echo "✅ UV project detected"
        uv sync --all-extras || {
            echo "❌ UV environment setup failed"
            return 1
        }
        TEST_CMD="uv run pytest"
        LINT_CMD="uv run ruff"
    else
        echo "⚠️  Standard Python project (legacy mode)"
        TEST_CMD="pytest"
        LINT_CMD="ruff"
    fi

    # Step 2: Run tests (CANNOT PROCEED WITHOUT PASSING)
    echo "Running test suite..."
    $TEST_CMD tests/ -v --tb=short || {
        echo "❌ TESTS FAILED - Workflow cannot continue"
        echo "Fix all test failures before proceeding to Phase 7"
        return 1
    }

    # Step 3: Code quality checks (CANNOT PROCEED WITHOUT PASSING)
    echo "Running code quality checks..."
    $LINT_CMD check . || {
        echo "❌ LINTING FAILED - Workflow cannot continue"
        echo "Fix all linting issues before proceeding to Phase 7"
        return 1
    }

    $LINT_CMD format . --check || {
        echo "⚠️  Code formatting issues detected, auto-fixing..."
        $LINT_CMD format .
    }

    # Step 4: Pre-commit hooks (CANNOT PROCEED WITHOUT PASSING)
    echo "Running pre-commit hooks..."
    if [[ ! -f ".git/hooks/pre-commit" ]]; then
        echo "Installing pre-commit hooks..."
        if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
            uv run pre-commit install
        else
            pre-commit install
        fi
    fi

    if [[ -f "pyproject.toml" && -f "uv.lock" ]]; then
        uv run pre-commit run --all-files || {
    else
        pre-commit run --all-files || {
    fi
        echo "❌ PRE-COMMIT HOOKS FAILED - Workflow cannot continue"
        echo "Fix all pre-commit issues before proceeding to Phase 7"
        return 1
    }

    echo "✅ PHASE 6: ALL QUALITY GATES PASSED"
    echo "✅ Tests passed, linting passed, formatting passed, pre-commit passed"

    # Record test results for OrchestratorAgent validation
    echo "Recording test results..."
    record_phase_6_results "$worktree_path" "success"

    return 0
}

# Record Phase 6 results for orchestrator validation
record_phase_6_results() {
    local worktree_path="$1"
    local status="$2"

    local state_file="$worktree_path/.task/phase_6_testing.json"
    mkdir -p "$(dirname "$state_file")"

    cat > "$state_file" << EOF
{
    "phase_6_testing": {
        "completed": true,
        "status": "$status",
        "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
        "test_results": {
            "pytest_exit_code": 0,
            "precommit_exit_code": 0,
            "lint_exit_code": 0,
            "format_exit_code": 0,
            "skipped_tests": 0,
            "quality_gates_passed": true
        }
    }
}
EOF
}
```

#### Pre-PR Creation Validation (Phase 8)

Before creating any PR, agents MUST verify Phase 6 completion:

```bash
# Validate Phase 6 completion before PR creation
validate_pre_pr_requirements() {
    local worktree_path="$1"

    local phase_6_file="$worktree_path/.task/phase_6_testing.json"

    if [[ ! -f "$phase_6_file" ]]; then
        echo "❌ Phase 6 (Testing) was not completed - cannot create PR"
        echo "Run Phase 6 testing first"
        return 1
    fi

    local phase_6_status=$(jq -r '.phase_6_testing.status' "$phase_6_file")
    if [[ "$phase_6_status" != "success" ]]; then
        echo "❌ Phase 6 (Testing) failed - cannot create PR"
        echo "Fix all test failures before creating PR"
        return 1
    fi

    echo "✅ Phase 6 validation passed - ready for PR creation"
    return 0
}
```

### Quality Gate Enforcement

#### WorkflowManager Requirements

- MUST call `execute_phase_6_testing()` before Phase 7 (Documentation)
- MUST call `validate_pre_pr_requirements()` before Phase 8 (PR Creation)
- MUST NOT proceed if any quality gate fails
- MUST save test results for OrchestratorAgent validation

#### OrchestratorAgent Requirements

- MUST validate `phase_6_testing.json` exists for all completed tasks
- MUST check `test_results.quality_gates_passed` is true
- MUST NOT merge PRs from tasks that failed testing
- MUST report test validation failures clearly

### Pre-commit Configuration Validation

Agents should verify that `.pre-commit-config.yaml` includes these essential hooks:

```yaml
# Required pre-commit configuration
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [ --fix ]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict
      - id: debug-statements

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: uv run pytest  # or pytest for non-UV projects
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-push]
```

### Error Handling and Recovery

When testing fails, agents should:

1. **Log detailed error information** including which specific tests/checks failed
2. **Save workflow state** to allow resumption after fixes
3. **Provide clear guidance** on how to fix the failures
4. **NEVER bypass testing requirements** - no automatic skips allowed
5. **Wait for manual fixes** before continuing workflow

### Testing Documentation Requirements

All agents MUST document:
- Which testing commands they run
- How they detect UV vs standard Python projects
- What constitutes a "passing" test result
- How they record test results for validation
- What happens when tests fail

This ensures consistent, high-quality development practices across all agents and workflows.

## Troubleshooting: Orchestrator and Worktree Failures

When the mandatory orchestrator workflow encounters issues, use these troubleshooting procedures:

### Common Orchestrator Failures

#### 1. Orchestrator Agent Not Found
**Symptoms**: `/agent:orchestrator-agent` returns "agent not found" error
**Solution**:
```bash
# Check if orchestrator files exist
ls -la .claude/agents/orchestrator-agent.md
ls -la src/orchestrator/

# If missing, restore from main branch
git checkout main -- .claude/agents/orchestrator-agent.md
git checkout main -- src/orchestrator/
```

#### 2. Orchestrator Hangs or Times Out
**Symptoms**: Orchestrator starts but never completes, no progress updates
**Solution**:
```bash
# Kill hung orchestrator processes
pkill -f "claude.*orchestrator"
pkill -f "python.*orchestrator"

# Check system resources
df -h  # Disk space
free -h  # Memory (Linux) or vm_stat (macOS)

# Restart with verbose logging
/agent:orchestrator-agent
# Add troubleshooting flag if available
```

#### 3. Task Analysis Fails
**Symptoms**: Orchestrator fails during task decomposition phase
**Fallback Procedure**:
1. Try simpler task breakdown manually
2. Use WorkflowManager directly for single tasks:
   ```
   /agent:workflow-manager

   Task: Execute workflow for /prompts/[single-prompt].md
   ```
3. Execute critical tasks manually as last resort (document as emergency)

### Common Worktree Failures

#### 1. Worktree Creation Fails
**Symptoms**: "fatal: cannot create worktree" or permission errors
**Solution**:
```bash
# Check git repository status
git status
git worktree list

# Clean up existing worktrees if needed
git worktree prune

# Check disk space and permissions
df -h
ls -la .worktrees/

# Create worktree manually as fallback
git worktree add .worktrees/manual-fix-$(date +%s) -b manual-fix-branch
```

#### 2. Worktree Branch Conflicts
**Symptoms**: Branch already exists or checkout fails
**Solution**:
```bash
# List existing branches
git branch -a

# Remove conflicting remote branch
git push origin --delete conflicting-branch-name

# Clean up local references
git worktree prune
git branch -D conflicting-branch-name

# Try worktree creation again
```

#### 3. Worktree Cleanup Issues
**Symptoms**: Cannot remove worktree, "worktree locked" errors
**Solution**:
```bash
# Force unlock worktree
git worktree unlock .worktrees/stuck-worktree/

# Force remove worktree
git worktree remove --force .worktrees/stuck-worktree/

# Manual cleanup if needed
rm -rf .worktrees/stuck-worktree/
git worktree prune
```

### Fallback Strategies

#### 1. Orchestrator Unavailable - Use WorkflowManager
When orchestrator completely fails, use WorkflowManager for individual tasks:
```
/agent:workflow-manager

Task: [describe specific task]
Emergency fallback from orchestrator failure: [brief reason]
```

#### 2. WorkflowManager Unavailable - Manual Workflow
When both orchestrator and WorkflowManager fail:
1. **Document the failure** in an issue immediately
2. **Work in a regular branch** (not main):
   ```bash
   git checkout -b emergency-manual-fix-$(date +%s)
   ```
3. **Follow manual workflow**:
   - Make minimal, focused changes
   - Test thoroughly
   - Create PR with detailed explanation
   - Tag as `emergency` and `manual-workflow`

#### 3. Complete Agent System Failure
For extreme cases where all agents are unavailable:
1. **Create emergency issue** documenting the system failure
2. **Work carefully on feature branch** with manual procedures
3. **Document all steps taken** for post-incident analysis
4. **Restore agent system** before continuing normal development
5. **Conduct post-mortem** to prevent recurrence

### Recovery Procedures

#### 1. State Recovery
If orchestrator fails mid-execution:
```bash
# Check for state files
find . -name "*.orchestrator.state" -o -name "*.workflow.state"

# Review partial progress
cat .task/progress.json  # If exists

# Clean up partial work
git worktree list
# Remove failed worktrees as needed
```

#### 2. Resource Recovery
Clean up after failed orchestrator runs:
```bash
# Clean up processes
pkill -f "claude.*orchestrator"
pkill -f "python.*orchestrator"

# Clean up temporary files
find /tmp -name "*orchestrator*" -mtime +1 -delete
find /tmp -name "*worktree*" -mtime +1 -delete

# Clean up git worktrees
git worktree prune
```

#### 3. System Health Check
Before retrying failed operations:
```bash
# Check system resources
df -h                    # Disk space
ps aux | grep claude     # Running processes
git status              # Repository state
git worktree list       # Active worktrees

# Test basic agent functionality
/agent:task-analyzer
Simple test task analysis
```

### Prevention Measures

1. **Regular Maintenance**:
   - Run `git worktree prune` weekly
   - Monitor disk space before large operations
   - Keep agents updated with latest versions

2. **Monitoring**:
   - Watch for repeated failures in similar scenarios
   - Document failure patterns for system improvements
   - Monitor system resource usage during orchestration

3. **Backup Strategies**:
   - Keep known-good versions of agent files
   - Maintain manual procedure documentation
   - Regular testing of fallback procedures

### When to Escalate

Escalate to system maintainers when:
- Same failure occurs > 3 times
- Worktree system becomes completely unusable
- Agent files appear corrupted or missing
- System resource issues prevent normal operation
- Manual fallbacks also fail consistently

Remember: The goal is to maintain development velocity while preserving quality and safety standards.

## Memories and Best Practices

- Remember to not use artificial dev timescales in planning or estimating.
- **Core Value - Humility**: Always demonstrate humility in all development and communication. Never make claims of speedup or performance improvements without measured evidence. Focus on functionality and correctness over optimization claims. Let results speak for themselves.
