# Master Orchestration: Complete Pyright Type Safety for Gadugi v0.3

## Mission
Achieve 100% pyright type safety in Gadugi v0.3 through parallel execution of fixes and establish permanent enforcement.

## Current State
- 217 pyright errors remaining
- Multiple files with type issues
- No enforcement mechanism in place

## Execution Plan

### PARALLEL EXECUTION - 4 Concurrent Tasks

Execute these 4 prompt files IN PARALLEL:

1. **Batch 1: High-Error Services** (pyright-batch-1-services.md)
   - Target: 94 errors in service files
   - Priority: Highest error count files first
   - Branch: feature/pyright-batch-1-services

2. **Batch 2: Orchestrator Engines** (pyright-batch-2-orchestrators.md)
   - Target: 28 errors in engine files
   - Priority: Core functionality
   - Branch: feature/pyright-batch-2-orchestrators

3. **Batch 3: Remaining Files** (pyright-batch-3-remaining.md)
   - Target: ~95 errors in tests and other files
   - Priority: Import resolution and remaining issues
   - Branch: feature/pyright-batch-3-remaining

4. **Batch 4: Enforcement Setup** (pyright-batch-4-enforcement.md)
   - Target: Prevent future type issues
   - Priority: CI/CD and tooling setup
   - Branch: feature/pyright-enforcement-setup

## Orchestrator Instructions

```bash
/agent:orchestrator-agent

Execute these tasks in PARALLEL:
1. Fix service files with highest error counts (Batch 1)
2. Fix orchestrator engine type issues (Batch 2)
3. Fix remaining files and test imports (Batch 3)
4. Set up enforcement mechanisms (Batch 4)

Base branch: feature/gadugi-v0.3-regeneration
Execution mode: PARALLEL (4 concurrent tasks)

For each batch:
- Create feature branch from base
- Fix all pyright errors in assigned files
- Test functionality still works
- Create PR to feature/gadugi-v0.3-regeneration
- Ensure CI passes

Success criteria:
- Zero pyright errors in gadugi-v0.3
- Pre-commit hooks prevent new type errors
- CI fails on type errors
- All agents instructed on type safety
```

## Common Fix Patterns

### Pattern 1: Optional Attribute Access
```python
# WRONG
if self.connection:
    self.connection.close()

# CORRECT
if self.connection is not None:
    self.connection.close()
```

### Pattern 2: Type Annotations
```python
# WRONG
def process(data):
    return {"result": data}

# CORRECT
def process(data: str) -> Dict[str, str]:
    return {"result": data}
```

### Pattern 3: Async Types
```python
# WRONG
async def fetch():
    return data

# CORRECT
async def fetch() -> Optional[Dict[str, Any]]:
    return data
```

### Pattern 4: Dataclass Fields
```python
# WRONG
@dataclass
class Config:
    items: List[str] = []

# CORRECT
@dataclass
class Config:
    items: List[str] = field(default_factory=list)
```

### Pattern 5: Test Imports
```python
# Add to top of test files
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestrator"))
```

## Verification After Completion

After all batches complete:

1. **Run full type check**:
   ```bash
   cd gadugi-v0.3 && pyright
   ```
   Expected: "0 errors, 0 warnings"

2. **Test pre-commit hook**:
   ```bash
   pre-commit run pyright --all-files
   ```
   Expected: All passed

3. **Verify CI integration**:
   - Push changes
   - Check GitHub Actions includes pyright step
   - Verify it fails on type errors

## Final Deliverables

1. **Zero pyright errors** in entire v0.3 codebase
2. **4 PRs** fixing different batches of issues
3. **Enforcement mechanisms** in place:
   - pyrightconfig.json (strict mode)
   - Pre-commit hooks
   - CI/CD integration
   - Agent instructions
4. **Documentation** for maintaining type safety

## Start Execution

Begin parallel execution NOW with all 4 batches simultaneously.