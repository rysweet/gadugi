# Event Router Design

## Architecture Overview

The Event Router is a central message broker that enables async communication between agents using protobuf-encoded events. It manages agent lifecycles and provides reliable message delivery.

## Components

### 1. Core Router
- **EventRouter**: Main routing engine with topic-based pub/sub
- **EventBus**: In-memory message bus with priority queuing
- **TopicManager**: Manages topic subscriptions and patterns
- **MessageSerializer**: Protobuf serialization/deserialization

### 2. Process Management
- **ProcessManager**: Spawns and monitors agent subprocesses
- **AgentRegistry**: Tracks running agents and their capabilities
- **HealthMonitor**: Heartbeat monitoring and failure detection
- **ProcessIsolator**: Resource isolation using cgroups/namespaces

### 3. Reliability Layer
- **DeadLetterQueue**: Persistent storage for failed events
- **RetryManager**: Exponential backoff retry logic
- **EventStore**: Optional event persistence for recovery
- **CircuitBreaker**: Prevents cascading failures

### 4. Observability
- **MetricsCollector**: Prometheus metrics export
- **EventLogger**: Structured logging of all events
- **TracingContext**: Distributed tracing support

## Data Flow

1. **Event Reception**:
   - Agent sends protobuf event to router
   - Router deserializes and validates event
   - Event assigned priority and timestamp

2. **Routing Decision**:
   - Topic extracted from event metadata
   - Subscribers looked up from registry
   - Filtering rules applied (namespace, type)

3. **Delivery**:
   - Events queued for each subscriber
   - Async delivery with acknowledgment
   - Failed deliveries sent to DLQ

4. **Process Spawning**:
   - AgentStarted event triggers spawn
   - New subprocess created with isolation
   - Agent registered in registry
   - Health monitoring initiated

## Technology Stack

- **Language**: Python 3.11+
- **Async Framework**: asyncio with uvloop
- **Message Format**: Protocol Buffers 3
- **Queue**: asyncio.Queue with priority support
- **Process Management**: asyncio.subprocess
- **Persistence**: SQLite for DLQ, Redis for cache
- **Monitoring**: Prometheus client library

## Key Design Decisions

1. **In-Memory First**: Primary routing in memory for speed
2. **Subprocess Isolation**: Each agent runs in separate process
3. **At-Most-Once Delivery**: Default mode, with at-least-once optional
4. **Topic Hierarchy**: Dot-separated topics (e.g., "agent.task.completed")
5. **Protobuf Everything**: All events use protobuf for consistency

## Subprocess Execution Model

When orchestrator delegates tasks to agents via `claude -p`:
- Runs fully autonomously without approval prompts
- Captures stdout/stderr for logging
- Monitors exit codes for success/failure
- Sends completion events when done
- Only requests approval for truly critical operations (production changes, destructive actions)

## Error Handling

- Network failures: Automatic retry with exponential backoff
- Process crashes: Automatic restart with state recovery
- Message failures: Dead letter queue with manual inspection
- Resource exhaustion: Circuit breaker activation

## Security

- Process isolation prevents cross-agent access
- Message validation prevents malformed events
- Rate limiting prevents event flooding
<<<<<<< HEAD
- Authentication via agent tokens (future)
=======
- Authentication via agent tokens (future)
>>>>>>> feature/gadugi-v0.3-regeneration
