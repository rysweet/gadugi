import json

"""Tests for event data models."""

from gadugi.event_service.events import (
    Event,
    GitHubEvent,
    LocalEvent,
    AgentEvent,
    create_github_event,
    create_local_event,
    create_agent_event,
)


class TestGitHubEvent:
    """Test GitHubEvent model."""

    def test_creation(self):
        """Test GitHubEvent creation."""
        event = GitHubEvent(
            webhook_event="issues",
            repository="owner/repo",
            number=123,
            action="opened",
            actor="user",
            title="Test Issue",
            body="Test body",
            labels=["bug", "enhancement"],
        )

        assert event.webhook_event == "issues"
        assert event.repository == "owner/repo"
        assert event.number == 123
        assert event.action == "opened"
        assert event.actor == "user"
        assert event.title == "Test Issue"
        assert event.body == "Test body"
        assert event.labels == ["bug", "enhancement"]

    def test_defaults(self):
        """Test default values."""
        event = GitHubEvent()
        assert event.webhook_event == ""
        assert event.repository == ""
        assert event.number is None
        assert event.labels == []
        assert event.assignees == []


class TestLocalEvent:
    """Test LocalEvent model."""

    def test_creation(self):
        """Test LocalEvent creation."""
        event = LocalEvent(
            event_name="file_changed",
            working_directory="/path/to/project",
            environment={"VAR": "value"},
            files_changed=["file1.py", "file2.py"],
        )

        assert event.event_name == "file_changed"
        assert event.working_directory == "/path/to/project"
        assert event.environment == {"VAR": "value"}
        assert event.files_changed == ["file1.py", "file2.py"]

    def test_defaults(self):
        """Test default values."""
        event = LocalEvent()
        assert event.event_name == ""
        assert event.working_directory == ""
        assert event.environment == {}
        assert event.files_changed == []


class TestAgentEvent:
    """Test AgentEvent model."""

    def test_creation(self):
        """Test AgentEvent creation."""
        event = AgentEvent(
            agent_name="workflow-manager",
            task_id="task-123",
            phase="implementation",
            status="completed",
            message="Task completed successfully",
            context={"branch": "feature/test"},
        )

        assert event.agent_name == "workflow-manager"
        assert event.task_id == "task-123"
        assert event.phase == "implementation"
        assert event.status == "completed"
        assert event.message == "Task completed successfully"
        assert event.context == {"branch": "feature/test"}

    def test_defaults(self):
        """Test default values."""
        event = AgentEvent()
        assert event.agent_name == ""
        assert event.task_id == ""
        assert event.phase == ""
        assert event.status == ""
        assert event.message == ""
        assert event.context == {}


class TestEvent:
    """Test Event model."""

    def test_creation(self):
        """Test Event creation."""
        event = Event(
            event_id="test-123",
            event_type="test.event",
            timestamp=1234567890,
            source="test",
            metadata={"key": "value"},
        )

        assert event.event_id == "test-123"
        assert event.event_type == "test.event"
        assert event.timestamp == 1234567890
        assert event.source == "test"
        assert event.metadata == {"key": "value"}

    def test_defaults(self):
        """Test default values."""
        event = Event()
        assert event.event_id  # UUID generated
        assert event.event_type == ""
        assert event.timestamp  # Current time
        assert event.source == ""
        assert event.metadata == {}
        assert event.payload == {}

    def test_serialization(self):
        """Test JSON serialization."""
        github_event = GitHubEvent(
            webhook_event="issues", repository="owner/repo", action="opened"
        )

        event = Event(
            event_type="github.issues.opened",
            source="github",
            payload={"github_event": github_event},
        )

        # Test to_dict
        event_dict = event.to_dict()
        assert "event_id" in event_dict
        assert event_dict["event_type"] == "github.issues.opened"
        assert event_dict["source"] == "github"
        assert "github_event" in event_dict["payload"]

        # Test to_json
        event_json = event.to_json()
        assert isinstance(event_json, str)
        parsed = json.loads(event_json)
        assert parsed["event_type"] == "github.issues.opened"

    def test_deserialization(self):
        """Test JSON deserialization."""
        # First create an event and get its dict representation
        github_event = GitHubEvent(
            webhook_event="issues", repository="owner/repo", action="opened"
        )

        original_event = Event(
            event_id="test-123",
            event_type="github.issues.opened",
            timestamp=1234567890,
            source="github",
            metadata={"key": "value"},
            payload={"github_event": github_event},
        )

        # Convert to dict and back
        data = original_event.to_dict()

        # Test from_dict
        event = Event.from_dict(data)
        assert event.event_id == "test-123"
        assert event.event_type == "github.issues.opened"
        assert event.source == "github"

        restored_github_event = event.get_github_event()
        assert restored_github_event is not None
        assert restored_github_event.webhook_event == "issues"
        assert restored_github_event.repository == "owner/repo"

        # Test from_json
        json_str = original_event.to_json()
        event2 = Event.from_json(json_str)
        assert event2.event_id == event.event_id
        assert event2.event_type == event.event_type

    def test_event_type_detection(self):
        """Test event type detection methods."""
        # GitHub event
        github_event = Event(payload={"github_event": GitHubEvent()})
        assert github_event.is_github_event()
        assert not github_event.is_local_event()
        assert not github_event.is_agent_event()

        # Local event
        local_event = Event(payload={"local_event": LocalEvent()})
        assert not local_event.is_github_event()
        assert local_event.is_local_event()
        assert not local_event.is_agent_event()

        # Agent event
        agent_event = Event(payload={"agent_event": AgentEvent()})
        assert not agent_event.is_github_event()
        assert not agent_event.is_local_event()
        assert agent_event.is_agent_event()

    def test_payload_getters(self):
        """Test payload getter methods."""
        github_payload = GitHubEvent(repository="test/repo")
        local_payload = LocalEvent(event_name="test")
        agent_payload = AgentEvent(agent_name="test-agent")

        # GitHub event
        github_event = Event(payload={"github_event": github_payload})
        assert github_event.get_github_event() == github_payload
        assert github_event.get_local_event() is None
        assert github_event.get_agent_event() is None

        # Local event
        local_event = Event(payload={"local_event": local_payload})
        assert local_event.get_github_event() is None
        assert local_event.get_local_event() == local_payload
        assert local_event.get_agent_event() is None

        # Agent event
        agent_event = Event(payload={"agent_event": agent_payload})
        assert agent_event.get_github_event() is None
        assert agent_event.get_local_event() is None
        assert agent_event.get_agent_event() == agent_payload


class TestEventCreators:
    """Test event creator functions."""

    def test_create_github_event(self):
        """Test create_github_event function."""
        event = create_github_event(
            event_type="issues",
            repository="owner/repo",
            action="opened",
            actor="user",
            number=123,
            title="Test Issue",
            labels=["bug"],
        )

        assert event.event_type == "github.issues.opened"
        assert event.source == "github"
        assert event.is_github_event()

        github_event = event.get_github_event()
        assert github_event.webhook_event == "issues"
        assert github_event.repository == "owner/repo"
        assert github_event.action == "opened"
        assert github_event.actor == "user"
        assert github_event.number == 123
        assert github_event.title == "Test Issue"
        assert github_event.labels == ["bug"]

    def test_create_local_event(self):
        """Test create_local_event function."""
        event = create_local_event(
            event_name="file_changed",
            working_directory="/path/to/project",
            environment={"VAR": "value"},
            files_changed=["file.py"],
            custom_field="custom_value",
        )

        assert event.event_type == "local.file_changed"
        assert event.source == "local"
        assert event.is_local_event()
        assert event.metadata["custom_field"] == "custom_value"

        local_event = event.get_local_event()
        assert local_event.event_name == "file_changed"
        assert local_event.working_directory == "/path/to/project"
        assert local_event.environment == {"VAR": "value"}
        assert local_event.files_changed == ["file.py"]

    def test_create_agent_event(self):
        """Test create_agent_event function."""
        event = create_agent_event(
            agent_name="workflow-manager",
            task_id="task-123",
            phase="implementation",
            status="completed",
            message="Task done",
            context={"branch": "feature/test"},
            custom_field="custom_value",
        )

        assert event.event_type == "agent.workflow-manager.completed"
        assert event.source == "agent"
        assert event.is_agent_event()
        assert event.metadata["custom_field"] == "custom_value"

        agent_event = event.get_agent_event()
        assert agent_event.agent_name == "workflow-manager"
        assert agent_event.task_id == "task-123"
        assert agent_event.phase == "implementation"
        assert agent_event.status == "completed"
        assert agent_event.message == "Task done"
        assert agent_event.context == {"branch": "feature/test"}
