# Fix ALL Test File Pyright Errors (150+ errors)

## Target Directory
gadugi-v0.3/tests/

## Files to Fix
- test_worktree_manager.py (38 errors)
- test_test_writer.py (28 errors)
- test_workflow_manager.py (18 errors)
- test_code_reviewer.py (14 errors)
- test_agent_generator.py (12 errors)
- test_mcp_service.py (8 errors)
- ALL other test_*.py files

## Fix Pattern
Add this at the TOP of EVERY test file (before all other imports):

```python
import sys
import os
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "orchestrator"))
sys.path.insert(0, str(project_root / "services"))
sys.path.insert(0, str(project_root))
```

## Steps
1. Create branch: feature/pyright-test-fixes
2. Add import fix to ALL test files
3. Remove duplicate imports
4. Add missing imports like `os` where needed
5. Run `npx pyright gadugi-v0.3/tests/` to verify 0 errors
6. Create PR to feature/gadugi-v0.3-regeneration

## Success Criteria
- ALL test files have proper import setup
- `npx pyright gadugi-v0.3/tests/` shows 0 errors