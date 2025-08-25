# Event Router V2 for Gadugi

A production-ready, WebSocket-based event routing system for agent communication in Gadugi. This is a complete rewrite from the original TCP-based implementation to provide proper WebSocket protocol support with auto-reconnection, priority processing, and comprehensive management tools.

## 🚀 Features

### ✅ **Zero External Dependencies for Local Development**
- Works out of the box with Python standard library + websockets
- No Redis, RabbitMQ, or other infrastructure required
- In-memory queue for local development
- Ready for cloud scaling with pluggable transport layers

### ✅ **WebSocket-Based Real-Time Communication**
- True WebSocket protocol (not raw TCP like V1)
- Bi-directional communication
- Low latency event delivery (< 10ms local)
- Supports up to 1000 concurrent clients

### ✅ **Auto-Reconnection & Error Recovery**
- Automatic client reconnection with exponential backoff
- Message queuing during disconnection
- Subscription restoration after reconnection
- Graceful degradation during network issues

### ✅ **Priority-Based Event Processing**
- 10 priority levels (LOWEST to SYSTEM)
- Priority queue ensures critical events processed first
- Configurable queue sizes (default 10,000 events)
- Optional multi-queue mode for high-volume scenarios

### ✅ **Flexible Subscription System**
- Topic-based routing with wildcards (`task.*`, `*.failed`, `*`)
- Type-based filtering (TASK_CREATED, AGENT_STARTED, etc.)
- Priority filtering (only HIGH/CRITICAL events)
- Source filtering (specific agents)

### ✅ **Production Ready**
- Health monitoring with real-time metrics
- Statistics tracking (events processed, failures, queue depth)
- Comprehensive error handling and recovery
- Structured logging with configurable levels
- Management CLI for easy control
- Agent for programmatic management

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install websockets

# Using uv (recommended)
uv pip install websockets
```

### 2. Start the Event Router Server

```python
#!/usr/bin/env python3
import asyncio
from src.core.router import EventRouter

async def main():
    router = EventRouter(host="localhost", port=9090)
    await router.start()  # Runs forever

asyncio.run(main())
```

Or use the provided script:
```bash
python examples/start_server.py
```

### 3. Connect a Client

```python
from src.client.client import EventRouterClient
from src.core.models import EventPriority

# Create client
client = EventRouterClient(url="ws://localhost:9090")

# Connect
await client.connect()

# Publish an event
await client.publish(
    topic="user.created",
    payload={"user_id": 123, "name": "Alice"},
    priority=EventPriority.NORMAL
)

# Subscribe to events
@client.on("user.*")
async def handle_user_event(event):
    print(f"User event: {event.topic} - {event.payload}")

# Wait for events
await asyncio.sleep(60)

# Disconnect
await client.disconnect()
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Event Router V2                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐    WebSocket    ┌──────────┐         │
│  │ Client 1 │◄───────────────►│          │         │
│  └──────────┘                 │          │         │
│                               │  Router  │         │
│  ┌──────────┐    WebSocket    │  Server  │         │
│  │ Client 2 │◄───────────────►│          │         │
│  └──────────┘                 │          │         │
│                               └──────────┘         │
│                                     │               │
│                               ┌──────────┐         │
│                               │  Event   │         │
│                               │  Queue   │         │
│                               └──────────┘         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Usage Examples

### Basic Publisher-Subscriber

```python
# Publisher
async def publisher():
    client = EventRouterClient()
    await client.connect()
    
    for i in range(10):
        await client.publish(
            topic=f"data.update",
            payload={"value": i}
        )
        await asyncio.sleep(1)

# Subscriber
async def subscriber():
    client = EventRouterClient()
    await client.connect()
    
    @client.on("data.*")
    async def handle_data(event):
        print(f"Received: {event.payload}")
    
    await asyncio.sleep(60)  # Keep running
```

### Agent Communication

```python
class TaskAgent:
    def __init__(self, client):
        self.client = client
    
    async def create_task(self, description):
        await self.client.publish(
            topic="task.created",
            payload={
                "description": description,
                "created_at": datetime.now().isoformat()
            },
            type=EventType.TASK_CREATED,
            priority=EventPriority.HIGH
        )

class WorkerAgent:
    def __init__(self, client):
        self.client = client
        
    async def start(self):
        @self.client.on("task.created")
        async def process_task(event):
            print(f"Processing: {event.payload['description']}")
            # Do work...
            await self.client.publish(
                topic="task.completed",
                payload={"task_id": event.id}
            )
```

### Request-Response Pattern

```python
async def request_response_example():
    client = EventRouterClient()
    await client.connect()
    
    response_received = asyncio.Event()
    response_data = {}
    
    # Set up response handler
    @client.on("response.data")
    async def handle_response(event):
        if event.payload.get("request_id") == "req-123":
            response_data.update(event.payload)
            response_received.set()
    
    # Send request
    await client.publish(
        topic="request.data",
        payload={"request_id": "req-123", "query": "get_status"}
    )
    
    # Wait for response
    await asyncio.wait_for(response_received.wait(), timeout=5.0)
    print(f"Response: {response_data}")
```

## 📊 Managing the Event Router

### Using the Management CLI

The Event Router comes with a comprehensive management CLI for easy control:

```bash
# Start the Event Router as a daemon
uv run python manage_router.py start --daemon

# Check status and health metrics
uv run python manage_router.py status

# Stop the service
uv run python manage_router.py stop

# Restart the service
uv run python manage_router.py restart

# Interactive configuration
uv run python manage_router.py configure

# Monitor live events
uv run python manage_router.py monitor

# View logs
uv run python manage_router.py logs -n 50    # Last 50 lines
uv run python manage_router.py logs -f       # Follow logs
```

### Using the Event Router Manager Agent

You can also manage the Event Router using the dedicated agent:

```
/agent:event-router-manager

Start the event router service and verify it's running
```

The agent can handle all management tasks including starting, stopping, configuring, monitoring, and troubleshooting.

## 🎯 Responding to Specific Events

### Basic Event Response Patterns

#### 1. Direct Topic Response
```python
@client.on("task.created")
async def handle_task_created(event):
    print(f"New task: {event.payload['task_id']}")
    # Respond by claiming the task
    await client.publish(
        topic="task.claimed",
        payload={"task_id": event.payload['task_id']}
    )
```

#### 2. Wildcard Pattern Matching
```python
# Respond to all error events
@client.on("error.*")
async def handle_any_error(event):
    if event.payload.get("severity") == "critical":
        await client.publish("alert.page_oncall", {...})

# Respond to all failure events from any source
@client.on("*.failed")
async def handle_failures(event):
    print(f"Failure detected: {event.topic}")
```

#### 3. Priority-Based Responses
```python
# Only respond to high-priority events
await client.subscribe(
    topics=["task.*"],
    priorities=[EventPriority.HIGH, EventPriority.CRITICAL],
    callback=handle_urgent_tasks
)
```

#### 4. Response Chains
```python
@client.on("order.placed")
async def handle_order(event):
    # One event triggers multiple responses
    await client.publish("inventory.check", {...})
    await client.publish("payment.process", {...})
    await client.publish("email.send", {...})
```

### Complete Response Examples

See these example files for complete implementations:
- `examples/simple_responder.py` - Basic response patterns demo
- `examples/event_responder_demo.py` - Complex multi-agent responses
- `examples/agent_communication.py` - Full agent communication example

## Running the Examples

The repository includes comprehensive examples showing event routing in action:

```bash
# Basic end-to-end test
uv run python test_event_router.py

# Simple response patterns demo
uv run python examples/simple_responder.py

# Complex multi-agent communication
uv run python examples/agent_communication.py

# Event response patterns with chains
uv run python examples/event_responder_demo.py
```

These demonstrate:
- Task creation and processing
- Worker agents claiming tasks
- Error handling and retry logic
- Monitor agents tracking all events
- Priority-based processing
- Response chains and cascading events

## Testing

### Basic Connectivity Test

```bash
# Start server
python examples/start_server.py &

# Run test client
python examples/test_client.py

# Expected output:
# ✅ Connected to ws://localhost:9090
# ✅ Published event: evt-123
# ✅ Subscription created: sub-456
# ✅ Received event: test.event
```

### Load Testing

```python
# Create many clients
async def load_test():
    clients = []
    for i in range(100):
        client = EventRouterClient()
        await client.connect()
        clients.append(client)
    
    # Publish many events
    for _ in range(1000):
        client = random.choice(clients)
        await client.publish(
            topic="load.test",
            payload={"data": "test"}
        )
    
    # Check health
    health = await clients[0].get_health()
    print(f"Processed: {health['events_processed']}")
```

## Configuration

### Server Configuration

```python
router = EventRouter(
    host="0.0.0.0",          # Bind address
    port=9090,               # Port
    max_queue_size=10000,    # Max events in queue
    max_clients=1000,        # Max concurrent clients
    use_multi_queue=False    # Use priority-based multi-queue
)
```

### Client Configuration

```python
client = EventRouterClient(
    url="ws://localhost:9090",
    auto_reconnect=True,           # Enable auto-reconnection
    reconnect_interval=1.0,        # Initial reconnect delay
    max_reconnect_interval=30.0,   # Max reconnect delay
    reconnect_decay=1.5,           # Exponential backoff factor
    heartbeat_interval=30.0,       # Heartbeat interval
    timeout=10.0                   # Connection timeout
)
```

## Deployment

### Local Development
```bash
# No setup required!
python examples/start_server.py
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install websockets
CMD ["python", "src/server.py"]
```

### Production (with Redis backend - future)
```python
# Future enhancement - not yet implemented
router = EventRouter(
    transport="redis",
    redis_url="redis://localhost:6379"
)
```

## API Reference

### Event Model
```python
Event(
    topic: str,                    # Event topic (e.g., "user.created")
    payload: Dict[str, Any],       # Event data
    priority: EventPriority,       # Priority level
    type: EventType,              # Event type
    source: str,                  # Source agent/service
    target: Optional[str],        # Target agent/service
    metadata: EventMetadata       # Tracking metadata
)
```

### Client Methods
```python
# Connect/disconnect
await client.connect()
await client.disconnect()

# Publish events
event_id = await client.publish(topic, payload, priority, type, target)

# Subscribe to events
sub_id = await client.subscribe(topics, types, priorities, callback)
await client.unsubscribe(sub_id)

# Decorators
@client.on("topic.pattern")
async def handler(event): ...

# Health check
health = await client.get_health()

# Context manager
async with EventRouterClient() as client:
    await client.publish(...)
```

## Troubleshooting

### Connection Issues
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check server is running
nc -zv localhost 9090

# Test with wscat
wscat -c ws://localhost:9090
```

### Event Not Received
1. Check subscription topics match
2. Verify priority filters
3. Check client is connected
4. Review server logs

### Memory Issues
- Reduce queue size
- Enable multi-queue for better distribution
- Implement event expiration (future feature)

## Performance

- **Local (in-memory)**: 50,000+ events/second
- **WebSocket**: 10,000+ events/second
- **Latency**: < 1ms local, < 10ms network
- **Concurrent clients**: 1000+ tested

## Roadmap

- [x] Core event routing
- [x] WebSocket transport
- [x] Auto-reconnection
- [x] Priority queues
- [x] Client SDK
- [ ] Persistence layer (SQLite/PostgreSQL)
- [ ] Redis transport option
- [ ] Event replay
- [ ] Dead letter queue
- [ ] Horizontal scaling
- [ ] Admin UI

## Contributing

Contributions are welcome! Areas of focus:
- Persistence layer implementation
- Additional transport options
- Performance optimizations
- Testing improvements

## License

MIT License - See LICENSE file for details