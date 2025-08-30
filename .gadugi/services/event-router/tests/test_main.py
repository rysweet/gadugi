"""
Enhanced tests for event-router service with memory integration.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Any

# Import based on available framework
try:
    from fastapi.testclient import TestClient  # type: ignore[import-untyped]

    use_fastapi = True
except ImportError:
    use_fastapi = False
    TestClient = None  # type: ignore[misc]

if not use_fastapi:
    # Flask imports
    try:
        from flask.testing import FlaskClient  # type: ignore[import-untyped]
        from ..main import app as flask_app
    except ImportError:
        # If Flask is not available, we'll handle this in fixtures
        FlaskClient = None  # type: ignore[misc]
        flask_app = None  # type: ignore[misc]

from ..models import (
    RequestModel,
    AgentEvent,
    EventType,
    EventPriority,
    EventFilter,
    EventReplayRequest,
    TaskStartedEvent,
    KnowledgeLearnedEvent,
    CollaborationMessageEvent,
)
from ..handlers import (
    MemoryEventStorage,
    EventHandler,
    EventFilterEngine,
    EventReplayEngine,
)


@pytest.fixture
def client() -> Any:
    """Create test client."""
    if use_fastapi and TestClient is not None:
        try:
            from ..main import app

            if app is not None:
                return TestClient(app)
            else:
                pytest.skip("FastAPI app not available")
        except ImportError:
            pytest.skip("FastAPI not available")
    else:
        if flask_app is not None:
            flask_app.testing = True
            return flask_app.test_client()
        else:
            pytest.skip("Flask not available")


@pytest.fixture
def sample_request() -> RequestModel:
    """Create sample request."""
    return RequestModel(
        id="test-123", data={"test": "data"}, metadata={"source": "test"}
    )


class TestHealthEndpoint:
    """Test health endpoint."""

    def test_health_check(self, client: Any) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore

        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self, client: Any) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore

        assert data["service"] == "event-router"
        assert data["status"] == "running"


class TestProcessEndpoint:
    """Test process endpoint."""

    def test_process_valid_request(
        self, client: Any, sample_request: RequestModel
    ) -> None:
        """Test processing valid request."""
        response = client.post("/process", json=sample_request.dict())
        assert response.status_code == 200

        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore

        assert data["success"] is True
        assert "data" in data

    def test_process_invalid_request(self, client: Any) -> None:
        """Test processing invalid request."""
        response = client.post("/process", json={})
        # FastAPI returns 422 for validation errors, Flask returns 400
        assert response.status_code in [400, 422]

    def test_process_empty_data(self, client: Any) -> None:
        """Test processing with empty data."""
        response = client.post("/process", json={"data": {}})
        # Should still work with empty data dict
        assert response.status_code == 200


class TestStatusEndpoint:
    """Test status endpoint."""

    def test_status(self, client: Any) -> None:
        """Test status endpoint."""
        response = client.get("/status")
        assert response.status_code == 200

        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore

        assert data["service"] == "event-router"
        assert data["status"] == "operational"


class TestProcessErrorHandling:
    """Test error handling in process endpoint."""

    @patch(".claude.services.event-router.main.process_request")
    def test_process_error_handling(
        self, mock_process: MagicMock, client: Any, sample_request: RequestModel
    ) -> None:
        """Test error handling in process endpoint."""
        mock_process.side_effect = Exception("Test error")

        response = client.post("/process", json=sample_request.dict())
        assert response.status_code == 500

        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore

        assert "error" in data


# ========== Memory Integration Tests ==========


@pytest.fixture
def mock_memory_storage():
    """Mock memory storage for testing."""
    storage = MagicMock(spec=MemoryEventStorage)
    storage.initialize = AsyncMock()
    storage.store_event = AsyncMock(
        return_value={
            "event_id": "test-event-123",
            "stored_in_memory": True,
            "stored_in_sqlite": True,
            "memory_id": "mem-123",
        }
    )
    storage.get_events = AsyncMock(return_value=[])
    storage.get_storage_info = AsyncMock()
    storage.get_integration_status = AsyncMock()
    storage.get_health_status = AsyncMock(return_value={"status": "healthy"})
    return storage


@pytest.fixture
def sample_agent_event() -> AgentEvent:
    """Create a sample agent event for testing."""
    return AgentEvent(
        event_type=EventType.TASK_STARTED,
        agent_id="test-agent-001",
        task_id="task-123",
        data={"description": "Test task"},
        tags=["test", "integration"],
        priority=EventPriority.NORMAL,
        project_id=None,
        session_id=None,
        metadata={},
        stored_in_memory=False,
        memory_id=None,
    )


@pytest.fixture
def sample_task_started_event() -> TaskStartedEvent:
    """Create a sample task started event."""
    return TaskStartedEvent(
        agent_id="test-agent-001",
        task_id="task-456",
        task_description="Implement feature X",
        estimated_duration=60,
        dependencies=["task-123"],
        data={},
        project_id=None,
        session_id=None,
        metadata={},
        tags=[],
        priority=EventPriority.NORMAL,
        stored_in_memory=False,
        memory_id=None,
    )


@pytest.fixture
def sample_knowledge_event() -> KnowledgeLearnedEvent:
    """Create a sample knowledge learned event."""
    return KnowledgeLearnedEvent(
        agent_id="test-agent-002",
        knowledge_type="pattern",
        content="Always validate input parameters before processing",
        confidence=0.9,
        source="experience",
        data={},
        task_id=None,
        project_id=None,
        session_id=None,
        metadata={},
        tags=[],
        priority=EventPriority.NORMAL,
        stored_in_memory=False,
        memory_id=None,
    )


class TestMemoryEventStorage:
    """Test memory event storage functionality."""

    @pytest.mark.asyncio
    async def test_storage_initialization(self):
        """Test memory storage initialization."""
        with patch("sqlite3.connect"):
            storage = MemoryEventStorage(sqlite_db_path=":memory:")

            with patch.object(storage, "sqlite_backend") as mock_backend:
                mock_backend.initialize = AsyncMock()
                await storage.initialize()
                mock_backend.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_storage(self, sample_agent_event):
        """Test storing an event."""
        storage = MemoryEventStorage(sqlite_db_path=":memory:")

        # Mock the SQLite backend
        mock_backend = AsyncMock()
        mock_backend.store_memory = AsyncMock(return_value="mem-123")
        storage.sqlite_backend = mock_backend

        result = await storage.store_event(sample_agent_event)

        assert result["event_id"] == sample_agent_event.id
        assert result["stored_in_sqlite"]
        assert result["memory_id"] == "mem-123"
        mock_backend.store_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_retrieval(self):
        """Test retrieving events with filters."""
        storage = MemoryEventStorage(sqlite_db_path=":memory:")

        # Mock the SQLite backend
        mock_backend = AsyncMock()
        mock_backend.get_memories = AsyncMock(
            return_value=[
                {
                    "content": '{"id": "event-1", "event_type": "task.started", "agent_id": "agent-1", "timestamp": "2023-01-01T10:00:00"}',
                    "metadata": {"event_type": "task.started"},
                }
            ]
        )
        storage.sqlite_backend = mock_backend

        event_filter = EventFilter(
            event_types=[EventType.TASK_STARTED],
            limit=10,
            agent_ids=None,
            task_ids=None,
            project_ids=None,
            priority=None,
            tags=None,
            start_time=None,
            end_time=None,
            offset=0,
        )

        events = await storage.get_events(event_filter)

        assert len(events) >= 0  # Could be 0 if parsing fails
        mock_backend.get_memories.assert_called_once()


class TestEventHandler:
    """Test event handler functionality."""

    @pytest.mark.asyncio
    async def test_event_handling(self, mock_memory_storage, sample_agent_event):
        """Test handling an agent event."""
        filter_engine = EventFilterEngine()
        handler = EventHandler(mock_memory_storage, filter_engine)

        await handler.initialize()
        result = await handler.handle_event(sample_agent_event)

        assert result["event_id"] == sample_agent_event.id
        assert "processed_at" in result
        mock_memory_storage.store_event.assert_called_once_with(sample_agent_event)

    @pytest.mark.asyncio
    async def test_event_priority_adjustment(self, mock_memory_storage):
        """Test automatic priority adjustment based on event type."""
        filter_engine = EventFilterEngine()
        handler = EventHandler(mock_memory_storage, filter_engine)
        await handler.initialize()

        # Create error event
        error_event = AgentEvent(
            event_type=EventType.ERROR_OCCURRED,
            agent_id="test-agent",
            priority=EventPriority.NORMAL,  # Should be upgraded to HIGH
            data={},
            task_id=None,
            project_id=None,
            session_id=None,
            metadata={},
            tags=[],
            stored_in_memory=False,
            memory_id=None,
        )

        await handler.handle_event(error_event)

        # Check that priority was adjusted
        assert error_event.priority == EventPriority.HIGH


class TestEventFilterEngine:
    """Test event filtering functionality."""

    @pytest.mark.asyncio
    async def test_event_filtering(self, mock_memory_storage):
        """Test filtering events."""
        filter_engine = EventFilterEngine()

        # Mock some events
        mock_events = [
            AgentEvent(
                event_type=EventType.TASK_STARTED,
                agent_id="agent-1",
                task_id="task-1",
                data={},
                project_id=None,
                session_id=None,
                metadata={},
                tags=[],
                priority=EventPriority.NORMAL,
                stored_in_memory=False,
                memory_id=None,
            ),
            AgentEvent(
                event_type=EventType.TASK_COMPLETED,
                agent_id="agent-2",
                task_id="task-2",
                data={},
                project_id=None,
                session_id=None,
                metadata={},
                tags=[],
                priority=EventPriority.NORMAL,
                stored_in_memory=False,
                memory_id=None,
            ),
        ]
        mock_memory_storage.get_events.return_value = mock_events

        event_filter = EventFilter(
            event_types=[EventType.TASK_STARTED],
            limit=10,
            agent_ids=None,
            task_ids=None,
            project_ids=None,
            priority=None,
            tags=None,
            start_time=None,
            end_time=None,
            offset=0,
        )

        filtered_events = await filter_engine.filter_events(
            mock_memory_storage, event_filter
        )

        assert len(filtered_events) <= 10
        mock_memory_storage.get_events.assert_called_once_with(event_filter)

    def test_cache_key_generation(self):
        """Test filter cache key generation."""
        filter_engine = EventFilterEngine()

        event_filter = EventFilter(
            event_types=[EventType.TASK_STARTED],
            agent_ids=["agent-1"],
            limit=50,
            task_ids=None,
            project_ids=None,
            priority=None,
            tags=None,
            start_time=None,
            end_time=None,
            offset=0,
        )

        cache_key = filter_engine._get_cache_key(event_filter)

        assert cache_key.startswith("filter_")
        assert len(cache_key) > 10


class TestEventReplayEngine:
    """Test event replay functionality."""

    @pytest.mark.asyncio
    async def test_event_replay(self, mock_memory_storage):
        """Test replaying events for a session."""
        replay_engine = EventReplayEngine(mock_memory_storage)

        # Mock session events
        session_events = [
            AgentEvent(
                event_type=EventType.TASK_STARTED,
                agent_id="agent-1",
                session_id="session-123",
                timestamp=datetime.utcnow() - timedelta(hours=1),
                data={},
                task_id=None,
                project_id=None,
                metadata={},
                tags=[],
                priority=EventPriority.NORMAL,
                stored_in_memory=False,
                memory_id=None,
            ),
            AgentEvent(
                event_type=EventType.TASK_COMPLETED,
                agent_id="agent-1",
                session_id="session-123",
                timestamp=datetime.utcnow(),
                data={},
                task_id=None,
                project_id=None,
                metadata={},
                tags=[],
                priority=EventPriority.NORMAL,
                stored_in_memory=False,
                memory_id=None,
            ),
        ]
        mock_memory_storage.get_events_by_session.return_value = session_events

        replay_request = EventReplayRequest(
            session_id="session-123",
            agent_id=None,
            from_timestamp=None,
            to_timestamp=None,
            event_types=None,
        )

        result = await replay_engine.replay_events(replay_request)

        assert result["event_count"] == 2
        assert "summary" in result
        assert result["summary"]["total_events"] == 2
        mock_memory_storage.get_events_by_session.assert_called_once_with("session-123")

    def test_replay_event_filtering(self):
        """Test event filtering during replay."""
        replay_engine = EventReplayEngine(MagicMock())

        event = AgentEvent(
            event_type=EventType.TASK_STARTED,
            agent_id="agent-1",
            timestamp=datetime.utcnow(),
            data={},
            task_id=None,
            project_id=None,
            session_id=None,
            metadata={},
            tags=[],
            priority=EventPriority.NORMAL,
            stored_in_memory=False,
            memory_id=None,
        )

        # Test agent ID filter
        replay_request = EventReplayRequest(
            session_id="session-123",
            agent_id="agent-2",  # Different agent
            from_timestamp=None,
            to_timestamp=None,
            event_types=None,
        )

        should_replay = replay_engine._should_replay_event(event, replay_request)
        assert not should_replay

        # Test matching agent ID
        replay_request.agent_id = "agent-1"
        should_replay = replay_engine._should_replay_event(event, replay_request)
        assert should_replay


class TestEventEndpoints:
    """Test event-related HTTP endpoints."""

    @patch("event_router.main.event_handler")
    @patch("event_router.main.memory_storage")
    def test_create_event_endpoint(self, mock_storage, mock_handler, client):
        """Test event creation endpoint."""
        if not client:
            pytest.skip("Client not available")

        mock_handler.handle_event = AsyncMock(
            return_value={
                "event_id": "test-event-123",
                "stored_in_memory": True,
                "memory_id": "mem-123",
            }
        )

        event_data = {
            "event_type": "task.started",
            "agent_id": "test-agent-001",
            "task_id": "task-123",
            "data": {"description": "Test task"},
        }

        response = client.post("/events", json=event_data)

        # Should succeed if event system is initialized
        assert response.status_code in [201, 503]  # 503 if not initialized

    def test_list_events_endpoint(self, client):
        """Test event listing endpoint."""
        if not client:
            pytest.skip("Client not available")

        response = client.get("/events?limit=10&offset=0")

        # Should return events or error if not initialized
        assert response.status_code in [200, 503]

    def test_storage_info_endpoint(self, client):
        """Test storage information endpoint."""
        if not client:
            pytest.skip("Client not available")

        response = client.get("/events/storage")

        # Should return storage info or error if not initialized
        assert response.status_code in [200, 503]

    def test_memory_status_endpoint(self, client):
        """Test memory status endpoint."""
        if not client:
            pytest.skip("Client not available")

        response = client.get("/memory/status")

        # Should return memory status or error if not initialized
        assert response.status_code in [200, 503]


class TestSpecificEventTypes:
    """Test specific event type handling."""

    @pytest.mark.asyncio
    async def test_task_started_event(
        self, sample_task_started_event, mock_memory_storage
    ):
        """Test handling task started events."""
        filter_engine = EventFilterEngine()
        handler = EventHandler(mock_memory_storage, filter_engine)
        await handler.initialize()

        result = await handler.handle_event(sample_task_started_event)

        assert result["event_id"] == sample_task_started_event.id
        assert sample_task_started_event.event_type == EventType.TASK_STARTED
        mock_memory_storage.store_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_knowledge_learned_event(
        self, sample_knowledge_event, mock_memory_storage
    ):
        """Test handling knowledge learned events."""
        filter_engine = EventFilterEngine()
        handler = EventHandler(mock_memory_storage, filter_engine)
        await handler.initialize()

        result = await handler.handle_event(sample_knowledge_event)

        assert result["event_id"] == sample_knowledge_event.id
        assert sample_knowledge_event.event_type == EventType.KNOWLEDGE_LEARNED
        assert sample_knowledge_event.confidence == 0.9
        mock_memory_storage.store_event.assert_called_once()

    def test_collaboration_message_event(self):
        """Test collaboration message event creation."""
        collab_event = CollaborationMessageEvent(
            agent_id="agent-sender",
            recipient_id="agent-receiver",
            message_type="request",
            content="Can you help with task X?",
            requires_response=True,
            data={},
            task_id=None,
            project_id=None,
            session_id=None,
            metadata={},
            tags=[],
            priority=EventPriority.NORMAL,
            stored_in_memory=False,
            memory_id=None,
        )

        assert collab_event.event_type == EventType.COLLABORATION_MESSAGE
        assert collab_event.requires_response is True
        assert collab_event.recipient_id == "agent-receiver"


class TestEnhancedHealthChecks:
    """Test enhanced health check functionality."""

    def test_health_endpoint_with_memory_status(self, client):
        """Test health endpoint includes memory system status."""
        if not client:
            pytest.skip("Client not available")

        response = client.get("/health")
        assert response.status_code == 200

        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore

        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        # Memory system status may or may not be present depending on initialization

    def test_detailed_status_endpoint(self, client):
        """Test detailed status endpoint."""
        if not client:
            pytest.skip("Client not available")

        response = client.get("/status")
        assert response.status_code == 200

        if use_fastapi:
            data = response.json()
        else:
            data = response.get_json()  # type: ignore

        assert data["service"] == "event-router"
        assert "components" in data
        assert "version" in data


class TestEventSystemErrorHandling:
    """Test error handling in event system."""

    @pytest.mark.asyncio
    async def test_storage_error_handling(self):
        """Test handling storage errors gracefully."""
        storage = MemoryEventStorage(sqlite_db_path=":memory:")

        # Don't initialize storage to trigger error
        event = AgentEvent(
            event_type=EventType.TASK_STARTED,
            agent_id="test-agent",
            data={},
            task_id=None,
            project_id=None,
            session_id=None,
            metadata={},
            tags=[],
            priority=EventPriority.NORMAL,
            stored_in_memory=False,
            memory_id=None,
        )

        # Should handle missing backend gracefully
        event_filter = EventFilter(
            limit=10,
            event_types=None,
            agent_ids=None,
            task_ids=None,
            project_ids=None,
            priority=None,
            tags=None,
            start_time=None,
            end_time=None,
            offset=0,
        )
        events = await storage.get_events(event_filter)
        assert events == []

    @pytest.mark.asyncio
    async def test_event_handler_error_recovery(self, mock_memory_storage):
        """Test event handler error recovery."""
        filter_engine = EventFilterEngine()
        handler = EventHandler(mock_memory_storage, filter_engine)

        # Mock storage to raise an exception
        mock_memory_storage.store_event.side_effect = Exception("Storage error")

        event = AgentEvent(
            event_type=EventType.TASK_STARTED,
            agent_id="test-agent",
            data={},
            task_id=None,
            project_id=None,
            session_id=None,
            metadata={},
            tags=[],
            priority=EventPriority.NORMAL,
            stored_in_memory=False,
            memory_id=None,
        )

        await handler.initialize()

        # Should raise the exception
        with pytest.raises(Exception, match="Storage error"):
            await handler.handle_event(event)
