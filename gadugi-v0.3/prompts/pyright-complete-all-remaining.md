# Complete Pyright Type Safety - Fix ALL 226 Remaining Errors

## Current State
226 pyright errors remain in gadugi-v0.3 after previous fixes

## Error Distribution
```
38 errors - tests/test_worktree_manager.py
34 errors - services/neo4j-graph/neo4j_graph_service.py
28 errors - tests/test_test_writer.py
18 errors - tests/test_workflow_manager.py
14 errors - tests/test_code_reviewer.py
12 errors - tests/test_agent_generator.py
12 errors - src/orchestrator/worktree_manager_engine.py
9 errors - services/mcp/mcp_service.py
8 errors - tests/test_mcp_service.py
7 errors - src/orchestrator/workflow_manager_engine.py
... and more
```

## CRITICAL FIX PATTERNS

### For ALL Test Files (Fix Import Issues)
Add this to the TOP of EVERY test file:
```python
import sys
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "orchestrator"))
sys.path.insert(0, str(project_root / "services"))
sys.path.insert(0, str(project_root))
```

### For Service Files
```python
# Optional imports
try:
    from neo4j import GraphDatabase  # type: ignore[import]
except ImportError:
    GraphDatabase = None

# Dataclass fields
from dataclasses import dataclass, field
@dataclass
class Config:
    items: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
```

### For Engine Files
```python
# Type annotations
from typing import Dict, Any, Optional, List
import subprocess

def run_command(self, cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True)

# Optional returns
def get_value(self) -> Optional[str]:
    if self.value:
        return self.value
    return None
```

## EXECUTION PLAN

### Phase 1: Test Files (120+ errors)
Fix ALL test files in parallel:
- test_worktree_manager.py (38 errors)
- test_test_writer.py (28 errors)
- test_workflow_manager.py (18 errors)
- test_code_reviewer.py (14 errors)
- test_agent_generator.py (12 errors)
- test_mcp_service.py (8 errors)
- All other test files

### Phase 2: Service Files (43+ errors)
- neo4j_graph_service.py (34 errors)
- mcp_service.py (9 errors)

### Phase 3: Engine Files (19+ errors)
- worktree_manager_engine.py (12 errors)
- workflow_manager_engine.py (7 errors)

### Phase 4: Remaining Files
- Any other files with errors

## REQUIREMENTS
- Fix ALL 226 errors
- Work in parallel batches
- Create separate branches for each batch
- Base branch: feature/gadugi-v0.3-regeneration
- Create PRs immediately after fixing
- Merge PRs as soon as CI passes
- DO NOT STOP until pyright shows 0 errors

## SUCCESS CRITERIA
```bash
cd gadugi-v0.3
npx pyright
# Expected: "0 errors, 0 warnings, 0 informations"
```

## Pre-commit Hook Update
After achieving 0 errors, update `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: pyright
      name: pyright
      entry: npx pyright
      language: system
      types: [python]
      pass_filenames: false
      always_run: true
```