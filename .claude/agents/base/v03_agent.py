"""
V0.3 Agent Base Class with Memory Integration
==============================================

This is the foundation for all v0.3 agents. It provides:
- Memory persistence across sessions
- Knowledge base loading from MD files
- Learning from experience
- Pattern recognition
- Collaboration capabilities
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

# Import the memory integration
from ...shared.memory_integration import AgentMemoryInterface
from .whiteboard_collaboration import WhiteboardManager, SharedWhiteboard, AccessLevel, WhiteboardType

# Import aiohttp for event handling
try:
    import aiohttp
except ImportError:
    aiohttp = None

# Import mixins
from .memory_mixin import MemoryMixin
from .whiteboard_mixin import WhiteboardMixin
from .event_handler_mixin import EventHandlerMixin
from .state_mixin import StateMixin

# Import event models
try:
    from .event_models import (
        AgentEvent,
        AgentInitializedEvent,
        TaskStartedEvent,
        TaskCompletedEvent,
        KnowledgeLearnedEvent,
        CollaborationMessageEvent,
        EventType,
        EventPriority
    )
    EVENTS_AVAILABLE = True
except (ImportError, SyntaxError) as e:
    # Fallback if event router models are not available or have dependency issues
    print(f"Event models not available ({e.__class__.__name__}: {e}), using simplified event system")
    AgentEvent = None
    AgentInitializedEvent = None
    TaskStartedEvent = None
    TaskCompletedEvent = None
    KnowledgeLearnedEvent = None
    CollaborationMessageEvent = None
    EventType = None
    EventPriority = None
    EVENTS_AVAILABLE = False


@dataclass
class EventConfiguration:
    """Configuration for event publishing."""
    enabled: bool = True
    event_router_url: str = "http://localhost:8000"
    timeout_seconds: int = 5
    retry_attempts: int = 3
    batch_size: int = 10
    emit_heartbeat: bool = True
    heartbeat_interval: int = 60  # seconds
    store_in_memory: bool = True  # Store high-priority events in agent's memory
    graceful_degradation: bool = True  # Continue operation if event router fails


@dataclass
class AgentCapabilities:
    """Defines what an agent can do and knows."""
    can_parallelize: bool = False
    can_create_prs: bool = False
    can_write_code: bool = False
    can_review_code: bool = False
    can_test: bool = False
    can_document: bool = False
    expertise_areas: List[str] = field(default_factory=list)
    max_parallel_tasks: int = 1


@dataclass
class TaskOutcome:
    """Result of a task execution."""
    success: bool
    task_id: str
    task_type: str
    steps_taken: List[str]
    duration_seconds: float
    error: Optional[str] = None
    lessons_learned: Optional[str] = None


class V03Agent(MemoryMixin, WhiteboardMixin, EventHandlerMixin, StateMixin):
    """
    Base class for v0.3 memory-enabled agents.

    Every v0.3 agent inherits from this class to gain:
    - Persistent memory across sessions
    - Knowledge base management
    - Learning capabilities
    - Collaboration features
    - Event publishing capabilities
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: Optional[AgentCapabilities] = None,
        event_config: Optional[EventConfiguration] = None
    ):
        """Initialize a v0.3 agent."""
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities or AgentCapabilities()
        self.event_config = event_config or EventConfiguration()

        # Memory interface (will be initialized in async setup)
        self.memory: Optional[AgentMemoryInterface] = None
        self.knowledge_loaded = False
        self.start_time = datetime.now()

        # Track current task for context
        self.current_task_id: Optional[str] = None

        # Whiteboard collaboration
        self.whiteboard_manager: Optional[WhiteboardManager] = None
        self.current_whiteboards: Dict[str, SharedWhiteboard] = {}  # task_id -> whiteboard

        # Learning metrics
        self.tasks_completed = 0
        self.success_rate = 0.0
        self.learned_patterns: Dict[str, List[Dict]] = {}

        # Event publishing
        self._event_session: Optional[Any] = None  # aiohttp.ClientSession if available
        self._event_batch: List[Dict[str, Any]] = []
        self._last_heartbeat = datetime.now()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._event_publishing_enabled = False

    async def initialize(self, mcp_url: str = "http://localhost:8000") -> None:
        """
        Initialize the agent with memory system.
        Must be called before using the agent.
        """
        print(f"🚀 Initializing {self.agent_type} agent: {self.agent_id}")

        # Create memory interface
        self.memory = AgentMemoryInterface(
            agent_id=self.agent_id,
            mcp_base_url=mcp_url
        )

        # Enter async context
        await self.memory.__aenter__()

        # Initialize whiteboard system
        await self._initialize_whiteboard_system()

        # Initialize event publishing
        await self._initialize_event_system()

        # Load knowledge base
        await self._load_knowledge_base()

        # Recall recent memories
        await self._recall_recent_context()

        # Store initialization
        await self.memory.remember_short_term(
            f"Agent {self.agent_id} initialized",
            tags=["initialization", self.agent_type]
        )

        # Emit initialization event
        await self.emit_initialized()

        print(f"✅ {self.agent_type} agent ready with memory system, whiteboards, and event publishing")

    # Memory and whiteboard initialization are now handled by mixins

    async def start_task(self, task_description: str) -> str:
        """Begin a new task with memory tracking."""
        # Start task using StateMixin
        task_id = await super().start_task(task_description)
        
        # Initialize task in memory
        if self.memory:
            self.memory.task_id = self.current_task_id
            await self.remember_task_start(task_description)

        # Create or join task whiteboard
        await self._setup_task_whiteboard(task_description)

        # Emit task started event
        await self.emit_task_started(task_description)

        # Check for similar past tasks
        similar = await self.find_similar_tasks(task_description)
        if similar:
            print(f"💡 Found {len(similar)} similar past tasks")
            # Could use these to inform approach

        return self.current_task_id or task_id



    async def learn_from_outcome(self, outcome: TaskOutcome) -> None:
        """Learn from task execution outcome."""
        # Learn using MemoryMixin
        await super().learn_from_outcome(outcome)
        
        # Emit task completed event
        await self.emit_task_completed(
            outcome.task_id,
            outcome.task_type,
            success=outcome.success,
            duration_seconds=outcome.duration_seconds,
            artifacts=getattr(outcome, 'artifacts', []),
            result=outcome.lessons_learned or ("Task completed successfully" if outcome.success else "Task failed"),
            error=outcome.error if not outcome.success else None
        )

    async def collaborate(self, message: str, decision: Optional[str] = None) -> None:
        """Collaborate with other agents via whiteboard."""
        # Use WhiteboardMixin for collaboration
        await super().collaborate(message, decision)
        
        # Emit collaboration event
        await self.emit_collaboration(
            message=message,
            message_type="collaboration",
            decision=decision
        )



    async def shutdown(self) -> None:
        """Clean shutdown with memory persistence."""
        # Store final state using MemoryMixin
        await self.remember_shutdown()

        # Emit shutdown event using EventHandlerMixin
        await self.emit_shutdown_event()

        # Clean up event system using EventHandlerMixin
        await self.cleanup_event_system()

        # Close memory connection
        if self.memory:
            await self.memory.__aexit__(None, None, None)

        print(f"👋 {self.agent_type} agent shut down gracefully")


    # =================
    # Abstract methods for subclasses to implement
    # ================

    async def execute_task(self, task: Dict[str, Any]) -> TaskOutcome:
        """Execute a task. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement execute_task")

    async def can_handle_task(self, task_description: str) -> bool:
        """Check if agent can handle a task type."""
        # Default implementation - override in subclasses
        return True


# Example concrete agent implementation
class ExampleWorkflowAgent(V03Agent):
    """Example of how to create a v0.3 agent."""

    def __init__(self):
        capabilities = AgentCapabilities(
            can_create_prs=True,
            can_parallelize=True,
            expertise_areas=["git", "workflow", "pr_management"]
        )
        super().__init__(
            agent_id="workflow_example",
            agent_type="workflow-manager",
            capabilities=capabilities
        )

    async def execute_task(self, task: Dict[str, Any]) -> TaskOutcome:
        """Execute a workflow task."""
        start = datetime.now()

        try:
            # Remember starting
            if self.memory:
                await self.memory.remember_short_term(f"Starting workflow: {task.get('description')}")

            # Simulate workflow execution
            steps = [
                "Parse requirements",
                "Create branch",
                "Implement changes",
                "Run tests",
                "Create PR"
            ]

            for step in steps:
                if self.memory:
                    await self.memory.remember_short_term(f"Executing: {step}")
                await asyncio.sleep(0.1)  # Simulate work

            # Success!
            duration = (datetime.now() - start).total_seconds()

            return TaskOutcome(
                success=True,
                task_id=self.current_task_id or "unknown",
                task_type="workflow",
                steps_taken=steps,
                duration_seconds=duration,
                lessons_learned="Workflow completed successfully"
            )

        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            return TaskOutcome(
                success=False,
                task_id=self.current_task_id or "unknown",
                task_type="workflow",
                steps_taken=[],
                duration_seconds=duration,
                error=str(e),
                lessons_learned=f"Error encountered: {e}"
            )


async def test_v03_agent():
    """Test the V03Agent base class."""
    print("\n" + "="*60)
    print("Testing V0.3 Agent with Memory")
    print("="*60)

    # Create and initialize agent
    agent = ExampleWorkflowAgent()

    try:
        await agent.initialize()

        # Start a task
        task_id = await agent.start_task("Create PR for feature X")
        print(f"\n📋 Started task: {task_id}")

        # Execute task
        outcome = await agent.execute_task({
            "description": "Create PR for feature X",
            "branch": "feature-x"
        })

        # Learn from outcome
        await agent.learn_from_outcome(outcome)

        # Collaborate via whiteboard
        await agent.collaborate(
            "Working on feature X implementation",
            decision="Proceeding with implementation"
        )

        # Update task progress
        await agent.update_task_progress(
            completed_steps=["Set up JWT library", "Created user model"],
            current_step="Implementing login endpoint",
            blocked_items=["Need security review"]
        )

        # Report an issue
        await agent.report_issue(
            "Password complexity validation missing",
            severity="medium"
        )

        # Discover relevant whiteboards
        relevant_whiteboards = await agent.discover_relevant_whiteboards(limit=5)
        print(f"\n🔍 Found {len(relevant_whiteboards)} relevant whiteboards")

        # Share expertise
        expertise = await agent.share_expertise("workflow")
        print(f"\n📚 Sharing expertise: {expertise['knowledge_items']} knowledge items")

        # Test whiteboard creation
        design_wb_id = await agent.create_design_whiteboard(
            "Should we use JWT or session-based auth?"
        )
        if design_wb_id:
            print(f"\n📋 Created design whiteboard: {design_wb_id}")

        print(f"\n✅ Test completed successfully!")

    finally:
        await agent.shutdown()


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_v03_agent())
