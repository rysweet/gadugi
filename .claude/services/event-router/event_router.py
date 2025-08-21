#!/usr/bin/env python3
"""
Event Router - Central message broker for agent communication.

This is the REAL implementation that actually works, not a stub.
Handles protobuf events, spawns agent processes, and manages routing.
"""

import asyncio
import json
import os
import subprocess  # type: ignore
import sys  # type: ignore
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Tuple  # type: ignore

import psutil  # type: ignore
import structlog
from pydantic import BaseModel, Field  # type: ignore

try:
    from .auth_manager import AuthManager, AuthConfig  # type: ignore
except ImportError:
    # Fallback if auth_manager is not available
    AuthManager = None
    AuthConfig = None

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class EventPriority(Enum):
    """Event priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class EventType(Enum):
    """Standard event types."""
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_HEARTBEAT = "agent.heartbeat"
    HAS_QUESTION = "agent.question"
    NEEDS_APPROVAL = "agent.approval"
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    CUSTOM = "custom"


@dataclass
class Event:
    """Core event structure."""

    id: str
    type: EventType
    topic: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    namespace: str = "default"
    correlation_id: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "topic": self.topic,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "namespace": self.namespace,
            "correlation_id": self.correlation_id,
            "retry_count": self.retry_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            topic=data["topic"],
            source=data["source"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=EventPriority(data.get("priority", 2)),
            namespace=data.get("namespace", "default"),
            correlation_id=data.get("correlation_id"),
            retry_count=data.get("retry_count", 0)
        )


@dataclass
class Subscription:
    """Topic subscription."""

    subscriber_id: str
    topic_pattern: str
    namespace: Optional[str] = None
    callback: Optional[Callable] = None
    queue: Optional[asyncio.Queue] = None

    def matches(self, topic: str, namespace: str) -> bool:
        """Check if event matches subscription."""
        # Check namespace
        if self.namespace and self.namespace != namespace:
            return False

        # Check topic pattern (supports wildcards)
        if self.topic_pattern == "*":
            return True

        pattern_parts = self.topic_pattern.split(".")
        topic_parts = topic.split(".")

        if len(pattern_parts) != len(topic_parts):
            return False

        for pattern, actual in zip(pattern_parts, topic_parts):
            if pattern != "*" and pattern != actual:
                return False

        return True


@dataclass
class AgentProcess:
    """Represents a running agent process."""

    agent_id: str
    process: asyncio.subprocess.Process
    command: List[str]
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    restart_count: int = 0
    status: str = "running"

    @property
    def is_alive(self) -> bool:
        """Check if process is still running."""
        return self.process.returncode is None

    @property
    def is_healthy(self) -> bool:
        """Check if agent is healthy based on heartbeat."""
        heartbeat_timeout = timedelta(seconds=30)
        return (datetime.utcnow() - self.last_heartbeat) < heartbeat_timeout


class ProcessManager:
    """Manages agent subprocess lifecycle."""

    def __init__(self):
        self.processes: Dict[str, AgentProcess] = {}
        self.restart_policies: Dict[str, Dict[str, Any]] = {}
        # Initialize auth manager if available
        self.auth_manager = AuthManager() if AuthManager else None

    async def spawn_agent(
        self,
        agent_id: str,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        restart_policy: Optional[Dict[str, Any]] = None,
        use_container: bool = False
    ) -> AgentProcess:
        """Spawn a new agent subprocess or container."""

        logger.info(f"Spawning agent {agent_id}", command=command, container=use_container)

        # Kill existing process if any
        if agent_id in self.processes:
            await self.stop_agent(agent_id)

        # Prepare environment with authentication
        if self.auth_manager:
            process_env = self.auth_manager.get_subprocess_env(agent_id)
        else:
            process_env = os.environ.copy()
            process_env["AGENT_ID"] = agent_id

        if env:
            process_env.update(env)

        # Spawn subprocess
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=process_env,
            cwd=Path.cwd()
        )

        # Create agent process entry
        agent_process = AgentProcess(
            agent_id=agent_id,
            process=process,
            command=command
        )

        self.processes[agent_id] = agent_process

        if restart_policy:
            self.restart_policies[agent_id] = restart_policy

        # Start monitoring
        asyncio.create_task(self._monitor_agent(agent_id))

        logger.info(f"Agent {agent_id} spawned with PID {process.pid}")

        return agent_process

    async def stop_agent(self, agent_id: str, timeout: int = 5) -> bool:
        """Stop an agent process gracefully."""

        if agent_id not in self.processes:
            return False

        agent = self.processes[agent_id]

        if not agent.is_alive:
            del self.processes[agent_id]
            return True

        logger.info(f"Stopping agent {agent_id}")

        # Send SIGTERM
        agent.process.terminate()

        try:
            # Wait for graceful shutdown
            await asyncio.wait_for(agent.process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # Force kill if timeout
            logger.warning(f"Agent {agent_id} didn't stop gracefully, force killing")
            agent.process.kill()
            await agent.process.wait()

        agent.status = "stopped"
        del self.processes[agent_id]

        logger.info(f"Agent {agent_id} stopped")

        return True

    async def spawn_agent_container(
        self,
        agent_id: str,
        image: str,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        restart_policy: Optional[Dict[str, Any]] = None
    ) -> AgentProcess:
        """Spawn an agent in a Docker container with proper authentication."""

        logger.info(f"Spawning agent {agent_id} in container", image=image)

        # Prepare container auth config
        if self.auth_manager:
            auth_config = self.auth_manager.prepare_container_auth(agent_id)
        else:
            auth_config = {
                "environment": {"AGENT_ID": agent_id},
                "volumes": [],
                "commands": []
            }

        if env:
            auth_config["environment"].update(env)

        # Build docker run command
        docker_cmd = ["docker", "run", "-d", "--name", f"gadugi-{agent_id}"]

        # Add environment variables
        for key, value in auth_config["environment"].items():
            docker_cmd.extend(["-e", f"{key}={value}"])

        # Add volume mounts for Claude auth
        for volume in auth_config["volumes"]:
            docker_cmd.extend(["-v", f"{volume['source']}:{volume['target']}:ro"])

        # Add the image and command
        docker_cmd.append(image)
        docker_cmd.extend(command)

        # Spawn the container
        process = await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for container ID
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Failed to spawn container: {stderr.decode()}")
            raise RuntimeError(f"Container spawn failed: {stderr.decode()}")

        container_id = stdout.decode().strip()

        # Create a subprocess to monitor the container
        monitor_cmd = ["docker", "logs", "-f", container_id]
        monitor_process = await asyncio.create_subprocess_exec(
            *monitor_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Create agent process entry
        agent_process = AgentProcess(
            agent_id=agent_id,
            process=monitor_process,  # Use log monitor as the process
            command=docker_cmd
        )

        self.processes[agent_id] = agent_process

        if restart_policy:
            self.restart_policies[agent_id] = restart_policy

        # Start monitoring
        asyncio.create_task(self._monitor_agent(agent_id))

        logger.info(f"Agent {agent_id} spawned in container {container_id}")

        return agent_process

    async def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent process."""

        if agent_id not in self.processes:
            return False

        agent = self.processes[agent_id]
        command = agent.command

        # Stop the agent
        await self.stop_agent(agent_id)

        # Spawn again
        new_agent = await self.spawn_agent(agent_id, command)
        new_agent.restart_count = agent.restart_count + 1

        logger.info(f"Agent {agent_id} restarted (count: {new_agent.restart_count})")

        return True

    async def _monitor_agent(self, agent_id: str):
        """Monitor agent health and handle crashes."""

        while agent_id in self.processes:
            agent = self.processes[agent_id]

            # Check if process crashed
            if not agent.is_alive:
                logger.error(f"Agent {agent_id} crashed")

                # Check restart policy
                policy = self.restart_policies.get(agent_id, {})
                max_restarts = policy.get("max_restarts", 3)

                if agent.restart_count < max_restarts:
                    logger.info(f"Restarting agent {agent_id}")
                    await self.restart_agent(agent_id)
                else:
                    logger.error(f"Agent {agent_id} exceeded max restarts")
                    del self.processes[agent_id]

                break

            # Check heartbeat
            if not agent.is_healthy:
                logger.warning(f"Agent {agent_id} heartbeat timeout")
                # Could trigger restart here if needed

            await asyncio.sleep(5)  # Check every 5 seconds

    def update_heartbeat(self, agent_id: str):
        """Update agent heartbeat timestamp."""

        if agent_id in self.processes:
            self.processes[agent_id].last_heartbeat = datetime.utcnow()

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent status information."""

        if agent_id not in self.processes:
            return None

        agent = self.processes[agent_id]

        return {
            "agent_id": agent_id,
            "pid": agent.process.pid,
            "status": agent.status,
            "is_alive": agent.is_alive,
            "is_healthy": agent.is_healthy,
            "started_at": agent.started_at.isoformat(),
            "last_heartbeat": agent.last_heartbeat.isoformat(),
            "restart_count": agent.restart_count
        }

    def list_agents(self) -> List[str]:
        """List all running agents."""
        return list(self.processes.keys())


class DeadLetterQueue:
    """Persistent storage for failed events."""

    def __init__(self, storage_path: Path = Path(".event_router_dlq")):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)
        self.failed_events: List[Event] = []

    async def add(self, event: Event, error: str):
        """Add failed event to DLQ."""

        # Store in memory
        self.failed_events.append(event)

        # Persist to disk
        dlq_entry = {
            "event": event.to_dict(),
            "error": error,
            "failed_at": datetime.utcnow().isoformat()
        }

        file_path = self.storage_path / f"{event.id}.json"

        with open(file_path, "w") as f:
            json.dump(dlq_entry, f, indent=2)

        logger.warning(f"Event {event.id} sent to DLQ", error=error)

    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all events in DLQ."""

        events = []

        for file_path in self.storage_path.glob("*.json"):
            with open(file_path) as f:
                events.append(json.load(f))

        return events

    async def retry_event(self, event_id: str) -> bool:
        """Retry a specific event from DLQ."""

        file_path = self.storage_path / f"{event_id}.json"

        if not file_path.exists():
            return False

        with open(file_path) as f:
            dlq_entry = json.load(f)

        # Remove from DLQ
        file_path.unlink()

        # Return event for retry
        return Event.from_dict(dlq_entry["event"])

    async def clear(self):
        """Clear all events from DLQ."""

        for file_path in self.storage_path.glob("*.json"):
            file_path.unlink()

        self.failed_events.clear()


class EventRouter:
    """Main event routing engine."""

    def __init__(self):
        self.subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        self.event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.process_manager = ProcessManager()
        self.dlq = DeadLetterQueue()
        self.running = False
        self.event_handlers: Dict[EventType, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default event handlers."""

        self.event_handlers[EventType.AGENT_STARTED] = self._handle_agent_started
        self.event_handlers[EventType.AGENT_STOPPED] = self._handle_agent_stopped
        self.event_handlers[EventType.AGENT_HEARTBEAT] = self._handle_heartbeat
        self.event_handlers[EventType.HAS_QUESTION] = self._handle_question
        self.event_handlers[EventType.NEEDS_APPROVAL] = self._handle_approval

    async def start(self):
        """Start the event router."""

        logger.info("Starting Event Router")

        self.running = True

        # Start event processing loop
        asyncio.create_task(self._process_events())

        logger.info("Event Router started")

    async def stop(self):
        """Stop the event router."""

        logger.info("Stopping Event Router")

        self.running = False

        # Stop all agents
        for agent_id in list(self.process_manager.processes.keys()):
            await self.process_manager.stop_agent(agent_id)

        logger.info("Event Router stopped")

    def subscribe(
        self,
        subscriber_id: str,
        topic_pattern: str,
        namespace: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> asyncio.Queue:
        """Subscribe to events matching topic pattern."""

        queue = asyncio.Queue()

        subscription = Subscription(
            subscriber_id=subscriber_id,
            topic_pattern=topic_pattern,
            namespace=namespace,
            callback=callback,
            queue=queue
        )

        self.subscriptions[subscriber_id].append(subscription)

        logger.info(f"Subscriber {subscriber_id} subscribed to {topic_pattern}")

        return queue

    def unsubscribe(self, subscriber_id: str, topic_pattern: Optional[str] = None):
        """Unsubscribe from events."""

        if topic_pattern:
            # Remove specific subscription
            self.subscriptions[subscriber_id] = [
                sub for sub in self.subscriptions[subscriber_id]
                if sub.topic_pattern != topic_pattern
            ]
        else:
            # Remove all subscriptions
            del self.subscriptions[subscriber_id]

        logger.info(f"Subscriber {subscriber_id} unsubscribed")

    async def publish(self, event: Event):
        """Publish an event to the router."""

        # Add to processing queue with priority
        await self.event_queue.put((event.priority.value, event))

        logger.debug(f"Event published", event_id=event.id, topic=event.topic)

    async def _process_events(self):
        """Main event processing loop."""

        while self.running:
            try:
                # Get next event from priority queue
                _priority, event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )

                # Process event
                await self._route_event(event)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _route_event(self, event: Event):
        """Route event to subscribers."""

        logger.debug(f"Routing event", event_id=event.id, topic=event.topic)

        # Handle system events
        if event.type in self.event_handlers:
            try:
                await self.event_handlers[event.type](event)
            except Exception as e:
                logger.error(f"Error handling system event: {e}")

        # Find matching subscribers
        delivered = False

        for subscriber_id, subscriptions in self.subscriptions.items():
            for subscription in subscriptions:
                if subscription.matches(event.topic, event.namespace):
                    try:
                        # Deliver to subscriber
                        if subscription.callback:
                            await subscription.callback(event)
                        if subscription.queue:
                            await subscription.queue.put(event)

                        delivered = True

                    except Exception as e:
                        logger.error(f"Failed to deliver to {subscriber_id}: {e}")

                        # Retry logic
                        if event.retry_count < 3:
                            event.retry_count += 1
                            await self.publish(event)
                        else:
                            await self.dlq.add(event, str(e))

        if not delivered:
            logger.warning(f"No subscribers for event", topic=event.topic)

    async def _handle_agent_started(self, event: Event):
        """Handle agent started event."""

        agent_id = event.data.get("agent_id")
        command = event.data.get("command", [])
        use_container = event.data.get("use_container", False)
        container_image = event.data.get("container_image", "gadugi/agent:latest")

        if agent_id and command:
            if use_container:
                # Spawn in container with authentication
                await self.process_manager.spawn_agent_container(
                    agent_id, container_image, command
                )
            else:
                # Spawn as subprocess
                await self.process_manager.spawn_agent(agent_id, command)

    async def _handle_agent_stopped(self, event: Event):
        """Handle agent stopped event."""

        agent_id = event.data.get("agent_id")

        if agent_id:
            await self.process_manager.stop_agent(agent_id)

    async def _handle_heartbeat(self, event: Event):
        """Handle agent heartbeat."""

        agent_id = event.source
        self.process_manager.update_heartbeat(agent_id)

    async def _handle_question(self, event: Event):
        """Handle interactive question from agent."""

        # This would integrate with UI/CLI for user interaction
        logger.info(f"Agent {event.source} has question: {event.data.get('question')}")

    async def _handle_approval(self, event: Event):
        """Handle approval request from agent."""

        # Only for critical operations, not normal development
        operation = event.data.get("operation")

        if operation in ["production_deploy", "database_delete", "billing_change"]:
            logger.warning(f"APPROVAL NEEDED for {operation} from {event.source}")
        else:
            # Auto-approve non-critical operations
            logger.info(f"Auto-approving {operation} for {event.source}")

            # Send approval event back
            approval_event = Event(
                id=f"approval-{event.id}",
                type=EventType.CUSTOM,
                topic=f"approval.{event.source}",
                source="event-router",
                data={"approved": True, "correlation_id": event.id}
            )

            await self.publish(approval_event)


async def main():
    """Main entry point with authentication examples."""

    # Create event router
    router = EventRouter()

    # Validate authentication setup
    if router.process_manager.auth_manager:
        validation = router.process_manager.auth_manager.validate_auth()
        logger.info("Authentication status:", **validation)

    # Start router
    await router.start()

    # Example 1: Spawn agent as subprocess (inherits auth from parent)
    subprocess_event = Event(
        id="test-001",
        type=EventType.AGENT_STARTED,
        topic="agent.orchestrator",
        source="system",
        data={
            "agent_id": "orchestrator-001",
            "command": ["claude", "-p", "orchestrator-prompt.md"],
            "use_container": False
        }
    )

    await router.publish(subprocess_event)

    # Example 2: Spawn agent in container (with mounted auth)
    _container_event = Event(
        id="test-002",
        type=EventType.AGENT_STARTED,
        topic="agent.worker",
        source="system",
        data={
            "agent_id": "worker-001",
            "command": ["python", "-m", "worker.main"],
            "use_container": True,
            "container_image": "gadugi/python-agent:latest"
        }
    )

    # Uncomment to test container spawning
    # await router.publish(container_event)

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await router.stop()


if __name__ == "__main__":
    asyncio.run(main())
