"""
State Management Mixin for V03Agent
===================================

This mixin handles all state-related functionality including:
- Task state tracking and management
- Agent state initialization
- Current task context management
- State persistence and recovery
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ...shared.memory_integration import AgentMemoryInterface


class StateMixinProtocol(Protocol):
    """Protocol defining expected attributes for classes using StateMixin."""

    agent_id: str
    agent_type: str
    current_task_id: Optional[str]
    start_time: datetime
    tasks_completed: int
    success_rate: float
    learned_patterns: Dict[str, List[Dict[str, Any]]]
    memory: Optional["AgentMemoryInterface"]


class StateMixin:
    """
    Mixin providing state management capabilities for V03Agent.

    This mixin requires the following attributes to be present on the class:
    - agent_id: str
    - agent_type: str
    - current_task_id: Optional[str]
    - start_time: datetime
    - tasks_completed: int
    - success_rate: float
    - learned_patterns: Dict[str, List[Dict]]
    - memory: Optional[AgentMemoryInterface]
    """

    # Type hints for attributes expected from the base class
    agent_id: str
    agent_type: str
    current_task_id: Optional[str]
    start_time: datetime
    tasks_completed: int
    success_rate: float
    learned_patterns: Dict[str, List[Dict[str, Any]]]
    memory: Optional["AgentMemoryInterface"]

    async def start_task(self, task_description: str) -> str:
        """Begin a new task with state tracking."""
        # Create task ID
        task_hash = hashlib.md5(
            f"{task_description}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        self.current_task_id = f"task_{task_hash}"

        # Initialize task in memory
        if self.memory:
            self.memory.task_id = self.current_task_id

        return self.current_task_id

    def get_current_task_id(self) -> Optional[str]:
        """Get the current task ID."""
        return self.current_task_id

    def clear_current_task(self) -> None:
        """Clear the current task ID."""
        self.current_task_id = None

    def get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state summary."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "current_task_id": self.current_task_id,
            "tasks_completed": self.tasks_completed,
            "success_rate": self.success_rate,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "has_active_task": self.current_task_id is not None,
            "learned_patterns_count": sum(
                len(patterns) for patterns in self.learned_patterns.values()
            ),
        }

    def is_task_active(self) -> bool:
        """Check if there is an active task."""
        return self.current_task_id is not None

    def get_uptime_seconds(self) -> float:
        """Get agent uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def get_task_metrics(self) -> Dict[str, Any]:
        """Get task completion metrics."""
        return {
            "tasks_completed": self.tasks_completed,
            "success_rate": self.success_rate,
            "learned_patterns": len(self.learned_patterns),
        }

    async def persist_state(self) -> None:
        """Persist current agent state to memory."""
        if self.memory:
            state_data = self.get_agent_state()
            await self.memory.remember_short_term(
                f"Agent state snapshot: {state_data}",
                tags=["state", "snapshot", self.agent_type],
            )

    async def recover_state(self) -> bool:
        """Attempt to recover previous state from memory."""
        if not self.memory:
            return False

        try:
            # Look for recent state snapshots
            memories = await self.memory.recall_memories(short_term_only=True, limit=10)

            for memory in memories:
                if "state snapshot" in memory.get("content", "").lower():
                    # Found a state snapshot - could extract and restore state
                    print("  🔄 Found previous state snapshot")
                    return True

            return False

        except Exception as e:
            print(f"  ⚠️ Failed to recover state: {e}")
            return False
