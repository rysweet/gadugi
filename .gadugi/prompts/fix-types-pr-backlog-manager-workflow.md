# WorkflowManager Task Execution

## Task Information
- **Task ID**: fix-types-PrBacklogManager
- **Task Name**: fix-types-PrBacklogManager
- **Original Prompt**: /Users/ryan/src/gadugi/.worktrees/task-fix-types-PrBacklogManager/prompts/fix-types-PrBacklogManager-workflow.md
- **Phase Focus**: Full Implementation

## Implementation Requirements

- Maintain test functionality and coverage
- Use typing.Protocol for mock object interfaces
- Add comprehensive type hints to test fixtures
- Ensure no runtime behavior changes
```

---

**Execute the complete WorkflowManager workflow for this task.**

## Technical Specifications

See original prompt for technical details.

## Implementation Plan

Follow the implementation steps from the original prompt.

## Success Criteria

Complete all phases successfully with working implementation.

## Execution Instructions

**CRITICAL**: You are executing as WorkflowManager in a parallel execution environment.

1. **Complete All 9 Phases**: Execute the full WorkflowManager workflow
   - Phase 1: Initial Setup (analyze this prompt)
   - Phase 2: Issue Management (link to existing issue if provided)
   - Phase 3: Branch Management (you're already in the correct branch)
   - Phase 4: Research and Planning
   - Phase 5: **IMPLEMENTATION** (CREATE ACTUAL FILES - this is critical)
   - Phase 6: Testing
   - Phase 7: Documentation
   - Phase 8: Pull Request Creation
   - Phase 9: Code Review

2. **File Creation is Mandatory**: You MUST create actual implementation files, not just update Memory.md

3. **Context Preservation**: All implementation context is provided above

4. **Worktree Awareness**: You are executing in an isolated worktree environment

## Target Files
Target files will be determined during implementation phase.

## Dependencies
No specific dependencies identified.

## Original Prompt Content

```markdown
# WorkflowManager Task Execution

## Task Information
- **Task ID**: fix-types-PrBacklogManager
- **Task Name**: Fix Type Errors in PR Backlog Manager Tests
- **Original Prompt**: /Users/ryan/src/gadugi/prompts/fix-types-PrBacklogManager.md
- **Phase Focus**: Full Implementation

## Implementation Requirements

- Maintain test functionality and coverage
- Use typing.Protocol for mock object interfaces
- Add comprehensive type hints to test fixtures
- Ensure no runtime behavior changes

## Technical Specifications

See original prompt for technical details.

## Implementation Plan

Follow the implementation steps from the original prompt.

## Success Criteria

Complete all phases successfully with working implementation.

## Execution Instructions

**CRITICAL**: You are executing as WorkflowManager in a parallel execution environment.

1. **Complete All 9 Phases**: Execute the full WorkflowManager workflow
   - Phase 1: Initial Setup (analyze this prompt)
   - Phase 2: Issue Management (link to existing issue if provided)
   - Phase 3: Branch Management (you're already in the correct branch)
   - Phase 4: Research and Planning
   - Phase 5: **IMPLEMENTATION** (CREATE ACTUAL FILES - this is critical)
   - Phase 6: Testing
   - Phase 7: Documentation
   - Phase 8: Pull Request Creation
   - Phase 9: Code Review

2. **File Creation is Mandatory**: You MUST create actual implementation files, not just update Memory.md

3. **Context Preservation**: All implementation context is provided above

4. **Worktree Awareness**: You are executing in an isolated worktree environment

## Target Files
Expected files to be created/modified:
- `tests/agents/pr_backlog_manager/test_delegation_coordinator.py`
- `tests/agents/pr_backlog_manager/test_core.py`
- `tests/agents/pr_backlog_manager/test_integration.py`
- `tests/agents/pr_backlog_manager/test_readiness_assessor.py`
- `tests/agents/pr_backlog_manager/test_github_actions_integration.py`


## Dependencies
No specific dependencies identified.

## Original Prompt Content

```markdown
# Fix Type Errors in PR Backlog Manager Tests

## Objective
Fix all pyright type errors in the PR Backlog Manager agent test files, which account for ~330 errors.

## Target Files
- tests/agents/pr_backlog_manager/test_delegation_coordinator.py (142 errors)
- tests/agents/pr_backlog_manager/test_core.py (57 errors)
- tests/agents/pr_backlog_manager/test_integration.py (48 errors)
- tests/agents/pr_backlog_manager/test_readiness_assessor.py (46 errors)
- tests/agents/pr_backlog_manager/test_github_actions_integration.py (39 errors)

## Focus Areas
1. **reportAttributeAccessIssue**: Fix mock object attribute access with proper type stubs
2. **reportOptionalSubscript**: Handle optional dictionary/list access properly
3. **reportOptionalMemberAccess**: Add None checks before accessing optional attributes

## Strategy
1. Create type stubs for mock objects used in tests
2. Add proper None checks for optional values
3. Use Union types where multiple types are possible
4. Ensure all GitHub API mock responses have correct types
5. Fix delegation status and state type issues

## Requirements
- Maintain test functionality and coverage
- Use typing.Protocol for mock object interfaces
- Add comprehensive type hints to test fixtures
- Ensure no runtime behavior changes
```

---

**Execute the complete WorkflowManager workflow for this task.**

```

---

**Execute the complete WorkflowManager workflow for this task.**
