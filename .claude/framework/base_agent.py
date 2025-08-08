"""Base Agent class for the Gadugi agent framework."""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .frontmatter_parser import parse_agent_definition
from .tool_registry import ToolRegistry

# Import service dependencies
try:
    from ..services.event_router import EventRouter, Event, EventType, Subscription
    from ..services.memory_system import MemorySystem, Memory, MemoryType
except ImportError:
    # Mock imports for development
    class EventRouter:
        async def subscribe(self, *args, **kwargs): pass
        async def publish(self, event: Any): pass
    
    class Event:
        def __init__(self, **kwargs): 
            self.type = kwargs.get("type", "")
            self.data = kwargs.get("data", {})
    
    class EventType:
        pass
    
    class Subscription:
        pass
    
    class MemorySystem:
        async def store_memory(self, memory: Any): pass
        async def retrieve_context(self, query: str, limit: int = 10): return []
    
    class Memory:
        def __init__(self, **kwargs): pass
    
    class MemoryType:
        CONTEXT = "context"


logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """Metadata for an agent parsed from frontmatter."""
    
    name: str
    version: str = "1.0.0"
    description: str = ""
    tools: List[Dict[str, Any]] = field(default_factory=list)
    events: Dict[str, List[str]] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMetadata":
        """Create metadata from dictionary."""
        return cls(
            name=data.get("name", "UnnamedAgent"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            tools=data.get("tools", []),
            events=data.get("events", {"subscribes": [], "publishes": []}),
            settings=data.get("settings", {}),
        )


@dataclass
class AgentResponse:
    """Response from agent processing."""
    
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseAgent(ABC):
    """Base class for all agents in the Gadugi platform."""
    
    def __init__(
        self,
        agent_def_path: Optional[Path] = None,
        metadata: Optional[AgentMetadata] = None,
        event_router: Optional[EventRouter] = None,
        memory_system: Optional[MemorySystem] = None,
    ):
        """Initialize the base agent.
        
        Args:
            agent_def_path: Path to agent definition file
            metadata: Pre-parsed agent metadata
            event_router: Event router service instance
            memory_system: Memory system service instance
        """
        # Parse metadata from file or use provided
        if agent_def_path and agent_def_path.exists():
            self.metadata = parse_agent_definition(agent_def_path)
        elif metadata:
            self.metadata = metadata
        else:
            self.metadata = AgentMetadata(name="BaseAgent")
        
        # Service connections
        self.event_router = event_router or EventRouter()
        self.memory_system = memory_system or MemorySystem()
        
        # Tool registry
        self.tool_registry = ToolRegistry()
        self._register_tools()
        
        # Agent state
        self.agent_id = f"{self.metadata.name}_{uuid.uuid4().hex[:8]}"
        self.state: Dict[str, Any] = {}
        self.running = False
        self.subscriptions: List[Subscription] = []
        
        # Event processing
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._processing_task: Optional[asyncio.Task[None]] = None
        
        # Interactive support
        self._pending_questions: Dict[str, asyncio.Future[str]] = {}
        self._pending_approvals: Dict[str, asyncio.Future[bool]] = {}
        
        logger.info(f"Initialized agent {self.agent_id} ({self.metadata.name} v{self.metadata.version})")
    
    def _register_tools(self) -> None:
        """Register tools from metadata."""
        for tool_def in self.metadata.tools:
            tool_name = tool_def.get("name")
            required = tool_def.get("required", False)
            
            if tool_name:
                # Register tool placeholder
                self.tool_registry.register(
                    name=tool_name,
                    handler=self._create_tool_handler(tool_name),
                    required=required,
                )
    
    def _create_tool_handler(self, tool_name: str) -> Any:
        """Create a tool handler function."""
        async def handler(**kwargs: Any) -> Any:
            # Default implementation - can be overridden
            logger.debug(f"Invoking tool {tool_name} with params: {kwargs}")
            return {"tool": tool_name, "params": kwargs, "result": "success"}
        return handler
    
    @abstractmethod
    async def init(self) -> None:
        """Initialize agent resources.
        
        This method should be implemented by concrete agents to set up
        any required resources, connections, or initial state.
        """
        pass
    
    async def register(self) -> None:
        """Register with orchestrator and event router."""
        logger.info(f"Registering agent {self.agent_id}")
        
        # Subscribe to configured events
        if "subscribes" in self.metadata.events:
            for event_type in self.metadata.events["subscribes"]:
                subscription = await self.event_router.subscribe(
                    event_type=event_type,
                    handler=self._handle_event,
                    agent_id=self.agent_id,
                )
                self.subscriptions.append(subscription)
                logger.debug(f"Subscribed to event: {event_type}")
        
        # Store registration in memory
        registration_memory = Memory(
            type=MemoryType.CONTEXT,
            content=f"Agent {self.metadata.name} registered at {datetime.now()}",
            metadata={
                "agent_id": self.agent_id,
                "version": self.metadata.version,
                "events": self.metadata.events,
            },
        )
        await self.memory_system.store_memory(registration_memory)
    
    async def listen(self) -> None:
        """Start listening for events."""
        if self.running:
            logger.warning(f"Agent {self.agent_id} is already listening")
            return
        
        logger.info(f"Agent {self.agent_id} starting to listen for events")
        self.running = True
        
        # Start event processing task
        self._processing_task = asyncio.create_task(self._process_events())
    
    async def _handle_event(self, event: Event) -> None:
        """Handle incoming event by adding to queue."""
        if self.running:
            await self._event_queue.put(event)
            logger.debug(f"Queued event: {event.type}")
    
    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self.running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0,
                )
                
                # Process the event
                logger.debug(f"Processing event: {event.type}")
                response = await self.process(event)
                
                # Handle response
                if not response.success:
                    logger.error(f"Failed to process event {event.type}: {response.error}")
                
                # Store processing result in memory
                result_memory = Memory(
                    type=MemoryType.CONTEXT,
                    content=f"Processed event {event.type}",
                    metadata={
                        "agent_id": self.agent_id,
                        "event_type": event.type,
                        "success": response.success,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                await self.memory_system.store_memory(result_memory)
                
            except asyncio.TimeoutError:
                # No events to process
                continue
            except Exception as e:
                logger.error(f"Error processing events: {e}")
    
    @abstractmethod
    async def process(self, event: Event) -> AgentResponse:
        """Process incoming events.
        
        This method should be implemented by concrete agents to handle
        specific event types and perform the agent's core functionality.
        
        Args:
            event: The event to process
            
        Returns:
            AgentResponse with processing result
        """
        pass
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info(f"Cleaning up agent {self.agent_id}")
        
        # Stop listening
        self.running = False
        
        # Cancel processing task
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        # Unsubscribe from events
        for subscription in self.subscriptions:
            # Unsubscribe logic would go here
            pass
        
        # Store cleanup in memory
        cleanup_memory = Memory(
            type=MemoryType.CONTEXT,
            content=f"Agent {self.metadata.name} cleaned up at {datetime.now()}",
            metadata={"agent_id": self.agent_id},
        )
        await self.memory_system.store_memory(cleanup_memory)
    
    async def invoke_tool(self, tool_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Invoke a registered tool.
        
        Args:
            tool_name: Name of the tool to invoke
            params: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        params = params or {}
        
        try:
            result = await self.tool_registry.invoke(tool_name, **params)
            logger.debug(f"Tool {tool_name} invoked successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to invoke tool {tool_name}: {e}")
            raise
    
    async def ask_question(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Interactive Q&A support.
        
        Args:
            question: The question to ask
            context: Optional context for the question
            
        Returns:
            The answer to the question
        """
        question_id = f"q_{uuid.uuid4().hex[:8]}"
        future: asyncio.Future[str] = asyncio.Future()
        self._pending_questions[question_id] = future
        
        # Publish hasQuestion event
        question_event = Event(
            type="agent.hasQuestion",
            source=self.agent_id,
            data={
                "question_id": question_id,
                "question": question,
                "context": context or {},
                "agent": self.metadata.name,
            },
        )
        await self.event_router.publish(question_event)
        
        # Wait for answer
        try:
            answer = await asyncio.wait_for(future, timeout=30.0)
            return answer
        except asyncio.TimeoutError:
            del self._pending_questions[question_id]
            return "No answer received (timeout)"
    
    async def request_approval(self, action: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """Request user approval for an action.
        
        Args:
            action: The action requiring approval
            details: Optional details about the action
            
        Returns:
            True if approved, False otherwise
        """
        approval_id = f"a_{uuid.uuid4().hex[:8]}"
        future: asyncio.Future[bool] = asyncio.Future()
        self._pending_approvals[approval_id] = future
        
        # Publish needsApproval event
        approval_event = Event(
            type="agent.needsApproval",
            source=self.agent_id,
            data={
                "approval_id": approval_id,
                "action": action,
                "details": details or {},
                "agent": self.metadata.name,
            },
        )
        await self.event_router.publish(approval_event)
        
        # Wait for approval
        try:
            approved = await asyncio.wait_for(future, timeout=60.0)
            return approved
        except asyncio.TimeoutError:
            del self._pending_approvals[approval_id]
            return False  # Default to not approved on timeout
    
    def answer_question(self, question_id: str, answer: str) -> None:
        """Provide answer to a pending question.
        
        Args:
            question_id: ID of the question
            answer: The answer to provide
        """
        if question_id in self._pending_questions:
            self._pending_questions[question_id].set_result(answer)
            del self._pending_questions[question_id]
    
    def provide_approval(self, approval_id: str, approved: bool) -> None:
        """Provide approval decision.
        
        Args:
            approval_id: ID of the approval request
            approved: Whether the action is approved
        """
        if approval_id in self._pending_approvals:
            self._pending_approvals[approval_id].set_result(approved)
            del self._pending_approvals[approval_id]
    
    async def save_state(self) -> None:
        """Save agent state to memory system."""
        state_memory = Memory(
            type=MemoryType.CONTEXT,
            content=f"Agent state for {self.metadata.name}",
            metadata={
                "agent_id": self.agent_id,
                "state": self.state,
                "timestamp": datetime.now().isoformat(),
            },
        )
        await self.memory_system.store_memory(state_memory)
    
    async def load_state(self) -> None:
        """Load agent state from memory system."""
        # Retrieve most recent state
        memories = await self.memory_system.retrieve_context(
            f"Agent state for {self.metadata.name}",
            limit=1,
        )
        
        if memories:
            latest_memory = memories[0]
            if "state" in latest_memory.metadata:
                self.state = latest_memory.metadata["state"]
                logger.info(f"Loaded state for agent {self.agent_id}")