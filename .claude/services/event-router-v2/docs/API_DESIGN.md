# Event Router V2 - API Design Document

## Core Design Philosophy

The Event Router V2 API is designed with these principles:
1. **Simple Things Should Be Simple**: Publishing an event should be one line of code
2. **Complex Things Should Be Possible**: Advanced filtering, routing, and patterns supported
3. **Fail Gracefully**: Clear errors, automatic recovery, sensible defaults
4. **Transport Agnostic**: Same API whether using memory, WebSocket, or Redis

## Client SDK API

### Initialization

```python
from gadugi.event_router import EventRouterClient

# Auto-detect best transport (memory for local, WebSocket for remote)
client = EventRouterClient()

# Explicit transport selection
client = EventRouterClient(transport="websocket", url="ws://localhost:8080")

# With configuration
client = EventRouterClient(
    config={
        "transport": "redis",
        "connection": {
            "host": "redis.example.com",
            "port": 6379,
            "password": "secret"
        },
        "reconnect": {
            "enabled": True,
            "max_attempts": 5,
            "backoff": "exponential"
        }
    }
)

# Async context manager (recommended)
async with EventRouterClient() as client:
    await client.publish("test", {"data": "value"})
```

### Publishing Events

#### Simple Publishing

```python
# Minimal - just type and payload
await client.publish("user.created", {"id": 123, "name": "Alice"})

# With metadata
await client.publish(
    type="order.placed",
    payload={"order_id": 456, "total": 99.99},
    source="order_service",
    target="payment_service",
    priority=8,
    correlation_id="req-789"
)

# Fire and forget (no wait for acknowledgment)
client.publish_nowait("metric.recorded", {"cpu": 75})
```

#### Batch Publishing

```python
# Publish multiple events efficiently
events = [
    ("user.created", {"id": 1}),
    ("user.created", {"id": 2}),
    ("user.created", {"id": 3})
]
results = await client.publish_batch(events)

# With options per event
events = [
    Event(type="high.priority", payload={}, priority=9),
    Event(type="low.priority", payload={}, priority=2)
]
await client.publish_events(events)
```

#### Transactional Publishing

```python
# All or nothing publishing
async with client.transaction() as tx:
    await tx.publish("order.created", order_data)
    await tx.publish("inventory.reserved", items)
    await tx.publish("payment.initiated", payment)
    # All events published atomically on commit
```

### Subscribing to Events

#### Decorator Style (Recommended)

```python
# Simple handler
@client.on("user.created")
async def handle_user_created(event):
    print(f"New user: {event.payload['name']}")

# Multiple event types
@client.on("user.created", "user.updated", "user.deleted")
async def handle_user_events(event):
    print(f"User event: {event.type}")

# Pattern matching
@client.on_pattern(r"order\.(created|updated)")
async def handle_orders(event):
    await process_order(event)

# With filtering
@client.on("payment.*", filter={"payload.amount": {"$gt": 100}})
async def handle_large_payments(event):
    await audit_payment(event)
```

#### Programmatic Subscription

```python
# Basic subscription
subscription = await client.subscribe(
    "user.*",
    handler=lambda e: print(f"User event: {e}")
)

# With filtering
subscription = await client.subscribe(
    topics=["order.*", "payment.*"],
    filter={
        "priority": {"$gte": 7},
        "source": {"$in": ["order_service", "payment_service"]}
    },
    handler=process_critical_event
)

# Unsubscribe when done
await subscription.unsubscribe()

# Or use context manager
async with client.subscribe("test.*") as subscription:
    async for event in subscription:
        print(event)
        if event.payload.get("stop"):
            break
```

#### Stream Processing

```python
# Process events as a stream
async for event in client.stream("sensor.*"):
    await process_sensor_data(event)

# With batching
async for batch in client.stream("logs.*", batch_size=100, timeout=1.0):
    await bulk_insert_logs(batch)

# Windowed processing
async for window in client.window("metrics.*", size="1m", slide="30s"):
    avg = sum(e.payload["value"] for e in window) / len(window)
    await client.publish("metrics.average", {"value": avg})
```

### Request-Response Pattern

```python
# Make a request
response = await client.request(
    "calculator.add",
    {"x": 10, "y": 20},
    timeout=5.0
)
print(f"Result: {response.payload['result']}")  # Result: 30

# Handle requests
@client.respond("calculator.add")
async def add_numbers(request):
    x = request.payload["x"]
    y = request.payload["y"]
    return {"result": x + y}

# With validation
@client.respond("user.get")
async def get_user(request):
    user_id = request.payload.get("id")
    if not user_id:
        raise ValueError("User ID required")
    
    user = await db.get_user(user_id)
    if not user:
        raise NotFoundError(f"User {user_id} not found")
    
    return user.to_dict()
```

### Advanced Patterns

#### Event Sourcing

```python
# Append events to stream
stream = client.event_stream("order-123")
await stream.append("order.created", order_data)
await stream.append("order.paid", payment_data)
await stream.append("order.shipped", shipping_data)

# Read events from stream
events = await stream.read(from_version=0)
for event in events:
    print(f"Version {event.version}: {event.type}")

# Subscribe to stream updates
@stream.on_append
async def handle_order_update(event):
    await update_read_model(event)
```

#### Saga Pattern

```python
# Define a saga
@client.saga("process_order")
class ProcessOrderSaga:
    @client.on("order.created")
    async def start(self, event):
        # Reserve inventory
        await client.publish("inventory.reserve", {
            "order_id": event.payload["id"],
            "items": event.payload["items"]
        })
    
    @client.on("inventory.reserved")
    async def inventory_reserved(self, event):
        # Process payment
        await client.publish("payment.process", {
            "order_id": event.payload["order_id"],
            "amount": event.payload["total"]
        })
    
    @client.on("payment.completed")
    async def payment_completed(self, event):
        # Ship order
        await client.publish("shipping.create", {
            "order_id": event.payload["order_id"]
        })
        self.complete()  # Saga done
    
    @client.on("inventory.failed", "payment.failed")
    async def handle_failure(self, event):
        # Compensate
        await client.publish("order.cancel", {
            "order_id": event.payload["order_id"],
            "reason": event.payload["error"]
        })
        self.compensate()  # Run compensation
```

#### Circuit Breaker

```python
# Automatic circuit breaker
@client.on("external.api.call")
@client.circuit_breaker(
    failure_threshold=5,
    recovery_timeout=30,
    expected_exception=ApiException
)
async def call_external_api(event):
    response = await external_api.call(event.payload)
    return response
```

## Agent Integration API

### Base Agent Class

```python
from gadugi.event_router import EventEnabledAgent

class MyAgent(EventEnabledAgent):
    """Agent with built-in event support."""
    
    async def on_start(self):
        """Called when agent starts."""
        await self.publish("agent.started", {
            "agent_id": self.id,
            "capabilities": self.capabilities
        })
    
    @event_handler("task.assigned")
    async def handle_task(self, event):
        """Handle assigned tasks."""
        task = event.payload
        
        try:
            result = await self.process_task(task)
            await self.publish("task.completed", {
                "task_id": task["id"],
                "result": result
            })
        except Exception as e:
            await self.publish("task.failed", {
                "task_id": task["id"],
                "error": str(e)
            })
    
    async def process_task(self, task):
        """Process the task."""
        # Implementation here
        return {"status": "success"}
```

### Orchestrator Integration

```python
from gadugi.event_router import OrchestratorMixin

class WorkflowOrchestrator(OrchestratorMixin):
    """Orchestrator with event coordination."""
    
    async def execute_workflow(self, workflow_id: str):
        """Execute a workflow with event tracking."""
        
        # Start workflow
        await self.publish_workflow_event("started", workflow_id)
        
        # Execute steps with event coordination
        async with self.workflow_context(workflow_id) as ctx:
            # Step 1: Assign task
            task_event = await ctx.publish_and_wait(
                "task.assign",
                {"task": "analyze_code"},
                wait_for="task.completed",
                timeout=30
            )
            
            # Step 2: Based on result, route to next step
            if task_event.payload["result"]["issues"]:
                await ctx.publish("review.needed", {
                    "issues": task_event.payload["result"]["issues"]
                })
            else:
                await ctx.publish("deployment.approved", {
                    "workflow_id": workflow_id
                })
        
        # Workflow complete
        await self.publish_workflow_event("completed", workflow_id)
```

## Management API

### CLI Commands

```bash
# Start event router
event-router start --transport websocket --port 8080

# Check status
event-router status
# Output:
# Event Router Status: Running
# Transport: WebSocket (connected)
# Events Published: 10,234
# Active Subscriptions: 45
# Queue Depth: 123

# Monitor events in real-time
event-router monitor --filter "type:user.*"
# [2024-01-01 12:00:00] user.created {"id": 123, "name": "Alice"}
# [2024-01-01 12:00:01] user.updated {"id": 123, "email": "alice@example.com"}

# Replay events
event-router replay --from "2024-01-01T00:00:00" --to "2024-01-01T12:00:00"

# Export events
event-router export --format json --output events.json

# Purge old events
event-router purge --older-than "30d" --confirm
```

### Management Agent

```python
from gadugi.event_router import ManagementAgent

# Create management agent
manager = ManagementAgent(client)

# Get statistics
stats = await manager.get_stats()
print(f"Total events: {stats.total_events}")
print(f"Events/sec: {stats.events_per_second}")

# List subscriptions
subs = await manager.list_subscriptions()
for sub in subs:
    print(f"{sub.id}: {sub.topics} ({sub.client_id})")

# Monitor health
health = await manager.health_check()
if not health.is_healthy:
    print(f"Issues: {health.issues}")

# Manage dead letter queue
dlq = await manager.get_dead_letter_queue()
for event in dlq:
    print(f"Failed event: {event.id} - {event.last_error}")
    
# Retry failed events
await manager.retry_failed_events(event_ids=[e.id for e in dlq])
```

## HTTP REST API

### Publishing Events

```http
POST /api/v1/events
Content-Type: application/json
Authorization: Bearer <token>

{
  "type": "user.created",
  "payload": {
    "id": 123,
    "name": "Alice"
  },
  "priority": 5,
  "source": "api"
}

Response:
{
  "event_id": "evt_abc123",
  "status": "published",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Subscribing via Server-Sent Events

```http
GET /api/v1/events/stream?topics=user.*&filter=priority:gt:5
Accept: text/event-stream
Authorization: Bearer <token>

Response (SSE stream):
data: {"id":"evt_1","type":"user.created","payload":{"id":123}}

data: {"id":"evt_2","type":"user.updated","payload":{"id":123}}
```

### Management Endpoints

```http
# Health check
GET /health
Response:
{
  "status": "healthy",
  "checks": {
    "transport": "ok",
    "persistence": "ok",
    "queue": "ok"
  }
}

# Metrics
GET /metrics
Response (Prometheus format):
# HELP event_router_events_published_total Total events published
# TYPE event_router_events_published_total counter
event_router_events_published_total 10234

# Statistics
GET /api/v1/stats
Response:
{
  "events_published": 10234,
  "events_delivered": 10100,
  "active_subscriptions": 45,
  "queue_depth": 123,
  "error_rate": 0.01
}
```

## Error Handling

### Client Errors

```python
from gadugi.event_router import (
    EventRouterError,
    ConnectionError,
    PublishError,
    SubscriptionError,
    TimeoutError
)

try:
    await client.publish("test", {})
except ConnectionError as e:
    # Handle connection issues
    print(f"Connection failed: {e}")
    await client.reconnect()
except PublishError as e:
    # Handle publish failures
    print(f"Publish failed: {e}")
    if e.retryable:
        await asyncio.sleep(1)
        await client.publish("test", {})
except TimeoutError as e:
    # Handle timeouts
    print(f"Operation timed out: {e}")
```

### Event Error Handling

```python
@client.on("user.created")
@client.error_handler(
    max_retries=3,
    backoff="exponential",
    dead_letter_queue=True
)
async def handle_user(event):
    # If this fails, will retry 3 times
    # Then send to dead letter queue
    await risky_operation(event)

# Global error handler
@client.on_error
async def handle_error(error, event):
    logger.error(f"Event {event.id} failed: {error}")
    await alert_team(error, event)
```

## Performance Optimization

### Batching

```python
# Configure batching
client = EventRouterClient(
    batch_size=100,
    batch_timeout=0.1  # 100ms
)

# Events are automatically batched
for i in range(1000):
    client.publish_nowait("metric", {"value": i})
# Sent in 10 batches of 100
```

### Connection Pooling

```python
# Use connection pool for high throughput
client = EventRouterClient(
    pool_size=10,
    pool_timeout=30
)

# Connections are reused automatically
async def high_volume_publish():
    tasks = []
    for i in range(10000):
        task = client.publish("event", {"id": i})
        tasks.append(task)
    await asyncio.gather(*tasks)
```

### Caching

```python
# Enable client-side caching
client = EventRouterClient(
    cache_size=1000,
    cache_ttl=60  # seconds
)

# Duplicate events are deduplicated
await client.publish("user.created", {"id": 123})
await client.publish("user.created", {"id": 123})  # Cached, not sent
```

## Security

### Authentication

```python
# API key authentication
client = EventRouterClient(
    auth={"type": "api_key", "key": "secret-key"}
)

# JWT authentication
client = EventRouterClient(
    auth={"type": "jwt", "token": jwt_token}
)

# mTLS authentication
client = EventRouterClient(
    auth={
        "type": "mtls",
        "cert": "/path/to/cert.pem",
        "key": "/path/to/key.pem"
    }
)
```

### Authorization

```python
# Topic-based permissions
@client.on("admin.*")
@client.require_permission("admin")
async def handle_admin_event(event):
    # Only called if client has admin permission
    pass

# Custom authorization
@client.on("sensitive.*")
@client.authorize
async def check_auth(event, context):
    user = context.user
    return user.has_permission(f"read:{event.type}")
```

### Encryption

```python
# End-to-end encryption
client = EventRouterClient(
    encryption={
        "enabled": True,
        "algorithm": "AES-256-GCM",
        "key": encryption_key
    }
)

# Payloads are encrypted before transmission
await client.publish("sensitive", {"ssn": "123-45-6789"})
```

This API design provides a clean, intuitive interface for developers while supporting advanced patterns and production requirements.
