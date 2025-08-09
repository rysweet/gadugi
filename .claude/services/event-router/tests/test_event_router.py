"""
Comprehensive tests for Event Router.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ..event_router import (
    Event,
    EventPriority,
    EventRouter,
    EventType,
    ProcessManager,
    Subscription,
    AgentProcess,
    DeadLetterQueue
)


@pytest.fixture
def event_router():
    """Create event router instance."""
    return EventRouter()


@pytest.fixture
def process_manager():
    """Create process manager instance."""
    return ProcessManager()


@pytest.fixture
def sample_event():
    """Create sample event."""
    return Event(
        id="test-001",
        type=EventType.CUSTOM,
        topic="test.topic",
        source="test-source",
        data={"message": "test"}
    )


@pytest.fixture
async def dlq(tmp_path):
    """Create DLQ with temp storage."""
    return DeadLetterQueue(storage_path=tmp_path / "dlq")


class TestEvent:
    """Test Event class."""
    
    def test_event_creation(self):
        """Test creating an event."""
        event = Event(
            id="test-001",
            type=EventType.AGENT_STARTED,
            topic="agent.start",
            source="test",
            data={"agent": "test"}
        )
        
        assert event.id == "test-001"
        assert event.type == EventType.AGENT_STARTED
        assert event.priority == EventPriority.NORMAL
        assert event.namespace == "default"
        
    def test_event_to_dict(self, sample_event):
        """Test converting event to dict."""
        event_dict = sample_event.to_dict()
        
        assert event_dict["id"] == "test-001"
        assert event_dict["type"] == EventType.CUSTOM.value
        assert event_dict["topic"] == "test.topic"
        assert "timestamp" in event_dict
        
    def test_event_from_dict(self):
        """Test creating event from dict."""
        data = {
            "id": "test-002",
            "type": "agent.started",
            "topic": "test.topic",
            "source": "test",
            "data": {"test": True},
            "timestamp": datetime.utcnow().isoformat(),
            "priority": 1
        }
        
        event = Event.from_dict(data)
        
        assert event.id == "test-002"
        assert event.type == EventType.AGENT_STARTED
        assert event.priority == EventPriority.HIGH


class TestSubscription:
    """Test Subscription class."""
    
    def test_exact_match(self):
        """Test exact topic matching."""
        sub = Subscription(
            subscriber_id="test",
            topic_pattern="agent.started"
        )
        
        assert sub.matches("agent.started", "default") is True
        assert sub.matches("agent.stopped", "default") is False
        
    def test_wildcard_match(self):
        """Test wildcard topic matching."""
        sub = Subscription(
            subscriber_id="test",
            topic_pattern="agent.*"
        )
        
        assert sub.matches("agent.started", "default") is True
        assert sub.matches("agent.stopped", "default") is True
        assert sub.matches("task.created", "default") is False
        
    def test_namespace_match(self):
        """Test namespace filtering."""
        sub = Subscription(
            subscriber_id="test",
            topic_pattern="*",
            namespace="production"
        )
        
        assert sub.matches("any.topic", "production") is True
        assert sub.matches("any.topic", "development") is False


class TestProcessManager:
    """Test ProcessManager class."""
    
    @pytest.mark.asyncio
    async def test_spawn_agent(self, process_manager):
        """Test spawning an agent process."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.returncode = None
            mock_subprocess.return_value = mock_process
            
            agent = await process_manager.spawn_agent(
                "test-agent",
                ["python", "-m", "test"]
            )
            
            assert agent.agent_id == "test-agent"
            assert agent.process == mock_process
            assert "test-agent" in process_manager.processes
            
    @pytest.mark.asyncio
    async def test_stop_agent(self, process_manager):
        """Test stopping an agent."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.pid = 12345
            mock_process.returncode = None
            mock_subprocess.return_value = mock_process
            
            # Spawn agent
            await process_manager.spawn_agent("test-agent", ["python"])
            
            # Stop agent
            result = await process_manager.stop_agent("test-agent")
            
            assert result is True
            mock_process.terminate.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_restart_agent(self, process_manager):
        """Test restarting an agent."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.pid = 12345
            mock_process.returncode = None
            mock_subprocess.return_value = mock_process
            
            # Spawn agent
            await process_manager.spawn_agent("test-agent", ["python"])
            
            # Restart agent
            result = await process_manager.restart_agent("test-agent")
            
            assert result is True
            assert mock_subprocess.call_count == 2  # Initial + restart
            
    def test_update_heartbeat(self, process_manager):
        """Test updating agent heartbeat."""
        agent = AgentProcess(
            agent_id="test-agent",
            process=MagicMock(),
            command=["python"]
        )
        
        process_manager.processes["test-agent"] = agent
        
        old_heartbeat = agent.last_heartbeat
        process_manager.update_heartbeat("test-agent")
        
        assert agent.last_heartbeat > old_heartbeat
        
    def test_agent_health_check(self):
        """Test agent health checking."""
        agent = AgentProcess(
            agent_id="test-agent",
            process=MagicMock(returncode=None),
            command=["python"]
        )
        
        # Fresh agent should be healthy
        assert agent.is_alive is True
        assert agent.is_healthy is True
        
        # Old heartbeat should be unhealthy
        agent.last_heartbeat = datetime.utcnow() - timedelta(minutes=5)
        assert agent.is_healthy is False


class TestDeadLetterQueue:
    """Test DeadLetterQueue class."""
    
    @pytest.mark.asyncio
    async def test_add_to_dlq(self, dlq, sample_event):
        """Test adding event to DLQ."""
        await dlq.add(sample_event, "Test error")
        
        # Check in-memory storage
        assert len(dlq.failed_events) == 1
        
        # Check file storage
        file_path = dlq.storage_path / f"{sample_event.id}.json"
        assert file_path.exists()
        
        with open(file_path) as f:
            data = json.load(f)
            assert data["event"]["id"] == sample_event.id
            assert data["error"] == "Test error"
            
    @pytest.mark.asyncio
    async def test_get_all_from_dlq(self, dlq, sample_event):
        """Test getting all events from DLQ."""
        await dlq.add(sample_event, "Error 1")
        
        event2 = Event(
            id="test-002",
            type=EventType.CUSTOM,
            topic="test",
            source="test",
            data={}
        )
        await dlq.add(event2, "Error 2")
        
        events = await dlq.get_all()
        
        assert len(events) == 2
        assert any(e["event"]["id"] == "test-001" for e in events)
        assert any(e["event"]["id"] == "test-002" for e in events)
        
    @pytest.mark.asyncio
    async def test_retry_from_dlq(self, dlq, sample_event):
        """Test retrying event from DLQ."""
        await dlq.add(sample_event, "Test error")
        
        # Retry event
        retried_event = await dlq.retry_event(sample_event.id)
        
        assert retried_event.id == sample_event.id
        
        # Check file was removed
        file_path = dlq.storage_path / f"{sample_event.id}.json"
        assert not file_path.exists()


class TestEventRouter:
    """Test EventRouter class."""
    
    @pytest.mark.asyncio
    async def test_start_stop(self, event_router):
        """Test starting and stopping router."""
        await event_router.start()
        assert event_router.running is True
        
        await event_router.stop()
        assert event_router.running is False
        
    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, event_router):
        """Test subscription management."""
        # Subscribe
        queue = event_router.subscribe(
            "test-subscriber",
            "test.*"
        )
        
        assert queue is not None
        assert "test-subscriber" in event_router.subscriptions
        
        # Unsubscribe
        event_router.unsubscribe("test-subscriber")
        assert "test-subscriber" not in event_router.subscriptions
        
    @pytest.mark.asyncio
    async def test_publish_event(self, event_router, sample_event):
        """Test publishing an event."""
        await event_router.start()
        
        # Subscribe to events
        queue = event_router.subscribe("test", "test.*")
        
        # Publish event
        await event_router.publish(sample_event)
        
        # Give router time to process
        await asyncio.sleep(0.1)
        
        # Check event was delivered
        assert not queue.empty()
        delivered_event = await queue.get()
        assert delivered_event.id == sample_event.id
        
        await event_router.stop()
        
    @pytest.mark.asyncio
    async def test_event_routing_with_namespace(self, event_router):
        """Test event routing with namespace filtering."""
        await event_router.start()
        
        # Subscribe to production namespace only
        prod_queue = event_router.subscribe(
            "prod-subscriber",
            "*",
            namespace="production"
        )
        
        # Subscribe to all namespaces
        all_queue = event_router.subscribe(
            "all-subscriber",
            "*"
        )
        
        # Publish production event
        prod_event = Event(
            id="prod-001",
            type=EventType.CUSTOM,
            topic="test",
            source="test",
            data={},
            namespace="production"
        )
        
        await event_router.publish(prod_event)
        
        # Publish dev event
        dev_event = Event(
            id="dev-001",
            type=EventType.CUSTOM,
            topic="test",
            source="test",
            data={},
            namespace="development"
        )
        
        await event_router.publish(dev_event)
        
        # Give router time to process
        await asyncio.sleep(0.1)
        
        # Check production subscriber only got production event
        assert not prod_queue.empty()
        event = await prod_queue.get()
        assert event.id == "prod-001"
        assert prod_queue.empty()
        
        # Check all subscriber got both events
        assert not all_queue.empty()
        event1 = await all_queue.get()
        event2 = await all_queue.get()
        
        event_ids = {event1.id, event2.id}
        assert "prod-001" in event_ids
        assert "dev-001" in event_ids
        
        await event_router.stop()
        
    @pytest.mark.asyncio
    async def test_priority_queue_ordering(self, event_router):
        """Test that events are processed by priority."""
        await event_router.start()
        
        queue = event_router.subscribe("test", "*")
        
        # Publish events in reverse priority order
        low_event = Event(
            id="low",
            type=EventType.CUSTOM,
            topic="test",
            source="test",
            data={},
            priority=EventPriority.LOW
        )
        
        high_event = Event(
            id="high",
            type=EventType.CUSTOM,
            topic="test",
            source="test",
            data={},
            priority=EventPriority.HIGH
        )
        
        critical_event = Event(
            id="critical",
            type=EventType.CUSTOM,
            topic="test",
            source="test",
            data={},
            priority=EventPriority.CRITICAL
        )
        
        # Publish in wrong order
        await event_router.publish(low_event)
        await event_router.publish(high_event)
        await event_router.publish(critical_event)
        
        # Give router time to process
        await asyncio.sleep(0.1)
        
        # Events should be delivered in priority order
        event1 = await queue.get()
        event2 = await queue.get()
        event3 = await queue.get()
        
        assert event1.id == "critical"
        assert event2.id == "high"
        assert event3.id == "low"
        
        await event_router.stop()
        
    @pytest.mark.asyncio
    async def test_agent_started_handler(self, event_router):
        """Test agent started event handling."""
        with patch.object(event_router.process_manager, 'spawn_agent') as mock_spawn:
            mock_spawn.return_value = AsyncMock()
            
            await event_router.start()
            
            start_event = Event(
                id="start-001",
                type=EventType.AGENT_STARTED,
                topic="agent.start",
                source="test",
                data={
                    "agent_id": "test-agent",
                    "command": ["python", "-m", "test"]
                }
            )
            
            await event_router.publish(start_event)
            
            # Give router time to process
            await asyncio.sleep(0.1)
            
            mock_spawn.assert_called_once_with(
                "test-agent",
                ["python", "-m", "test"]
            )
            
            await event_router.stop()
            
    @pytest.mark.asyncio
    async def test_auto_approval_for_dev_tasks(self, event_router):
        """Test that normal dev tasks are auto-approved."""
        await event_router.start()
        
        # Subscribe to approval responses
        queue = event_router.subscribe("test", "approval.*")
        
        # Send approval request for normal dev task
        approval_event = Event(
            id="approval-001",
            type=EventType.NEEDS_APPROVAL,
            topic="approval.request",
            source="test-agent",
            data={
                "operation": "create_branch"
            }
        )
        
        await event_router.publish(approval_event)
        
        # Give router time to process
        await asyncio.sleep(0.1)
        
        # Should get auto-approval
        assert not queue.empty()
        response = await queue.get()
        assert response.data["approved"] is True
        
        await event_router.stop()
        
    @pytest.mark.asyncio
    async def test_manual_approval_for_critical_ops(self, event_router):
        """Test that critical operations need manual approval."""
        await event_router.start()
        
        # Subscribe to approval responses
        queue = event_router.subscribe("test", "approval.*")
        
        # Send approval request for critical operation
        approval_event = Event(
            id="approval-002",
            type=EventType.NEEDS_APPROVAL,
            topic="approval.request",
            source="test-agent",
            data={
                "operation": "production_deploy"
            }
        )
        
        await event_router.publish(approval_event)
        
        # Give router time to process
        await asyncio.sleep(0.1)
        
        # Should NOT get auto-approval for production deploy
        assert queue.empty()
        
        await event_router.stop()
        
    @pytest.mark.asyncio
    async def test_dlq_on_delivery_failure(self, event_router, sample_event):
        """Test that failed deliveries go to DLQ after retries."""
        await event_router.start()
        
        # Subscribe with failing callback
        async def failing_callback(event):
            raise Exception("Delivery failed")
            
        event_router.subscribe(
            "failing-subscriber",
            "test.*",
            callback=failing_callback
        )
        
        # Set retry count to max
        sample_event.retry_count = 3
        
        await event_router.publish(sample_event)
        
        # Give router time to process
        await asyncio.sleep(0.1)
        
        # Check event went to DLQ
        dlq_events = await event_router.dlq.get_all()
        assert len(dlq_events) > 0
        
        await event_router.stop()