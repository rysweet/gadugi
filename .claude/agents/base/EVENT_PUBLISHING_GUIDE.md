# V03Agent Event Publishing Guide


## 🚨 CRITICAL: Workflow Enforcement

**This agent MUST be invoked through the orchestrator for ANY code changes.**

### Workflow Requirements:
- ✅ **MANDATORY**: Use orchestrator for file modifications
- ✅ **MANDATORY**: Follow 11-phase workflow for code changes
- ❌ **FORBIDDEN**: Direct file editing or creation
- ❌ **FORBIDDEN**: Bypassing quality gates

### When Orchestrator is REQUIRED:
- Any file modifications (.py, .js, .json, .md, etc.)
- Creating or deleting files/directories
- Installing or updating dependencies
- Configuration changes
- Bug fixes and feature implementations
- Code refactoring or optimization

### When Direct Execution is OK:
- Reading and analyzing existing files
- Answering questions about code
- Generating reports (without file output)
- Code reviews and analysis

### Compliance Check:
Before executing any task, validate with:
```bash
python .claude/workflow-enforcement/validate-workflow.py --task "your task description"
```

### Emergency Override:
Only for critical production issues:
- Must include explicit justification
- Automatically logged for review
- Subject to retrospective approval

**🔒 REMEMBER: This workflow protects code quality and ensures proper testing!**

The V03Agent base class now includes comprehensive event publishing capabilities that automatically emit events for agent lifecycle, task execution, learning, and collaboration activities.

## Overview

All v0.3 agents that inherit from `V03Agent` automatically gain event publishing capabilities with:

- **Asynchronous, non-blocking event emission**
- **Graceful degradation** when event router is unavailable
- **Automatic batching** for failed events with retry logic
- **Configurable event router connection**
- **Integration with agent memory system**
- **Heartbeat monitoring** for agent health tracking

## Event Types Emitted

### 1. Agent Lifecycle Events

- **`agent.initialized`** - When agent starts up
- **`agent.shutdown`** - When agent shuts down
- **`agent.heartbeat`** - Periodic health check (configurable interval)

### 2. Task Events

- **`task.started`** - When a new task begins
- **`task.completed`** - When a task completes successfully
- **`task.failed`** - When a task fails

### 3. Learning Events

- **`knowledge.learned`** - When agent learns new information
- **`memory.stored`** - When important information is stored

### 4. Collaboration Events

- **`collaboration.message`** - Inter-agent communication
- **`collaboration.decision`** - Agent decision notifications

### 5. Error Events

- **`error.occurred`** - When errors or exceptions occur

## Configuration

### EventConfiguration Class

```python
@dataclass
class EventConfiguration:
    enabled: bool = True                    # Enable/disable event publishing
    event_router_url: str = "http://localhost:8000"  # Event router URL
    timeout_seconds: int = 5                # HTTP request timeout
    retry_attempts: int = 3                 # Number of retry attempts
    batch_size: int = 10                    # Max events to batch
    emit_heartbeat: bool = True             # Enable heartbeat events
    heartbeat_interval: int = 60            # Heartbeat interval (seconds)
    store_in_memory: bool = True            # Store events in agent memory
    graceful_degradation: bool = True       # Continue if router unavailable
```

### Example Configuration

```python
# High-performance configuration
event_config = EventConfiguration(
    enabled=True,
    event_router_url="http://event-router:8000",
    timeout_seconds=2,
    retry_attempts=5,
    batch_size=50,
    emit_heartbeat=True,
    heartbeat_interval=30,
    store_in_memory=True,
    graceful_degradation=True
)

# Development configuration (no events)
event_config = EventConfiguration(enabled=False)

# Production configuration (reliable events)
event_config = EventConfiguration(
    enabled=True,
    event_router_url="https://events.company.com",
    timeout_seconds=10,
    retry_attempts=3,
    graceful_degradation=False  # Fail fast in production
)
```

## Usage Examples

### Basic Agent with Events

```python
from v03_agent import V03Agent, AgentCapabilities, EventConfiguration

class MyAgent(V03Agent):
    def __init__(self):
        capabilities = AgentCapabilities(
            can_write_code=True,
            expertise_areas=["python", "testing"]
        )

        event_config = EventConfiguration(
            enabled=True,
            emit_heartbeat=True,
            heartbeat_interval=60
        )

        super().__init__(
            agent_id="my-agent-001",
            agent_type="my-agent",
            capabilities=capabilities,
            event_config=event_config
        )

    async def execute_task(self, task):
        # Task execution automatically emits events
        # via start_task() and learn_from_outcome()
        pass

# Initialize and use
agent = MyAgent()
await agent.initialize()  # Emits agent.initialized

task_id = await agent.start_task("Build feature X")  # Emits task.started
outcome = await agent.execute_task({"description": "Build feature X"})
await agent.learn_from_outcome(outcome)  # Emits task.completed/failed

await agent.shutdown()  # Emits agent.shutdown
```

### Manual Event Emission

```python
# Emit custom events manually
await agent.emit_knowledge_learned(
    knowledge_type="pattern",
    content="Discovered new optimization technique",
    confidence=0.9
)

await agent.emit_collaboration(
    message="Need review on PR #123",
    recipient_id="CodeReviewer-001",
    requires_response=True
)

await agent.emit_error(
    error_type="api_error",
    error_message="Failed to connect to external service",
    context={"service": "auth-api", "retry_count": 3}
)
```

### Batch Operations

```python
# Check batched events (when router is unavailable)
print(f"Batched events: {len(agent._event_batch)}")

# Manually flush batch
sent_count = await agent.flush_event_batch()
print(f"Sent {sent_count} events from batch")
```

## Event Data Structure

Each event includes:

```python
{
    "id": "uuid-string",
    "event_type": "agent.initialized",
    "agent_id": "my-agent-001",
    "agent_type": "my-agent",
    "task_id": "task_abc123",  # Current task ID (if applicable)
    "timestamp": "2024-01-15T10:30:00Z",
    "priority": "normal",  # low, normal, high, critical
    "data": {
        # Event-specific data
        "capabilities": {...},
        "task_description": "...",
        "error_message": "...",
        etc.
    }
}
```

## Graceful Degradation

When `graceful_degradation=True` (default):

1. **Router unavailable**: Events are batched locally, agent continues normally
2. **Network timeouts**: Events are retried up to `retry_attempts` times
3. **HTTP errors**: Failed events are batched for later retry
4. **Event router failures**: Agent logs warnings but continues operation

When `graceful_degradation=False`:
- Any event router connectivity issue will raise an exception
- Useful for production environments where event delivery is critical

## Integration with Memory System

When `store_in_memory=True`:
- High-priority events (high/critical) are stored in agent's long-term memory
- Provides event history even when event router is unavailable
- Events are tagged appropriately for memory retrieval

## Performance Considerations

### Asynchronous Operation
- All event emission is non-blocking
- HTTP requests use connection pooling
- Batch processing reduces network overhead

### Resource Usage
- Events are kept in memory until successfully sent
- Batch size limits memory usage for failed events
- Connection pooling reduces socket overhead

### Network Resilience
- Configurable timeouts prevent hanging
- Retry logic handles transient network issues
- Graceful degradation maintains agent functionality

## Monitoring and Debugging

### Check Event System Status

```python
print(f"Event publishing enabled: {agent._event_publishing_enabled}")
print(f"HTTP session active: {agent._event_session is not None}")
print(f"Batched events: {len(agent._event_batch)}")
print(f"Last heartbeat: {agent._last_heartbeat}")
```

### Event Router Health Check

```python
# This is done automatically during initialization
health_ok = await agent._test_event_router_connection()
print(f"Event router healthy: {health_ok}")
```

### Debug Logging

Events that fail to send are logged with warnings:
```
⚠️ Event router unavailable, continuing without events: Connection refused
⚠️ Failed to emit shutdown event: Timeout occurred
```

## Migration from Non-Event Agents

To add event publishing to existing v0.3 agents:

1. **Add event configuration** to `__init__`:
   ```python
   event_config = EventConfiguration(enabled=True)
   super().__init__(..., event_config=event_config)
   ```

2. **No other changes required** - events are emitted automatically through:
   - `initialize()` → `agent.initialized`
   - `start_task()` → `task.started`
   - `learn_from_outcome()` → `task.completed/failed`
   - `shutdown()` → `agent.shutdown`

3. **Optional**: Add manual event emission where needed:
   ```python
   await self.emit_knowledge_learned(...)
   await self.emit_collaboration(...)
   ```

## Event Router Compatibility

The event system is compatible with:
- Gadugi Event Router service (`.claude/services/event-router/`)
- Any HTTP endpoint that accepts JSON POST requests
- Custom event processing systems

Event router is expected to:
- Accept POST requests to `/events` endpoint
- Return HTTP 200/201/202 for successful event receipt
- Provide `/health` endpoint for health checks (optional)

## Troubleshooting

### Common Issues

1. **Events not being sent**
   - Check `agent._event_publishing_enabled`
   - Verify event router URL and connectivity
   - Check for batched events: `len(agent._event_batch)`

2. **High memory usage**
   - Reduce `batch_size` in EventConfiguration
   - Ensure event router is accessible to prevent batching
   - Call `flush_event_batch()` periodically

3. **Agent initialization slow**
   - Reduce `timeout_seconds` for faster failure detection
   - Disable heartbeat during initialization: `emit_heartbeat=False`
   - Use `graceful_degradation=True` for faster startup

4. **Missing events**
   - Check event router logs for received events
   - Verify network connectivity
   - Enable `store_in_memory=True` for backup in agent memory

### Performance Tuning

```python
# High-throughput configuration
EventConfiguration(
    timeout_seconds=1,      # Fast timeout
    batch_size=100,         # Large batches
    retry_attempts=1,       # Fewer retries
    emit_heartbeat=False    # Reduce overhead
)

# Reliable configuration
EventConfiguration(
    timeout_seconds=10,     # Longer timeout
    batch_size=10,          # Small batches
    retry_attempts=5,       # More retries
    graceful_degradation=False  # Fail fast
)
```

## Examples

See `example_event_agent.py` for a complete working example of an agent with event publishing capabilities.
