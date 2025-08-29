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
import hashlib
import json
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import uuid
from contextlib import asynccontextmanager
from urllib.parse import urljoin

# Import the memory integration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.memory_integration import AgentMemoryInterface
from .whiteboard_collaboration import WhiteboardManager, SharedWhiteboard, WhiteboardPermission

# Import event models
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "event-router"))
    from models import (
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


class V03Agent:
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
        self._event_session: Optional[aiohttp.ClientSession] = None
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

    async def _initialize_whiteboard_system(self) -> None:
        """Initialize the whiteboard collaboration system."""
        try:
            self.whiteboard_manager = WhiteboardManager()
            await self.whiteboard_manager.initialize()
            print(f"  📋 Whiteboard system initialized for {self.agent_id}")
        except Exception as e:
            print(f"  ⚠️ Whiteboard system initialization failed: {e}")
            self.whiteboard_manager = None

    async def _load_knowledge_base(self) -> None:
        """Load agent's knowledge from MD files."""
        knowledge_dir = Path(f".claude/agents/{self.agent_type}/knowledge")

        if not knowledge_dir.exists():
            # Try alternative path
            knowledge_dir = Path(f".claude/agents/{self.agent_type.replace('-', '_')}/knowledge")

        if knowledge_dir.exists():
            print(f"📚 Loading knowledge base from {knowledge_dir}")
            loaded_count = 0

            for md_file in knowledge_dir.glob("*.md"):
                try:
                    content = md_file.read_text()

                    # Extract title from first # heading if present
                    lines = content.split('\n')
                    title = md_file.stem
                    for line in lines:
                        if line.startswith('# '):
                            title = line[2:].strip()
                            break

                    # Create knowledge node
                    knowledge_id = await self.memory.add_knowledge(
                        concept=title,
                        description=content[:500],  # First 500 chars as description
                        confidence=0.9  # High confidence for pre-loaded knowledge
                    )

                    # Also store as long-term memory for retrieval
                    await self.memory.remember_long_term(
                        content,
                        tags=["knowledge_base", md_file.stem, "foundational"]
                    )

                    loaded_count += 1
                    print(f"  📖 Loaded: {title}")

                except Exception as e:
                    print(f"  ⚠️ Failed to load {md_file.name}: {e}")

            self.knowledge_loaded = True
            print(f"  ✅ Loaded {loaded_count} knowledge files")
        else:
            print(f"  ℹ️ No knowledge directory at {knowledge_dir}")

    async def _recall_recent_context(self, limit: int = 10) -> None:
        """Recall recent memories to establish context."""
        try:
            memories = await self.memory.recall_memories(limit=limit)

            if memories:
                print(f"🧠 Recalled {len(memories)} recent memories")

                # Analyze patterns in recent memories
                for memory in memories:
                    if memory.get('memory_type') == 'procedural':
                        task_type = memory.get('metadata', {}).get('task_type')
                        if task_type:
                            if task_type not in self.learned_patterns:
                                self.learned_patterns[task_type] = []
                            self.learned_patterns[task_type].append(memory)
        except Exception as e:
            print(f"  ℹ️ No recent memories available: {e}")

    async def start_task(self, task_description: str) -> str:
        """Begin a new task with memory tracking."""
        # Create task ID
        task_hash = hashlib.md5(
            f"{task_description}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        self.current_task_id = f"task_{task_hash}"

        # Initialize task in memory
        if self.memory:
            self.memory.task_id = self.current_task_id
            await self.memory.remember_short_term(
                f"Started task: {task_description}",
                tags=["task_start", "event"],
                importance=0.8
            )

        # Create or join task whiteboard
        await self._setup_task_whiteboard(task_description)

        # Emit task started event
        await self.emit_task_started(task_description)

        # Check for similar past tasks
        similar = await self.find_similar_tasks(task_description)
        if similar:
            print(f"💡 Found {len(similar)} similar past tasks")
            # Could use these to inform approach

        return self.current_task_id

    async def find_similar_tasks(self, task_description: str) -> List[Dict]:
        """Find similar tasks from memory."""
        # Search memories for similar content
        # This is a simplified version - could use embeddings for better similarity
        memories = await self.memory.recall_memories(limit=50)

        similar = []
        task_words = set(task_description.lower().split())

        for memory in memories:
            content = memory.get('content', '').lower()
            content_words = set(content.split())

            # Simple word overlap similarity
            overlap = len(task_words & content_words)
            if overlap > min(3, len(task_words) // 2):
                similar.append(memory)

        return similar[:5]  # Top 5 most relevant

    async def _setup_task_whiteboard(self, task_description: str) -> None:
        """Set up whiteboard for the current task."""
        if not self.whiteboard_manager or not self.current_task_id:
            return

        try:
            # Try to find existing whiteboard for this task
            existing = await self.whiteboard_manager.discover_whiteboards(
                agent_id=self.agent_id,
                task_id=self.current_task_id,
                limit=1
            )

            if existing:
                # Join existing whiteboard
                whiteboard_id = existing[0]['whiteboard_id']
                whiteboard = await self.whiteboard_manager.get_whiteboard(
                    whiteboard_id, self.agent_id
                )
                if whiteboard:
                    self.current_whiteboards[self.current_task_id] = whiteboard
                    print(f"  📋 Joined existing whiteboard: {whiteboard_id}")
                    return

            # Create new task coordination whiteboard
            whiteboard_id = await self.whiteboard_manager.create_whiteboard(
                name=f"Task: {task_description[:50]}...",
                created_by=self.agent_id,
                task_id=self.current_task_id,
                template_id="task_coordination"
            )

            whiteboard = await self.whiteboard_manager.get_whiteboard(
                whiteboard_id, self.agent_id
            )

            if whiteboard:
                self.current_whiteboards[self.current_task_id] = whiteboard

                # Initialize whiteboard with task info
                await whiteboard.write(self.agent_id, "task_overview.description", task_description)
                await whiteboard.write(self.agent_id, f"agent_assignments.{self.agent_type}", {
                    "assigned_to": self.agent_id,
                    "agent_type": self.agent_type,
                    "capabilities": self.capabilities.expertise_areas,
                    "status": "active",
                    "started_at": datetime.now().isoformat()
                })

                print(f"  📋 Created task whiteboard: {whiteboard_id}")

        except Exception as e:
            print(f"  ⚠️ Failed to set up task whiteboard: {e}")

    async def learn_from_outcome(self, outcome: TaskOutcome) -> None:
        """Learn from task execution outcome."""
        if outcome.success:
            # Store successful pattern
            procedure_id = await self.memory.store_procedure(
                procedure_name=f"successful_{outcome.task_type}",
                steps=outcome.steps_taken,
                context=f"Task {outcome.task_id} completed in {outcome.duration_seconds}s"
            )

            # Remember the success
            await self.memory.remember_long_term(
                f"Successfully completed {outcome.task_type}: {outcome.lessons_learned or 'No specific lessons'}",
                tags=["success", outcome.task_type, "learning"],
                importance=0.8
            )

            # Update success rate
            self.tasks_completed += 1
            self.success_rate = (
                (self.success_rate * (self.tasks_completed - 1) + 1.0)
                / self.tasks_completed
            )

            print(f"✅ Learned from success: {outcome.task_type}")

            # Emit task completed event
            await self.emit_task_completed(
                outcome.task_id,
                outcome.task_type,
                success=True,
                duration_seconds=outcome.duration_seconds,
                artifacts=getattr(outcome, 'artifacts', []),
                result=outcome.lessons_learned or "Task completed successfully"
            )
        else:
            # Remember what didn't work
            await self.memory.remember_long_term(
                f"Failed {outcome.task_type}: {outcome.error}. Lesson: {outcome.lessons_learned or 'Analyze error'}",
                tags=["failure", outcome.task_type, "learning", "error"],
                importance=0.9  # High importance for failures
            )

            # Update success rate
            self.tasks_completed += 1
            self.success_rate = (
                self.success_rate * (self.tasks_completed - 1)
                / self.tasks_completed
            )

            print(f"📝 Learned from failure: {outcome.task_type}")

            # Emit task completed event (with failure)
            await self.emit_task_completed(
                outcome.task_id,
                outcome.task_type,
                success=False,
                duration_seconds=outcome.duration_seconds,
                error=outcome.error,
                result=outcome.lessons_learned or "Task failed"
            )

    async def collaborate(self, message: str, decision: Optional[str] = None) -> None:
        """Collaborate with other agents via whiteboard."""
        if self.current_task_id and self.current_task_id in self.current_whiteboards:
            whiteboard = self.current_whiteboards[self.current_task_id]

            try:
                # Add communication to whiteboard
                current_comms = await whiteboard.read(self.agent_id, "communications") or []
                current_comms.append({
                    "message": message,
                    "from": self.agent_id,
                    "agent_type": self.agent_type,
                    "timestamp": datetime.now().isoformat(),
                    "type": "message"
                })
                await whiteboard.write(self.agent_id, "communications", current_comms)

                # Add decision if provided
                if decision:
                    current_decisions = await whiteboard.read(self.agent_id, "decisions") or []
                    current_decisions.append({
                        "decision": decision,
                        "reasoning": message,
                        "decided_by": self.agent_id,
                        "agent_type": self.agent_type,
                        "timestamp": datetime.now().isoformat()
                    })
                    await whiteboard.write(self.agent_id, "decisions", current_decisions)

                print(f"  📋 Added collaboration message to whiteboard")

            except Exception as e:
                print(f"  ⚠️ Failed to write to whiteboard: {e}")
                # Fall back to memory system
                if self.memory:
                    await self.memory.write_to_whiteboard(
                        "collaboration",
                        {
                            "message": message,
                            "decision": decision,
                            "timestamp": datetime.now().isoformat(),
                            "agent": self.agent_id
                        }
                    )

        # Emit collaboration event
        await self.emit_collaboration(
            message=message,
            message_type="collaboration",
            decision=decision
        )

    async def get_relevant_knowledge(self, query: str) -> List[Dict]:
        """Retrieve relevant knowledge for a query."""
        # Search long-term memories
        memories = await self.memory.recall_memories(
            memory_types=["long_term", "semantic"],
            limit=20
        )

        # Filter for relevance (simple keyword matching)
        query_words = set(query.lower().split())
        relevant = []

        for memory in memories:
            content = memory.get('content', '').lower()
            if any(word in content for word in query_words):
                relevant.append(memory)

        return relevant

    async def share_expertise(self, topic: str) -> Dict[str, Any]:
        """Share agent's expertise on a topic."""
        knowledge = await self.get_relevant_knowledge(topic)
        procedures = await self.memory.recall_procedure()

        # Filter procedures related to topic
        relevant_procedures = [
            p for p in procedures
            if topic.lower() in p.get('procedure_name', '').lower()
        ]

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "expertise_shared": topic,
            "knowledge_items": len(knowledge),
            "procedures": len(relevant_procedures),
            "confidence": self.success_rate,
            "knowledge": knowledge[:5],  # Top 5 items
            "procedures": relevant_procedures[:3]  # Top 3 procedures
        }

    async def create_design_whiteboard(self, problem_statement: str, project_id: Optional[str] = None) -> Optional[str]:
        """Create a design decision whiteboard."""
        if not self.whiteboard_manager:
            return None

        try:
            whiteboard_id = await self.whiteboard_manager.create_whiteboard(
                name=f"Design Decision: {problem_statement[:50]}...",
                created_by=self.agent_id,
                task_id=self.current_task_id,
                project_id=project_id,
                template_id="design_decision"
            )

            whiteboard = await self.whiteboard_manager.get_whiteboard(whiteboard_id, self.agent_id)
            if whiteboard:
                await whiteboard.write(self.agent_id, "problem_statement", problem_statement)
                print(f"  📋 Created design whiteboard: {whiteboard_id}")
                return whiteboard_id

        except Exception as e:
            print(f"  ⚠️ Failed to create design whiteboard: {e}")

        return None

    async def create_problem_solving_whiteboard(self, problem_description: str) -> Optional[str]:
        """Create a problem solving whiteboard."""
        if not self.whiteboard_manager:
            return None

        try:
            whiteboard_id = await self.whiteboard_manager.create_whiteboard(
                name=f"Problem: {problem_description[:50]}...",
                created_by=self.agent_id,
                task_id=self.current_task_id,
                template_id="problem_solving"
            )

            whiteboard = await self.whiteboard_manager.get_whiteboard(whiteboard_id, self.agent_id)
            if whiteboard:
                await whiteboard.write(self.agent_id, "problem_definition.description", problem_description)
                print(f"  📋 Created problem-solving whiteboard: {whiteboard_id}")
                return whiteboard_id

        except Exception as e:
            print(f"  ⚠️ Failed to create problem-solving whiteboard: {e}")

        return None

    async def invite_agent_to_whiteboard(self, whiteboard_id: str, agent_id: str, permission: WhiteboardPermission) -> bool:
        """Invite another agent to a whiteboard."""
        if not self.whiteboard_manager:
            return False

        try:
            whiteboard = await self.whiteboard_manager.get_whiteboard(whiteboard_id, self.agent_id)
            if whiteboard:
                success = await whiteboard.grant_access(self.agent_id, agent_id, permission)
                if success:
                    print(f"  📋 Granted {permission.value} access to {agent_id} for whiteboard {whiteboard_id}")
                return success

        except Exception as e:
            print(f"  ⚠️ Failed to invite agent to whiteboard: {e}")

        return False

    async def discover_relevant_whiteboards(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Discover whiteboards relevant to current agent and task."""
        if not self.whiteboard_manager:
            return []

        try:
            # Search by current task
            relevant = []
            if self.current_task_id:
                task_whiteboards = await self.whiteboard_manager.discover_whiteboards(
                    agent_id=self.agent_id,
                    task_id=self.current_task_id,
                    limit=limit
                )
                relevant.extend(task_whiteboards)

            # Search by expertise areas
            for expertise in self.capabilities.expertise_areas:
                expert_whiteboards = await self.whiteboard_manager.discover_whiteboards(
                    agent_id=self.agent_id,
                    template_category=expertise,
                    limit=3
                )
                relevant.extend(expert_whiteboards)

            # Remove duplicates and limit results
            seen = set()
            unique_relevant = []
            for wb in relevant:
                wb_id = wb.get('whiteboard_id')
                if wb_id and wb_id not in seen:
                    seen.add(wb_id)
                    unique_relevant.append(wb)
                if len(unique_relevant) >= limit:
                    break

            return unique_relevant

        except Exception as e:
            print(f"  ⚠️ Failed to discover whiteboards: {e}")
            return []

    async def get_whiteboard_summary(self, whiteboard_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of whiteboard content."""
        if not self.whiteboard_manager:
            return None

        try:
            whiteboard = await self.whiteboard_manager.get_whiteboard(whiteboard_id, self.agent_id)
            if whiteboard:
                info = await whiteboard.get_info(self.agent_id)
                content = await whiteboard.read(self.agent_id)

                return {
                    "info": info,
                    "content_summary": {
                        "keys": list(content.keys()) if content else [],
                        "size": len(json.dumps(content)) if content else 0,
                        "last_update": info.get("metadata", {}).get("last_modified")
                    }
                }

        except Exception as e:
            print(f"  ⚠️ Failed to get whiteboard summary: {e}")

        return None

    async def update_task_progress(self, completed_steps: List[str], current_step: str, blocked_items: Optional[List[str]] = None) -> None:
        """Update task progress on the whiteboard."""
        if not self.current_task_id or self.current_task_id not in self.current_whiteboards:
            return

        try:
            whiteboard = self.current_whiteboards[self.current_task_id]

            progress_update = {
                "completed_steps": completed_steps,
                "current_step": current_step,
                "blocked_items": blocked_items or [],
                "updated_by": self.agent_id,
                "updated_at": datetime.now().isoformat()
            }

            await whiteboard.write(self.agent_id, "progress", progress_update)
            print(f"  📋 Updated task progress on whiteboard")

        except Exception as e:
            print(f"  ⚠️ Failed to update task progress: {e}")

    async def report_issue(self, issue_description: str, severity: str = "medium") -> None:
        """Report an issue to the task whiteboard."""
        if not self.current_task_id or self.current_task_id not in self.current_whiteboards:
            return

        try:
            whiteboard = self.current_whiteboards[self.current_task_id]
            current_issues = await whiteboard.read(self.agent_id, "issues") or []

            new_issue = {
                "issue": issue_description,
                "severity": severity,
                "reported_by": self.agent_id,
                "agent_type": self.agent_type,
                "timestamp": datetime.now().isoformat(),
                "status": "open"
            }

            current_issues.append(new_issue)
            await whiteboard.write(self.agent_id, "issues", current_issues)
            print(f"  📋 Reported issue to whiteboard: {issue_description}")

        except Exception as e:
            print(f"  ⚠️ Failed to report issue: {e}")

    async def shutdown(self) -> None:
        """Clean shutdown with memory persistence."""
        # Store final state
        await self.memory.remember_long_term(
            f"Agent {self.agent_id} shutting down. Tasks completed: {self.tasks_completed}, Success rate: {self.success_rate:.2%}",
            tags=["shutdown", "metrics"]
        )

        # Emit shutdown event
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

        # Close memory connection
        if self.memory:
            await self.memory.__aexit__(None, None, None)

        print(f"👋 {self.agent_type} agent shut down gracefully")

    # =================
    # Event System Methods
    # =================

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
            "priority": "normal"
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
