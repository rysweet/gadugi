from typing import Any, Dict, List, Optional

import logging
import sys

#!/usr/bin/env python3
"""
Agent Integration Helpers for Simple Memory Manager

This module provides helper functions and patterns for integrating all agents
with the GitHub Issues-only memory management system, replacing Memory.md operations.
"""

from pathlib import Path

# Add path for SimpleMemoryManager import
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from simple_memory_manager import SimpleMemoryManager


class AgentMemoryIntegration:
    """
    Helper class for agent memory operations using GitHub Issues.

    This replaces all Memory.md file operations with GitHub Issues API calls,
    providing a consistent interface for all agents.
    """

    def __init__(self, agent_name: str, repo_path: Optional[str] = None):
        """
        Initialize agent memory integration.

        Args:
            agent_name: Name of the agent (e.g., 'WorkflowManager', 'OrchestratorAgent')
            repo_path: Path to repository (defaults to current directory)
        """
        self.agent_name = agent_name
        self.repo_path = repo_path
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")

        # Initialize memory manager
        self.memory = SimpleMemoryManager(repo_path)

    def update_current_goals(
        self,
        goals: List[str],
        priority: str = "high",
        related_issues: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Update current project goals"""
        content = "\n".join([f"- {goal}" for goal in goals])

        return self.memory.update_memory(
            content=content,
            section="current-goals",
            agent=self.agent_name,
            priority=priority,
            related_issues=related_issues,
        )

    def add_completed_task(
        self,
        task_description: str,
        details: Optional[str] = None,
        related_issues: Optional[List[int]] = None,
        related_prs: Optional[List[int]] = None,
        related_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Add completed task to memory"""
        content = f"**Task**: {task_description}"
        if details:
            content += f"\n\n**Details**: {details}"

        return self.memory.update_memory(
            content=content,
            section="completed-tasks",
            agent=self.agent_name,
            priority="medium",
            related_issues=related_issues,
            related_prs=related_prs,
            related_files=related_files,
        )

    def add_important_context(
        self,
        context: str,
        priority: str = "high",
        related_issues: Optional[List[int]] = None,
        related_commits: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Add important architectural or technical context"""
        return self.memory.update_memory(
            content=context,
            section="important-context",
            agent=self.agent_name,
            priority=priority,
            related_issues=related_issues,
            related_commits=related_commits,
        )

    def add_next_steps(
        self,
        steps: List[str],
        priority: str = "medium",
        related_issues: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Add next steps or future work items"""
        content = "\n".join([f"- {step}" for step in steps])

        return self.memory.update_memory(
            content=content,
            section="next-steps",
            agent=self.agent_name,
            priority=priority,
            related_issues=related_issues,
        )

    def add_reflection(
        self, insight: str, category: str = "general", priority: str = "low"
    ) -> Dict[str, Any]:
        """Add learning or insights for future improvements"""
        content = f"**Category**: {category}\n\n{insight}"

        return self.memory.update_memory(
            content=content,
            section="reflections",
            agent=self.agent_name,
            priority=priority,
        )

    def read_current_goals(self) -> List[Dict[str, Any]]:
        """Read current project goals"""
        memory_data = self.memory.read_memory(section="current-goals")
        return memory_data.get("filtered_section", [])

    def read_recent_accomplishments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Read recent completed tasks"""
        memory_data = self.memory.read_memory(section="completed-tasks", limit=limit)
        return memory_data.get("filtered_section", [])

    def read_important_context(self) -> List[Dict[str, Any]]:
        """Read important context and decisions"""
        memory_data = self.memory.read_memory(section="important-context")
        return memory_data.get("filtered_section", [])

    def search_memory(
        self, query: str, section: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search memory for specific content"""
        result = self.memory.search_memory(query, section)
        return result.get("results", []) if result.get("success") else []

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of current memory state"""
        status = self.memory.get_memory_status()
        if not status.get("success"):
            return {"error": status.get("error", "Failed to get memory status")}

        return {
            "memory_issue_number": status["memory_issue"]["number"],
            "memory_issue_url": status["memory_issue"]["url"],
            "total_memory_entries": status["memory_content"]["total_comments"],
            "sections": status["memory_content"]["sections"],
            "section_counts": status["memory_content"]["section_counts"],
            "last_updated": status["memory_content"]["last_updated"],
        }


class WorkflowManagerMemoryMixin:
    """
    Mixin class for WorkflowManager memory integration.

    This replaces the old Memory.md update patterns with GitHub Issues operations.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_agent = AgentMemoryIntegration("WorkflowManager")

    def update_workflow_progress(
        self,
        phase: str,
        description: str,
        issue_number: Optional[int] = None,
        pr_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update memory with workflow progress"""

        related_issues = [issue_number] if issue_number else None
        related_prs = [pr_number] if pr_number else None

        return self.memory_agent.add_completed_task(
            task_description=f"Workflow Phase {phase}",
            details=description,
            related_issues=related_issues,
            related_prs=related_prs,
        )

    def record_implementation_details(
        self,
        feature: str,
        files_modified: List[str],
        technical_notes: str,
        pr_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Record technical implementation details"""
        content = f"**Feature**: {feature}\n"
        content += f"**Files Modified**: {', '.join(files_modified)}\n\n"
        content += f"**Technical Notes**: {technical_notes}"

        return self.memory_agent.add_important_context(
            context=content,
            related_prs=[pr_number] if pr_number else None,
            related_files=files_modified,
        )

    def capture_workflow_insights(self, insights: List[str]) -> Dict[str, Any]:
        """Capture insights from workflow execution"""
        return self.memory_agent.add_reflection(
            insight="\n".join([f"- {insight}" for insight in insights]),
            category="workflow-execution",
        )


class OrchestratorAgentMemoryMixin:
    """
    Mixin class for OrchestratorAgent memory integration.

    Handles memory coordination across parallel task execution.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_agent = AgentMemoryIntegration("OrchestratorAgent")

    def record_orchestration_start(
        self, task_count: int, tasks: List[str], orchestration_id: str
    ) -> Dict[str, Any]:
        """Record start of parallel orchestration"""
        content = f"**Orchestration ID**: {orchestration_id}\n"
        content += f"**Task Count**: {task_count}\n"
        content += "**Tasks**:\n" + "\n".join([f"- {task}" for task in tasks])

        return self.memory_agent.add_important_context(context=content, priority="high")

    def record_orchestration_results(
        self,
        orchestration_id: str,
        successful_tasks: int,
        failed_tasks: int,
        performance_metrics: Dict[str, Any],
        created_prs: List[int],
    ) -> Dict[str, Any]:
        """Record orchestration completion results"""
        content = f"**Orchestration ID**: {orchestration_id}\n"
        content += (
            f"**Success Rate**: {successful_tasks}/{successful_tasks + failed_tasks}\n"
        )
        content += (
            f"**Performance**: {performance_metrics.get('total_time', 'N/A')} seconds\n"
        )
        content += f"**Speedup**: {performance_metrics.get('speedup_factor', 'N/A')}x\n"
        if created_prs:
            content += f"**Created PRs**: {', '.join([f'#{pr}' for pr in created_prs])}"

        return self.memory_agent.add_completed_task(
            task_description=f"Parallel Orchestration ({orchestration_id})",
            details=content,
            related_prs=created_prs,
        )

    def record_performance_insights(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Record performance optimization insights"""
        content = "**Parallel Execution Insights**:\n"
        for key, value in insights.items():
            content += f"- **{key}**: {value}\n"

        return self.memory_agent.add_reflection(
            insight=content, category="performance-optimization", priority="medium"
        )


class CodeReviewerMemoryMixin:
    """
    Mixin class for Code-Reviewer memory integration.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_agent = AgentMemoryIntegration("Code-Reviewer")

    def record_review_insights(
        self,
        pr_number: int,
        review_summary: str,
        key_findings: List[str],
        recommendations: List[str],
    ) -> Dict[str, Any]:
        """Record code review insights"""
        content = f"**PR**: #{pr_number}\n"
        content += f"**Summary**: {review_summary}\n\n"
        content += "**Key Findings**:\n" + "\n".join(
            [f"- {finding}" for finding in key_findings]
        )
        content += "\n\n**Recommendations**:\n" + "\n".join(
            [f"- {rec}" for rec in recommendations]
        )

        return self.memory_agent.add_important_context(
            context=content, related_prs=[pr_number], priority="medium"
        )

    def record_architectural_patterns(
        self, patterns: List[str], pr_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Record architectural patterns observed during review"""
        content = "**Architectural Patterns Observed**:\n"
        content += "\n".join([f"- {pattern}" for pattern in patterns])

        return self.memory_agent.add_reflection(
            insight=content, category="architectural-patterns", priority="medium"
        )


def create_agent_memory_helper(
    agent_name: str, repo_path: Optional[str] = None
) -> AgentMemoryIntegration:
    """
    Factory function to create agent memory integration helper.

    Args:
        agent_name: Name of the agent
        repo_path: Path to repository

    Returns:
        AgentMemoryIntegration instance configured for the agent
    """
    return AgentMemoryIntegration(agent_name, repo_path)


def migrate_memory_md_to_github(
    memory_md_path: str, agent_name: str = "MigrationTool"
) -> Dict[str, Any]:
    """
    Utility function to migrate existing Memory.md content to GitHub Issues.

    Args:
        memory_md_path: Path to existing Memory.md file
        agent_name: Name of agent performing migration

    Returns:
        Migration results
    """
    try:
        memory_path = Path(memory_md_path)
        if not memory_path.exists():
            return {
                "success": False,
                "error": f"Memory.md file not found at {memory_md_path}",
            }

        # Initialize memory agent
        memory_agent = AgentMemoryIntegration(agent_name)

        # Read Memory.md content
        with open(memory_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse Memory.md sections (simplified parsing)
        sections = {
            "current-goals": [],
            "completed-tasks": [],
            "important-context": [],
            "next-steps": [],
            "reflections": [],
        }

        current_section = None
        current_content = []

        for line in content.split("\n"):
            line = line.strip()

            # Check for section headers
            if line.startswith("## Current Goals") or "current goals" in line.lower():
                current_section = "current-goals"
                current_content = []
            elif (
                line.startswith("## Recent Accomplishments")
                or "accomplishments" in line.lower()
            ):
                current_section = "completed-tasks"
                current_content = []
            elif (
                line.startswith("## Important Context")
                or "important context" in line.lower()
            ):
                current_section = "important-context"
                current_content = []
            elif line.startswith("## Next Steps") or "next steps" in line.lower():
                current_section = "next-steps"
                current_content = []
            elif line.startswith("## Reflections") or "reflections" in line.lower():
                current_section = "reflections"
                current_content = []
            elif line.startswith("##"):
                # End of tracked sections
                if current_section and current_content:
                    sections[current_section].append("\n".join(current_content))
                current_section = None
                current_content = []
            elif current_section and line:
                current_content.append(line)

        # Add final section if exists
        if current_section and current_content:
            sections[current_section].append("\n".join(current_content))

        # Migrate each section to GitHub Issues
        migration_results = {"success": True, "migrated_sections": {}, "errors": []}

        for section_name, section_content_list in sections.items():
            if section_content_list:
                # Combine all content for this section
                combined_content = "\n\n".join(section_content_list)

                if combined_content.strip():
                    result = memory_agent.memory.update_memory(
                        content=combined_content,
                        section=section_name,
                        agent=f"{agent_name} (Migration)",
                        priority="medium",
                    )

                    if result.get("success"):
                        migration_results["migrated_sections"][section_name] = {
                            "content_length": len(combined_content),
                            "comment_id": result.get("comment_id"),
                        }
                    else:
                        migration_results["errors"].append(
                            f"Failed to migrate {section_name}: {result.get('error')}"
                        )

        if migration_results["errors"]:
            migration_results["success"] = False

        return migration_results

    except Exception as e:
        return {"success": False, "error": f"Migration failed: {str(e)}"}


# Convenience functions for common memory operations
def quick_update_goals(goals: List[str], agent_name: str = "QuickUpdate") -> bool:
    """Quickly update current goals"""
    memory = AgentMemoryIntegration(agent_name)
    result = memory.update_current_goals(goals)
    return result.get("success", False)


def quick_add_accomplishment(
    task: str, agent_name: str = "QuickUpdate", pr_number: Optional[int] = None
) -> bool:
    """Quickly add accomplished task"""
    memory = AgentMemoryIntegration(agent_name)
    result = memory.add_completed_task(
        task, related_prs=[pr_number] if pr_number else None
    )
    return result.get("success", False)


def quick_search_memory(query: str) -> List[str]:
    """Quick memory search returning content strings"""
    memory = AgentMemoryIntegration("QuickSearch")
    results = memory.search_memory(query)
    return [result.get("content", "") for result in results]
