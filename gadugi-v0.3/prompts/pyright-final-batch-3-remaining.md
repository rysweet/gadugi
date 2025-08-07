# Pyright Type Safety Fix - Final Batch 3: Remaining Files

## Target: Fix 33 Errors in Test and Other Files

### Test Files (Import Resolution)

All test files need proper path setup. Add to the TOP of each test file:

```python
import sys
from pathlib import Path

# Set up paths for imports
test_dir = Path(__file__).parent
project_root = test_dir.parent

# Add all necessary paths
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "orchestrator"))
sys.path.insert(0, str(project_root / "services"))

# Now imports will work
from workflow_manager_engine import WorkflowManager
from worktree_manager_engine import WorktreeManager
```

#### Files to fix:
- tests/test_architect.py (4 errors)
- tests/test_workflow_manager.py
- tests/test_worktree_manager.py  
- tests/test_code_reviewer.py
- tests/test_memory_manager.py
- tests/test_team_coach.py
- tests/test_gadugi_engine.py
- All other test files with import errors

### Engine Files

#### architect_engine.py (4 errors)
Issues:
- Optional field handling in ArchitectureResponse
- Error response construction

Fixes:
```python
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class ArchitectureResponse:
    success: bool
    design: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    @classmethod
    def create_error(cls, error_msg: str) -> "ArchitectureResponse":
        return cls(success=False, error=error_msg)
```

### Remaining Engine Files
Fix type annotations in:
- prompt_writer_engine.py
- code_writer_engine.py  
- readme_agent_engine.py
- test_writer_engine.py
- execution_monitor_engine.py
- agent_generator_engine.py

Common fixes:
```python
# Add return types
def process(self, task: str) -> Dict[str, Any]:
    return {"result": "success"}

# Fix Optional handling
if self.config is not None:
    self.config.update(new_values)

# Add async types
async def generate(self) -> AsyncGenerator[str, None]:
    for item in items:
        yield item
```

## Requirements
- Branch from feature/gadugi-v0.3-regeneration
- Create feature branch: feature/pyright-final-batch-3-remaining
- Focus on test import fixes first (quick wins)
- Then fix remaining engine files
- Preserve all functionality