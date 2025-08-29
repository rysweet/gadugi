# Claude AI Assistant Core Instructions

⚠️ **CRITICAL**: This is the refactored, streamlined version optimized for parallel task execution.

🚨 **WORKFLOW ENFORCEMENT ACTIVE**: ALL code changes MUST use orchestrator workflow.

## 🚀 Default Approach: Parallel Task Execution

**For ANY new task, ALWAYS:**
1. Analyze if it can be broken into parallel subtasks
2. Use the Task tool to spawn multiple Claude instances
3. Execute independent tasks simultaneously
4. Monitor and aggregate results

### Example Pattern
```
# When given: "Fix all type errors in the codebase"
# DO THIS (parallel):
Task 1: Fix .claude/agents errors
Task 2: Fix tests/ errors  
Task 3: Fix .claude/shared errors
Task 4: Fix orchestrator errors
# All execute simultaneously

# NOT THIS (sequential):
Fix file 1, then file 2, then file 3...
```

## 📋 Essential Instructions (ALWAYS Apply)

### 1. Memory Management
- **FIRST ACTION**: Read `.github/Memory.md` for context
- **UPDATE REGULARLY**: After completing significant tasks
- **COMMIT**: Memory.md changes to preserve context

### 2. UV Python Environment
**In UV projects (has `pyproject.toml` + `uv.lock`):**
- ✅ Always: `uv run python`, `uv run pytest`
- ❌ Never: `python`, `pytest` (without `uv run`)

### 3. Development Workflow
**For code changes:**
- Use orchestrator → WorkflowManager → 13 phases
- Never edit files directly
- Always create worktrees for isolation

### 4. 🚨 CRITICAL: Workflow Enforcement

**MANDATORY for ALL code changes:**

#### What Requires Orchestrator:
- ✅ Any file modification (.py, .js, .ts, .json, .md, etc.)
- ✅ Creating/deleting files or directories
- ✅ Installing/updating dependencies
- ✅ Configuration changes
- ✅ Git operations (commits, branches, merges)
- ✅ Bug fixes, features, refactoring

#### What Allows Direct Execution:
- ❌ Reading/analyzing existing files
- ❌ Answering questions about code
- ❌ Generating reports or documentation
- ❌ Searching/exploring codebase

#### The 11 Mandatory Phases:
1. **Task Validation** - Requirements validation
2. **Environment Setup** - Development environment prep
3. **Dependency Analysis** - Impact assessment
4. **Worktree Creation** - Isolated branch creation
5. **Implementation** - Code changes execution
6. **Testing** - Comprehensive test suites
7. **Quality Gates** - Type checking, linting, security
8. **Documentation** - Update relevant docs
9. **Review** - Code review and validation
10. **Integration** - Branch merging
11. **Cleanup** - Resource cleanup

#### Enforcement Mechanisms:
- Pre-execution validation hooks
- Real-time workflow monitoring
- Automated compliance checking
- Graceful violation handling with warnings

#### Workflow Validation:
```bash
# Check workflow compliance
.claude/workflow-enforcement/workflow-checker.py --task "your task" --files file1.py file2.py

# Quick workflow reminder
cat .claude/workflow-enforcement/workflow-reminder.md
```

#### Emergency Override:
Only for critical production issues - requires explicit justification and is logged.

### 5. PR Policy
- **NEVER merge without explicit user approval**
- Always wait for "merge it" or similar confirmation

## 📚 Task-Specific Instructions (Load When Needed)

### For Orchestration & Workflow Management
```bash
# Load when: Managing complex multi-task workflows
cat .claude/instructions/orchestration.md
```

### For Testing & Quality Assurance
```bash
# Load when: Running tests, fixing type errors, quality gates
cat .claude/instructions/testing-qa.md
# Type-fixing tools location: .claude/type-fixing-tools/
```

### For Worktree & Git Management
```bash
# Load when: Creating branches, managing worktrees, git operations
cat .claude/instructions/git-worktree.md
```

### For UV Environment Setup
```bash
# Load when: Setting up Python environments, managing dependencies
cat .claude/instructions/uv-environment.md
```

### For Troubleshooting
```bash
# Load when: Orchestrator fails, worktree issues, recovery needed
cat .claude/instructions/troubleshooting.md
```

### For Agent Development
```bash
# Load when: Creating or modifying agents
cat .claude/instructions/agent-development.md
```

## 🎯 Quick Decision Tree

**🚨 FIRST: Will this modify ANY files?** → ✅ MUST use orchestrator workflow
**Multiple related tasks?** → Use parallel Task execution  
**Working with Python?** → Check for UV project (`uv.lock` exists)
**Creating PR?** → Wait for user merge approval
**Tests failing?** → Load testing-qa.md
**Orchestrator issues?** → Load troubleshooting.md
**Read-only analysis?** → ✅ Direct execution OK

## 🔧 Core Tool Usage for Parallel Execution

### Launching Parallel Tasks
Use multiple Task tool invocations in a single message to execute in parallel.
Each task runs in its own Claude subprocess with focused context.

### Pattern Recognition for Parallelization
- **File-based work**: Each directory/module = separate task
- **Test fixes**: Group by test directory
- **Type errors**: Group by component
- **Documentation**: Separate task per doc type

## 🔗 Reference Links

- **Generic Instructions**: `claude-generic-instructions.md`
- **Guidelines**: `.claude/Guidelines.md`
- **Full Legacy CLAUDE.md**: `CLAUDE_LEGACY.md` (1,103 lines)

## ⚡ Performance Tips

1. **Batch Tool Calls**: Multiple tools in one message execute faster
2. **Parallel Over Sequential**: 3-5x faster for independent tasks
3. **Focus Context**: Give each parallel task only what it needs
4. **Early Validation**: Check prerequisites before spawning tasks

---
*This refactored version is ~100 lines vs 1,100 lines in the original.*
*Load task-specific instructions only when needed to minimize context usage.*