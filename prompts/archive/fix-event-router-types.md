# Fix Event Router Type Errors

## Objective
Fix the 67 type annotation errors in the Event Router component without using type suppressions.

## Current Issues
1. **67 pyright errors** in `.claude/services/event-router/`
2. Type annotation issues with async functions
3. Missing or incorrect return types
4. Untyped event handlers

## Requirements
1. Fix ALL type errors properly (no `# type: ignore`)
2. Maintain functionality while adding proper types
3. Use proper async type hints
4. Ensure event routing still works

## Files to Fix
```
.claude/services/event-router/
├── __init__.py
├── router.py        # Main router with type issues
├── events.py        # Event definitions need typing
├── handlers.py      # Handler type annotations
└── process_manager.py # Process spawning types
```

## Common Fixes Needed
```python
# Before (incorrect)
async def handle_event(event):
    return await process(event)

# After (correct)
from typing import Any, Dict, Optional, Awaitable

async def handle_event(event: Dict[str, Any]) -> Awaitable[Optional[Dict[str, Any]]]:
    return await process(event)
```

## Testing
```bash
# Check types
uv run pyright .claude/services/event-router/

# Run tests
uv run pytest .claude/services/event-router/tests/ -v

# Verify functionality
uv run python -c "from claude.services.event_router import EventRouter; router = EventRouter(); print('Router initialized')"
```

## Success Criteria
- ZERO pyright errors in event-router
- NO type suppressions used
- All tests still pass
- Event routing functionality preserved
- Proper async type annotations

This is a UV project - use `uv run` for all Python commands.

Create PR when complete.
