#!/usr/bin/env python3
"""
Simple wrapper for agents to interact with the memory system

This provides a simple API for agents to read/write memories without
needing to understand the full memory system implementation.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add memory_utils to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_interface import AgentMemoryInterface
from memory_manager import MemoryLevel


class AgentMemoryWrapper:
    """Simple wrapper for agent memory operations"""

    def __init__(self, agent_id: str, agent_type: str):
        """
        Initialize memory wrapper for an agent

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (e.g., 'orchestrator-agent')
        """
        self.interface = AgentMemoryInterface(agent_id, agent_type)

    def get_project_goals(self) -> List[str]:
        """Get current project goals from memory"""
        context = self.interface.get_project_context()
        if not context or not context.get("exists"):
            return []

        goals_section = context.get("sections", {}).get("Current Priorities", {})
        if hasattr(goals_section, "entries"):
            return [entry.content for entry in goals_section.entries]
        return []

    def get_workflow_practices(self) -> List[str]:
        """Get team workflow practices"""
        workflow = self.interface.get_team_workflow()
        if not workflow or not workflow.get("exists"):
            return []

        practices = []
        for section_name, section in workflow.get("sections", {}).items():
            if hasattr(section, "entries"):
                practices.extend(
                    [f"{section_name}: {entry.content}" for entry in section.entries]
                )
        return practices

    def record_accomplishment(self, description: str) -> bool:
        """Record an accomplishment in agent memory"""
        return self.interface.record_agent_memory("Accomplishments", description)

    def record_learning(self, topic: str, insight: str) -> bool:
        """Record a learning or insight"""
        return self.interface.record_agent_memory("Learnings", f"{topic}: {insight}")

    def record_error(
        self, error_type: str, description: str, solution: Optional[str] = None
    ) -> bool:
        """Record an error and its solution"""
        entry = f"{error_type}: {description}"
        if solution:
            entry += f" | Solution: {solution}"
        return self.interface.record_agent_memory("Error Patterns", entry)

    def search_memories(self, query: str) -> List[Dict[str, str]]:
        """Search across all accessible memories"""
        results = self.interface.search_accessible_memories(query)
        return [
            {"level": level, "file": filename, "match": match}
            for level, filename, match in results
        ]

    def get_my_memories(self) -> Dict[str, Any]:
        """Get all memories specific to this agent"""
        return self.interface.get_agent_memory()

    def can_modify_project_memory(self) -> bool:
        """Check if this agent can modify project-level memory"""
        return self.interface.can_write(MemoryLevel.PROJECT)

    def can_modify_team_memory(self) -> bool:
        """Check if this agent can modify team-level memory"""
        return self.interface.can_write(MemoryLevel.TEAM)


# Helper functions for common agent types
def get_orchestrator_memory() -> AgentMemoryWrapper:
    """Get memory wrapper for OrchestratorAgent"""
    return AgentMemoryWrapper("orchestrator", "orchestrator-agent")


def get_workflow_memory() -> AgentMemoryWrapper:
    """Get memory wrapper for WorkflowManager"""
    return AgentMemoryWrapper("workflow-manager", "workflow-manager")


def get_reviewer_memory() -> AgentMemoryWrapper:
    """Get memory wrapper for CodeReviewer"""
    return AgentMemoryWrapper("code-reviewer", "code-reviewer")


# Example usage
if __name__ == "__main__":
    # Example: OrchestratorAgent using memory
    orchestrator = get_orchestrator_memory()

    # Get project goals
    goals = orchestrator.get_project_goals()
    print("Project Goals:")
    for goal in goals[:3]:  # Show first 3
        print(f"  - {goal}")

    # Record an accomplishment
    success = orchestrator.record_accomplishment(
        "Successfully migrated to hierarchical memory system"
    )
    print(f"\nRecorded accomplishment: {success}")

    # Search memories
    results = orchestrator.search_memories("workflow")
    print(f"\nSearch results for 'workflow': {len(results)} matches")

    # Check permissions
    print(f"\nCan modify project memory: {orchestrator.can_modify_project_memory()}")
    print(f"Can modify team memory: {orchestrator.can_modify_team_memory()}")
