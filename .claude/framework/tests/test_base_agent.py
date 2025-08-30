
"""Tests for the BaseAgent class."""

import asyncio

import pytest

from ..base_agent import AgentMetadata, AgentResponse, BaseAgent


class TestAgentImpl(BaseAgent):
    """Test implementation of BaseAgent."""

    async def init(self) -> None:
        """Initialize test agent."""
        self.state["initialized"] = True

    async def process(self, event: Any) -> AgentResponse:  # type: ignore[assignment]
        """Process test event."""
        return AgentResponse(
            success=True,
            result=f"Processed: {event}",
        )


class TestBaseAgent:
    """Test suite for BaseAgent."""

    @pytest.fixture
    def agent_metadata(self):
        """Create test agent metadata."""
        return AgentMetadata(
            name="TestAgent",
            version="1.0.0",
            description="Test agent",
            tools=[{"name": "test_tool", "required": True}],
            events={
                "subscribes": ["test.event"],
                "publishes": ["result.event"],
            },
            settings={"timeout": 30},
        )

    @pytest.fixture
    async def test_agent(self, agent_metadata):
        """Create test agent instance."""
        agent = TestAgentImpl(
            metadata=agent_metadata,
            event_router=AsyncMock(),  # type: ignore[assignment]
            memory_system=AsyncMock(),  # type: ignore[assignment]
        )
        await agent.init()
        return agent

    @pytest.mark.asyncio
    async def test_agent_initialization(self, test_agent):
        """Test agent initialization."""
        assert test_agent.metadata.name == "TestAgent"
        assert test_agent.state["initialized"] is True
        assert test_agent.agent_id.startswith("TestAgent_")

    @pytest.mark.asyncio
    async def test_agent_registration(self, test_agent):
        """Test agent registration."""
        await test_agent.register()

        # Check event subscriptions
        test_agent.event_router.subscribe.assert_called()

        # Check memory storage
        test_agent.memory_system.store_memory.assert_called()

    @pytest.mark.asyncio
    async def test_agent_listen_and_process(self, test_agent):
        """Test agent event listening and processing."""
        # Start listening
        await test_agent.listen()
        assert test_agent.running is True

        # Simulate event
        mock_event = MagicMock()  # type: ignore[assignment]
        mock_event.type = "test.event"
        mock_event.data = {"test": "data"}

        await test_agent._handle_event(mock_event)

        # Give time for processing
        await asyncio.sleep(0.1)

        # Clean up
        await test_agent.cleanup()
        assert test_agent.running is False

    @pytest.mark.asyncio
    async def test_tool_invocation(self, test_agent):
        """Test tool invocation."""

        # Register a test tool
        async def test_tool_handler(param1: str) -> str:
            return f"Result: {param1}"

        test_agent.tool_registry.register(
            "test_tool",
            test_tool_handler,
            required=True,
        )

        # Invoke tool
        result = await test_agent.invoke_tool("test_tool", {"param1": "test"})
        assert result == "Result: test"

    @pytest.mark.asyncio
    async def test_ask_question(self, test_agent):
        """Test interactive question asking."""
        # Start question in background
        question_task = asyncio.create_task(test_agent.ask_question("Test question?"))

        # Give time for event to be published
        await asyncio.sleep(0.1)

        # Simulate answer
        questions = list(test_agent._pending_questions.keys())
        if questions:
            test_agent.answer_question(questions[0], "Test answer")

        # Get answer
        answer = await question_task
        assert answer == "Test answer"

    @pytest.mark.asyncio
    async def test_request_approval(self, test_agent):
        """Test approval request."""
        # Start approval request in background
        approval_task = asyncio.create_task(test_agent.request_approval("Delete file?"))

        # Give time for event to be published
        await asyncio.sleep(0.1)

        # Simulate approval
        approvals = list(test_agent._pending_approvals.keys())
        if approvals:
            test_agent.provide_approval(approvals[0], True)

        # Get approval
        approved = await approval_task
        assert approved is True

    @pytest.mark.asyncio
    async def test_state_management(self, test_agent):
        """Test state save and load."""
        # Set state
        test_agent.state["test_key"] = "test_value"

        # Save state
        await test_agent.save_state()
        test_agent.memory_system.store_memory.assert_called()

        # Simulate load
        mock_memory = MagicMock()  # type: ignore[assignment]
        mock_memory.metadata = {"state": {"test_key": "loaded_value"}}
        test_agent.memory_system.retrieve_context.return_value = [mock_memory]

        # Clear and reload state
        test_agent.state.clear()
        await test_agent.load_state()

        assert test_agent.state["test_key"] == "loaded_value"


class TestAgentMetadata:
    """Test suite for AgentMetadata."""

    def test_metadata_creation(self):
        """Test creating agent metadata."""
        metadata = AgentMetadata(
            name="TestAgent",
            version="2.0.0",
            description="Test description",
        )

        assert metadata.name == "TestAgent"
        assert metadata.version == "2.0.0"
        assert metadata.description == "Test description"

    def test_metadata_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "name": "DictAgent",
            "version": "1.5.0",
            "tools": [{"name": "tool1"}],
            "events": {"subscribes": ["event1"]},
        }

        metadata = AgentMetadata.from_dict(data)

        assert metadata.name == "DictAgent"
        assert metadata.version == "1.5.0"
        assert len(metadata.tools) == 1
        assert "subscribes" in metadata.events


class TestAgentResponse:
    """Test suite for AgentResponse."""

    def test_response_creation(self):
        """Test creating agent response."""
        response = AgentResponse(
            success=True,
            result="Test result",
            metadata={"key": "value"},
        )

        assert response.success is True
        assert response.result == "Test result"
        assert response.metadata["key"] == "value"

    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        response = AgentResponse(
            success=False,
            error="Test error",
        )

        data = response.to_dict()

        assert data["success"] is False
        assert data["error"] == "Test error"
        assert data["result"] is None
