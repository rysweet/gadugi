# Claude AI Assistant Core Instructions

⚠️ **CRITICAL**: This is the refactored, streamlined version optimized for parallel task execution.

🚨 **WORKFLOW ENFORCEMENT ACTIVE**: ALL code changes MUST use orchestrator workflow.
⛔ **NO EMERGENCY OVERRIDES**: If blocked, FIX THE PROBLEM. Iterate until compliant.

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

### 2. Python Environment Management
**Two separate environments to consider:**

**Host Project** (root directory):
- If has `pyproject.toml` + `uv.lock`: Use `uv run` for host project code
- Otherwise: Use system Python or host's package manager

**Gadugi System** (.gadugi/ directory):
- Always has its own `pyproject.toml` + `uv.lock` in `.gadugi/`
- Use `./gadugi` wrapper script or `cd .gadugi && uv run`
- Completely isolated from host project dependencies

### 3. Development Workflow - 13-Phase Process
**For ANY code changes, follow these phases YOURSELF (no separate WorkflowManager agent):**

#### Phase 1: Requirements Analysis
- Parse the task/prompt
- Identify success criteria
- Extract constraints
- Define deliverables

#### Phase 2: Design Planning
- Architecture decisions
- Technology choices
- Component breakdown
- Interface definitions

#### Phase 3: Task Decomposition
- Break into subtasks
- Identify dependencies
- Estimate effort
- Assign priorities

#### Phase 4: Environment Setup
- Create worktree/branch
- Set up dependencies
- Configure tools
- Verify environment

#### Phase 5: Implementation
- Core functionality
- Follow TDD when possible
- Incremental commits
- Code documentation

#### Phase 6: Testing
- Unit tests
- Integration tests
- Edge cases
- Performance tests

#### Phase 7: Code Review Prep
- Self-review
- Linting
- Format code
- Update documentation

#### Phase 8: Quality Gates
- Type checking (pyright/mypy)
- Pre-commit hooks MUST pass
- Coverage requirements
- Performance benchmarks

#### Phase 9: Documentation
- API documentation
- Usage examples
- Configuration guide
- Changelog update

#### Phase 10: PR Creation
- Descriptive title
- Comprehensive description
- Link issues
- Add reviewers

#### Phase 11: CI/CD Validation
- Monitor CI pipeline
- Fix any failures
- Verify all checks pass
- Update if needed

#### Phase 12: Review Response
- Address feedback
- Make requested changes
- Discuss alternatives
- Update PR description

#### Phase 13: Merge & Cleanup
- Squash if needed
- Merge PR (WITH USER APPROVAL ONLY)
- Delete branch
- Update issues

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

#### ⛔ NO Emergency Overrides:
NEVER use emergency overrides. If workflow blocks you:
1. Fix the underlying problem
2. Iterate and improve until compliant
3. Emergency overrides = failure to follow process

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

## 📁 Repository Organization

**KEEP ROOT CLEAN** - Never create files in repository root:
- Scripts → `.claude/scripts/` or `scripts/`
- Tests → `tests/`
- Docs → `docs/` or `.claude/docs/`
- Services → `.claude/services/`
- Temp files → `/tmp/`
