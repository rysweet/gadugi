#!/usr/bin/env python3
"""
Event Responder Demo - Shows how agents respond to specific events.

This example demonstrates:
1. Task Manager creating tasks
2. Workers responding to task.created events
3. Monitor responding to all events
4. Error handler responding to failures
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.router import EventRouter
from src.core.models import EventPriority
from src.client.client import EventRouterClient


class TaskManagerAgent:
    """Creates tasks that other agents respond to."""

    def __init__(self, client: EventRouterClient):
        self.client = client
        self.name = "TaskManager"

    async def start(self):
        print(f"[{self.name}] Starting...")

        # Create tasks periodically
        for i in range(3):
            await asyncio.sleep(2)
            task_id = f"task-{i+1:03d}"

            await self.client.publish(
                topic="task.created",
                payload={
                    "task_id": task_id,
                    "type": "process_data" if i % 2 == 0 else "generate_report",
                    "priority": "high" if i == 0 else "normal",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                priority=EventPriority.HIGH if i == 0 else EventPriority.NORMAL,
            )
            print(f"[{self.name}] Created {task_id}")


class WorkerAgent:
    """Responds to task.created events by processing tasks."""

    def __init__(self, client: EventRouterClient, worker_id: str):
        self.client = client
        self.worker_id = worker_id
        self.name = f"Worker-{worker_id}"
        self.processing = False

    async def start(self):
        print(f"[{self.name}] Starting and subscribing to task.created events...")

        # Subscribe to task creation events
        @self.client.on("task.created")
        async def respond_to_task(event):
            # Only claim if not already processing
            if not self.processing:
                task_id = event.payload.get("task_id")
                task_type = event.payload.get("type")

                # Decide if this worker can handle this task type
                if task_type == "process_data" and self.worker_id == "A":
                    await self.claim_and_process_task(task_id, task_type)
                elif task_type == "generate_report" and self.worker_id == "B":
                    await self.claim_and_process_task(task_id, task_type)

    async def claim_and_process_task(self, task_id: str, task_type: str):
        """Claim and process a task."""
        self.processing = True

        # Publish task.claimed event
        await self.client.publish(
            topic="task.claimed",
            payload={
                "task_id": task_id,
                "worker_id": self.worker_id,
                "claimed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        print(f"[{self.name}] Claimed {task_id} ({task_type})")

        # Simulate processing
        await asyncio.sleep(3)

        # Randomly succeed or fail (90% success rate)
        import random

        if random.random() < 0.9:
            # Publish task.completed event
            await self.client.publish(
                topic="task.completed",
                payload={
                    "task_id": task_id,
                    "worker_id": self.worker_id,
                    "result": f"Processed {task_type} successfully",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                },
                priority=EventPriority.NORMAL,
            )
            print(f"[{self.name}] Completed {task_id}")
        else:
            # Publish task.failed event
            await self.client.publish(
                topic="task.failed",
                payload={
                    "task_id": task_id,
                    "worker_id": self.worker_id,
                    "error": "Simulated processing error",
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                },
                priority=EventPriority.HIGH,
            )
            print(f"[{self.name}] Failed {task_id}")

        self.processing = False


class ErrorHandlerAgent:
    """Responds to task.failed events by creating alerts."""

    def __init__(self, client: EventRouterClient):
        self.client = client
        self.name = "ErrorHandler"

    async def start(self):
        print(f"[{self.name}] Starting and subscribing to failure events...")

        # Subscribe to all failure events
        @self.client.on("*.failed")
        async def respond_to_failure(event):
            task_id = event.payload.get("task_id")
            error = event.payload.get("error")

            print(f"[{self.name}] Detected failure in {task_id}: {error}")

            # Respond by creating an alert
            await self.client.publish(
                topic="system.alert",
                payload={
                    "alert_type": "task_failure",
                    "task_id": task_id,
                    "error": error,
                    "severity": "high",
                    "suggested_action": "retry_task",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                priority=EventPriority.CRITICAL,
            )

            # Also create a retry task
            await self.client.publish(
                topic="task.retry_requested",
                payload={
                    "original_task_id": task_id,
                    "retry_count": 1,
                    "reason": error,
                },
            )
            print(f"[{self.name}] Created alert and retry request for {task_id}")


class MonitorAgent:
    """Responds to ALL events by logging and tracking metrics."""

    def __init__(self, client: EventRouterClient):
        self.client = client
        self.name = "Monitor"
        self.event_counts = {}
        self.task_stats = {"created": 0, "claimed": 0, "completed": 0, "failed": 0}

    async def start(self):
        print(f"[{self.name}] Starting and subscribing to ALL events...")

        # Subscribe to everything
        @self.client.on("*")
        async def respond_to_any_event(event):
            # Count events by topic
            self.event_counts[event.topic] = self.event_counts.get(event.topic, 0) + 1

            # Track task statistics
            if event.topic.startswith("task."):
                action = event.topic.split(".")[1]
                if action in self.task_stats:
                    self.task_stats[action] += 1

            # Log high-priority events
            if event.priority >= EventPriority.HIGH:
                print(f"[{self.name}] HIGH PRIORITY: {event.topic} from {event.source}")

            # Respond to system alerts by logging
            if event.topic == "system.alert":
                severity = event.payload.get("severity")
                alert_type = event.payload.get("alert_type")
                print(f"[{self.name}] ALERT [{severity}]: {alert_type}")

        # Periodically publish statistics
        async def publish_stats():
            while True:
                await asyncio.sleep(10)
                await self.client.publish(
                    topic="monitor.stats",
                    payload={
                        "event_counts": self.event_counts,
                        "task_stats": self.task_stats,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    priority=EventPriority.LOW,
                )
                print(
                    f"[{self.name}] Stats - Tasks: created={self.task_stats['created']}, "
                    f"completed={self.task_stats['completed']}, failed={self.task_stats['failed']}"
                )

        asyncio.create_task(publish_stats())


class RetryCoordinator:
    """Responds to task.retry_requested events by re-creating tasks."""

    def __init__(self, client: EventRouterClient):
        self.client = client
        self.name = "RetryCoordinator"

    async def start(self):
        print(f"[{self.name}] Starting and subscribing to retry requests...")

        @self.client.on("task.retry_requested")
        async def respond_to_retry_request(event):
            original_task_id = event.payload.get("original_task_id")
            retry_count = event.payload.get("retry_count", 1)

            if retry_count <= 3:  # Max 3 retries
                new_task_id = f"{original_task_id}-retry{retry_count}"

                # Re-create the task
                await self.client.publish(
                    topic="task.created",
                    payload={
                        "task_id": new_task_id,
                        "type": "process_data",  # Default type for retry
                        "priority": "high",  # Elevated priority for retries
                        "retry_of": original_task_id,
                        "retry_count": retry_count,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    },
                    priority=EventPriority.HIGH,
                )
                print(
                    f"[{self.name}] Created retry task {new_task_id} (attempt {retry_count})"
                )
            else:
                print(f"[{self.name}] Max retries exceeded for {original_task_id}")

                # Publish final failure event
                await self.client.publish(
                    topic="task.abandoned",
                    payload={
                        "task_id": original_task_id,
                        "reason": "max_retries_exceeded",
                        "retry_count": retry_count,
                    },
                    priority=EventPriority.CRITICAL,
                )


async def run_demo():
    """Run the event responder demo."""
    print("=" * 60)
    print("Event Responder Demo")
    print("=" * 60)

    # Start Event Router
    print("\n1. Starting Event Router...")
    router = EventRouter(host="localhost", port=9092)
    server_task = asyncio.create_task(router.start())
    await asyncio.sleep(1)

    # Create clients for each agent
    print("\n2. Creating Agent Clients...")

    # Task Manager
    tm_client = EventRouterClient(url="ws://localhost:9092")
    await tm_client.connect()
    task_manager = TaskManagerAgent(tm_client)

    # Workers
    worker_a_client = EventRouterClient(url="ws://localhost:9092")
    await worker_a_client.connect()
    worker_a = WorkerAgent(worker_a_client, "A")

    worker_b_client = EventRouterClient(url="ws://localhost:9092")
    await worker_b_client.connect()
    worker_b = WorkerAgent(worker_b_client, "B")

    # Error Handler
    error_client = EventRouterClient(url="ws://localhost:9092")
    await error_client.connect()
    error_handler = ErrorHandlerAgent(error_client)

    # Monitor
    monitor_client = EventRouterClient(url="ws://localhost:9092")
    await monitor_client.connect()
    monitor = MonitorAgent(monitor_client)

    # Retry Coordinator
    retry_client = EventRouterClient(url="ws://localhost:9092")
    await retry_client.connect()
    retry_coordinator = RetryCoordinator(retry_client)

    # Start all agents
    print("\n3. Starting All Agents...")
    await worker_a.start()
    await worker_b.start()
    await error_handler.start()
    await monitor.start()
    await retry_coordinator.start()
    await asyncio.sleep(1)

    # Start task creation
    print("\n4. Creating Tasks and Observing Responses...")
    print("-" * 40)
    await task_manager.start()

    # Let the system run
    await asyncio.sleep(15)

    # Show final stats
    print("\n5. Final Statistics:")
    print("-" * 40)
    health = await router.get_health()
    print(f"Events Processed: {health.events_processed}")
    print(f"Active Subscriptions: {health.active_subscriptions}")
    print(f"Connected Clients: {health.connected_clients}")

    # Cleanup
    print("\n6. Shutting down...")
    await tm_client.disconnect()
    await worker_a_client.disconnect()
    await worker_b_client.disconnect()
    await error_client.disconnect()
    await monitor_client.disconnect()
    await retry_client.disconnect()

    await router.stop()
    server_task.cancel()

    print("\n✅ Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted")
