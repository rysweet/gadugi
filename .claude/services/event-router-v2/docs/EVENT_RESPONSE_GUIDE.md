# Event Response Guide - How to Respond to Specific Events

## Quick Start

To respond to specific events in the Event Router, you subscribe to topics and provide handlers that execute when matching events arrive.

## Response Patterns

### 1. Direct Topic Response

Respond to a specific event topic:

```python
from src.client.client import EventRouterClient

client = EventRouterClient()
await client.connect()

@client.on("task.created")
async def handle_task_created(event):
    print(f"New task: {event.payload['task_id']}")
    
    # Respond by claiming the task
    await client.publish(
        topic="task.claimed",
        payload={"task_id": event.payload['task_id']}
    )
```

### 2. Wildcard Pattern Matching

Use wildcards to respond to multiple related events:

```python
# Respond to all error events
@client.on("error.*")
async def handle_any_error(event):
    if "critical" in event.payload.get("severity", ""):
        await client.publish(
            topic="alert.page_oncall",
            payload={"error": event.id}
        )

# Respond to all agent events
@client.on("agent.*")
async def track_agent_lifecycle(event):
    print(f"Agent event: {event.topic}")
```

### 3. Priority-Based Responses

Respond only to high-priority events:

```python
from src.core.models import EventPriority

await client.subscribe(
    topics=["task.*"],
    priorities=[EventPriority.HIGH, EventPriority.CRITICAL],
    callback=async def(event):
        # Only receives HIGH and CRITICAL priority tasks
        await client.publish(
            topic="task.escalated",
            payload={"task_id": event.payload["task_id"]}
        )
)
```

### 4. Conditional Responses

Check event payload and respond conditionally:

```python
@client.on("order.placed")
async def handle_order(event):
    total = event.payload.get("total", 0)
    
    if total > 1000:
        # High-value order - priority processing
        await client.publish(
            topic="order.priority",
            payload=event.payload,
            priority=EventPriority.HIGH
        )
    elif total < 10:
        # Low-value order - fraud check
        await client.publish(
            topic="order.review",
            payload={"order_id": event.payload["order_id"], "reason": "low_value"}
        )
    else:
        # Normal processing
        await client.publish(
            topic="order.process",
            payload=event.payload
        )
```

### 5. Response Chains

One event triggers multiple coordinated responses:

```python
@client.on("deployment.started")
async def handle_deployment(event):
    deployment_id = event.payload["deployment_id"]
    
    # Trigger multiple responses in sequence or parallel
    
    # 1. Notify team
    await client.publish(
        topic="notification.slack",
        payload={"channel": "#deployments", "message": f"Deployment {deployment_id} started"}
    )
    
    # 2. Start monitoring
    await client.publish(
        topic="monitoring.track",
        payload={"deployment_id": deployment_id, "metrics": ["cpu", "memory", "errors"]}
    )
    
    # 3. Create rollback checkpoint
    await client.publish(
        topic="backup.create",
        payload={"deployment_id": deployment_id, "type": "pre_deployment"}
    )
```

### 6. Stateful Responses

Maintain state between events:

```python
class StatefulResponder:
    def __init__(self, client):
        self.client = client
        self.active_tasks = {}
        self.error_counts = {}
    
    async def start(self):
        @self.client.on("task.started")
        async def track_start(event):
            task_id = event.payload["task_id"]
            self.active_tasks[task_id] = event.payload
        
        @self.client.on("task.completed")
        async def track_completion(event):
            task_id = event.payload["task_id"]
            if task_id in self.active_tasks:
                duration = time.time() - self.active_tasks[task_id]["start_time"]
                
                # Respond if task took too long
                if duration > 300:  # 5 minutes
                    await self.client.publish(
                        topic="performance.alert",
                        payload={"task_id": task_id, "duration": duration}
                    )
                
                del self.active_tasks[task_id]
        
        @self.client.on("error.*")
        async def track_errors(event):
            source = event.source
            self.error_counts[source] = self.error_counts.get(source, 0) + 1
            
            # Circuit breaker pattern
            if self.error_counts[source] >= 5:
                await self.client.publish(
                    topic="circuit.open",
                    payload={"source": source, "error_count": self.error_counts[source]}
                )
```

### 7. Aggregation Responses

Collect multiple events and respond with aggregated data:

```python
class AggregatorResponder:
    def __init__(self, client):
        self.client = client
        self.metrics = []
    
    async def start(self):
        @self.client.on("metrics.reported")
        async def collect_metrics(event):
            self.metrics.append(event.payload)
            
            # Every 10 metrics, publish aggregate
            if len(self.metrics) >= 10:
                avg_cpu = sum(m["cpu"] for m in self.metrics) / len(self.metrics)
                max_memory = max(m["memory"] for m in self.metrics)
                
                await self.client.publish(
                    topic="metrics.aggregate",
                    payload={
                        "period": "10_events",
                        "avg_cpu": avg_cpu,
                        "max_memory": max_memory,
                        "sample_count": len(self.metrics)
                    }
                )
                
                self.metrics = []  # Reset
```

## Real-World Agent Examples

### Task Worker Agent

```python
class TaskWorkerAgent:
    """Agent that responds to task.created events by processing tasks."""
    
    def __init__(self, client, capabilities):
        self.client = client
        self.capabilities = capabilities  # What tasks this worker can handle
        self.busy = False
    
    async def start(self):
        @self.client.on("task.created")
        async def respond_to_task(event):
            # Only respond if not busy and capable
            if not self.busy and event.payload["type"] in self.capabilities:
                await self.process_task(event)
    
    async def process_task(self, event):
        self.busy = True
        task_id = event.payload["task_id"]
        
        # Claim the task
        await self.client.publish(
            topic="task.claimed",
            payload={"task_id": task_id, "worker": self.worker_id}
        )
        
        try:
            # Process based on type
            result = await self.execute_task(event.payload)
            
            # Publish completion
            await self.client.publish(
                topic="task.completed",
                payload={"task_id": task_id, "result": result}
            )
        except Exception as e:
            # Publish failure
            await self.client.publish(
                topic="task.failed",
                payload={"task_id": task_id, "error": str(e)}
            )
        finally:
            self.busy = False
```

### Monitor Agent

```python
class MonitorAgent:
    """Agent that responds to ALL events for monitoring."""
    
    def __init__(self, client):
        self.client = client
        self.event_counts = {}
        self.alert_thresholds = {
            "error": 10,
            "failure": 5,
            "timeout": 3
        }
    
    async def start(self):
        # Monitor everything
        @self.client.on("*")
        async def monitor_all(event):
            # Count by topic
            self.event_counts[event.topic] = self.event_counts.get(event.topic, 0) + 1
            
            # Check for alert conditions
            for keyword, threshold in self.alert_thresholds.items():
                if keyword in event.topic:
                    if self.event_counts[event.topic] >= threshold:
                        await self.client.publish(
                            topic="monitor.alert",
                            payload={
                                "event_topic": event.topic,
                                "count": self.event_counts[event.topic],
                                "threshold": threshold
                            },
                            priority=EventPriority.HIGH
                        )
                        # Reset count after alert
                        self.event_counts[event.topic] = 0
```

### Orchestrator Agent

```python
class OrchestratorAgent:
    """Agent that coordinates workflows by responding to phase completions."""
    
    def __init__(self, client):
        self.client = client
        self.workflows = {}
    
    async def start(self):
        @self.client.on("workflow.started")
        async def init_workflow(event):
            workflow_id = event.payload["workflow_id"]
            self.workflows[workflow_id] = {
                "phases": event.payload["phases"],
                "current": 0
            }
            
            # Start first phase
            await self.start_phase(workflow_id, 0)
        
        @self.client.on("phase.completed")
        async def handle_phase_completion(event):
            workflow_id = event.payload["workflow_id"]
            phase_num = event.payload["phase_number"]
            
            if workflow_id in self.workflows:
                workflow = self.workflows[workflow_id]
                
                if phase_num == workflow["current"]:
                    # Move to next phase
                    next_phase = phase_num + 1
                    
                    if next_phase < len(workflow["phases"]):
                        await self.start_phase(workflow_id, next_phase)
                    else:
                        # Workflow complete
                        await self.client.publish(
                            topic="workflow.completed",
                            payload={"workflow_id": workflow_id}
                        )
                        del self.workflows[workflow_id]
    
    async def start_phase(self, workflow_id, phase_num):
        workflow = self.workflows[workflow_id]
        phase = workflow["phases"][phase_num]
        workflow["current"] = phase_num
        
        await self.client.publish(
            topic="phase.start",
            payload={
                "workflow_id": workflow_id,
                "phase_number": phase_num,
                "phase_name": phase["name"],
                "tasks": phase["tasks"]
            }
        )
```

## Best Practices

### 1. Use Specific Topics When Possible
- More specific = better performance
- `task.created` better than `task.*`
- `*` should only be used for monitoring

### 2. Handle Errors Gracefully
```python
@client.on("task.process")
async def safe_handler(event):
    try:
        await process_task(event)
    except Exception as e:
        # Don't crash - publish error event
        await client.publish(
            topic="handler.error",
            payload={"event_id": event.id, "error": str(e)}
        )
```

### 3. Avoid Infinite Loops
```python
# BAD - Can cause infinite loop
@client.on("task.*")
async def bad_handler(event):
    await client.publish(topic="task.updated", ...)  # This triggers itself!

# GOOD - Specific topics prevent loops
@client.on("task.created")
async def good_handler(event):
    await client.publish(topic="task.processing", ...)  # Different topic
```

### 4. Use Priority Appropriately
- CRITICAL: System failures, security issues
- HIGH: Important business events, errors
- NORMAL: Regular operations
- LOW: Logging, metrics, debug info

### 5. Clean Up Subscriptions
```python
# If subscription is temporary
sub_id = await client.subscribe(topics=["temp.*"], callback=handler)
# ... do work ...
await client.unsubscribe(sub_id)
```

## Testing Event Responses

```python
async def test_response_handler():
    # Create test client
    client = EventRouterClient()
    await client.connect()
    
    # Track responses
    responses = []
    
    @client.on("response.test")
    async def capture_response(event):
        responses.append(event)
    
    # Set up handler to test
    @client.on("input.test")
    async def handler_under_test(event):
        # This is what we're testing
        await client.publish(
            topic="response.test",
            payload={"processed": event.payload["value"] * 2}
        )
    
    # Send test event
    await client.publish(
        topic="input.test",
        payload={"value": 5}
    )
    
    # Wait for response
    await asyncio.sleep(0.5)
    
    # Verify
    assert len(responses) == 1
    assert responses[0].payload["processed"] == 10
    
    await client.disconnect()
```

## Common Patterns Summary

| Pattern | Use Case | Example |
|---------|----------|---------|
| Direct Response | Handle specific event | `@client.on("user.login")` |
| Wildcard | Handle category of events | `@client.on("error.*")` |
| Priority Filter | Only important events | `priorities=[HIGH, CRITICAL]` |
| Conditional | Check payload first | `if event.payload["amount"] > 100` |
| Chain | Trigger multiple actions | One event → many publishes |
| Stateful | Track across events | Maintain counters, timers |
| Aggregation | Batch processing | Collect N events, then respond |

The Event Router makes it easy to build reactive, event-driven systems where agents respond to specific conditions and coordinate through events.