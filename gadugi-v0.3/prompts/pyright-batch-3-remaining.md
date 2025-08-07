# Pyright Type Safety Fix - Batch 3: Remaining Files

## Target Files
Fix remaining pyright errors across the codebase:

### 1. Test Files Import Resolution
All test files need proper path setup:

```python
# Add to top of EACH test file
import sys
from pathlib import Path

# Add src/orchestrator to path for imports
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src" / "orchestrator"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Now imports will work
from workflow_manager_engine import WorkflowManager
```

Files to fix:
- tests/test_workflow_manager.py
- tests/test_worktree_manager.py
- tests/test_code_reviewer.py
- tests/test_memory_manager.py
- tests/test_team_coach.py
- tests/test_architect.py
- tests/test_gadugi_engine.py
- All other test files

### 2. Remaining Engine Files
Fix any remaining type errors in:
- src/orchestrator/prompt_writer_engine.py
- src/orchestrator/code_writer_engine.py
- src/orchestrator/task_decomposer_engine.py
- src/orchestrator/readme_agent_engine.py
- src/orchestrator/test_writer_engine.py
- src/orchestrator/execution_monitor_engine.py
- src/orchestrator/agent_generator_engine.py

Common patterns:
```python
# Fix return type annotations
def process_task(self, task: str) -> Dict[str, Any]:
    return {"status": "complete"}

# Fix Optional handling
config: Optional[Dict[str, Any]] = self.load_config()
if config is not None:
    # safe to use config
    
# Fix list/dict type hints
results: List[Dict[str, Any]] = []
for item in items:
    results.append({"item": item})
```

### 3. Demo and Utility Files
Fix type errors in:
- src/orchestrator/demo_*.py files
- src/orchestrator/simple_decomposer.py
- src/orchestrator/api_client_engine.py

## Requirements
- Branch from feature/gadugi-v0.3-regeneration
- Create feature branch: feature/pyright-batch-3-remaining
- Focus on import resolution first (quick wins)
- Then fix type annotations
- Preserve all functionality