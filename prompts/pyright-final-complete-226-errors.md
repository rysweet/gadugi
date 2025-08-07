# CRITICAL: Fix ALL 226 Pyright Errors - Complete Resolution

## Current State
- 226 pyright errors remain in gadugi-v0.3
- Previous PRs (#198-205) were merged but errors persist
- Need COMPLETE resolution to achieve 0 errors

## Error Analysis
```bash
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
46 errors - remaining files
```

## PARALLEL EXECUTION PLAN

### Batch 1: Test Files (150+ errors)
**Branch**: feature/pyright-batch-1-all-tests
**Files to fix**:
- tests/test_worktree_manager.py (38 errors)
- tests/test_test_writer.py (28 errors)
- tests/test_workflow_manager.py (18 errors)
- tests/test_code_reviewer.py (14 errors)
- tests/test_agent_generator.py (12 errors)
- tests/test_mcp_service.py (8 errors)
- ALL other test files

**Fix Pattern**:
```python
# Add at TOP of EVERY test file (before all other imports)
import sys
import os
from pathlib import Path

# Add paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "orchestrator"))
sys.path.insert(0, str(project_root / "services"))
sys.path.insert(0, str(project_root))

# Then the rest of imports
import asyncio
import pytest
# ... etc
```

### Batch 2: Service Files (43 errors)
**Branch**: feature/pyright-batch-2-all-services
**Files to fix**:
- services/neo4j-graph/neo4j_graph_service.py (34 errors)
- services/mcp/mcp_service.py (9 errors)

**Fix Patterns**:
```python
# Neo4j optional import
try:
    from neo4j import GraphDatabase, AsyncGraphDatabase  # type: ignore[import]
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None
    AsyncGraphDatabase = None

# Redis optional import
try:
    import redis  # type: ignore[import]
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Dataclass fixes
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class NodeData:
    id: str
    labels: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### Batch 3: Engine Files (19 errors)
**Branch**: feature/pyright-batch-3-all-engines
**Files to fix**:
- src/orchestrator/worktree_manager_engine.py (12 errors)
- src/orchestrator/workflow_manager_engine.py (7 errors)

**Fix Patterns**:
```python
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# Subprocess return types
def run_command(self, cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False
    )

# Optional returns
def get_branch(self) -> Optional[str]:
    result = self.run_command(["git", "branch", "--show-current"])
    if result.returncode == 0 and result.stdout:
        return result.stdout.strip()
    return None

# Async functions
async def execute_task(self, task: str) -> Dict[str, Any]:
    return {"status": "complete", "task": task}
```

### Batch 4: Remaining Files
**Branch**: feature/pyright-batch-4-remaining
**Fix any remaining files with errors**

## EXECUTION INSTRUCTIONS

1. **Create 4 worktrees in parallel**
2. **Execute all batches simultaneously**
3. **Fix EVERY error - no exceptions**
4. **Run `npx pyright` after each batch to verify**
5. **Create PR immediately when batch is complete**
6. **Do NOT stop until 0 errors remain**

## VERIFICATION COMMANDS

After each batch:
```bash
cd gadugi-v0.3
npx pyright [fixed-files] 2>&1 | grep "0 errors"
```

After all batches:
```bash
cd gadugi-v0.3
npx pyright
# MUST show: "0 errors, 0 warnings"
```

## PR REQUIREMENTS

Each PR should:
- Target branch: feature/gadugi-v0.3-regeneration
- Title: "fix: resolve [batch] pyright errors ([X] → 0 errors)"
- Include exact error count reduction
- List all files fixed
- Verify CI passes

## CRITICAL SUCCESS CRITERIA

- **ZERO pyright errors in gadugi-v0.3**
- **All PRs merged to feature branch**
- **Pre-commit hooks pass with pyright**
- **CI/CD fully green**

## DO NOT STOP UNTIL COMPLETE

Continue iterating and fixing until:
```bash
npx pyright gadugi-v0.3
# Shows: "0 errors, 0 warnings"
```