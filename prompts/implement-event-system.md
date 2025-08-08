# Task: Implement Event System (#236)

## Description
Implement the event router service based on the recipes and existing reference implementation.

## Requirements
1. **Location**: `.claude/services/event-router/`
2. **Recipe**: `.claude/recipes/event-system/requirements.md`
3. **Protobuf schemas**: `.claude/protos/`
4. **Reference**: `gadugi-v0.3/services/event-router/event_router_service.py`

## Implementation Requirements
- Async pub/sub with topic filtering
- Agent registration and discovery
- Process isolation for agents
- Dead letter queue for failed events
- Priority-based event routing
- Circuit breaker pattern for failing subscribers
- Event replay capability

## Quality Requirements
- All Python code must use `uv run` for commands
- Code must be pyright clean
- Code must be ruff formatted
- All tests must pass
- 90%+ test coverage

## Files to Create/Modify
1. `.claude/services/event-router/event_router.py` - Main service implementation
2. `.claude/services/event-router/models.py` - Event and subscription models
3. `.claude/services/event-router/dead_letter_queue.py` - DLQ implementation
4. `.claude/services/event-router/tests/test_event_router.py` - Unit tests
5. `.claude/services/event-router/__init__.py` - Module exports