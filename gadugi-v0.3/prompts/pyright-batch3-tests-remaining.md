# Fix Pyright Errors - Batch 3: Tests and Remaining Files

## Task Description
Fix pyright errors in test files and remaining components:

**Target Areas:**
- All test files with import errors (`tests/` directory)
- `services/event-router/event_router_service.py` (6 errors)
- `src/orchestrator/code_reviewer_engine.py` (3 errors)
- Any other remaining files with pyright errors

## Requirements
- Work on feature/gadugi-v0.3-regeneration branch
- Create feature branch: `fix/pyright-batch3-tests-remaining`
- Fix actual type issues, don't just add ignore comments
- Common error patterns to fix:
  - Missing type annotations
  - Import resolution issues (add sys.path adjustments)
  - Undefined variables
  - Type mismatches
  - Missing return types
  - Test import resolution
- Ensure pyright passes for all remaining files after fixes
- Create PR to feature/gadugi-v0.3-regeneration branch

## Success Criteria
- All remaining pyright errors (approximately 47 errors) are resolved
- All test files have proper imports and type annotations
- No new pyright errors introduced
- All files maintain functionality
- Clean, type-safe code with proper annotations