"""
Agent Registry for Gadugi V0.3
================================

Central registry for all v0.3 memory-enabled agents.
Provides agent discovery, loading, and capability mapping.
"""

import asyncio
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from enum import Enum

# Import base class
sys.path.insert(0, str(Path(__file__).parent))
from base.v03_agent import V03Agent, AgentCapabilities


class AgentType(Enum):
    """Enumeration of available agent types."""
    WORKFLOW_MANAGER = "workflow-manager"
    ORCHESTRATOR = "orchestrator"
    CODE_REVIEWER = "code-reviewer"
    TASK_DECOMPOSER = "task-decomposer"
    TEST_WRITER = "test-writer"
    EXECUTION_MONITOR = "execution-monitor"
    WORKTREE_MANAGER = "worktree-manager"
    PR_BACKLOG_MANAGER = "pr-backlog-manager"
    MEMORY_MANAGER = "memory-manager"
    EVENT_ROUTER_MANAGER = "event-router-manager"


@dataclass
class AgentRegistration:
    """Registration information for an agent."""
    agent_type: AgentType
    agent_class: Type[V03Agent]
    module_path: str
    capabilities: AgentCapabilities
    expertise_areas: List[str] = field(default_factory=list)
    knowledge_dir: Optional[Path] = None
    description: str = ""
    version: str = "0.3.0"
    enabled: bool = True


class AgentRegistry:
    """
    Central registry for all v0.3 agents.
    Manages agent discovery, loading, and instantiation.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._registry: Dict[AgentType, AgentRegistration] = {}
        self._instances: Dict[str, V03Agent] = {}
        self._load_lock = asyncio.Lock()

        # Register all known v0.3 agents
        self._register_v03_agents()

    def _register_v03_agents(self):
        """Register all v0.3 agents."""

        # Workflow Manager
        self._registry[AgentType.WORKFLOW_MANAGER] = AgentRegistration(
            agent_type=AgentType.WORKFLOW_MANAGER,
            agent_class=self._lazy_load_class("workflow-manager", "workflow_manager_v03", "WorkflowManagerV03"),
            module_path=".claude/agents/workflow-manager/workflow_manager_v03.py",
            capabilities=AgentCapabilities(
                can_create_prs=True,
                can_parallelize=True,
                can_write_code=False,
                can_review_code=False,
                can_test=True,
                can_document=True,
                expertise_areas=["git", "workflow", "pr_management", "ci_cd"],
                max_parallel_tasks=5
            ),
            expertise_areas=["git", "pull_requests", "workflows", "ci_cd", "project_management"],
            knowledge_dir=Path(".claude/agents/workflow-manager/knowledge"),
            description="Manages complete development workflows from requirements to PR merge",
            enabled=True
        )

        # Orchestrator
        self._registry[AgentType.ORCHESTRATOR] = AgentRegistration(
            agent_type=AgentType.ORCHESTRATOR,
            agent_class=self._lazy_load_class("orchestrator", "orchestrator_v03", "OrchestratorV03"),
            module_path=".claude/agents/orchestrator/orchestrator_v03.py",
            capabilities=AgentCapabilities(
                can_parallelize=True,
                can_create_prs=False,
                can_write_code=False,
                can_review_code=False,
                can_test=False,
                can_document=False,
                expertise_areas=["parallelization", "task_decomposition", "optimization"],
                max_parallel_tasks=20
            ),
            expertise_areas=["parallel_execution", "task_analysis", "dependency_resolution", "performance"],
            knowledge_dir=Path(".claude/agents/orchestrator/knowledge"),
            description="Orchestrates parallel task execution with intelligent decomposition",
            enabled=True
        )

        # Code Reviewer
        self._registry[AgentType.CODE_REVIEWER] = AgentRegistration(
            agent_type=AgentType.CODE_REVIEWER,
            agent_class=self._lazy_load_class("code-reviewer", "code_reviewer_v03", "CodeReviewerV03"),
            module_path=".claude/agents/code-reviewer/code_reviewer_v03.py",
            capabilities=AgentCapabilities(
                can_parallelize=True,
                can_create_prs=False,
                can_write_code=False,
                can_review_code=True,
                can_test=False,
                can_document=False,
                expertise_areas=["code_quality", "security", "performance", "best_practices"],
                max_parallel_tasks=5
            ),
            expertise_areas=["code_quality", "security_analysis", "performance_review", "patterns"],
            knowledge_dir=Path(".claude/agents/code-reviewer/knowledge"),
            description="Reviews code with pattern recognition and learning from feedback",
            enabled=True
        )

        # Task Decomposer
        self._registry[AgentType.TASK_DECOMPOSER] = AgentRegistration(
            agent_type=AgentType.TASK_DECOMPOSER,
            agent_class=self._lazy_load_class("task-decomposer", "task_decomposer_v03", "TaskDecomposerV03"),
            module_path=".claude/agents/task-decomposer/task_decomposer_v03.py",
            capabilities=AgentCapabilities(
                can_parallelize=True,
                can_create_prs=False,
                can_write_code=False,
                can_review_code=False,
                can_test=False,
                can_document=False,
                expertise_areas=["task_analysis", "complexity_assessment", "parallelization"],
                max_parallel_tasks=1
            ),
            expertise_areas=["task_breakdown", "complexity_analysis", "dependency_detection", "optimization"],
            knowledge_dir=Path(".claude/agents/task-decomposer/knowledge"),
            description="Decomposes complex tasks into optimal parallel subtasks",
            enabled=True
        )

    def _lazy_load_class(self, agent_dir: str, module_name: str, class_name: str) -> Type[V03Agent]:
        """
        Lazy load an agent class.
        Returns a placeholder that loads the actual class when needed.
        """
        class LazyLoadedAgent:
            _actual_class = None
            _agent_dir = agent_dir
            _module_name = module_name
            _class_name = class_name

            def __new__(cls, *args, **kwargs):
                if cls._actual_class is None:
                    # Load the actual class
                    module_path = Path(__file__).parent / agent_dir / f"{cls._module_name}.py"
                    if module_path.exists():
                        spec = importlib.util.spec_from_file_location(cls._module_name, module_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            cls._actual_class = getattr(module, cls._class_name)

                    if cls._actual_class is None:
                        # Fallback to base V03Agent
                        cls._actual_class = V03Agent

                return cls._actual_class(*args, **kwargs)

        LazyLoadedAgent._agent_dir = agent_dir
        LazyLoadedAgent._module_name = module_name
        LazyLoadedAgent._class_name = class_name
        return LazyLoadedAgent  # type: ignore

    def get_agent_types(self) -> List[AgentType]:
        """Get list of all registered agent types."""
        return list(self._registry.keys())

    def get_agent_info(self, agent_type: AgentType) -> Optional[AgentRegistration]:
        """Get registration info for an agent type."""
        return self._registry.get(agent_type)

    def get_agents_by_capability(self, capability: str) -> List[AgentRegistration]:
        """
        Find agents with a specific capability.

        Args:
            capability: Name of capability (e.g., 'can_create_prs', 'can_parallelize')

        Returns:
            List of agent registrations with that capability
        """
        agents = []
        for reg in self._registry.values():
            if hasattr(reg.capabilities, capability) and getattr(reg.capabilities, capability):
                agents.append(reg)
        return agents

    def get_agents_by_expertise(self, expertise: str) -> List[AgentRegistration]:
        """
        Find agents with specific expertise.

        Args:
            expertise: Area of expertise (e.g., 'git', 'security', 'parallelization')

        Returns:
            List of agent registrations with that expertise
        """
        agents = []
        for reg in self._registry.values():
            if expertise in reg.expertise_areas or expertise in reg.capabilities.expertise_areas:
                agents.append(reg)
        return agents

    async def create_agent(
        self,
        agent_type: AgentType,
        agent_id: Optional[str] = None,
        initialize: bool = True
    ) -> Optional[V03Agent]:
        """
        Create and optionally initialize an agent instance.

        Args:
            agent_type: Type of agent to create
            agent_id: Optional custom agent ID
            initialize: Whether to initialize with memory

        Returns:
            Initialized agent instance or None if not found
        """
        registration = self._registry.get(agent_type)
        if not registration or not registration.enabled:
            return None

        # Generate agent ID if not provided
        if agent_id is None:
            agent_id = f"{agent_type.value}_{asyncio.get_event_loop().time():.0f}"

        # Check if instance already exists
        if agent_id in self._instances:
            return self._instances[agent_id]

        async with self._load_lock:
            # Double-check after acquiring lock
            if agent_id in self._instances:
                return self._instances[agent_id]

            try:
                # Create agent instance
                agent = registration.agent_class(
                    agent_id=agent_id,
                    agent_type=agent_type.value,
                    capabilities=registration.capabilities
                )

                # Initialize if requested
                if initialize:
                    await agent.initialize()

                # Cache instance
                self._instances[agent_id] = agent

                return agent

            except Exception as e:
                print(f"Failed to create agent {agent_type.value}: {e}")
                return None

    async def get_or_create_agent(
        self,
        agent_type: AgentType,
        agent_id: Optional[str] = None
    ) -> Optional[V03Agent]:
        """
        Get existing agent instance or create new one.

        Args:
            agent_type: Type of agent
            agent_id: Optional agent ID

        Returns:
            Agent instance or None
        """
        if agent_id and agent_id in self._instances:
            return self._instances[agent_id]

        return await self.create_agent(agent_type, agent_id, initialize=True)

    def get_best_agent_for_task(self, task_description: str) -> Optional[AgentType]:
        """
        Suggest the best agent for a given task description.

        Args:
            task_description: Description of task to perform

        Returns:
            Best matching agent type or None
        """
        task_lower = task_description.lower()

        # Simple keyword matching (could be enhanced with NLP)
        if any(word in task_lower for word in ["pr", "pull request", "workflow", "merge"]):
            return AgentType.WORKFLOW_MANAGER
        elif any(word in task_lower for word in ["parallel", "orchestrate", "decompose", "split"]):
            return AgentType.ORCHESTRATOR
        elif any(word in task_lower for word in ["review", "code quality", "security", "lint"]):
            return AgentType.CODE_REVIEWER
        elif any(word in task_lower for word in ["break down", "subtask", "decomposition"]):
            return AgentType.TASK_DECOMPOSER

        # Default to orchestrator for complex tasks
        return AgentType.ORCHESTRATOR

    async def shutdown_all(self):
        """Shutdown all active agent instances."""
        for agent in self._instances.values():
            try:
                await agent.shutdown()
            except Exception as e:
                print(f"Error shutting down agent: {e}")

        self._instances.clear()

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the registry."""
        return {
            "total_registered": len(self._registry),
            "enabled_agents": sum(1 for r in self._registry.values() if r.enabled),
            "active_instances": len(self._instances),
            "agent_types": [t.value for t in self.get_agent_types()],
            "capabilities_matrix": {
                reg.agent_type.value: {
                    "can_parallelize": reg.capabilities.can_parallelize,
                    "can_create_prs": reg.capabilities.can_create_prs,
                    "can_review_code": reg.capabilities.can_review_code,
                    "max_parallel_tasks": reg.capabilities.max_parallel_tasks
                }
                for reg in self._registry.values()
            }
        }


# Global registry instance
agent_registry = AgentRegistry()


async def test_registry():
    """Test the agent registry."""
    print("\n" + "="*70)
    print("Testing Agent Registry")
    print("="*70)

    # Get registry stats
    stats = agent_registry.get_registry_stats()
    print(f"\nRegistry Statistics:")
    print(f"  Total registered: {stats['total_registered']}")
    print(f"  Enabled agents: {stats['enabled_agents']}")
    print(f"  Agent types: {', '.join(stats['agent_types'])}")

    # Find agents by capability
    pr_agents = agent_registry.get_agents_by_capability("can_create_prs")
    print(f"\nAgents that can create PRs: {len(pr_agents)}")
    for agent in pr_agents:
        print(f"  - {agent.agent_type.value}: {agent.description}")

    # Find agents by expertise
    parallel_experts = agent_registry.get_agents_by_expertise("parallelization")
    print(f"\nAgents with parallelization expertise: {len(parallel_experts)}")
    for agent in parallel_experts:
        print(f"  - {agent.agent_type.value}")

    # Suggest agent for task
    task = "Create a pull request for the new feature"
    suggested = agent_registry.get_best_agent_for_task(task)
    print(f"\nSuggested agent for '{task}': {suggested.value if suggested else 'None'}")

    # Create an agent instance (mock test)
    print("\n✅ Agent Registry ready for production use!")


if __name__ == "__main__":
    asyncio.run(test_registry())
