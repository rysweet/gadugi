# Fix ALL 226 Pyright Errors in Gadugi v0.3

## Critical Mission
Fix ALL 226 pyright errors in gadugi-v0.3 to achieve complete type safety.

## Phase 1: Test Files (150+ errors)
**Directory**: gadugi-v0.3/tests/

### Fix for ALL test files
Add this at the TOP of EVERY test_*.py file (before all other imports):
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

### Common issues to fix:
- Remove duplicate sys.path.insert lines
- Add missing `import os` where needed
- Ensure imports come AFTER the path setup

## Phase 2: Service Files (43 errors)

### gadugi-v0.3/services/neo4j-graph/neo4j_graph_service.py
Fix imports:
```python
try:
    from neo4j import GraphDatabase, AsyncGraphDatabase  # type: ignore[import]
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None
    AsyncGraphDatabase = None
```

Fix dataclass fields:
```python
from dataclasses import dataclass, field
@dataclass
class NodeData:
    labels: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
```

### gadugi-v0.3/services/mcp/mcp_service.py
Fix Redis import:
```python
try:
    import redis  # type: ignore[import]
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
```

## Phase 3: Engine Files (19 errors)

### gadugi-v0.3/src/orchestrator/worktree_manager_engine.py
Fix subprocess types:
```python
import subprocess
from typing import Optional, List

def run_command(self, cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)

def get_current_branch(self) -> Optional[str]:
    result = self.run_command(["git", "branch", "--show-current"])
    if result.returncode == 0 and result.stdout:
        return result.stdout.strip()
    return None
```

### gadugi-v0.3/src/orchestrator/workflow_manager_engine.py
Fix async types:
```python
from typing import Dict, Any
async def execute_phase(self, phase: str) -> Dict[str, Any]:
    return {"status": "complete", "phase": phase}
```

## Workflow Steps
1. Create branch: feature/pyright-complete-fix
2. Fix ALL test files first
3. Fix service files
4. Fix engine files
5. Run `npx pyright gadugi-v0.3` to verify
6. Create PR to feature/gadugi-v0.3-regeneration

## Success Criteria
- `npx pyright gadugi-v0.3` shows "0 errors, 0 warnings"
- All files properly typed
- PR passes CI checks