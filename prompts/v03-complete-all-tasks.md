# Orchestrator: Complete ALL v0.3 Implementation Tasks

## CRITICAL DIRECTIVE
DO NOT STOP until ALL tasks are 100% complete with:
- Zero pyright errors
- All tests passing
- All worktrees cleaned up
- Full implementation of all components

## Governance Notice
ALL tasks MUST be delegated to WorkflowManager instances via 'claude -p' subprocess invocation as per Issue #148 requirements.

## Tasks for Execution (Priority Order)

### Task 1: Fix All Pyright Errors
- Prompt file: /Users/ryan/src/gadugi2/gadugi/prompts/v03-fix-pyright-errors.md
- Priority: CRITICAL (blocks everything else)
- Must achieve: 0 pyright errors across ALL components

### Task 2: Implement Team Coach
- Prompt file: /Users/ryan/src/gadugi2/gadugi/prompts/v03-implement-team-coach.md
- Priority: HIGH
- Must achieve: Full implementation with 0 errors

### Task 3: Complete Testing
- Prompt file: /Users/ryan/src/gadugi2/gadugi/prompts/v03-complete-testing.md
- Dependencies: Tasks 1 and 2 must complete first
- Must achieve: All tests passing, 80%+ coverage

### Task 4: Worktree Cleanup
- Prompt file: /Users/ryan/src/gadugi2/gadugi/prompts/v03-worktree-cleanup.md  
- Priority: HIGH (system hygiene)
- Must achieve: All worktrees cleaned, cleanup added to workflow

## Execution Plan
1. Execute Tasks 1 and 2 in parallel (both are independent)
2. Execute Task 3 after Tasks 1 and 2 complete
3. Execute Task 4 in parallel with Task 3
4. Verify ALL components have:
   - Zero pyright errors
   - Passing tests
   - Clean worktrees

## Success Criteria
- `uv run python validate_v03_implementation.py` shows 100% WORKING
- `git worktree list` shows only main worktree
- All GitHub issues created and PRs submitted
- System ready for production use

## IMPORTANT
- Each task MUST complete its full 11-phase workflow
- Use worktree isolation for each task
- All Python commands must use `uv run` prefix
- DO NOT STOP until everything is 100% complete

/agent:orchestrator-agent

Execute ALL tasks to 100% completion. Do not stop until everything is done.