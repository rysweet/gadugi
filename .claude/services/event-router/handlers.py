"""
Enhanced request handlers for event-router with memory system integration.
Provides event persistence, filtering, replay, and agent lifecycle tracking.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

# Import memory system components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'memory'))

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    try:
        from ...shared.memory_integration import AgentMemoryInterface as _AgentMemoryInterfaceType
        from ...services.memory.sqlite_memory_backend import SQLiteMemoryBackend as _SQLiteMemoryBackendType
    except ImportError:
        pass

# Create protocol classes for type checking
@runtime_checkable
class AgentMemoryInterface(Protocol):
    def __init__(self, agent_id: str, mcp_base_url: str) -> None:
        ...
    async def __aenter__(self) -> 'AgentMemoryInterface':
        ...
    async def __aexit__(self, *args: Any) -> None:
        ...
    async def remember_long_term(self, content: str, memory_type: str, tags: List[str], importance: float) -> str:
        ...
    async def recall_memories(self, limit: int) -> List[Dict[str, Any]]:
        ...

@runtime_checkable
class SQLiteMemoryBackend(Protocol):
    def __init__(self, db_path: str) -> None:
        ...
    async def initialize(self) -> None:
        ...
    async def store_memory(self, agent_id: str, content: str, memory_type: str, 
                           task_id: Optional[str], importance_score: float, 
                           metadata: Dict[str, Any]) -> str:
        ...
    async def get_memories(self, agent_id: str, memory_type: Optional[str] = None, 
                           task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        ...
    async def get_stats(self) -> Dict[str, Any]:
        ...

# Try to import the actual implementations
try:
    from memory_integration import AgentMemoryInterface as _AgentMemoryInterface  # type: ignore
    from sqlite_memory_backend import SQLiteMemoryBackend as _SQLiteMemoryBackend  # type: ignore
    AgentMemoryInterfaceImpl = _AgentMemoryInterface
    SQLiteMemoryBackendImpl = _SQLiteMemoryBackend
except ImportError:
    try:
        from ...shared.memory_integration import AgentMemoryInterface as _AgentMemoryInterface  # type: ignore
        from ...services.memory.sqlite_memory_backend import SQLiteMemoryBackend as _SQLiteMemoryBackend  # type: ignore
        AgentMemoryInterfaceImpl = _AgentMemoryInterface  # type: ignore
        SQLiteMemoryBackendImpl = _SQLiteMemoryBackend  # type: ignore
    except ImportError:
        # Fallback - create mock implementations
        class AgentMemoryInterfaceImpl:  # type: ignore
            def __init__(self, agent_id: str, mcp_base_url: str) -> None:
                pass
            async def __aenter__(self) -> Any:
                return self
            async def __aexit__(self, *args: Any) -> None:
                pass
            async def remember_long_term(self, content: str, memory_type: str, tags: List[str], importance: float) -> str:
                return "mock-memory-id"
            async def recall_memories(self, limit: int) -> List[Dict[str, Any]]:
                return []
        
        class SQLiteMemoryBackendImpl:  # type: ignore
            def __init__(self, db_path: str) -> None:
                pass
            async def initialize(self) -> None:
                pass
            async def store_memory(self, agent_id: str, content: str, memory_type: str, 
                                   task_id: Optional[str], importance_score: float, 
                                   metadata: Dict[str, Any]) -> str:
                return "mock-memory-id"
            async def get_memories(self, agent_id: str, memory_type: Optional[str] = None, 
                                   task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
                return []
            async def get_stats(self) -> Dict[str, Any]:
                return {"total_memories": 0, "memory_types": {}}

from models import (
    AgentEvent, EventType, EventPriority, EventFilter,
    EventReplayRequest, EventStorageInfo, MemoryIntegrationStatus
)
from subscriptions import get_subscription_manager

logger = logging.getLogger(__name__)


def health_check() -> Dict[str, str]:
    """Perform health check."""
    # Add actual health checks here
    return {"status": "healthy", "service": "event-router"}


def validate_input(data: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """Validate incoming request data.

    Args:
        data: Optional dictionary containing request data to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Raises:
        None - all exceptions are caught and returned as validation errors
    """
    try:
        # Basic validation
        if not data:
            return False, "Request data is required"

        # Check if data key exists for proper request structure
        if "data" not in data and not isinstance(data, dict):
            return False, "Invalid request format"

        # Add more validation logic as needed
        return True, None
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False, str(e)


def process_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process the incoming request data.

    Args:
        data: Dictionary containing validated request data

    Returns:
        Dictionary containing processed result with metadata

    Raises:
        Exception: Re-raises any processing errors for proper error handling
    """
    try:
        # Add actual processing logic here
        result: Dict[str, Any] = {
            "processed": True,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # If data has an id field, include it
        if "id" in data:
            result["request_id"] = data["id"]

        # Implement actual business logic based on recipe

        return result
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise


# Async versions for potential FastAPI compatibility
async def async_health_check() -> Dict[str, str]:
    """Async version of health check."""
    return health_check()


async def async_validate_input(data: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """Async version of validation."""
    return validate_input(data)


async def async_process_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Async version of process request."""
    return process_request(data)


# ========== Memory Event Storage ==========

class MemoryEventStorage:
    """Handles event persistence using the memory system."""

    def __init__(
        self,
        memory_backend_url: Optional[str] = None,
        sqlite_db_path: str = ".claude/data/events.db"
    ):
        self.memory_backend_url = memory_backend_url or "http://localhost:8000"
        self.sqlite_db_path = sqlite_db_path
        self.sqlite_backend: Optional[SQLiteMemoryBackend] = None
        self.memory_interface: Optional[AgentMemoryInterface] = None
        self._event_cache: List[AgentEvent] = []

    async def initialize(self) -> None:
        """Initialize the storage backend."""
        try:
            # Initialize SQLite backend
            self.sqlite_backend = SQLiteMemoryBackendImpl(self.sqlite_db_path)  # type: ignore
            if hasattr(self.sqlite_backend, 'initialize'):
                await self.sqlite_backend.initialize()

            # Initialize memory interface for high-priority events
            self.memory_interface = AgentMemoryInterfaceImpl(  # type: ignore
                agent_id="event_router_service",
                mcp_base_url=self.memory_backend_url
            )

            logger.info("✅ Memory event storage initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize memory storage: {e}")
            raise

    async def store_event(self, event: AgentEvent) -> Dict[str, Any]:
        """Store an event in the memory system."""
        try:
            result = {
                "event_id": event.id,
                "stored_in_memory": False,
                "stored_in_sqlite": False,
                "memory_id": None
            }

            # Always store in SQLite
            if self.sqlite_backend:
                # Convert event to dict with ISO format datetime
                event_dict = event.dict()
                # Convert datetime to ISO format string
                if isinstance(event_dict.get('timestamp'), datetime):
                    event_dict['timestamp'] = event_dict['timestamp'].isoformat()
                
                memory_id = await self.sqlite_backend.store_memory(
                    agent_id=event.agent_id,
                    content=json.dumps(event_dict),
                    memory_type=f"event_{event.event_type}",
                    task_id=event.task_id,
                    importance_score=self._get_importance_score(event.priority),
                    metadata={
                        "event_type": event.event_type,
                        "priority": event.priority,
                        "tags": event.tags,
                        "session_id": event.session_id,
                        "project_id": event.project_id
                    }
                )
                result["stored_in_sqlite"] = True
                result["memory_id"] = memory_id

            # Store high-priority events in memory system
            if (event.priority in [EventPriority.HIGH, EventPriority.CRITICAL]
                and self.memory_interface):
                try:
                    async with self.memory_interface as mem:
                        mem_id = await mem.remember_long_term(
                            content=f"Event: {event.event_type} from {event.agent_id}",
                            memory_type="event",
                            tags=event.tags + [event.event_type, event.priority],
                            importance=self._get_importance_score(event.priority)
                        )
                        result["stored_in_memory"] = True
                        result["memory_id"] = mem_id
                except Exception as e:
                    logger.warning(f"Failed to store in memory system: {e}")

            # Update event with storage info
            event.stored_in_memory = result["stored_in_memory"] or result["stored_in_sqlite"]
            event.memory_id = result["memory_id"]

            # Cache for quick access
            self._event_cache.append(event)
            if len(self._event_cache) > 1000:  # Limit cache size
                self._event_cache = self._event_cache[-500:]

            return result

        except Exception as e:
            logger.error(f"❌ Error storing event {event.id}: {e}")
            raise

    async def get_events(self, event_filter: EventFilter) -> List[AgentEvent]:
        """Retrieve events based on filter criteria."""
        try:
            if not self.sqlite_backend:
                return []

            events = []

            # Build query parameters
            memory_type = None
            if event_filter.event_types:
                # Use first event type for now - could be enhanced for multiple types
                memory_type = f"event_{event_filter.event_types[0]}"

            # Get memories from SQLite
            memories = await self.sqlite_backend.get_memories(
                agent_id=event_filter.agent_ids[0] if event_filter.agent_ids else "",
                memory_type=memory_type,
                task_id=event_filter.task_ids[0] if event_filter.task_ids else None,
                limit=event_filter.limit
            )

            for memory in memories:
                try:
                    event_data = json.loads(memory["content"])
                    event = AgentEvent(**event_data)

                    # Apply additional filtering
                    if self._matches_filter(event, event_filter):
                        events.append(event)

                except Exception as e:
                    logger.warning(f"Failed to parse event from memory: {e}")

            return events[:event_filter.limit]

        except Exception as e:
            logger.error(f"❌ Error retrieving events: {e}")
            return []

    async def get_events_by_session(self, session_id: str) -> List[AgentEvent]:
        """Get all events for a specific session."""
        event_filter = EventFilter(
            limit=1000,  # High limit for session recovery
            event_types=None,
            agent_ids=None,
            task_ids=None,
            project_ids=None,
            priority=None,
            tags=None,
            start_time=None,
            end_time=None,
            offset=0
        )

        all_events = await self.get_events(event_filter)
        return [e for e in all_events if e.session_id == session_id]

    async def get_storage_info(self) -> EventStorageInfo:
        """Get information about event storage."""
        try:
            if not self.sqlite_backend:
                return EventStorageInfo(
                    total_events=0,
                    events_by_type={},
                    oldest_event=None,
                    newest_event=None,
                    storage_size_mb=None
                )

            stats = await self.sqlite_backend.get_stats()

            # Parse event types from memory types
            events_by_type = {}
            for mem_type, count in stats.get("memory_types", {}).items():
                if mem_type.startswith("event_"):
                    event_type = mem_type.replace("event_", "")
                    events_by_type[event_type] = count

            return EventStorageInfo(
                total_events=stats.get("total_memories", 0),
                events_by_type=events_by_type,
                oldest_event=None,
                newest_event=None,
                storage_size_mb=None  # Could calculate if needed
            )

        except Exception as e:
            logger.error(f"❌ Error getting storage info: {e}")
            return EventStorageInfo(
                total_events=0,
                events_by_type={},
                oldest_event=None,
                newest_event=None,
                storage_size_mb=None
            )

    async def get_integration_status(self) -> MemoryIntegrationStatus:
        """Get memory system integration status."""
        try:
            connected = self.sqlite_backend is not None
            backend_type = "sqlite"

            # Try to get a simple status from memory system
            try:
                if self.memory_interface:
                    async with self.memory_interface as mem:
                        await mem.recall_memories(limit=1)
                    backend_type = "sqlite+memory"
            except Exception:
                pass

            return MemoryIntegrationStatus(
                connected=connected,
                backend_type=backend_type,
                last_sync=datetime.utcnow() if connected else None,
                pending_events=0,
                failed_events=0
            )

        except Exception as e:
            logger.error(f"❌ Error getting integration status: {e}")
            return MemoryIntegrationStatus(
                connected=False,
                backend_type="error",
                last_sync=None,
                pending_events=0,
                failed_events=0
            )

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of storage system."""
        try:
            status = {
                "status": "healthy",
                "sqlite_backend": self.sqlite_backend is not None,
                "memory_interface": self.memory_interface is not None,
                "cache_size": len(self._event_cache)
            }

            # Test SQLite connection
            if self.sqlite_backend:
                try:
                    stats = await self.sqlite_backend.get_stats()
                    status["sqlite_events"] = stats.get("total_memories", 0)
                except Exception as e:
                    status["status"] = "degraded"
                    status["sqlite_error"] = str(e)

            return status

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _get_importance_score(self, priority: EventPriority) -> float:
        """Convert priority to importance score."""
        priority_scores = {
            EventPriority.LOW: 0.3,
            EventPriority.NORMAL: 0.5,
            EventPriority.HIGH: 0.8,
            EventPriority.CRITICAL: 1.0
        }
        return priority_scores.get(priority, 0.5)

    def _matches_filter(self, event: AgentEvent, event_filter: EventFilter) -> bool:
        """Check if event matches filter criteria."""
        try:
            # Event type filter
            if event_filter.event_types and event.event_type not in event_filter.event_types:
                return False

            # Agent ID filter
            if event_filter.agent_ids and event.agent_id not in event_filter.agent_ids:
                return False

            # Task ID filter
            if event_filter.task_ids and event.task_id not in event_filter.task_ids:
                return False

            # Project ID filter
            if event_filter.project_ids and event.project_id not in event_filter.project_ids:
                return False

            # Priority filter
            if event_filter.priority and event.priority != event_filter.priority:
                return False

            # Tags filter (AND logic)
            if event_filter.tags:
                if not all(tag in event.tags for tag in event_filter.tags):
                    return False

            # Time range filter
            if event_filter.start_time and event.timestamp < event_filter.start_time:
                return False

            if event_filter.end_time and event.timestamp > event_filter.end_time:
                return False

            return True

        except Exception as e:
            logger.warning(f"Error applying filter: {e}")
            return False


# ========== Event Handler ==========

class EventHandler:
    """Main event handler with routing and processing logic."""

    def __init__(
        self,
        storage: MemoryEventStorage,
        filter_engine: "EventFilterEngine"
    ):
        self.storage = storage
        self.filter_engine = filter_engine
        self._routing_rules: Dict[str, List[str]] = {}
        self.subscription_manager = get_subscription_manager()

    async def initialize(self) -> None:
        """Initialize the event handler."""
        try:
            # Set up default routing rules
            self._routing_rules = {
                EventType.AGENT_INITIALIZED: ["memory", "sqlite"],
                EventType.TASK_STARTED: ["memory", "sqlite"],
                EventType.TASK_COMPLETED: ["memory", "sqlite"],
                EventType.KNOWLEDGE_LEARNED: ["memory", "sqlite"],
                EventType.COLLABORATION_MESSAGE: ["sqlite"],
                EventType.ERROR_OCCURRED: ["memory", "sqlite"],
                EventType.SYSTEM_HEALTH_CHECK: ["sqlite"]
            }

            logger.info("✅ Event handler initialized with routing rules")

        except Exception as e:
            logger.error(f"❌ Failed to initialize event handler: {e}")
            raise

    async def handle_event(self, event: AgentEvent) -> Dict[str, Any]:
        """Process and route an event."""
        try:
            logger.info(f"📥 Handling event: {event.event_type} from {event.agent_id}")

            # Apply routing rules
            routing_targets = self._routing_rules.get(event.event_type, ["sqlite"])

            # Adjust priority based on event type
            if event.event_type in [EventType.ERROR_OCCURRED, EventType.TASK_FAILED]:
                event.priority = EventPriority.HIGH
            elif event.event_type in [EventType.AGENT_INITIALIZED, EventType.KNOWLEDGE_LEARNED]:
                event.priority = EventPriority.NORMAL

            # Store the event
            storage_result = await self.storage.store_event(event)

            # Add processing metadata
            result = {
                **storage_result,
                "routing_targets": routing_targets,
                "processed_at": datetime.utcnow().isoformat()
            }

            # Route to subscribers
            await self._route_to_subscribers(event)
            
            logger.info(f"✅ Event {event.id} processed successfully")
            return result

        except Exception as e:
            logger.error(f"❌ Error handling event {event.id}: {e}")
            raise
    
    async def _route_to_subscribers(self, event: AgentEvent) -> None:
        """Route event to all subscribed agents."""
        try:
            # Get subscribers for this event type
            subscribers = self.subscription_manager.get_subscribers(event.event_type)
            
            if not subscribers:
                logger.debug(f"No subscribers for event type: {event.event_type}")
                return
            
            logger.info(f"📨 Routing {event.event_type} to {len(subscribers)} subscribers")
            
            # Process subscriptions by priority
            for subscription in subscribers:
                try:
                    # Apply subscription filter if present
                    if subscription.filter:
                        if not self._matches_filter(event, subscription.filter):
                            continue
                    
                    # In production, this would invoke the agent
                    # For now, we'll log the routing
                    logger.info(
                        f"  → Routing to {subscription.agent_id}.{subscription.handler} "
                        f"(priority: {subscription.priority.value})"
                    )
                    
                    # TODO: Implement actual agent invocation
                    # This would typically:
                    # 1. Start agent container if not running
                    # 2. Send event to agent's handler function
                    # 3. Track agent response
                    
                except Exception as e:
                    logger.error(
                        f"Failed to route to {subscription.agent_id}.{subscription.handler}: {e}"
                    )
                    # Continue routing to other subscribers
                    
        except Exception as e:
            logger.error(f"Error in event routing: {e}")
            # Don't fail the entire event processing if routing fails
    
    def _matches_filter(self, event: AgentEvent, filter_dict: Dict[str, Any]) -> bool:
        """Check if event matches subscription filter."""
        for key, value in filter_dict.items():
            event_value = event.data.get(key) if hasattr(event, 'data') else None
            if event_value != value:
                return False
        return True


# ========== Event Filter Engine ==========

class EventFilterEngine:
    """Advanced event filtering and querying engine."""

    def __init__(self):
        self.filter_cache: Dict[str, List[AgentEvent]] = {}
        self.cache_ttl = timedelta(minutes=5)

    async def filter_events(
        self,
        storage: MemoryEventStorage,
        event_filter: EventFilter
    ) -> List[AgentEvent]:
        """Apply complex filtering to events."""
        try:
            # Create cache key
            cache_key = self._get_cache_key(event_filter)

            # Check cache first
            if cache_key in self.filter_cache:
                logger.debug(f"🎯 Using cached filter results for {cache_key}")
                return self.filter_cache[cache_key]

            # Get events from storage
            events = await storage.get_events(event_filter)

            # Apply additional filtering logic
            filtered_events = []
            for event in events:
                if self._apply_advanced_filters(event, event_filter):
                    filtered_events.append(event)

            # Apply sorting and pagination
            filtered_events = self._sort_and_paginate(filtered_events, event_filter)

            # Cache results
            self.filter_cache[cache_key] = filtered_events

            logger.info(f"🔍 Filtered {len(events)} events to {len(filtered_events)} results")
            return filtered_events

        except Exception as e:
            logger.error(f"❌ Error filtering events: {e}")
            return []

    def _get_cache_key(self, event_filter: EventFilter) -> str:
        """Generate cache key for filter."""
        return f"filter_{hash(str(event_filter.dict()))}"

    def _apply_advanced_filters(self, event: AgentEvent, event_filter: EventFilter) -> bool:
        """Apply advanced filtering logic."""
        # Could add more sophisticated filtering here
        return True

    def _sort_and_paginate(self, events: List[AgentEvent], event_filter: EventFilter) -> List[AgentEvent]:
        """Sort events and apply pagination."""
        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        start_idx = event_filter.offset
        end_idx = start_idx + event_filter.limit

        return events[start_idx:end_idx]


# ========== Event Replay Engine ==========

class EventReplayEngine:
    """Engine for replaying events during crash recovery."""

    def __init__(self, storage: MemoryEventStorage):
        self.storage = storage

    async def replay_events(self, replay_request: EventReplayRequest) -> Dict[str, Any]:
        """Replay events for crash recovery."""
        try:
            logger.info(f"🔄 Starting event replay for session {replay_request.session_id}")

            # Get events for the session
            session_events = await self.storage.get_events_by_session(
                replay_request.session_id
            )

            # Filter by time range if specified
            filtered_events = []
            for event in session_events:
                if self._should_replay_event(event, replay_request):
                    filtered_events.append(event)

            # Sort events by timestamp
            filtered_events.sort(key=lambda e: e.timestamp)

            # Generate replay summary
            summary = self._generate_replay_summary(filtered_events)

            result = {
                "event_count": len(filtered_events),
                "summary": summary,
                "replayed_events": [e.dict() for e in filtered_events]
            }

            logger.info(f"✅ Replayed {len(filtered_events)} events for session {replay_request.session_id}")
            return result

        except Exception as e:
            logger.error(f"❌ Error replaying events: {e}")
            raise

    def _should_replay_event(self, event: AgentEvent, replay_request: EventReplayRequest) -> bool:
        """Determine if event should be included in replay."""
        # Agent ID filter
        if replay_request.agent_id and event.agent_id != replay_request.agent_id:
            return False

        # Time range filters
        if replay_request.from_timestamp and event.timestamp < replay_request.from_timestamp:
            return False

        if replay_request.to_timestamp and event.timestamp > replay_request.to_timestamp:
            return False

        # Event type filter
        if replay_request.event_types and event.event_type not in replay_request.event_types:
            return False

        return True

    def _generate_replay_summary(self, events: List[AgentEvent]) -> Dict[str, Any]:
        """Generate summary of replayed events."""
        summary = {
            "total_events": len(events),
            "event_types": {},
            "agents": set(),
            "tasks": set(),
            "time_range": {}
        }

        for event in events:
            # Count by event type
            event_type = event.event_type
            summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1

            # Track agents and tasks
            summary["agents"].add(event.agent_id)
            if event.task_id:
                summary["tasks"].add(event.task_id)

        # Convert sets to lists for JSON serialization
        summary["agents"] = list(summary["agents"])
        summary["tasks"] = list(summary["tasks"])

        # Time range
        if events:
            summary["time_range"] = {
                "start": events[0].timestamp.isoformat(),
                "end": events[-1].timestamp.isoformat()
            }

        return summary
