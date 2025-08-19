# Achieve Zero Pyright Errors for Team Coach Implementation

## Objective
Execute comprehensive pyright error fixes for the Team Coach implementation to achieve ZERO errors and meet mandatory quality compliance requirements.

## Context
Working in the task-team-coach worktree where the Team Coach component is extensively implemented with Phase 1, 2, and 3 functionality. Currently facing 1276 pyright errors that must be reduced to ZERO.

## Current Situation
- **Location**: `/Users/ryan/src/gadugi2/gadugi/.worktrees/task-team-coach`
- **Team Coach Status**: Extensively implemented with comprehensive functionality
- **Problem**: 1276 pyright errors preventing completion
- **Requirement**: Achieve ZERO pyright errors (Zero BS Principle)

## Key Error Categories Identified
1. **Import Resolution Issues**: Missing shared module imports
2. **Type Annotation Problems**: Missing or incorrect type hints
3. **Syntax Errors**: Indentation and structural issues
4. **Unused Imports/Variables**: Cleanup needed
5. **Missing Dependencies**: Some packages not available in UV environment

## Critical Files Needing Fixes
- `.claude/agents/shared_test_instructions.py` (syntax errors)
- All team-coach phase files with import issues
- Agent files with missing shared module imports
- Test files with unused imports

## Technical Requirements
1. **Fix ALL 1276 pyright errors to achieve ZERO errors**
2. **Maintain all existing Team Coach functionality**
3. **Use proper UV project commands** (`uv run pyright`, etc.)
4. **Follow mandatory quality gates** (pyright, ruff, tests)
5. **Preserve type safety throughout the codebase**

## Success Criteria
- `uv run pyright --stats` shows 0 errors, 0 warnings
- All Team Coach functionality preserved
- All tests passing with `uv run pytest`
- Proper type safety throughout
- Code passes `uv run ruff check` and `uv run ruff format`
- Pre-commit hooks passing
- Code review ready

## Implementation Strategy
1. **Systematic Error Analysis**: Run pyright with detailed output to categorize errors
2. **Import Resolution**: Fix missing shared module imports and dependencies
3. **Type Annotations**: Add proper type hints throughout the codebase
4. **Syntax Fixes**: Correct indentation and structural issues
5. **Code Cleanup**: Remove unused imports and variables
6. **Quality Validation**: Ensure all quality gates pass

## Priority
**CRITICAL** - This is a mandatory requirement for Team Coach completion and follows the Zero BS Principle of achieving actual ZERO errors, not approximations.
