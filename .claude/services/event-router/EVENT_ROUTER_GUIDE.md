# Event Router Service Usage Guide

## Overview

The Event Router Service is a real-time event-driven communication system for Gadugi v0.3. It provides:
- Asynchronous event publishing and subscription
- Priority-based event queuing
- WebSocket-based real-time delivery
- Event filtering and routing
- Support for protobuf messages (when available)

## How It's Supposed to Work

### Architecture
```
Agents/Services → Event Router → Subscribers
                      ↓
                 Event Queue
                      ↓
                 Processing
                      ↓
                 Delivery
```

### Key Components

1. **Event Types**:
   - AGENT_STARTED, AGENT_COMPLETED, AGENT_FAILED
   - TASK_CREATED, TASK_UPDATED, TASK_COMPLETED
   - WORKFLOW_STARTED, WORKFLOW_COMPLETED
   - SYSTEM_ALERT, CUSTOM_EVENT

2. **Event Priorities**:
   - CRITICAL: Immediate processing
   - HIGH: Priority processing
   - NORMAL: Standard processing
   - LOW: Background processing

3. **Subscription Types**:
   - ALL: Receive all events
   - FILTERED: Receive filtered events
   - PATTERN: Pattern-based matching
   - CONDITIONAL: Custom condition matching

## Starting the Service

### Method 1: Direct Python Execution
```bash
cd /home/rysweet/gadugi/.claude/services/event-router
python3 event_router_service.py
```

### Method 2: Using asyncio script
```python
#!/usr/bin/env python3
import asyncio
from event_router_service import EventRouterService

async def main():
    # Create service
    service = EventRouterService(
        host="localhost",
        port=9090,
        max_workers=10,
        queue_size=10000
    )
    
    # Start service
    await service.start()
    
    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Client Usage Examples

### 1. Publishing Events (Python Client)
```python
import asyncio
import json
import websockets
from datetime import datetime

async def publish_event():
    uri = "ws://localhost:9090"
    
    async with websockets.connect(uri) as websocket:
        # Publish an event
        event_message = {
            "type": "publish_event",
            "event": {
                "type": "task_created",
                "priority": "normal",
                "source": "task_manager",
                "target": "worker_pool",
                "payload": {
                    "task_id": "task-123",
                    "description": "Process data batch",
                    "created_at": datetime.now().isoformat()
                },
                "metadata": {
                    "user": "system",
                    "version": "1.0"
                }
            }
        }
        
        await websocket.send(json.dumps(event_message))
        
        # Wait for acknowledgment
        response = await websocket.recv()
        print(f"Response: {response}")

asyncio.run(publish_event())
```

### 2. Subscribing to Events
```python
import asyncio
import json
import websockets

async def subscribe_to_events():
    uri = "ws://localhost:9090"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to specific event types
        subscription_message = {
            "type": "subscribe",
            "subscription": {
                "type": "filtered",
                "filter": {
                    "event_types": ["task_created", "task_completed"],
                    "sources": ["task_manager"],
                    "priorities": ["high", "critical"]
                }
            }
        }
        
        await websocket.send(json.dumps(subscription_message))
        
        # Receive events
        while True:
            message = await websocket.recv()
            event = json.loads(message)
            print(f"Received event: {event}")

asyncio.run(subscribe_to_events())
```

### 3. Direct API Usage (No WebSocket)
```python
from event_router_service import EventRouterService, Event, EventType, EventPriority
from datetime import datetime

# Create service instance
service = EventRouterService()

# Create and publish event directly
event = Event(
    id="evt-001",
    type=EventType.AGENT_STARTED,
    priority=EventPriority.HIGH,
    timestamp=datetime.now(),
    source="orchestrator",
    target="monitor",
    payload={"agent": "code_reviewer", "task": "review_pr_123"},
    metadata={"version": "1.0"}
)

# Publish event (async)
await service.publish_event(event)

# Subscribe with callback
def handle_event(event: Event):
    print(f"Received: {event.type.value} from {event.source}")

subscription = await service.subscribe(
    subscriber_id="monitor",
    event_filter=EventFilter(
        event_types=[EventType.AGENT_STARTED, EventType.AGENT_COMPLETED]
    ),
    callback=handle_event
)
```

## Integration with Gadugi Agents

### Agent Publishing Events
```python
# In an agent's execute method
async def execute(self, task):
    # Publish start event
    await self.event_router.publish_event(
        Event(
            type=EventType.AGENT_STARTED,
            source=self.agent_id,
            payload={"task_id": task.id}
        )
    )
    
    try:
        # Do work
        result = await self.process_task(task)
        
        # Publish completion
        await self.event_router.publish_event(
            Event(
                type=EventType.AGENT_COMPLETED,
                source=self.agent_id,
                payload={"task_id": task.id, "result": result}
            )
        )
    except Exception as e:
        # Publish failure
        await self.event_router.publish_event(
            Event(
                type=EventType.AGENT_FAILED,
                source=self.agent_id,
                payload={"task_id": task.id, "error": str(e)}
            )
        )
```

## Current Implementation Status

### What Works:
- ✅ Event data structures (Event, EventFilter, Subscription)
- ✅ Priority-based event queue
- ✅ WebSocket server setup
- ✅ Event publishing mechanism
- ✅ Subscription management
- ✅ Event filtering logic
- ✅ Statistics tracking

### What Needs Implementation:
- ⚠️ Actual protobuf message parsing (currently falls back to JSON)
- ⚠️ Persistent storage for events
- ⚠️ Dead letter queue integration
- ⚠️ Authentication/authorization
- ⚠️ Horizontal scaling support
- ⚠️ Event replay functionality

### Known Issues:
1. The Flask app in main.py is separate from the WebSocket server
2. No automatic reconnection for dropped WebSocket connections
3. No event persistence across service restarts
4. Limited error recovery mechanisms

## Testing the Service

### Quick Test Script
```python
#!/usr/bin/env python3
import asyncio
import json
import websockets

async def test_event_router():
    # Start the service first
    # Then run this test
    
    uri = "ws://localhost:9090"
    
    try:
        async with websockets.connect(uri) as ws:
            print("Connected to Event Router")
            
            # Test ping
            await ws.send(json.dumps({"type": "ping"}))
            pong = await ws.recv()
            print(f"Ping response: {pong}")
            
            # Test event publish
            event = {
                "type": "publish_event",
                "event": {
                    "type": "custom_event",
                    "priority": "normal",
                    "source": "test_client",
                    "payload": {"test": True}
                }
            }
            await ws.send(json.dumps(event))
            ack = await ws.recv()
            print(f"Publish response: {ack}")
            
            print("✅ Event Router is working!")
            
    except Exception as e:
        print(f"❌ Event Router test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_event_router())
```

## Recommendations for Use

1. **For Agent Communication**: Use for loose coupling between agents
2. **For Monitoring**: Subscribe to all agent events for system monitoring
3. **For Workflows**: Coordinate multi-agent workflows via events
4. **For Logging**: Centralize event logging through subscriptions
5. **For Testing**: Use filtered subscriptions to test specific scenarios

## Next Steps

To make the Event Router production-ready:
1. Add persistent storage (Redis/PostgreSQL)
2. Implement proper authentication
3. Add event replay capabilities
4. Integrate with dead letter queue
5. Add health check endpoints
6. Implement circuit breakers
7. Add metrics and monitoring