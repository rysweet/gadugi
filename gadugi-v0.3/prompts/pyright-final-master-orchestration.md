# Master Orchestration: Complete Pyright Type Safety - Final Push

## Mission
Achieve ZERO pyright errors in Gadugi v0.3 through parallel execution of final fixes.

## Current State
- Starting: 167 pyright errors remaining
- Target: 0 errors
- Already merged: PRs #189, #190, #191

## Error Distribution
```
44 errors - neo4j_graph_service.py
33 errors - gadugi_cli_service.py  
17 errors - mcp_service.py
13 errors - llm_proxy_service.py
12 errors - worktree_manager_engine.py
8 errors - integration_test_agent_engine.py
7 errors - workflow_manager_engine.py
6 errors - event_router_service.py
4 errors - architect_engine.py
4 errors - test_architect.py
19 errors - remaining files
```

## PARALLEL EXECUTION - 3 Concurrent Batches

Execute these 3 prompt files IN PARALLEL:

### Batch 1: Service Files (107 errors)
**Prompt**: pyright-final-batch-1-services.md
- neo4j_graph_service.py (44 errors)
- gadugi_cli_service.py (33 errors)
- mcp_service.py (17 errors)  
- llm_proxy_service.py (13 errors)
**Branch**: feature/pyright-final-batch-1-services

### Batch 2: Orchestrator Engines (27 errors)
**Prompt**: pyright-final-batch-2-orchestrators.md
- worktree_manager_engine.py (12 errors)
- integration_test_agent_engine.py (8 errors)
- workflow_manager_engine.py (7 errors)
**Branch**: feature/pyright-final-batch-2-orchestrators

### Batch 3: Tests & Remaining (33 errors)
**Prompt**: pyright-final-batch-3-remaining.md
- Test files import resolution
- architect_engine.py (4 errors)
- event_router_service.py (6 errors)
- Remaining engine files
**Branch**: feature/pyright-final-batch-3-remaining

## Orchestrator Instructions

```bash
/agent:orchestrator-agent

Execute these tasks in PARALLEL:
1. Fix 107 errors in service files (Batch 1)
2. Fix 27 errors in orchestrator engines (Batch 2)  
3. Fix 33 errors in tests and remaining files (Batch 3)

Base branch: feature/gadugi-v0.3-regeneration
Execution mode: PARALLEL (3 concurrent tasks)

For each batch:
- Create feature branch from base
- Fix ALL pyright errors in assigned files
- Run pyright to verify zero errors in those files
- Test functionality still works
- Create PR to feature/gadugi-v0.3-regeneration
- Ensure CI passes

Success criteria:
- Zero pyright errors in entire gadugi-v0.3
- All tests still pass
- All functionality preserved
- 3 PRs ready to merge
```

## Common Fix Patterns Reference

### Import Resolution
```python
# For optional dependencies
try:
    from neo4j import GraphDatabase  # type: ignore[import]
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    GraphDatabase = None
```

### Dataclass Fields
```python
from dataclasses import dataclass, field

@dataclass
class Config:
    items: List[str] = field(default_factory=list)  # NOT: = None or = []
    settings: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None  # OK for Optional types
```

### Optional Handling
```python
# WRONG
if self.connection:
    self.connection.close()

# CORRECT  
if self.connection is not None:
    self.connection.close()
```

### Test Imports
```python
# Add to TOP of test files
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestrator"))
```

## Verification After Completion

Once all 3 batches complete:

1. **Merge all PRs** to feature/gadugi-v0.3-regeneration
2. **Run final check**:
   ```bash
   npx pyright
   ```
   Expected: "0 errors, 0 warnings, 0 informations"

3. **Test pre-commit**:
   ```bash
   pre-commit run pyright --all-files
   ```
   Expected: All passed

4. **Create final PR** from feature/gadugi-v0.3-regeneration to main

## START EXECUTION NOW

Begin parallel execution with all 3 batches simultaneously.
Target: ZERO pyright errors in 30 minutes.