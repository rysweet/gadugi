# Gadugi v0.3 Event System Guide

## Overview

The Gadugi v0.3 event system provides a comprehensive event-driven architecture for agent communication, coordination, and learning. This guide covers the complete event system implementation based on the v0.3 specification.

## Core Concepts

### Event-Driven Architecture

All agents in Gadugi v0.3 communicate through events routed by the central Event Router service. This ensures:
- **Loose coupling** between agents
- **Scalability** through asynchronous communication
- **Observability** via event logging and persistence
- **Resilience** with graceful degradation

### Event Flow

```
Agent A                Event Router              Agent B
   │                        │                        │
   ├──emit(event)──────────►│                        │
   │                        ├──route(subscribers)───►│
   │                        │                        ├──handle(event)
   │                        │◄──emit(response)──────┤
   │◄──route(response)──────┤                        │
```

## Event Types

### Core System Events (Required for all agents)

These events MUST be emitted by all agents as part of the v0.3 specification:

#### 1. `{agent_type}.started`
Emitted when an agent begins task execution.

```python
await agent.emit_started(
    input_data={"task": "Implement feature X"},
    task_id="task-123"
)
```

**Payload:**
- `input`: Any - The input data for the task
- `task_id`: string - Unique task identifier
- `timestamp`: datetime - Event timestamp

#### 2. `{agent_type}.stopped`
Emitted when an agent completes task execution.

```python
await agent.emit_stopped(
    output_data={"result": "Feature implemented"},
    task_id="task-123",
    success=True,
    duration_seconds=45.3
)
```

**Payload:**
- `output`: Any - The task output/result
- `task_id`: string - Task identifier
- `success`: boolean - Whether task succeeded
- `duration_seconds`: float - Execution duration
- `timestamp`: datetime - Event timestamp

#### 3. `{agent_type}.hasQuestion`
Emitted when an agent needs interactive input from the user.

```python
await agent.emit_has_question(
    question="Which database should we use?",
    context={"options": ["PostgreSQL", "MySQL", "SQLite"]},
    options=["PostgreSQL", "MySQL", "SQLite"]
)
```

**Payload:**
- `question`: string - The question to ask
- `context`: object - Additional context
- `options`: array - Possible answers (optional)
- `timestamp`: datetime - Event timestamp

**Priority:** HIGH (routed through orchestration to user)

#### 4. `{agent_type}.needsApproval`
Emitted when an agent needs user approval before proceeding.

```python
await agent.emit_needs_approval(
    command="rm -rf /important/data",
    description="Delete old backup files",
    risk_level="high"
)
```

**Payload:**
- `command`: string - The command/action needing approval
- `description`: string - Human-readable description
- `risk_level`: string - Risk assessment (low/medium/high)
- `timestamp`: datetime - Event timestamp

**Priority:** HIGH (routed through orchestration to user)

#### 5. `{agent_type}.cancel`
Emitted to cancel another agent's execution.

```python
await agent.emit_cancel(
    target_agent_id="workflow-001",
    reason="User requested cancellation"
)
```

**Payload:**
- `target_agent_id`: string - Agent to cancel
- `reason`: string - Cancellation reason
- `timestamp`: datetime - Event timestamp

**Priority:** CRITICAL

## Event Subscriptions

### Pattern-Based Routing

The Event Router uses pattern matching to route events to subscribers:

```python
# In subscriptions.py
subscription_manager.add_subscription(
    agent_id="orchestration",
    pattern="*.hasQuestion",  # Matches any agent's hasQuestion event
    handler="route_question_to_user",
    priority=EventPriority.HIGH
)
```

### Wildcard Patterns

- `*` matches any single segment
- `*.started` matches `orchestration.started`, `workflow.started`, etc.
- `workflow.*` matches all workflow events

### Default Subscription Configuration

```yaml
# event_config.yaml
agents:
  orchestration:
    subscribes:
      - pattern: "*.hasQuestion"
        handler: "route_question_to_user"
        priority: "high"
      - pattern: "*.needsApproval"
        handler: "route_approval_to_user"
        priority: "high"
      - pattern: "*.stopped"
        handler: "aggregate_results"
        priority: "normal"
```

## Implementation Guide

### 1. Agent Setup

All v0.3 agents inherit from `V03Agent` which provides event emission capabilities:

```python
from claude.agents.base.v03_agent import V03Agent

class MyAgent(V03Agent):
    def __init__(self):
        super().__init__(
            agent_id="my-agent-001",
            agent_type="MyAgent",
            capabilities=AgentCapabilities(
                can_write_code=True,
                expertise_areas=["python", "testing"]
            ),
            event_config=EventConfiguration(
                enabled=True,
                event_router_url="http://localhost:8001"
            )
        )

    async def execute_task(self, task):
        # Emit started event
        await self.emit_started(
            input_data=task,
            task_id=task["id"]
        )

        try:
            # Do work...
            result = await self.process_task(task)

            # Emit stopped event
            await self.emit_stopped(
                output_data=result,
                task_id=task["id"],
                success=True,
                duration_seconds=10.5
            )
        except Exception as e:
            # Emit error event
            await self.emit_error(
                error_type="TaskFailure",
                error_message=str(e)
            )
```

### 2. Event Router Configuration

The Event Router must be running to handle events:

```bash
# Start Event Router (default port 8001)
cd .claude/services/event-router
python main.py

# Configuration via environment
export PORT=8001
export EVENT_ROUTER_SQLITE_DB_PATH=".claude/data/events.db"
```

### 3. Testing Events

Use the test scripts to verify event flow:

```bash
# Test event emission from V03Agent
python .claude/services/event-router/test_v03_integration.py

# Test event flow between agents
python .claude/services/event-router/test_event_flow.py
```

## Event Priority and Processing

### Priority Levels

1. **CRITICAL** - Immediate processing required
   - System failures
   - Cancel events
   - Security issues

2. **HIGH** - User interaction required
   - hasQuestion events
   - needsApproval events
   - Blocking issues

3. **NORMAL** - Standard processing
   - Lifecycle events (started, stopped)
   - Task events
   - Knowledge events

4. **LOW** - Background processing
   - Metrics collection
   - Logging events
   - Heartbeats

### Processing Order

Events are processed in priority order, with CRITICAL events handled first:

```python
# In Event Router
subscribers.sort(key=lambda s: priority_order[s.priority])
for subscriber in subscribers:
    await route_to_agent(subscriber, event)
```

## Storage and Persistence

### Event Storage

All events are persisted to SQLite for:
- Audit trails
- Crash recovery
- Session replay
- Analytics

```sql
-- Events table structure
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    priority TEXT,
    data JSON,
    task_id TEXT,
    session_id TEXT
);
```

### Querying Events

```python
# Query recent events
GET /events?limit=10

# Filter by type
GET /events/filter
{
    "event_types": ["workflow.started", "workflow.stopped"],
    "time_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-31T23:59:59Z"
    }
}

# Get storage statistics
GET /events/storage
```

## Best Practices

### 1. Always Emit Core Events

```python
async def execute_task(self, task):
    # ALWAYS emit started
    await self.emit_started(input_data=task, task_id=task["id"])

    try:
        result = await self.do_work(task)
    finally:
        # ALWAYS emit stopped (even on failure)
        await self.emit_stopped(
            output_data=result,
            task_id=task["id"],
            success=result is not None,
            duration_seconds=elapsed
        )
```

### 2. Use Appropriate Priority

```python
# User interaction - HIGH priority
await self.emit_has_question(
    question="Should we proceed?",
    priority=EventPriority.HIGH  # Ensures quick routing
)

# Background task - LOW priority
await self.emit_task_started(
    task_description="Cleanup old files",
    priority=EventPriority.LOW
)
```

### 3. Include Sufficient Context

```python
# Good - includes context for decision making
await self.emit_needs_approval(
    command="DELETE FROM users WHERE last_login < '2020-01-01'",
    description="Remove inactive users from database",
    risk_level="high",
    context={
        "affected_records": 1523,
        "backup_available": True,
        "reversible": False
    }
)

# Bad - lacks context
await self.emit_needs_approval(
    command="delete_users()",
    description="Delete users"
)
```

### 4. Handle Event Failures Gracefully

```python
# V03Agent uses graceful degradation by default
event_config = EventConfiguration(
    graceful_degradation=True  # Continue if Event Router unavailable
)

# Events will be batched and retried when router is available
```

## Troubleshooting

### Events Not Being Received

1. Check Event Router is running:
```bash
curl http://localhost:8001/health
```

2. Verify agent configuration:
```python
# Check event_config.enabled is True
print(f"Events enabled: {agent.event_config.enabled}")
print(f"Router URL: {agent.event_config.event_router_url}")
```

3. Check Event Router logs:
```bash
# Look for routing messages
INFO:handlers:📥 Handling event: workflow.started from workflow-001
INFO:handlers:📨 Routing workflow.started to 2 subscribers
```

### Events Not Being Routed

1. Verify subscription patterns:
```python
# Check subscriptions are registered
python -c "
from subscriptions import get_subscription_manager
sm = get_subscription_manager()
print(sm.get_subscribers('workflow.started'))
"
```

2. Check pattern matching:
```python
# Test pattern matching
pattern = "*.started"
event_type = "workflow.started"
# Should match
```

### Storage Issues

1. Check SQLite database:
```bash
sqlite3 .claude/data/events.db "SELECT COUNT(*) FROM events;"
```

2. Verify storage endpoint:
```bash
curl http://localhost:8001/events/storage
```

## Migration from Pre-v0.3

### Key Changes

1. **Dynamic Event Types**: Event types are now strings, not enums
2. **Agent Type Prefixes**: Events use `{agent_type}.{event_name}` format
3. **Pattern Matching**: Subscriptions support wildcards
4. **Priority Routing**: Events are processed by priority

### Migration Checklist

- [ ] Update agents to inherit from `V03Agent`
- [ ] Add core event emissions (started, stopped, etc.)
- [ ] Configure event subscriptions in `subscriptions.py`
- [ ] Update Event Router to latest version
- [ ] Test event flow with `test_v03_integration.py`

## References

- [Gadugi v0.3 Specification](../prompts/Gadugi-v0.3/Gadugi-v0.3.md)
- [Event Router README](../services/event-router/README.md)
- [V03Agent Base Class](../agents/base/v03_agent.py)
- [Event Configuration](event_config.yaml)
- [Subscription Management](../services/event-router/subscriptions.py)
