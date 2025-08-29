#!/usr/bin/env python3
"""Example: Agent Communication via Event Router.

This example demonstrates:
1. Starting the event router server
2. Multiple agents communicating via events
3. Task creation, assignment, and completion workflow
4. Error handling and retries
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.router import EventRouter
from src.core.models import Event, EventType, EventPriority
from src.client.client import EventRouterClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskManagerAgent:
    """Agent that creates and manages tasks."""

    def __init__(self, client: EventRouterClient):
        self.client = client
        self.agent_id = "task_manager"
        self.pending_tasks = {}
        self.completed_tasks = {}

    async def start(self):
        """Start the task manager agent."""
        logger.info(f"Starting {self.agent_id}")

        # Subscribe to task events
        await self.client.subscribe(
            topics=["task.completed", "task.failed"],
            callback=self.handle_task_update  # type: ignore[assignment]
        )

        # Publish agent started event
        await self.client.publish(
            topic="agent.started",
            payload={"agent_id": self.agent_id, "type": "task_manager"},
            type=EventType.AGENT_STARTED
        )

    async def create_task(self, task_id: str, description: str, priority: EventPriority = EventPriority.NORMAL):
        """Create a new task."""
        task = {
            "task_id": task_id,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        }

        self.pending_tasks[task_id] = task

        # Publish task created event
        event_id = await self.client.publish(
            topic="task.created",
            payload=task,
            priority=priority,
            type=EventType.TASK_CREATED
        )

        logger.info(f"Created task {task_id}: {description} (event: {event_id})")
        return task_id

    async def handle_task_update(self, event: Event):
        """Handle task completion or failure."""
        task_id = event.payload.get("task_id")

        if event.type == EventType.TASK_COMPLETED:
            if task_id in self.pending_tasks:
                task = self.pending_tasks.pop(task_id)
                task["status"] = "completed"
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                task["result"] = event.payload.get("result")
                self.completed_tasks[task_id] = task
                logger.info(f"Task {task_id} completed: {event.payload.get('result')}")

        elif event.type == EventType.TASK_FAILED:
            if task_id in self.pending_tasks:
                task = self.pending_tasks[task_id]
                task["status"] = "failed"
                task["error"] = event.payload.get("error")
                logger.error(f"Task {task_id} failed: {event.payload.get('error')}")

    def get_stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        return {
            "pending": len(self.pending_tasks),
            "completed": len(self.completed_tasks),
            "total": len(self.pending_tasks) + len(self.completed_tasks)
        }


class WorkerAgent:
    """Agent that processes tasks."""

    def __init__(self, client: EventRouterClient, worker_id: str):
        self.client = client
        self.agent_id = f"worker_{worker_id}"
        self.worker_id = worker_id
        self.tasks_processed = 0
        self.current_task = None

    async def start(self):
        """Start the worker agent."""
        logger.info(f"Starting {self.agent_id}")

        # Subscribe to task created events
        await self.client.subscribe(
            topics=["task.created", "task.assigned"],
            callback=self.handle_task_event  # type: ignore[assignment]
        )

        # Publish agent started event
        await self.client.publish(
            topic="agent.started",
            payload={"agent_id": self.agent_id, "type": "worker"},
            type=EventType.AGENT_STARTED
        )

    async def handle_task_event(self, event: Event):
        """Handle task creation or assignment."""
        if event.type == EventType.TASK_CREATED and not self.current_task:
            # Claim the task
            task_id = event.payload.get("task_id")
            self.current_task = task_id

            # Publish task assigned event
            await self.client.publish(
                topic="task.assigned",
                payload={
                    "task_id": task_id,
                    "worker_id": self.worker_id,
                    "assigned_at": datetime.now(timezone.utc).isoformat()
                },
                type=EventType.TASK_ASSIGNED
            )

            logger.info(f"{self.agent_id} claimed task {task_id}")

            # Process the task
            await self.process_task(event.payload)

    async def process_task(self, task: Dict[str, Any]):
        """Process a task."""
        task_id = task.get("task_id")
        description = task.get("description")

        logger.info(f"{self.agent_id} processing task {task_id}: {description}")

        # Publish task started event
        await self.client.publish(
            topic="task.started",
            payload={
                "task_id": task_id,
                "worker_id": self.worker_id,
                "started_at": datetime.now(timezone.utc).isoformat()
            },
            type=EventType.TASK_STARTED
        )

        # Simulate task processing
        await asyncio.sleep(2)

        # Simulate success/failure (90% success rate)
        import random
        if random.random() < 0.9:
            # Task succeeded
            result = f"Processed: {description} (by {self.worker_id})"

            await self.client.publish(
                topic="task.completed",
                payload={
                    "task_id": task_id,
                    "worker_id": self.worker_id,
                    "result": result,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                },
                type=EventType.TASK_COMPLETED,
                priority=EventPriority.HIGH
            )

            logger.info(f"{self.agent_id} completed task {task_id}")
            self.tasks_processed += 1
        else:
            # Task failed
            error = "Simulated processing error"

            await self.client.publish(
                topic="task.failed",
                payload={
                    "task_id": task_id,
                    "worker_id": self.worker_id,
                    "error": error,
                    "failed_at": datetime.now(timezone.utc).isoformat()
                },
                type=EventType.TASK_FAILED,
                priority=EventPriority.HIGH
            )

            logger.error(f"{self.agent_id} failed task {task_id}: {error}")

        # Clear current task
        self.current_task = None

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        return {
            "worker_id": self.worker_id,
            "tasks_processed": self.tasks_processed,
            "busy": self.current_task is not None
        }


class MonitorAgent:
    """Agent that monitors system events."""

    def __init__(self, client: EventRouterClient):
        self.client = client
        self.agent_id = "monitor"
        self.event_counts = {}
        self.agent_status = {}

    async def start(self):
        """Start the monitor agent."""
        logger.info(f"Starting {self.agent_id}")

        # Subscribe to all events
        await self.client.subscribe(
            topics=["*"],
            callback=self.handle_event  # type: ignore[assignment]
        )

        # Publish agent started event
        await self.client.publish(
            topic="agent.started",
            payload={"agent_id": self.agent_id, "type": "monitor"},
            type=EventType.AGENT_STARTED
        )

        # Start periodic status reports
        asyncio.create_task(self.periodic_status())

    async def handle_event(self, event: Event):
        """Handle any event for monitoring."""
        # Count events by type
        event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1

        # Track agent status
        if event.type == EventType.AGENT_STARTED:
            agent_id = event.payload.get("agent_id")
            self.agent_status[agent_id] = "online"
        elif event.type == EventType.AGENT_STOPPED:
            agent_id = event.payload.get("agent_id")
            self.agent_status[agent_id] = "offline"

        # Log high-priority events
        if event.priority >= EventPriority.HIGH:
            logger.info(f"[MONITOR] High-priority event: {event.topic} from {event.source}")

    async def periodic_status(self):
        """Send periodic status reports."""
        while True:
            await asyncio.sleep(10)

            status = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_counts": self.event_counts.copy(),
                "agent_status": self.agent_status.copy(),
                "total_events": sum(self.event_counts.values())
            }

            await self.client.publish(
                topic="system.status",
                payload=status,
                type=EventType.SYSTEM_INFO,
                priority=EventPriority.LOW
            )

            logger.info(f"[MONITOR] Status: {status['total_events']} total events, "
                       f"{len(self.agent_status)} agents tracked")


async def run_example():
    """Run the agent communication example."""
    print("=" * 60)
    print("Event Router Agent Communication Example")
    print("=" * 60)

    # Start event router server
    print("\n1. Starting Event Router Server...")
    router = EventRouter(host="localhost", port=9090)
    server_task = asyncio.create_task(router.start())
    await asyncio.sleep(1)  # Give server time to start

    print("   ✓ Event Router running on ws://localhost:9090")

    # Create clients for agents
    print("\n2. Creating Agent Clients...")

    # Task Manager client
    tm_client = EventRouterClient(url="ws://localhost:9090")
    await tm_client.connect()
    task_manager = TaskManagerAgent(tm_client)

    # Worker clients
    worker1_client = EventRouterClient(url="ws://localhost:9090")
    await worker1_client.connect()
    worker1 = WorkerAgent(worker1_client, "w1")

    worker2_client = EventRouterClient(url="ws://localhost:9090")
    await worker2_client.connect()
    worker2 = WorkerAgent(worker2_client, "w2")

    # Monitor client
    monitor_client = EventRouterClient(url="ws://localhost:9090")
    await monitor_client.connect()
    monitor = MonitorAgent(monitor_client)

    print("   ✓ Created 4 agent clients")

    # Start agents
    print("\n3. Starting Agents...")
    await task_manager.start()
    await worker1.start()
    await worker2.start()
    await monitor.start()
    await asyncio.sleep(1)

    print("   ✓ All agents started")

    # Create tasks
    print("\n4. Creating Tasks...")
    tasks = [
        ("task-001", "Process user registration", EventPriority.HIGH),
        ("task-002", "Send email notification", EventPriority.NORMAL),
        ("task-003", "Generate report", EventPriority.LOW),
        ("task-004", "Update database", EventPriority.HIGH),
        ("task-005", "Backup files", EventPriority.NORMAL),
    ]

    for task_id, description, priority in tasks:
        await task_manager.create_task(task_id, description, priority)
        await asyncio.sleep(0.5)

    print(f"   ✓ Created {len(tasks)} tasks")

    # Wait for processing
    print("\n5. Processing Tasks...")
    print("   Workers are processing tasks...")
    await asyncio.sleep(15)

    # Get statistics
    print("\n6. Final Statistics:")
    print(f"   Task Manager: {task_manager.get_stats()}")
    print(f"   Worker 1: {worker1.get_stats()}")
    print(f"   Worker 2: {worker2.get_stats()}")

    # Get router health
    health = await router.get_health()
    print(f"\n7. Router Health:")
    print(f"   Status: {health.status}")
    print(f"   Events Processed: {health.events_processed}")
    print(f"   Active Subscriptions: {health.active_subscriptions}")
    print(f"   Connected Clients: {health.connected_clients}")

    # Cleanup
    print("\n8. Shutting down...")
    await tm_client.disconnect()
    await worker1_client.disconnect()
    await worker2_client.disconnect()
    await monitor_client.disconnect()

    await router.stop()
    server_task.cancel()

    print("\n✅ Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        print("\nExample interrupted")
