# Achieve Zero Pyright Errors - Final Push

## Objective
Fix ALL remaining 178 pyright errors to achieve ZERO errors across the entire codebase.

## Current State
- 178 errors remaining (down from 442)
- Previous PR used too many suppressions (505 `# type: ignore`)
- Need proper fixes, not suppressions

## Requirements
1. **NO TYPE SUPPRESSIONS** - Fix issues properly
2. Add proper type annotations
3. Fix import issues
4. Resolve attribute access problems
5. Handle optional types correctly

## Error Distribution
Based on previous analysis:
- Event Router: 67 errors
- Team Coach: ~30 errors (estimate)
- Various agents: ~40 errors
- Test files: ~20 errors
- Misc files: ~21 errors

## Strategy
1. **Fix imports first** - Many errors cascade from bad imports
2. **Add missing type stubs** - Some libraries need type stubs
3. **Proper Optional handling** - Use Optional[T] where needed
4. **Generic types** - Use TypeVar for generic functions
5. **Protocol definitions** - Define protocols for duck typing

## Common Patterns to Fix
```python
# Bad - causes errors
def process(data):
    return data.get("key")

# Good - properly typed
from typing import Any, Dict, Optional

def process(data: Dict[str, Any]) -> Optional[Any]:
    return data.get("key")
```

## Validation
```bash
# Must show ZERO errors
uv run pyright

# Also check with strict mode
uv run pyright --strict

# Ensure tests still pass
uv run pytest tests/ -v
```

## Success Criteria
- `uv run pyright` shows: "0 errors, 0 warnings"
- NO `# type: ignore` comments added
- All tests still pass
- Code remains functional

## Priority Order
1. Fix test infrastructure first (enables testing)
2. Fix Event Router (67 errors)
3. Fix Team Coach
4. Fix remaining agent errors
5. Clean up misc errors

This is a UV project - use `uv run` for all Python commands.

Create PR when complete with title: "fix: achieve ZERO pyright errors - proper type safety"
