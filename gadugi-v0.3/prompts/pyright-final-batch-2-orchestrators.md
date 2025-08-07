# Pyright Type Safety Fix - Final Batch 2: Orchestrator Engines

## Target: Fix 27 Errors in Orchestrator Files

### Priority Files (27 errors)

#### 1. worktree_manager_engine.py (12 errors)
Common issues:
- Missing return type annotations
- Optional handling for git operations
- Subprocess type hints

Fixes:
```python
from typing import Dict, Any, Optional, List
import subprocess

def run_git_command(self, args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        check=False
    )

def get_current_branch(self) -> Optional[str]:
    result = self.run_git_command(["branch", "--show-current"])
    if result.returncode == 0:
        return result.stdout.strip()
    return None
```

#### 2. workflow_manager_engine.py (7 errors)
Issues:
- Phase management type annotations
- State dictionary types
- Async function return types

Fixes:
```python
from typing import Dict, Any, List, Optional
from enum import Enum

class WorkflowPhase(Enum):
    SETUP = "setup"
    ISSUE = "issue"
    BRANCH = "branch"
    # ... etc

def get_current_phase(self) -> WorkflowPhase:
    return self.current_phase

async def execute_phase(self, phase: WorkflowPhase) -> Dict[str, Any]:
    # implementation
    return {"status": "complete", "phase": phase.value}
```

#### 3. integration_test_agent_engine.py (8 errors)
Issues:
- Dictionary literal syntax errors
- Missing json import
- Return type annotations

Fixes:
```python
import json
from typing import Dict, Any, List

def create_test_config(self) -> Dict[str, Any]:
    return {  # NOT: return {{
        "test_type": "integration",
        "framework": "pytest"
    }

def format_results(self, results: List[Dict[str, Any]]) -> str:
    return json.dumps(results, indent=2)
```

## Requirements
- Branch from feature/gadugi-v0.3-regeneration
- Create feature branch: feature/pyright-final-batch-2-orchestrators
- Fix all 27 errors in orchestrator engine files
- Ensure all async functions have proper return types
- Test orchestrator functionality after fixes