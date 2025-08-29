"""
Event Handling Mixin for V03Agent
=================================

This mixin handles all event-related functionality including:
- Event system initialization
- Event publishing and batching
- Heartbeat management
- All specific event types (initialization, task events, etc.)
"""

import asyncio
import aiohttp
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Protocol
from urllib.parse import urljoin

if TYPE_CHECKING:
    from dataclasses import dataclass
    from ...shared.memory_integration import AgentMemoryInterface
    
    @dataclass
    class EventConfiguration:
        """Configuration for event publishing."""
        enabled: bool
        event_router_url: str
        timeout_seconds: int
        retry_attempts: int
        batch_size: int
        emit_heartbeat: bool
        heartbeat_interval: int
        store_in_memory: bool
        graceful_degradation: bool
    
    @dataclass
    class AgentCapabilities:
        """Agent capabilities configuration."""
        can_parallelize: bool
        can_create_prs: bool
        can_write_code: bool
        can_review_code: bool
        can_test: bool
        can_document: bool
        expertise_areas: List[str]
        max_parallel_tasks: int


class EventHandlerProtocol(Protocol):
    """Protocol defining the interface that EventHandlerMixin expects from the base class."""
    agent_id: str
    agent_type: str
    current_task_id: Optional[str]
    start_time: datetime
    tasks_completed: int
    success_rate: float
    knowledge_loaded: bool
    capabilities: 'AgentCapabilities'
    memory: Optional['AgentMemoryInterface']
    event_config: 'EventConfiguration'
    _event_session: Optional[aiohttp.ClientSession]
    _event_batch: List[Dict[str, Any]]
    _last_heartbeat: datetime
    _heartbeat_task: Optional[asyncio.Task]
    _event_publishing_enabled: bool


class EventHandlerMixin:
    """
    Mixin providing event handling capabilities for V03Agent.
    
    This mixin requires the base class to implement EventHandlerProtocol.
    All required attributes are defined in the protocol above.
    """
    
    # Type hints for mixin attributes (these will be provided by the base class)
    agent_id: str
    agent_type: str
    current_task_id: Optional[str]
    start_time: datetime
    tasks_completed: int
    success_rate: float
    knowledge_loaded: bool
    capabilities: Any  # Will be AgentCapabilities from base
    memory: Optional[Any]  # Will be AgentMemoryInterface from base
    event_config: Any  # Will be EventConfiguration from base
    _event_session: Optional[aiohttp.ClientSession]
    _event_batch: List[Dict[str, Any]]
    _last_heartbeat: datetime
    _heartbeat_task: Optional[asyncio.Task]
    _event_publishing_enabled: bool

    async def _initialize_event_system(self) -> None:
        """Initialize the event publishing system."""
        if not self.event_config.enabled:
            print(f"  🔊 Event publishing disabled for {self.agent_id}")
            return

        try:
            # Create HTTP session for event publishing
            connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
            timeout = aiohttp.ClientTimeout(total=self.event_config.timeout_seconds)
            self._event_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )

            # Test connection to event router
            await self._test_event_router_connection()

            # Start heartbeat task if enabled
            if self.event_config.emit_heartbeat:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            self._event_publishing_enabled = True
            print(f"  🔊 Event publishing enabled for {self.agent_id}")

        except Exception as e:
            if self.event_config.graceful_degradation:
                print(f"  ⚠️ Event router unavailable, continuing without events: {e}")
                self._event_publishing_enabled = False
            else:
                print(f"  ❌ Event router connection failed: {e}")
                raise

    async def _test_event_router_connection(self) -> bool:
        """Test connection to event router."""
        if not self._event_session:
            return False

        try:
            health_url = urljoin(self.event_config.event_router_url, "/health")
            async with self._event_session.get(health_url) as response:
                if response.status == 200:
                    return True
                else:
                    raise aiohttp.ClientError(f"Health check failed with status {response.status}")
        except Exception as e:
            if not self.event_config.graceful_degradation:
                raise
            print(f"    Event router health check failed: {e}")
            return False

    async def _emit_event(self, event_data: Dict[str, Any]) -> bool:
        """Emit a single event to the event router."""
        if not self._event_publishing_enabled or not self._event_session:
            return False

        # Add metadata
        event_data.update({
            "id": str(uuid.uuid4()),
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "task_id": self.current_task_id,
            "timestamp": datetime.now().isoformat(),
            "priority": event_data.get("priority", "normal")
        })

        try:
            # Try to send immediately
            event_url = urljoin(self.event_config.event_router_url, "/events")
            async with self._event_session.post(event_url, json=event_data) as response:
                if response.status in (200, 201, 202):
                    # Store high-priority events in memory if enabled
                    if (self.event_config.store_in_memory and
                        self.memory and
                        event_data.get("priority") in ["high", "critical"]):
                        try:
                            await self.memory.remember_short_term(
                                f"Event: {event_data.get('event_type')} - {event_data.get('data', {})}",
                                tags=["event", event_data.get("event_type", "unknown")]
                            )
                        except Exception:
                            pass  # Don't fail event emission for memory storage issues
                    return True
                else:
                    raise aiohttp.ClientError(f"Event router returned status {response.status}")

        except Exception as e:
            if self.event_config.graceful_degradation:
                # Add to batch for later retry
                self._event_batch.append(event_data)
                if len(self._event_batch) > self.event_config.batch_size:
                    # Remove oldest events to prevent unbounded growth
                    self._event_batch = self._event_batch[-self.event_config.batch_size:]
                return False
            else:
                raise

    async def _heartbeat_loop(self) -> None:
        """Periodic heartbeat emission."""
        while self._event_publishing_enabled:
            try:
                await asyncio.sleep(self.event_config.heartbeat_interval)

                if self._event_publishing_enabled:
                    await self._emit_event({
                        "event_type": "agent.heartbeat",
                        "data": {
                            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                            "tasks_completed": self.tasks_completed,
                            "success_rate": self.success_rate,
                            "memory_loaded": self.knowledge_loaded,
                            "current_task": self.current_task_id is not None
                        }
                    })
                    self._last_heartbeat = datetime.now()

            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self.event_config.graceful_degradation:
                    print(f"  ⚠️ Heartbeat failed: {e}")
                # Continue heartbeat loop even if individual heartbeats fail

    async def emit_initialized(self, version: Optional[str] = None) -> bool:
        """Emit agent initialization event."""
        return await self._emit_event({
            "event_type": "agent.initialized",
            "priority": "high",
            "data": {
                "version": version or "v0.3",
                "capabilities": {
                    "can_parallelize": self.capabilities.can_parallelize,
                    "can_create_prs": self.capabilities.can_create_prs,
                    "can_write_code": self.capabilities.can_write_code,
                    "can_review_code": self.capabilities.can_review_code,
                    "can_test": self.capabilities.can_test,
                    "can_document": self.capabilities.can_document,
                    "expertise_areas": self.capabilities.expertise_areas,
                    "max_parallel_tasks": self.capabilities.max_parallel_tasks
                },
                "knowledge_loaded": self.knowledge_loaded,
                "event_config": {
                    "enabled": self.event_config.enabled,
                    "emit_heartbeat": self.event_config.emit_heartbeat,
                    "store_in_memory": self.event_config.store_in_memory
                }
            }
        })

    async def emit_task_started(self, task_description: str, estimated_duration: Optional[int] = None, dependencies: Optional[List[str]] = None) -> bool:
        """Emit task started event."""
        return await self._emit_event({
            "event_type": "task.started",
            "priority": "normal",
            "data": {
                "task_description": task_description,
                "estimated_duration": estimated_duration,
                "dependencies": dependencies or [],
                "agent_capabilities": self.capabilities.expertise_areas
            }
        })

    async def emit_task_completed(self,
                                task_id: str,
                                task_type: str,
                                success: bool = True,
                                duration_seconds: Optional[float] = None,
                                artifacts: Optional[List[str]] = None,
                                result: Optional[str] = None,
                                error: Optional[str] = None) -> bool:
        """Emit task completion event."""
        event_type = "task.completed" if success else "task.failed"
        priority = "normal" if success else "high"

        return await self._emit_event({
            "event_type": event_type,
            "priority": priority,
            "data": {
                "task_id": task_id,
                "task_type": task_type,
                "success": success,
                "duration": duration_seconds,
                "artifacts": artifacts or [],
                "result": result,
                "error": error,
                "success_metrics": {
                    "total_tasks_completed": self.tasks_completed,
                    "overall_success_rate": self.success_rate
                }
            }
        })

    async def emit_knowledge_learned(self,
                                   knowledge_type: str,
                                   content: str,
                                   confidence: float = 0.8,
                                   source: Optional[str] = None) -> bool:
        """Emit knowledge learning event."""
        return await self._emit_event({
            "event_type": "knowledge.learned",
            "priority": "normal",
            "data": {
                "knowledge_type": knowledge_type,
                "content": content[:500],  # Limit content length
                "confidence": confidence,
                "source": source,
                "learning_context": {
                    "current_task": self.current_task_id,
                    "agent_experience": self.tasks_completed,
                    "success_rate": self.success_rate
                }
            }
        })

    async def emit_collaboration(self,
                               message: str,
                               message_type: str = "notification",
                               recipient_id: Optional[str] = None,
                               requires_response: bool = False,
                               decision: Optional[str] = None) -> bool:
        """Emit collaboration event."""
        return await self._emit_event({
            "event_type": "collaboration.message",
            "priority": "high" if requires_response else "normal",
            "data": {
                "recipient_id": recipient_id,
                "message_type": message_type,
                "content": message,
                "requires_response": requires_response,
                "decision": decision,
                "collaboration_context": {
                    "current_task": self.current_task_id,
                    "agent_type": self.agent_type,
                    "expertise_areas": self.capabilities.expertise_areas
                }
            }
        })

    async def emit_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Emit error event."""
        return await self._emit_event({
            "event_type": "error.occurred",
            "priority": "critical",
            "data": {
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
                "agent_state": {
                    "current_task": self.current_task_id,
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "tasks_completed": self.tasks_completed
                }
            }
        })

    async def emit_shutdown_event(self) -> None:
        """Emit shutdown event."""
        if self._event_publishing_enabled:
            try:
                await self._emit_event({
                    "event_type": "agent.shutdown",
                    "agent_id": self.agent_id,
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "tasks_completed": self.tasks_completed,
                        "success_rate": self.success_rate,
                        "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
                    }
                })
            except Exception as e:
                print(f"  ⚠️ Failed to emit shutdown event: {e}")

    async def flush_event_batch(self) -> int:
        """Flush any batched events. Returns number of events successfully sent."""
        if not self._event_batch or not self._event_publishing_enabled:
            return 0

        sent_count = 0
        failed_events = []

        for event_data in self._event_batch:
            try:
                if await self._emit_event(event_data):
                    sent_count += 1
                else:
                    failed_events.append(event_data)
            except Exception:
                failed_events.append(event_data)

        # Keep failed events for next retry
        self._event_batch = failed_events

        if sent_count > 0:
            print(f"  📤 Flushed {sent_count} batched events")

        return sent_count

    async def cleanup_event_system(self) -> None:
        """Clean up event system resources."""
        # Stop heartbeat task
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close event session
        if self._event_session:
            await self._event_session.close()