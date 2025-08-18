# AI Assistant Instructions

This file combines generic Claude Code best practices with project-specific instructions for the AI-SIP workshop repository.

⚠️ **FIRST ACTION**: Check and update @.github/Memory.md ! ⚠️
⚠️ **NEW**: Memory.md now syncs with GitHub Issues via MemoryManagerAgent! ⚠️

⚠️ **SECOND ACTION**: When working on Claude agents or instructions, read https://docs.anthropic.com/en/docs/claude-code/memory ! ⚠️

---

## CRITICAL: UV Python Environment Usage

**In UV projects (with `pyproject.toml` and `uv.lock`), ALWAYS prefix Python commands with `uv run`:**
- ✅ `uv run python script.py`
- ✅ `uv run pytest tests/`
- ❌ Never: `python script.py` or `pytest tests/`

---

## CRITICAL: Workflow Execution Pattern

⚠️ **MANDATORY ORCHESTRATOR AND WORKFLOW MANAGER USAGE** ⚠️

## Every Repository File Change Must Use the Orchestrator to Invoke the Workflow via the Workflow Manager - No Exceptions

Any time there are changes to repository files required - whether it's fixing YAML
frontmatter, updating documentation, modifying configs, or writing code - you must
use the orchestrator to invoke the workflow via the workflow manager.

This means:
1. You invoke /agent:orchestrator-agent with a prompt file
2. The orchestrator creates worktrees and invokes workflow-manager
3. The workflow-manager executes all 13 phases
4. You NEVER edit files directly

This includes:
- Fixing CI failures (even "simple" ones)
- Adding missing metadata to agent files
- Updating README or documentation
- Changing configuration files
- Modifying ANY file that gets committed to git

Your brain will try to categorize some changes as "too trivial" or "not really code"
to justify skipping this chain. Don't. If it's going to be committed to the
repository, it must go through orchestrator → workflow-manager → 13 phases.

The complete chain is mandatory because:
- Orchestrator alone isn't enough (it must delegate to workflow-manager)
- Workflow-manager ensures Phase 9 (Code Review) happens
- Phase 10 (Review Response) addresses feedback
- All changes get proper tracking and validation

**VERIFICATION CHECKLIST:**
- ✅ Worktree created in `.worktrees/` directory
- ✅ Workflow state in `.github/workflow-states/task-*`
- ✅ All 13 phases documented in PR
- ✅ Phase tracking shows completion
- ❌ If these don't exist, workflow was NOT properly executed

This ensures:
- Proper worktree isolation for all changes
- Consistent branch management
- Complete workflow tracking
- Parallel execution when possible
- Professional development practices

**For ANY task that modifies code, configuration, or documentation files:**

1. **NEVER manually edit files directly**
2. **ALWAYS use the orchestrator agent as the entry point**

## ⚠️ CRITICAL: How the Orchestrator ACTUALLY Works

The orchestrator is NOT just a concept - it's a fully working implementation that:

### 1. Creates Prompt Files
For each task, create a prompt file in `/prompts/` directory:
```bash
# Example: /prompts/fix-bug-issue-256.md
Task: Fix the code-review-response agent merge policy violation
Issue: #256
Requirements:
- Update agent to ask for user approval before merging
- Add clear prompt waiting for user permission
```

### 2. Invokes via Claude CLI with SPECIFIC FLAGS
The orchestrator uses this EXACT command structure:
```bash
claude \
  -p "Read and follow the instructions in the file: /prompts/[task].md" \
  --dangerously-skip-permissions \
  --verbose \
  --max-turns=2000 \
  --output-format json
```

### 3. Parallel Execution Architecture
- **orchestrator_main.py**: Central coordination engine
- **process_registry.py**: Process tracking and monitoring
- **execution_engine.py**: Spawns subprocess.Popen with claude commands
- **worktree_manager.py**: Creates isolated `.worktrees/task-*` directories

### 4. CORRECT Invocation Pattern
```
/agent:orchestrator-agent

Execute these specific prompts in parallel:
- fix-bug-issue-256.md
- add-validation-issue-248.md
- remove-suppression-issue-249.md
```

### 5. What Actually Happens
1. Orchestrator reads prompt files from `/prompts/`
2. Creates worktrees in `.worktrees/task-[id]/`
3. Spawns parallel `claude` processes with JSON output
4. Each process runs workflow-manager in its worktree
5. Monitors execution via process_registry
6. Collects results and handles failures

**The Orchestrator will automatically**:
   - Create worktrees using worktree-manager
   - Spawn REAL parallel claude processes
   - Monitor execution with process tracking
   - Handle failures with fallback to sequential

## ❌ DO NOT DO THESE (Common Mistakes)

### Wrong Way 1: Direct Claude Invocation
```bash
# NEVER DO THIS - loses all tracking and logs
claude -p prompts/fix-bug.md
```

### Wrong Way 2: Made-up Commands
```bash
# NEVER INVENT COMMANDS - orchestrator has specific implementation
orchestrator-agent execute --parallel --tasks="..."  # NOT A REAL COMMAND
```

### Wrong Way 3: Direct File Editing
```python
# NEVER EDIT FILES DIRECTLY - always use orchestrator
with open('file.py', 'w') as f:
    f.write(new_content)
```

### Wrong Way 4: Skipping Prompt Files
```
# NEVER TRY TO EXECUTE WITHOUT PROMPT FILES
/agent:orchestrator-agent
Fix these bugs: [list]  # WRONG - need actual prompt files
```

## ✅ CORRECT WAY (The ONLY Way)

1. **Create prompt files** in `/prompts/` for each task
2. **Invoke orchestrator** with list of prompt files
3. **Let it handle everything** - worktrees, parallel execution, monitoring
4. **Check results** in `.worktrees/task-*/` and workflow states

4. **Agent Hierarchy**:
   - **OrchestratorAgent**: REQUIRED entry point for ALL code changes
   - **WorktreeManager**: Automatically invoked by orchestrator for isolation
   - **WorkflowManager**: Handles individual workflow execution (MANDATORY for all tasks)
   - **Code-Reviewer**: Executes Phase 9 reviews

**⚠️ GOVERNANCE ENFORCEMENT**:
- The OrchestratorAgent MUST ALWAYS delegate ALL task execution to WorkflowManager instances
- Direct execution is STRICTLY PROHIBITED
- If orchestrator executes directly without workflow-manager, this is a CRITICAL VIOLATION
- Every task MUST show evidence of:
  - Worktree creation (`.worktrees/task-*`)
  - Workflow state (`.github/workflow-states/task-*`)
  - 13 phase execution
- WITHOUT this evidence, the task was improperly executed and must be rejected

5. **Automated Workflow Handling**:
   - Issue creation
   - Worktree and branch management
   - Implementation tracking
   - PR creation
   - Code review invocation (Phase 9)
   - State management

6. **Mandatory 13-Phase Workflow** (ALL tasks MUST follow):
   - Phase 1: Initial Setup
   - Phase 2: Issue Creation
   - Phase 3: Branch Management
   - Phase 4: Research and Planning
   - Phase 5: Implementation
   - Phase 6: Testing
   - Phase 7: Documentation
   - Phase 8: Pull Request
   - Phase 9: Review (code-reviewer invocation)
   - Phase 10: Review Response
   - Phase 11: Settings Update
   - Phase 12: Deployment Readiness (when applicable)
   - Phase 13: Team Coach Reflection (MANDATORY - session end)

**Only execute manual steps for**:
- Read-only operations (searching, viewing files)
- Answering questions about the codebase
- Running tests or builds without changes
- Direct user requests for specific read-only actions

**Before ANY task, ask yourself**:
- Will this change version-controlled files? → MUST use OrchestratorAgent
- Multiple related tasks? → Use OrchestratorAgent
- Single task with code changes? → Use OrchestratorAgent
- Read-only investigation? → Can execute manually

**Workflow Validation Requirements**:
- Orchestrator MUST delegate ALL tasks to WorkflowManager
- ALL 13 workflow phases MUST be executed for every task
- NO direct execution bypassing workflow phases
- State tracking MUST be maintained throughout all phases
- Quality gates MUST be validated at each phase transition
- Phase 13 (Team Coach Reflection) MUST execute at session end for continuous improvement

**Enforcement Examples**:
- ✅ **Compliant**: `/agent:orchestrator-agent` → delegates to `/agent:workflow-manager` for each task
- ❌ **Violation**: Using `claude -p prompt.md` directly bypasses workflow phases
- ❌ **Violation**: Direct shell script execution without issue creation and PR workflow
- ✅ **Validation**: Pre-execution checks verify WorkflowManager delegation for all tasks
- ⚠️ **Detection**: Governance violations logged with specific error types and task IDs

### Phase 13: Team Coach Reflection Details

**Purpose**: Automatic session-end analysis for continuous improvement and learning.

**When Executed**:
- Automatically after Phase 12 completion
- At the end of every workflow session
- Before final state cleanup

**What It Does**:
1. **Performance Analysis**: Reviews metrics from all completed phases
2. **Pattern Recognition**: Identifies success patterns and improvement areas
3. **Recommendation Generation**: Creates actionable improvement suggestions
4. **Memory Update**: Saves insights to Memory.md for future reference
5. **Issue Creation**: Optionally creates GitHub issues for significant improvements

**Implementation Safety**:
- No subprocess spawning - uses direct agent invocation
- Timeout protection (max 2 minutes)
- Graceful degradation if Team Coach fails
- Non-blocking - workflow completes even on failure
- Prevents infinite loops through state tracking

**Benefits**:
- Automated performance tracking
- Continuous process improvement
- Knowledge accumulation in Memory.md
- Reduced manual review overhead
- Data-driven workflow optimization

### Emergency Procedures (Critical Production Issues)

⚠️ **EMERGENCY HOTFIX EXCEPTION** ⚠️

For **CRITICAL PRODUCTION ISSUES** requiring immediate fixes (security vulnerabilities, system downtime, data corruption), you may bypass the orchestrator requirement:

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

   Emergency hotfix bypassing normal orchestrator workflow
   due to production impact. Full workflow to follow.

   Fixes: [issue-number]"
   ```
5. **Immediately create follow-up issue** for proper workflow implementation
6. **Return to orchestrator requirement** for all subsequent changes

**Post-Emergency Actions**:
- Conduct immediate post-mortem
- Implement proper tests via orchestrator workflow
- Update documentation to prevent recurrence
- Review emergency decision in next team meeting

**Important**: Emergency exception should be used < 1% of the time. If used frequently, reassess development practices.

---

## Generic Claude Code Instructions

@claude-generic-instructions.md

## Project-Specific Instructions

Note: Project-specific instructions are integrated directly into this file above.

## Gadugi Development Guidelines

@.claude/Guidelines.md

---

## Worktree Lifecycle Management

**IMPORTANT**: Use the worktree-manager agent for creating isolated development environments for issues.

### When to Use Worktrees

Use worktrees for:
- Working on individual issues that require code changes
- Isolating development work from the main repository
- Preventing conflicts when multiple issues are being worked on
- Creating clean environments for testing and validation

### Worktree Lifecycle

1. **Creation Phase**:
   ```
   /agent:worktree-manager

   Create a new git worktree for issue [number].
   Branch name: [type]/issue-[number]-[description]
   ```
   - Creates isolated worktree in `.worktrees/issue-[number]/`
   - Sets up new branch from main
   - Initializes task metadata in `.task/` directory

2. **Development Phase**:
   - Navigate to worktree: `cd .worktrees/issue-[number]/`
   - All development happens in isolated environment
   - Changes don't affect main repository or other worktrees
   - Commit changes regularly with descriptive messages

3. **PR Creation Phase**:
   - Push branch from within worktree
   - Create PR using `gh pr create` from worktree directory
   - Reference issue number in PR description
   - **CRITICAL: Never merge PRs without explicit user approval** (see PR Merge Policy below)

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
/agent:worktree-manager
Create worktree for issue 44 about documenting lifecycle

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

### Worktree Agent Integration

The worktree-manager agent handles:
- Automatic branch naming based on issue type
- Task metadata initialization
- Proper isolation from main repository
- State tracking for development progress
- Integration with orchestrator for parallel work

Use worktrees whenever working on issues to maintain clean, isolated development environments.

## PR Merge Approval Policy

**⚠️ CRITICAL: NEVER merge PRs without explicit user approval**

### Required Workflow for PR Completion

1. **Create PR** - Use `gh pr create` with proper description
2. **Execute Code Review** - Phase 9 with code-reviewer agent
3. **Address Feedback** - Phase 10 with review response
4. **STOP AND WAIT** - Report PR status to user
5. **Only merge when user explicitly says to** - Wait for "merge it", "please merge", or similar

### Correct Pattern
```
Assistant: "PR #123 has passed review and all checks are green.
          Ready for merge. Awaiting your approval to proceed."
User: "Please merge it"
Assistant: [Now executes: gh pr merge 123]
```

### Incorrect Pattern (DO NOT DO THIS)
```
Assistant: "PR passed review, merging now..."  ❌
Assistant: [Auto-merges without asking]        ❌
```

### Why This Policy Exists
- User maintains control over main branch
- Allows final review before merge
- Prevents unwanted changes from entering production
- Ensures user awareness of all merges

### Commands Reference
```bash
# View PR status (always allowed)
gh pr view <pr-number>
gh pr checks <pr-number>

# Merge PR (ONLY with explicit user approval)
gh pr merge <pr-number> --merge --delete-branch
```

Remember: Even if all checks pass and review is approved, ALWAYS wait for explicit user permission before merging.

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
