# Fix Engine File Pyright Errors (19 errors)

## Target Files
- gadugi-v0.3/src/orchestrator/worktree_manager_engine.py (12 errors)
- gadugi-v0.3/src/orchestrator/workflow_manager_engine.py (7 errors)

## Fix Patterns

### Subprocess Types
```python
import subprocess
from typing import Dict, Any, Optional, List

def run_command(self, cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )
```

### Optional Returns
```python
def get_current_branch(self) -> Optional[str]:
    result = self.run_command(["git", "branch", "--show-current"])
    if result.returncode == 0 and result.stdout:
        return result.stdout.strip()
    return None
```

### Async Functions
```python
async def execute_phase(self, phase: str) -> Dict[str, Any]:
    # implementation
    return {"status": "complete", "phase": phase}
```

## Steps
1. Create branch: feature/pyright-engine-fixes
2. Fix worktree_manager_engine.py type annotations
3. Fix workflow_manager_engine.py type annotations
4. Add proper return types for all functions
5. Run `npx pyright gadugi-v0.3/src/orchestrator/` to verify 0 errors
6. Create PR to feature/gadugi-v0.3-regeneration

## Success Criteria
- Both engine files have 0 pyright errors
- All functions have proper return type annotations
- Subprocess operations properly typed