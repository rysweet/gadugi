"""Main Orchestrator implementation with parallel execution support."""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path  # type: ignore
from typing import Any, Dict, List, Optional, Tuple, Tuple  # type: ignore

from ...framework import BaseAgent, AgentMetadata, AgentResponse
from ...services.event_router import EventRouter, Event, EventType, EventPriority  # type: ignore

# Placeholder types for missing memory system (services not available in this context)
class MemorySystem:
    """Placeholder for MemorySystem."""
    def __init__(self) -> None:
        pass

class Memory:
    """Placeholder for Memory."""
    def __init__(self, type: Optional[str] = None, content: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.type = type
        self.content = content
        self.metadata = metadata or {}

class MemoryType:
    """Placeholder for MemoryType."""
    TASK = "task"
    RESULT = "result"
    ACHIEVEMENT = "achievement"
from .parallel_executor import ParallelExecutor, ExecutionMode
from .task_analyzer import TaskAnalyzer, TaskDependency  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class TaskDefinition:
    """Definition of a task to be executed."""

    id: str
    name: str
    description: str
    agent_type: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0  # Higher = more important
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3

    def __hash__(self) -> int:
        """Make hashable for use in sets."""
        return hash(self.id)


@dataclass
class ExecutionPlan:
    """Execution plan for parallel task processing."""

    id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    tasks: List[TaskDefinition] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    execution_order: List[List[str]] = field(default_factory=list)  # Batches of parallel tasks
    max_parallel: int = 4
    created_at: datetime = field(default_factory=datetime.now)

    def add_task(self, task: TaskDefinition) -> None:
        """Add a task to the execution plan."""
        self.tasks.append(task)
        self.dependency_graph[task.id] = task.dependencies

    def compute_execution_order(self) -> None:
        """Compute the optimal execution order based on dependencies."""
        # Topological sort with level-based batching
        in_degree = {task.id: 0 for task in self.tasks}

        for task_id, deps in self.dependency_graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Find tasks with no dependencies (can start immediately)
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        self.execution_order = []

        while queue:
            # Current batch (can be executed in parallel)
            batch = queue[:]
            self.execution_order.append(batch)
            queue = []

            # Process batch and find next level
            for task_id in batch:
                for dependent_id, deps in self.dependency_graph.items():
                    if task_id in deps:
                        in_degree[dependent_id] -= 1
                        if in_degree[dependent_id] == 0:
                            queue.append(dependent_id)


@dataclass
class ExecutionResult:
    """Result of task execution."""

    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    retries: int = 0

    def complete(self, success: bool, result: Any = None, error: Optional[str] = None) -> None:
        """Mark execution as complete."""
        self.success = success
        self.result = result
        self.error = error
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()


class Orchestrator(BaseAgent):
    """Orchestrator agent for coordinating parallel task execution.

    GOVERNANCE REQUIREMENT (Issue #148):
    The Orchestrator MUST delegate ALL task execution to WorkflowManager instances.
    Direct task execution is PROHIBITED to ensure complete 11-phase workflow execution.

    Each task is:
    1. Assigned to a dedicated worktree for isolation
    2. Delegated to a WorkflowManager subprocess via 'claude -p'
    3. Executed through the complete 11-phase workflow
    4. Monitored for successful completion of all phases
    """

    def __init__(
        self,
        event_router: Optional[EventRouter] = None,
        memory_system: Optional[MemorySystem] = None,
        max_parallel_tasks: int = 4,
        enable_worktrees: bool = True,
    ):
        """Initialize the Orchestrator.

        GOVERNANCE: All task execution MUST be delegated to WorkflowManager.
        The orchestrator only coordinates and monitors WorkflowManager instances.

        Args:
            event_router: Event router service
            memory_system: Memory system service
            max_parallel_tasks: Maximum parallel task execution
            enable_worktrees: Whether to use git worktrees for isolation
        """
        # Create metadata
        metadata = AgentMetadata(
            name="Orchestrator",
            version="2.0.0",
            description="Coordinates parallel execution of agents and tasks",
            tools=[
                {"name": "shell_command", "required": True},
                {"name": "file_reader", "required": True},
            ],
            events={
                "subscribes": [
                    "orchestration.requested",
                    "task.completed",
                    "task.failed",
                ],
                "publishes": [
                    "orchestration.started",
                    "orchestration.completed",
                    "task.assigned",
                ],
            },
            settings={
                "max_parallel_tasks": max_parallel_tasks,
                "enable_worktrees": enable_worktrees,
            },
        )

        super().__init__(
            metadata=metadata,
            event_router=event_router,
            memory_system=memory_system,
        )

        # Initialize components
        self.parallel_executor = ParallelExecutor(
            max_workers=max_parallel_tasks,
            enable_worktrees=enable_worktrees,
        )
        self.task_analyzer = TaskAnalyzer()

        # Execution state
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.execution_results: Dict[str, List[ExecutionResult]] = {}
        self._execution_lock = asyncio.Lock()

    async def init(self) -> None:
        """Initialize orchestrator resources."""
        logger.info("Initializing Orchestrator")

        # Initialize executor
        await self.parallel_executor.initialize()

        # Load any saved state
        await self.load_state()

        self.state["initialized"] = True
        self.state["total_tasks_executed"] = 0
        self.state["total_plans_executed"] = 0

    async def process(self, event: Event) -> AgentResponse:
        """Process orchestration events.

        Args:
            event: Event to process

        Returns:
            Processing response
        """
        try:
            if event.type == "orchestration.requested":
                return await self._handle_orchestration_request(event.data)

            elif event.type == "task.completed":
                return await self._handle_task_completion(event.data)

            elif event.type == "task.failed":
                return await self._handle_task_failure(event.data)

            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown event type: {event.type}",
                )

        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
            )

    async def _handle_orchestration_request(self, data: Dict[str, Any]) -> AgentResponse:
        """Handle orchestration request."""
        # Parse task definitions
        task_defs = data.get("tasks", [])
        if not task_defs:
            return AgentResponse(
                success=False,
                error="No tasks provided",
            )

        # Create tasks
        tasks = []
        for task_data in task_defs:
            task = TaskDefinition(
                id=task_data.get("id", f"task_{uuid.uuid4().hex[:8]}"),
                name=task_data.get("name", "Unnamed Task"),
                description=task_data.get("description", ""),
                agent_type=task_data.get("agent_type"),
                parameters=task_data.get("parameters", {}),
                dependencies=task_data.get("dependencies", []),
                priority=task_data.get("priority", 0),
                timeout_seconds=task_data.get("timeout", 300),
            )
            tasks.append(task)

        # Analyze dependencies
        dependencies = await self.task_analyzer.analyze_dependencies(tasks)

        # Create execution plan
        plan = ExecutionPlan(
            tasks=tasks,
            max_parallel=self.metadata.settings["max_parallel_tasks"],
        )

        # Build dependency graph
        for task in tasks:
            plan.add_task(task)

        # Add discovered dependencies
        for dep in dependencies:
            if dep.dependent_id in plan.dependency_graph:
                plan.dependency_graph[dep.dependent_id].append(dep.prerequisite_id)

        # Compute execution order
        plan.compute_execution_order()

        # Store plan
        async with self._execution_lock:
            self.active_plans[plan.id] = plan
            self.execution_results[plan.id] = []

        # Start execution
        asyncio.create_task(self._execute_plan(plan))

        # Publish orchestration started event
        await self.event_router.publish(
            Event(
                type="orchestration.started",
                source=self.agent_id,
                data={
                    "plan_id": plan.id,
                    "task_count": len(tasks),
                    "batch_count": len(plan.execution_order),
                },
                priority=EventPriority.HIGH,
            )
        )

        return AgentResponse(
            success=True,
            result={
                "plan_id": plan.id,
                "tasks": len(tasks),
                "execution_order": plan.execution_order,
            },
        )

    async def _execute_plan(self, plan: ExecutionPlan) -> None:
        """Execute a plan with parallel task processing."""
        logger.info(f"Executing plan {plan.id} with {len(plan.tasks)} tasks")
        start_time = time.time()

        try:
            # Execute batches in order
            for batch_index, batch in enumerate(plan.execution_order):
                logger.info(f"Executing batch {batch_index + 1}/{len(plan.execution_order)} with {len(batch)} tasks")

                # Get task definitions for batch
                batch_tasks = [
                    task for task in plan.tasks
                    if task.id in batch
                ]

                # Execute batch in parallel
                results = await self.parallel_executor.execute_batch(
                    batch_tasks,
                    mode=ExecutionMode.PARALLEL,
                )

                # Store results
                async with self._execution_lock:
                    self.execution_results[plan.id].extend(results)

                # Check for failures that should stop execution
                critical_failures = [r for r in results if not r.success and r.retries >= 3]
                if critical_failures:
                    logger.error(f"Critical failures in batch {batch_index + 1}, stopping execution")
                    break

                # Update state
                self.state["total_tasks_executed"] += len(batch)

            # Calculate final statistics
            all_results = self.execution_results[plan.id]
            successful = sum(1 for r in all_results if r.success)
            failed = len(all_results) - successful
            duration = time.time() - start_time

            # Store execution summary in memory
            summary_memory = Memory(
                type=MemoryType.ACHIEVEMENT,
                content=f"Executed plan {plan.id}: {successful}/{len(all_results)} successful",
                metadata={
                    "plan_id": plan.id,
                    "total_tasks": len(plan.tasks),
                    "successful": successful,
                    "failed": failed,
                    "duration_seconds": duration,
                    "batches": len(plan.execution_order),
                },
            )
            await self.memory_system.store_memory(summary_memory)

            # Publish completion event
            await self.event_router.publish(
                Event(
                    type="orchestration.completed",
                    source=self.agent_id,
                    data={
                        "plan_id": plan.id,
                        "successful": successful,
                        "failed": failed,
                        "duration": duration,
                    },
                    priority=EventPriority.HIGH,
                )
            )

            # Update state
            self.state["total_plans_executed"] += 1

            logger.info(f"Plan {plan.id} completed: {successful}/{len(all_results)} successful in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Error executing plan {plan.id}: {e}")

            # Publish failure event
            await self.event_router.publish(
                Event(
                    type="orchestration.failed",
                    source=self.agent_id,
                    data={
                        "plan_id": plan.id,
                        "error": str(e),
                    },
                    priority=EventPriority.CRITICAL,
                )
            )

        finally:
            # Clean up
            async with self._execution_lock:
                if plan.id in self.active_plans:
                    del self.active_plans[plan.id]

    async def _handle_task_completion(self, data: Dict[str, Any]) -> AgentResponse:
        """Handle task completion event."""
        task_id = data.get("task_id")
        plan_id = data.get("plan_id")

        logger.info(f"Task {task_id} completed successfully")

        # Update execution result if tracked
        if plan_id and plan_id in self.execution_results:
            for result in self.execution_results[plan_id]:
                if result.task_id == task_id:
                    result.complete(
                        success=True,
                        result=data.get("result"),
                    )
                    break

        return AgentResponse(success=True)

    async def _handle_task_failure(self, data: Dict[str, Any]) -> AgentResponse:
        """Handle task failure event."""
        task_id = data.get("task_id")
        plan_id = data.get("plan_id")
        error = data.get("error", "Unknown error")

        logger.warning(f"Task {task_id} failed: {error}")

        # Update execution result if tracked
        if plan_id and plan_id in self.execution_results:
            for result in self.execution_results[plan_id]:
                if result.task_id == task_id:
                    result.complete(
                        success=False,
                        error=error,
                    )
                    break

        return AgentResponse(success=True)

    async def get_execution_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an execution plan.

        Args:
            plan_id: Plan ID

        Returns:
            Status dictionary or None
        """
        async with self._execution_lock:
            if plan_id not in self.active_plans and plan_id not in self.execution_results:
                return None

            plan = self.active_plans.get(plan_id)
            results = self.execution_results.get(plan_id, [])

            completed = [r for r in results if r.end_time is not None]
            successful = [r for r in completed if r.success]
            failed = [r for r in completed if not r.success]
            in_progress = len(results) - len(completed)

            return {
                "plan_id": plan_id,
                "total_tasks": len(plan.tasks) if plan else 0,
                "completed": len(completed),
                "successful": len(successful),
                "failed": len(failed),
                "in_progress": in_progress,
                "is_active": plan_id in self.active_plans,
            }

    async def cleanup(self) -> None:
        """Clean up orchestrator resources."""
        # Cancel any active plans
        for plan_id in list(self.active_plans.keys()):
            logger.warning(f"Cancelling active plan {plan_id}")

        # Clean up executor
        await self.parallel_executor.cleanup()

        # Save final state
        await self.save_state()

        # Parent cleanup
        await super().cleanup()
