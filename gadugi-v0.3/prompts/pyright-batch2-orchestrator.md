# Fix Pyright Errors - Batch 2: Orchestrator Engines

## Task Description
Fix pyright errors in orchestrator engine files (42 errors total):

**Target Files:**
- `src/orchestrator/integration_test_agent_engine.py` (13 errors)
- `src/orchestrator/worktree_manager_engine.py` (12 errors)
- `src/orchestrator/workflow_manager_engine.py` (7 errors)
- `src/orchestrator/architect_engine.py` (4 errors)
- `src/orchestrator/memory_manager_engine.py` (3 errors)
- `src/orchestrator/gadugi_engine.py` (3 errors)

## Requirements
- Work on feature/gadugi-v0.3-regeneration branch
- Create feature branch: `fix/pyright-batch2-orchestrator`
- Fix actual type issues, don't just add ignore comments
- Common error patterns to fix:
  - Missing type annotations
  - Import resolution issues (add sys.path adjustments)
  - Undefined variables
  - Type mismatches
  - Missing return types
- Ensure pyright passes for these files after fixes
- Create PR to feature/gadugi-v0.3-regeneration branch

## Success Criteria
- All 42 errors in orchestrator engine files are resolved
- No new pyright errors introduced
- All files maintain functionality
- Clean, type-safe code with proper annotations