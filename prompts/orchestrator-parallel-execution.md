# Orchestrator Parallel Execution Request

<<<<<<< HEAD
Execute the following three tasks in parallel through WorkflowManager delegation:

## Task 1: Fix Code-Review-Response Agent PR Merge Policy (Issue #256)
**Prompt File**: prompts/fix-code-review-merge-policy-256.md
**Priority**: CRITICAL
**Description**: Update the code-review-response agent to enforce PR merge approval policy - must ask for explicit user approval before merging any PR.

## Task 2: Remove Error Suppression from Critical Paths (Issue #249)
**Prompt File**: workflow_249.md (in .worktrees/issue-249-error-suppression/)
**Priority**: HIGH
**Description**: Audit and remove error suppression (2>/dev/null and stderr=subprocess.DEVNULL) from critical code paths in tests and agent invocations.

## Task 3: Add Agent Registration Validation (Issue #248)
**Prompt File**: prompts/add-agent-registration-validation-248.md
**Priority**: HIGH
**Description**: Create comprehensive agent registration validation system for CI/CD with validation script, GitHub Actions workflow, and pre-commit hooks.

## Execution Requirements

1. **MANDATORY**: Create separate worktrees for each task
2. **MANDATORY**: Delegate ALL tasks to WorkflowManager instances
3. **MANDATORY**: Execute all 13 workflow phases for each task
4. **MANDATORY**: NO direct execution - only delegation

## Expected Workflow

For each task:
1. Create isolated worktree via worktree-manager
2. Delegate to WorkflowManager with proper prompt
3. Monitor WorkflowManager execution through all 13 phases
4. Validate completion and test results
5. Report status back

## Success Criteria

- All three tasks execute in parallel
- Each task has its own worktree (`.worktrees/task-*`)
- Each task has workflow state tracking (`.github/workflow-states/task-*`)
- All tests pass for each task
- PRs created for each task (but NOT merged without approval)
=======
Execute the following two tasks in parallel to complete the Gadugi v0.3 implementation:

## Tasks to Execute

### Task 1: implement-task-decomposer-agent.md
- Implement the Task Decomposer agent (#240)
- Location: `.claude/agents/task-decomposer/`
- Requirements: Break complex tasks into subtasks, identify dependencies, estimate parallelization potential
- Must inherit from BaseAgent framework and be pyright clean

### Task 2: implement-team-coach-agent.md  
- Implement the Team Coach agent (#241)
- Location: `.claude/agents/team-coach/`
- Requirements: Auto-analyze sessions, identify improvements, create GitHub issues, track performance
- Must inherit from BaseAgent framework and be pyright clean

## Execution Requirements

1. **Parallel Execution**: Both tasks should be executed simultaneously in separate worktrees
2. **Quality Standards**: All code must pass `uv run pyright` with zero errors
3. **Testing**: Include comprehensive test suites for both agents
4. **Integration**: Both agents must integrate with Event Router and Memory System
5. **Documentation**: Complete documentation for both agents

## Expected Outcomes

- Two new agents fully implemented and tested
- Zero pyright errors in all new code
- Comprehensive test coverage
- Full integration with existing Gadugi v0.3 framework
- Recipe files properly configured
- Documentation complete

Please execute these tasks in parallel for maximum efficiency.
>>>>>>> origin/feature/gadugi-v0.3-regeneration
