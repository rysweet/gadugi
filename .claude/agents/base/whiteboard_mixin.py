"""
Whiteboard Collaboration Mixin for V03Agent
===========================================

This mixin handles all whiteboard-related functionality including:
- Whiteboard system initialization
- Task whiteboard setup and management
- Collaboration via whiteboards
- Whiteboard discovery and management
- Progress tracking on whiteboards
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING, runtime_checkable

from .whiteboard_collaboration import WhiteboardManager, SharedWhiteboard, AccessLevel, WhiteboardType

if TYPE_CHECKING:
    from ...shared.memory_integration import AgentMemoryInterface
    from .v03_agent import AgentCapabilities


@runtime_checkable
class WhiteboardMixinHost(Protocol):
    """Protocol defining the interface expected by WhiteboardMixin from its host class."""

    # Required attributes from V03Agent
    agent_id: str
    agent_type: str
    capabilities: 'AgentCapabilities'
    memory: Optional['AgentMemoryInterface']
    current_task_id: Optional[str]
    whiteboard_manager: Optional[WhiteboardManager]
    current_whiteboards: Dict[str, SharedWhiteboard]


class WhiteboardMixin:
    """
    Mixin providing whiteboard collaboration capabilities for V03Agent.

    This mixin requires the host class to implement the WhiteboardMixinHost protocol.
    """

    async def _initialize_whiteboard_system(self: WhiteboardMixinHost) -> None:
        """Initialize the whiteboard collaboration system."""
        try:
            self.whiteboard_manager = WhiteboardManager()
            await self.whiteboard_manager.initialize()
            print(f"  📋 Whiteboard system initialized for {self.agent_id}")
        except Exception as e:
            print(f"  ⚠️ Whiteboard system initialization failed: {e}")
            self.whiteboard_manager = None

    async def _setup_task_whiteboard(self: WhiteboardMixinHost, task_description: str) -> None:
        """Set up whiteboard for the current task."""
        if not self.whiteboard_manager or not self.current_task_id:
            return

        try:
            # Try to find existing whiteboard for this task
            existing = self.whiteboard_manager.find_whiteboards()

            # Filter for task-related whiteboards
            task_whiteboards = [
                wb for wb in existing
                if hasattr(wb, 'metadata') and wb.metadata and wb.metadata.get('task_id') == self.current_task_id
            ]

            if task_whiteboards:
                # Join existing whiteboard
                whiteboard = task_whiteboards[0]
                whiteboard_id = whiteboard.whiteboard_id
                self.current_whiteboards[self.current_task_id] = whiteboard
                print(f"  📋 Joined existing whiteboard: {whiteboard_id}")
                return

            # Create new task coordination whiteboard
            wb = await self.whiteboard_manager.create_whiteboard(
                whiteboard_type=WhiteboardType.TASK_COORDINATION,
                owner_agent=self.agent_id,
                metadata={
                    "task_id": self.current_task_id,
                    "task_description": task_description
                }
            )
            whiteboard_id = wb.whiteboard_id

            # Get the whiteboard directly from manager
            whiteboard = self.whiteboard_manager.get_whiteboard(whiteboard_id)

            if whiteboard:
                self.current_whiteboards[self.current_task_id] = whiteboard

                # Initialize whiteboard with task info
                await whiteboard.write(self.agent_id, "task_overview.description", {"value": task_description})
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

    async def collaborate(self: WhiteboardMixinHost, message: str, decision: Optional[str] = None) -> None:
        """Collaborate with other agents via whiteboard."""
        if self.current_task_id and self.current_task_id in self.current_whiteboards:
            whiteboard = self.current_whiteboards[self.current_task_id]

            try:
                # Add communication to whiteboard
                comms_data = await whiteboard.read(self.agent_id, "communications") or {}
                current_comms = comms_data.get("messages", []) if isinstance(comms_data, dict) else []
                current_comms.append({
                    "message": message,
                    "from": self.agent_id,
                    "agent_type": self.agent_type,
                    "timestamp": datetime.now().isoformat(),
                    "type": "message"
                })
                await whiteboard.write(self.agent_id, "communications", {"messages": current_comms})

                # Add decision if provided
                if decision:
                    decisions_data = await whiteboard.read(self.agent_id, "decisions") or {}
                    current_decisions = decisions_data.get("decisions", []) if isinstance(decisions_data, dict) else []
                    current_decisions.append({
                        "decision": decision,
                        "reasoning": message,
                        "decided_by": self.agent_id,
                        "agent_type": self.agent_type,
                        "timestamp": datetime.now().isoformat()
                    })
                    await whiteboard.write(self.agent_id, "decisions", {"decisions": current_decisions})

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

    async def create_design_whiteboard(self: WhiteboardMixinHost, problem_statement: str, project_id: Optional[str] = None) -> Optional[str]:
        """Create a design decision whiteboard."""
        if not self.whiteboard_manager:
            return None

        try:
            # Create whiteboard with proper parameters
            wb = await self.whiteboard_manager.create_whiteboard(
                whiteboard_type=WhiteboardType.DESIGN_DECISION,
                owner_agent=self.agent_id,
                metadata={
                    "name": f"Design Decision: {problem_statement[:50]}...",
                    "task_id": self.current_task_id,
                    "project_id": project_id,
                    "template_id": "design_decision"
                }
            )
            whiteboard_id = wb.whiteboard_id

            whiteboard = self.whiteboard_manager.get_whiteboard(whiteboard_id)
            if whiteboard:
                await whiteboard.write(self.agent_id, "problem_statement", {"content": problem_statement})
                print(f"  📋 Created design whiteboard: {whiteboard_id}")
                return whiteboard_id

        except Exception as e:
            print(f"  ⚠️ Failed to create design whiteboard: {e}")

        return None

    async def create_problem_solving_whiteboard(self: WhiteboardMixinHost, problem_description: str) -> Optional[str]:
        """Create a problem solving whiteboard."""
        if not self.whiteboard_manager:
            return None

        try:
            # Create whiteboard with proper parameters
            wb = await self.whiteboard_manager.create_whiteboard(
                whiteboard_type=WhiteboardType.PROBLEM_SOLVING,
                owner_agent=self.agent_id,
                metadata={
                    "name": f"Problem: {problem_description[:50]}...",
                    "task_id": self.current_task_id,
                    "template_id": "problem_solving"
                }
            )
            whiteboard_id = wb.whiteboard_id

            whiteboard = self.whiteboard_manager.get_whiteboard(whiteboard_id)
            if whiteboard:
                await whiteboard.write(self.agent_id, "problem_definition.description", {"content": problem_description})
                print(f"  📋 Created problem-solving whiteboard: {whiteboard_id}")
                return whiteboard_id

        except Exception as e:
            print(f"  ⚠️ Failed to create problem-solving whiteboard: {e}")

        return None

    async def invite_agent_to_whiteboard(self: WhiteboardMixinHost, whiteboard_id: str, agent_id: str, permission: AccessLevel) -> bool:
        """Invite another agent to a whiteboard."""
        if not self.whiteboard_manager:
            return False

        try:
            whiteboard = self.whiteboard_manager.get_whiteboard(whiteboard_id)
            if whiteboard:
                # grant_access is not async and takes only 2 params
                whiteboard.grant_access(agent_id, permission)
                success = True
                if success:
                    print(f"  📋 Granted {permission.value} access to {agent_id} for whiteboard {whiteboard_id}")
                return success

        except Exception as e:
            print(f"  ⚠️ Failed to invite agent to whiteboard: {e}")

        return False

    async def discover_relevant_whiteboards(self: WhiteboardMixinHost, limit: int = 10) -> List[Dict[str, Any]]:
        """Discover whiteboards relevant to current agent and task."""
        if not self.whiteboard_manager:
            return []

        try:
            # Search by current task
            relevant: List[Dict[str, Any]] = []

            # Get all whiteboards and filter
            all_whiteboards = self.whiteboard_manager.find_whiteboards(
                accessible_by=self.agent_id
            )

            # Filter for task-related whiteboards
            if self.current_task_id:
                for wb in all_whiteboards:
                    if hasattr(wb, 'metadata') and wb.metadata and wb.metadata.get('task_id') == self.current_task_id:
                        relevant.append({
                            'whiteboard_id': wb.whiteboard_id,
                            'type': wb.whiteboard_type.value,
                            'owner': wb.owner_agent,
                            'metadata': wb.metadata
                        })

            # Filter by expertise areas
            for expertise in self.capabilities.expertise_areas:
                for wb in all_whiteboards:
                    if hasattr(wb, 'metadata') and wb.metadata and wb.metadata.get('template_category') == expertise:
                        wb_dict = {
                            'whiteboard_id': wb.whiteboard_id,
                            'type': wb.whiteboard_type.value,
                            'owner': wb.owner_agent,
                            'metadata': wb.metadata
                        }
                        if wb_dict not in relevant:
                            relevant.append(wb_dict)

            # Limit results
            return relevant[:limit]

        except Exception as e:
            print(f"  ⚠️ Failed to discover whiteboards: {e}")
            return []

    async def get_whiteboard_summary(self: WhiteboardMixinHost, whiteboard_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of whiteboard content."""
        if not self.whiteboard_manager:
            return None

        try:
            whiteboard = self.whiteboard_manager.get_whiteboard(whiteboard_id)
            if whiteboard:
                # Get whiteboard metadata directly from attributes
                content = await whiteboard.read(self.agent_id)

                info = {
                    "whiteboard_id": whiteboard.whiteboard_id,
                    "type": whiteboard.whiteboard_type.value,
                    "owner": whiteboard.owner_agent,
                    "created_at": whiteboard.created_at.isoformat() if hasattr(whiteboard, 'created_at') else None,
                    "last_modified": whiteboard.last_modified.isoformat() if hasattr(whiteboard, 'last_modified') else None,
                    "metadata": getattr(whiteboard, 'metadata', {})
                }

                return {
                    "info": info,
                    "content_summary": {
                        "keys": list(content.keys()) if content else [],
                        "size": len(str(content)) if content else 0,
                        "last_update": info.get("last_modified")
                    }
                }

        except Exception as e:
            print(f"  ⚠️ Failed to get whiteboard summary: {e}")

        return None

    async def update_task_progress(self: WhiteboardMixinHost, completed_steps: List[str], current_step: str, blocked_items: Optional[List[str]] = None) -> None:
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

    async def report_issue(self: WhiteboardMixinHost, issue_description: str, severity: str = "medium") -> None:
        """Report an issue to the task whiteboard."""
        if not self.current_task_id or self.current_task_id not in self.current_whiteboards:
            return

        try:
            whiteboard = self.current_whiteboards[self.current_task_id]
            issues_data = await whiteboard.read(self.agent_id, "issues") or {}

            # Ensure we have a list of issues
            if isinstance(issues_data, dict):
                current_issues = issues_data.get("issues", [])
            elif isinstance(issues_data, list):
                current_issues = issues_data
            else:
                current_issues = []

            new_issue = {
                "issue": issue_description,
                "severity": severity,
                "reported_by": self.agent_id,
                "agent_type": self.agent_type,
                "timestamp": datetime.now().isoformat(),
                "status": "open"
            }

            current_issues.append(new_issue)
            await whiteboard.write(self.agent_id, "issues", {"issues": current_issues})
            print(f"  📋 Reported issue to whiteboard: {issue_description}")

        except Exception as e:
            print(f"  ⚠️ Failed to report issue: {e}")
