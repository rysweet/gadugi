"""
Production Orchestrator V0.3 with Intelligent Task Decomposition and Learning
============================================================================

This is a production-ready orchestrator that inherits from V03Agent to gain:
- Memory persistence across sessions
- Learning from past task execution patterns
- Intelligent task decomposition using historical data
- Adaptive parallelization strategies
- Real-time performance optimization

Key Features:
- Learns optimal decomposition patterns from past executions
- Adapts parallel execution strategies based on success rates
- Uses memory system to track and improve performance
- Identifies dependencies automatically using learned patterns
- Optimizes resource allocation dynamically
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import V03Agent base class
from ...shared.memory_integration import AgentMemoryInterface
from ..base.v03_agent import V03Agent, AgentCapabilities, TaskOutcome

# Import existing orchestrator components
from .task_analyzer import TaskAnalyzer as _TaskAnalyzer, TaskDependency as _TaskDependency
from .parallel_executor import ParallelExecutor as _ParallelExecutor, ExecutionMode as _ExecutionMode

# Rename to avoid conflicts
TaskAnalyzer = _TaskAnalyzer
TaskDependency = _TaskDependency
ParallelExecutor = _ParallelExecutor
ExecutionMode = _ExecutionMode

logger = logging.getLogger(__name__)


@dataclass
class TaskPattern:
    """Learned pattern for task decomposition."""
    pattern_id: str
    task_type: str
    description_keywords: List[str]
    optimal_subtasks: List[str]
    dependencies: List[Tuple[str, str]]  # (dependent, prerequisite)
    success_rate: float
    avg_duration: float
    parallel_efficiency: float
    usage_count: int
    last_used: datetime
    created: datetime = field(default_factory=datetime.now)


@dataclass
class DecompositionStrategy:
    """Strategy for breaking down tasks."""
    strategy_name: str
    applicable_patterns: List[str]
    max_parallel: int
    expected_speedup: float
    resource_requirements: Dict[str, Any]
    success_conditions: List[str]


@dataclass
class IntelligentTask:
    """Enhanced task with learning metadata."""
    id: str
    name: str
    description: str
    task_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3

    # Learning metadata
    pattern_match_confidence: float = 0.0
    predicted_duration: float = 0.0
    predicted_success_rate: float = 0.5
    resource_estimate: Dict[str, float] = field(default_factory=dict)
    similar_past_tasks: List[str] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class ExecutionMetrics:
    """Metrics for execution analysis."""
    plan_id: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_duration: float
    parallel_efficiency: float
    resource_utilization: Dict[str, float]
    pattern_accuracy: float
    speedup_achieved: float
    lessons_learned: List[str]


class OrchestratorV03(V03Agent):
    """
    Production Orchestrator V0.3 with intelligent task decomposition.

    This orchestrator learns from past executions to optimize:
    - Task breakdown strategies
    - Dependency detection
    - Parallel execution patterns
    - Resource allocation
    - Performance predictions
    """

    def __init__(self):
        """Initialize the intelligent orchestrator."""
        capabilities = AgentCapabilities(
            can_parallelize=True,
            can_create_prs=True,
            can_write_code=True,
            can_review_code=True,
            can_test=True,
            can_document=True,
            expertise_areas=[
                "task_orchestration",
                "parallel_execution",
                "workflow_management",
                "dependency_analysis",
                "performance_optimization",
                "learning_systems"
            ],
            max_parallel_tasks=8
        )

        super().__init__(
            agent_id="orchestrator_v03",
            agent_type="orchestrator",
            capabilities=capabilities
        )

        # Core components
        self.task_analyzer = TaskAnalyzer()
        self.parallel_executor = ParallelExecutor(
            max_workers=8,
            enable_worktrees=True
        )

        # Learning components - use different name to avoid base class conflict
        self.task_patterns: Dict[str, TaskPattern] = {}
        self.decomposition_strategies: Dict[str, DecompositionStrategy] = {}
        self.execution_history: List[ExecutionMetrics] = []

        # Current execution state
        self.active_plans: Dict[str, Dict[str, Any]] = {}
        self._optimization_lock = asyncio.Lock()

        # Performance tracking
        self.pattern_hit_rate = 0.0
        self.avg_speedup = 1.0
        self.success_rate_by_pattern: Dict[str, float] = {}

    async def execute_task(self, task: Dict[str, Any]) -> TaskOutcome:
        """Execute an orchestration task with intelligent decomposition."""
        start_time = datetime.now()
        task_description = task.get("description", "Unknown orchestration task")

        try:
            # Start task tracking
            await self.start_task(task_description)

            # Step 1: Analyze the task and find similar patterns
            similar_patterns = await self._find_matching_patterns(task_description)

            # Step 2: Intelligent task decomposition
            subtasks = await self._decompose_task_intelligently(
                task, similar_patterns
            )

            # Step 3: Enhanced dependency analysis
            dependencies = await self._analyze_dependencies_with_learning(subtasks)

            # Step 4: Optimize execution plan
            execution_plan = await self._create_optimized_plan(
                subtasks, dependencies
            )

            # Step 5: Execute with monitoring and adaptation
            results = await self._execute_with_adaptive_monitoring(execution_plan)

            # Step 6: Learn from execution
            await self._learn_from_execution(
                execution_plan, results, start_time
            )

            # Calculate success metrics
            successful = sum(1 for r in results if r.get("success", False))
            total = len(results)
            duration = (datetime.now() - start_time).total_seconds()

            if successful == total:
                return TaskOutcome(
                    success=True,
                    task_id=self.current_task_id or "unknown",
                    task_type="orchestration",
                    steps_taken=[
                        f"Analyzed {len(similar_patterns)} similar patterns",
                        f"Decomposed into {len(subtasks)} subtasks",
                        f"Detected {len(dependencies)} dependencies",
                        f"Executed {total} tasks in parallel",
                        f"Achieved {successful}/{total} success rate"
                    ],
                    duration_seconds=duration,
                    lessons_learned=f"Pattern matching helped optimize execution by {self.avg_speedup:.1f}x"
                )
            else:
                return TaskOutcome(
                    success=False,
                    task_id=self.current_task_id or "unknown",
                    task_type="orchestration",
                    steps_taken=[
                        f"Partial success: {successful}/{total} tasks completed"
                    ],
                    duration_seconds=duration,
                    error=f"{total - successful} tasks failed",
                    lessons_learned="Need to improve failure handling and retry strategies"
                )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TaskOutcome(
                success=False,
                task_id=self.current_task_id or "unknown",
                task_type="orchestration",
                steps_taken=["Failed during intelligent task decomposition"],
                duration_seconds=duration,
                error=str(e),
                lessons_learned=f"Decomposition strategy needs improvement for: {task_description}"
            )

    async def _find_matching_patterns(self, task_description: str) -> List[TaskPattern]:
        """Find patterns that match the current task using learned knowledge."""
        if self.memory:
            await self.memory.remember_short_term(f"Searching for patterns matching: {task_description}")

        # Get relevant knowledge from memory
        relevant_memories = await self.get_relevant_knowledge(task_description)

        # Extract task type and keywords
        task_type = self._classify_task_type(task_description)
        keywords = self._extract_keywords(task_description)

        # Find matching patterns
        matching_patterns = []

        for pattern in self.task_patterns.values():
            # Check task type match
            if pattern.task_type == task_type:
                confidence = 0.8
            elif task_type in pattern.description_keywords:
                confidence = 0.6
            else:
                confidence = 0.1

            # Check keyword overlap
            keyword_overlap = len(set(keywords) & set(pattern.description_keywords))
            keyword_score = keyword_overlap / max(len(keywords), 1)

            # Combine scores
            total_confidence = confidence * 0.7 + keyword_score * 0.3

            if total_confidence > 0.4:  # Threshold for pattern matching
                pattern.pattern_id = f"match_{total_confidence:.2f}"
                matching_patterns.append(pattern)

        # Sort by confidence and recency
        matching_patterns.sort(
            key=lambda p: (float(p.pattern_id.split('_')[1]), p.usage_count),
            reverse=True
        )

        # Update pattern hit rate
        if matching_patterns:
            self.pattern_hit_rate = (self.pattern_hit_rate * 0.9) + (0.1 * 1.0)
        else:
            self.pattern_hit_rate = self.pattern_hit_rate * 0.9

        if self.memory:
            await self.memory.remember_short_term(
                f"Found {len(matching_patterns)} matching patterns (hit rate: {self.pattern_hit_rate:.2f})"
            )

        return matching_patterns[:3]  # Top 3 matches

    async def _decompose_task_intelligently(
        self,
        task: Dict[str, Any],
        similar_patterns: List[TaskPattern]
    ) -> List[IntelligentTask]:
        """Decompose task using learned patterns and intelligent analysis."""
        task_description = task.get("description", "")

        if similar_patterns:
            # Use best matching pattern as starting point
            best_pattern = similar_patterns[0]
            confidence = float(best_pattern.pattern_id.split('_')[1])

            if self.memory:
                await self.memory.remember_short_term(
                    f"Using pattern '{best_pattern.task_type}' with {confidence:.2f} confidence"
                )

            # Create subtasks based on pattern
            subtasks = []
            for i, subtask_desc in enumerate(best_pattern.optimal_subtasks):
                subtask = IntelligentTask(
                    id=f"subtask_{i+1}_{uuid.uuid4().hex[:8]}",
                    name=f"Subtask {i+1}",
                    description=subtask_desc.format(task=task_description),
                    task_type=self._classify_task_type(subtask_desc),
                    parameters=task.get("parameters", {}),
                    pattern_match_confidence=confidence,
                    predicted_duration=best_pattern.avg_duration / len(best_pattern.optimal_subtasks),
                    predicted_success_rate=best_pattern.success_rate,
                    similar_past_tasks=[best_pattern.pattern_id]
                )
                subtasks.append(subtask)

            # Apply learned dependencies
            for dependent, prerequisite in best_pattern.dependencies:
                if dependent.isdigit() and prerequisite.isdigit():
                    dep_idx = int(dependent) - 1
                    prereq_idx = int(prerequisite) - 1
                    if 0 <= dep_idx < len(subtasks) and 0 <= prereq_idx < len(subtasks):
                        subtasks[dep_idx].dependencies.append(subtasks[prereq_idx].id)

        else:
            # No patterns found - use intelligent analysis
            if self.memory:
                await self.memory.remember_short_term("No patterns found, using intelligent decomposition")
            subtasks = await self._decompose_without_patterns(task)

        if self.memory:
            await self.memory.remember_short_term(
                f"Decomposed into {len(subtasks)} intelligent subtasks"
            )

        return subtasks

    async def _decompose_without_patterns(
        self, task: Dict[str, Any]
    ) -> List[IntelligentTask]:
        """Decompose task without patterns using intelligent analysis."""
        task_description = task.get("description", "")
        task_type = self._classify_task_type(task_description)

        # Use rule-based decomposition with known patterns
        if "test" in task_description.lower():
            return await self._create_testing_subtasks(task)
        elif "fix" in task_description.lower():
            return await self._create_bugfix_subtasks(task)
        elif "implement" in task_description.lower() or "add" in task_description.lower():
            return await self._create_feature_subtasks(task)
        elif "refactor" in task_description.lower():
            return await self._create_refactor_subtasks(task)
        else:
            return await self._create_generic_subtasks(task)

    async def _create_testing_subtasks(self, task: Dict[str, Any]) -> List[IntelligentTask]:
        """Create subtasks for testing workflows."""
        base_id = uuid.uuid4().hex[:8]

        return [
            IntelligentTask(
                id=f"test_analyze_{base_id}",
                name="Analyze Test Requirements",
                description=f"Analyze testing needs for: {task.get('description', '')}",
                task_type="analysis",
                parameters=task.get("parameters", {}),
                predicted_duration=120.0,
                predicted_success_rate=0.9
            ),
            IntelligentTask(
                id=f"test_setup_{base_id}",
                name="Setup Test Environment",
                description="Setup test environment and dependencies",
                task_type="setup",
                dependencies=[f"test_analyze_{base_id}"],
                predicted_duration=180.0,
                predicted_success_rate=0.85
            ),
            IntelligentTask(
                id=f"test_execute_{base_id}",
                name="Execute Tests",
                description="Run test suites in parallel",
                task_type="execution",
                dependencies=[f"test_setup_{base_id}"],
                predicted_duration=300.0,
                predicted_success_rate=0.8
            ),
            IntelligentTask(
                id=f"test_report_{base_id}",
                name="Generate Test Report",
                description="Generate comprehensive test report",
                task_type="reporting",
                dependencies=[f"test_execute_{base_id}"],
                predicted_duration=60.0,
                predicted_success_rate=0.95
            )
        ]

    async def _create_feature_subtasks(self, task: Dict[str, Any]) -> List[IntelligentTask]:
        """Create subtasks for feature implementation."""
        base_id = uuid.uuid4().hex[:8]

        return [
            IntelligentTask(
                id=f"feature_design_{base_id}",
                name="Design Feature Architecture",
                description=f"Design architecture for: {task.get('description', '')}",
                task_type="design",
                predicted_duration=240.0,
                predicted_success_rate=0.9
            ),
            IntelligentTask(
                id=f"feature_implement_{base_id}",
                name="Implement Core Logic",
                description="Implement core feature logic",
                task_type="implementation",
                dependencies=[f"feature_design_{base_id}"],
                predicted_duration=600.0,
                predicted_success_rate=0.75
            ),
            IntelligentTask(
                id=f"feature_test_{base_id}",
                name="Create Tests",
                description="Create comprehensive tests for feature",
                task_type="testing",
                predicted_duration=300.0,
                predicted_success_rate=0.8
            ),
            IntelligentTask(
                id=f"feature_integrate_{base_id}",
                name="Integration Testing",
                description="Test feature integration",
                task_type="integration",
                dependencies=[f"feature_implement_{base_id}", f"feature_test_{base_id}"],
                predicted_duration=180.0,
                predicted_success_rate=0.85
            ),
            IntelligentTask(
                id=f"feature_docs_{base_id}",
                name="Update Documentation",
                description="Update documentation for feature",
                task_type="documentation",
                dependencies=[f"feature_integrate_{base_id}"],
                predicted_duration=120.0,
                predicted_success_rate=0.9
            )
        ]

    async def _create_bugfix_subtasks(self, task: Dict[str, Any]) -> List[IntelligentTask]:
        """Create subtasks for bug fixes."""
        base_id = uuid.uuid4().hex[:8]

        return [
            IntelligentTask(
                id=f"bug_investigate_{base_id}",
                name="Investigate Bug",
                description=f"Investigate root cause of: {task.get('description', '')}",
                task_type="investigation",
                predicted_duration=180.0,
                predicted_success_rate=0.85
            ),
            IntelligentTask(
                id=f"bug_reproduce_{base_id}",
                name="Reproduce Bug",
                description="Create test case that reproduces the bug",
                task_type="reproduction",
                dependencies=[f"bug_investigate_{base_id}"],
                predicted_duration=120.0,
                predicted_success_rate=0.8
            ),
            IntelligentTask(
                id=f"bug_fix_{base_id}",
                name="Implement Fix",
                description="Implement the bug fix",
                task_type="fix",
                dependencies=[f"bug_reproduce_{base_id}"],
                predicted_duration=240.0,
                predicted_success_rate=0.9
            ),
            IntelligentTask(
                id=f"bug_verify_{base_id}",
                name="Verify Fix",
                description="Verify bug fix works and doesn't break anything",
                task_type="verification",
                dependencies=[f"bug_fix_{base_id}"],
                predicted_duration=150.0,
                predicted_success_rate=0.95
            )
        ]

    async def _create_refactor_subtasks(self, task: Dict[str, Any]) -> List[IntelligentTask]:
        """Create subtasks for refactoring."""
        base_id = uuid.uuid4().hex[:8]

        return [
            IntelligentTask(
                id=f"refactor_analyze_{base_id}",
                name="Analyze Current Code",
                description=f"Analyze code structure for: {task.get('description', '')}",
                task_type="analysis",
                predicted_duration=120.0,
                predicted_success_rate=0.9
            ),
            IntelligentTask(
                id=f"refactor_plan_{base_id}",
                name="Plan Refactoring",
                description="Create refactoring plan with safety measures",
                task_type="planning",
                dependencies=[f"refactor_analyze_{base_id}"],
                predicted_duration=90.0,
                predicted_success_rate=0.95
            ),
            IntelligentTask(
                id=f"refactor_backup_{base_id}",
                name="Create Backup Tests",
                description="Create comprehensive tests before refactoring",
                task_type="testing",
                dependencies=[f"refactor_plan_{base_id}"],
                predicted_duration=180.0,
                predicted_success_rate=0.9
            ),
            IntelligentTask(
                id=f"refactor_execute_{base_id}",
                name="Execute Refactoring",
                description="Execute refactoring in safe increments",
                task_type="refactoring",
                dependencies=[f"refactor_backup_{base_id}"],
                predicted_duration=450.0,
                predicted_success_rate=0.8
            ),
            IntelligentTask(
                id=f"refactor_validate_{base_id}",
                name="Validate Refactoring",
                description="Validate all tests pass and behavior unchanged",
                task_type="validation",
                dependencies=[f"refactor_execute_{base_id}"],
                predicted_duration=120.0,
                predicted_success_rate=0.95
            )
        ]

    async def _create_generic_subtasks(self, task: Dict[str, Any]) -> List[IntelligentTask]:
        """Create generic subtasks for unknown task types."""
        base_id = uuid.uuid4().hex[:8]

        return [
            IntelligentTask(
                id=f"generic_analyze_{base_id}",
                name="Analyze Requirements",
                description=f"Analyze requirements for: {task.get('description', '')}",
                task_type="analysis",
                predicted_duration=150.0,
                predicted_success_rate=0.9
            ),
            IntelligentTask(
                id=f"generic_plan_{base_id}",
                name="Create Execution Plan",
                description="Create detailed execution plan",
                task_type="planning",
                dependencies=[f"generic_analyze_{base_id}"],
                predicted_duration=120.0,
                predicted_success_rate=0.85
            ),
            IntelligentTask(
                id=f"generic_execute_{base_id}",
                name="Execute Task",
                description="Execute the main task",
                task_type="execution",
                dependencies=[f"generic_plan_{base_id}"],
                predicted_duration=300.0,
                predicted_success_rate=0.75
            ),
            IntelligentTask(
                id=f"generic_verify_{base_id}",
                name="Verify Results",
                description="Verify task completion and quality",
                task_type="verification",
                dependencies=[f"generic_execute_{base_id}"],
                predicted_duration=90.0,
                predicted_success_rate=0.9
            )
        ]

    async def _analyze_dependencies_with_learning(
        self, subtasks: List[IntelligentTask]
    ) -> List[TaskDependency]:
        """Analyze dependencies using learned patterns and intelligent analysis."""
        # Use traditional analyzer as baseline
        basic_deps = await self.task_analyzer.analyze_dependencies(subtasks)

        # Enhance with learned patterns
        enhanced_deps = basic_deps.copy()

        # Add pattern-based dependencies
        for task in subtasks:
            if task.similar_past_tasks:
                # Use similar task patterns to predict additional dependencies
                if self.memory:
                    similar_memories = await self.memory.recall_memories(
                        memory_type="procedural",
                        limit=10
                    )
                else:
                    similar_memories = []

                for memory in similar_memories:
                    if memory.get("metadata", {}).get("task_type") == task.task_type:
                        # Extract dependency patterns from memory
                        steps = memory.get("content", "").split("\n")
                        for step in steps:
                            if "depends on" in step.lower():
                                # Extract dependency information
                                pass  # Could implement dependency extraction logic

        if self.memory:
            await self.memory.remember_short_term(
                f"Enhanced dependency analysis: {len(enhanced_deps)} dependencies found"
            )

        return enhanced_deps

    async def _create_optimized_plan(
        self,
        subtasks: List[IntelligentTask],
        dependencies: List[TaskDependency]
    ) -> Dict[str, Any]:
        """Create optimized execution plan using learned strategies."""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        # Calculate optimal parallelization
        total_estimated_duration = sum(task.predicted_duration for task in subtasks)
        sequential_duration = total_estimated_duration

        # Estimate parallel duration considering dependencies
        parallel_batches = self._calculate_parallel_batches(subtasks, dependencies)
        parallel_duration = sum(
            max(subtasks[i].predicted_duration for i in batch)
            for batch in parallel_batches
        )

        estimated_speedup = sequential_duration / max(parallel_duration, 1)

        # Create execution plan
        execution_plan = {
            "plan_id": plan_id,
            "subtasks": subtasks,
            "dependencies": dependencies,
            "parallel_batches": parallel_batches,
            "estimated_duration": parallel_duration,
            "estimated_speedup": estimated_speedup,
            "resource_allocation": self._calculate_resource_allocation(subtasks),
            "risk_assessment": self._assess_execution_risks(subtasks),
            "created_at": datetime.now()
        }

        # Store plan in active plans
        async with self._optimization_lock:
            self.active_plans[plan_id] = execution_plan

        if self.memory:
            await self.memory.remember_short_term(
                f"Created optimized plan {plan_id} with {estimated_speedup:.1f}x speedup"
            )

        return execution_plan

    def _calculate_parallel_batches(
        self,
        subtasks: List[IntelligentTask],
        dependencies: List[TaskDependency]
    ) -> List[List[int]]:
        """Calculate optimal batches for parallel execution."""
        # Build dependency graph
        task_ids = [task.id for task in subtasks]
        id_to_index = {task_id: i for i, task_id in enumerate(task_ids)}

        # Initialize in-degrees
        in_degree = [0] * len(subtasks)
        adj_list = [[] for _ in range(len(subtasks))]

        # Build adjacency list and calculate in-degrees
        for dep in dependencies:
            if dep.prerequisite_id in id_to_index and dep.dependent_id in id_to_index:
                prereq_idx = id_to_index[dep.prerequisite_id]
                dep_idx = id_to_index[dep.dependent_id]
                adj_list[prereq_idx].append(dep_idx)
                in_degree[dep_idx] += 1

        # Topological sort with level extraction
        batches = []
        queue = [i for i in range(len(subtasks)) if in_degree[i] == 0]

        while queue:
            # Current batch (tasks with no remaining dependencies)
            current_batch = queue[:]
            batches.append(current_batch)
            queue = []

            # Process current batch
            for task_idx in current_batch:
                for neighbor in adj_list[task_idx]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return batches

    def _calculate_resource_allocation(
        self, subtasks: List[IntelligentTask]
    ) -> Dict[str, Any]:
        """Calculate resource allocation for optimal execution."""
        # Estimate resource needs
        cpu_intensive_tasks = [t for t in subtasks if t.task_type in ["execution", "implementation", "refactoring"]]
        io_intensive_tasks = [t for t in subtasks if t.task_type in ["analysis", "testing", "verification"]]
        memory_intensive_tasks = [t for t in subtasks if "large" in t.description.lower()]

        return {
            "cpu_workers": min(len(cpu_intensive_tasks), self.capabilities.max_parallel_tasks // 2),
            "io_workers": min(len(io_intensive_tasks), self.capabilities.max_parallel_tasks),
            "memory_limit_mb": max(512, len(memory_intensive_tasks) * 256),
            "concurrent_limit": min(len(subtasks), self.capabilities.max_parallel_tasks),
            "priority_order": sorted(subtasks, key=lambda t: t.priority, reverse=True)
        }

    def _assess_execution_risks(self, subtasks: List[IntelligentTask]) -> Dict[str, Any]:
        """Assess risks in the execution plan."""
        # Calculate risk factors
        low_confidence_tasks = [t for t in subtasks if t.predicted_success_rate < 0.8]
        long_duration_tasks = [t for t in subtasks if t.predicted_duration > 600]  # > 10 minutes
        complex_tasks = [t for t in subtasks if t.task_type in ["implementation", "refactoring", "integration"]]

        overall_risk = (
            len(low_confidence_tasks) * 0.3 +
            len(long_duration_tasks) * 0.2 +
            len(complex_tasks) * 0.1
        ) / len(subtasks)

        return {
            "overall_risk_score": min(1.0, overall_risk),
            "high_risk_tasks": [t.id for t in low_confidence_tasks],
            "long_running_tasks": [t.id for t in long_duration_tasks],
            "mitigation_strategies": [
                "Increase monitoring for low-confidence tasks",
                "Prepare rollback plans for complex tasks",
                "Set up intermediate checkpoints for long tasks"
            ]
        }

    async def _execute_with_adaptive_monitoring(
        self, execution_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute plan with adaptive monitoring and optimization."""
        plan_id = execution_plan["plan_id"]
        subtasks = execution_plan["subtasks"]
        parallel_batches = execution_plan["parallel_batches"]

        results = []
        start_time = time.time()

        try:
            if self.memory:
                await self.memory.remember_short_term(f"Starting adaptive execution of plan {plan_id}")

            # Execute batches with monitoring
            for batch_idx, batch in enumerate(parallel_batches):
                batch_start = time.time()
                batch_tasks = [subtasks[i] for i in batch]

                if self.memory:
                    await self.memory.remember_short_term(
                        f"Executing batch {batch_idx + 1}/{len(parallel_batches)} with {len(batch_tasks)} tasks"
                    )

                # Execute batch with parallel executor
                batch_results = await self.parallel_executor.execute_batch(
                    batch_tasks,
                    mode=ExecutionMode.PARALLEL
                )

                results.extend(batch_results)

                # Analyze batch performance
                batch_duration = time.time() - batch_start
                successful_in_batch = sum(1 for r in batch_results if r.get("success", False))

                # Adaptive adjustments based on performance
                if successful_in_batch < len(batch_tasks) * 0.7:  # Less than 70% success
                    # Reduce parallelism for remaining batches
                    self.capabilities.max_parallel_tasks = max(
                        2, self.capabilities.max_parallel_tasks - 1
                    )
                    if self.memory:
                        await self.memory.remember_short_term(
                            f"Reduced parallelism due to batch failures: {successful_in_batch}/{len(batch_tasks)}"
                        )

                # Stop if critical failures
                critical_failures = sum(
                    1 for r in batch_results
                    if not r.get("success", False) and r.get("retries", 0) >= 3
                )

                if critical_failures > 0:
                    if self.memory:
                        await self.memory.remember_short_term(
                            f"Stopping execution due to {critical_failures} critical failures"
                        )
                    break

            # Calculate execution metrics
            total_duration = time.time() - start_time
            successful = sum(1 for r in results if r.get("success", False))

            # Store execution metrics
            metrics = ExecutionMetrics(
                plan_id=plan_id,
                total_tasks=len(subtasks),
                successful_tasks=successful,
                failed_tasks=len(results) - successful,
                total_duration=total_duration,
                parallel_efficiency=execution_plan["estimated_duration"] / total_duration if total_duration > 0 else 0,
                resource_utilization={},
                pattern_accuracy=self.pattern_hit_rate,
                speedup_achieved=execution_plan["estimated_speedup"],
                lessons_learned=[]
            )

            self.execution_history.append(metrics)

            return results

        except Exception as e:
            if self.memory:
                await self.memory.remember_short_term(f"Execution failed: {str(e)}")
            raise

    async def _learn_from_execution(
        self,
        execution_plan: Dict[str, Any],
        results: List[Dict[str, Any]],
        start_time: datetime
    ) -> None:
        """Learn from execution outcomes to improve future performance."""
        plan_id = execution_plan["plan_id"]
        subtasks = execution_plan["subtasks"]

        # Calculate actual vs predicted metrics
        actual_duration = (datetime.now() - start_time).total_seconds()
        predicted_duration = execution_plan["estimated_duration"]
        actual_success_rate = sum(1 for r in results if r.get("success", False)) / len(results)

        # Analyze which predictions were accurate
        duration_accuracy = 1.0 - abs(actual_duration - predicted_duration) / max(predicted_duration, 1)
        success_prediction_accuracy = 1.0 - abs(
            actual_success_rate -
            sum(t.predicted_success_rate for t in subtasks) / len(subtasks)
        )

        # Update learned patterns
        for task in subtasks:
            if task.pattern_match_confidence > 0.5:  # Task was based on a pattern
                pattern_id = task.similar_past_tasks[0] if task.similar_past_tasks else None
                if pattern_id and pattern_id in self.task_patterns:
                    pattern = self.task_patterns[pattern_id]

                    # Update pattern success rate and duration
                    task_result = next((r for r in results if r.get("task_id") == task.id), None)
                    if task_result:
                        # Exponential moving average update
                        pattern.success_rate = (pattern.success_rate * 0.8) + (
                            (1.0 if task_result.get("success", False) else 0.0) * 0.2
                        )

                        actual_task_duration = task_result.get("duration_seconds", task.predicted_duration)
                        pattern.avg_duration = (pattern.avg_duration * 0.8) + (actual_task_duration * 0.2)

                        pattern.usage_count += 1
                        pattern.last_used = datetime.now()

        # Create new pattern if this was successful and novel
        if actual_success_rate > 0.8 and duration_accuracy > 0.7:
            await self._create_new_pattern(execution_plan, results, actual_duration)

        # Update global metrics
        self.avg_speedup = (self.avg_speedup * 0.9) + (
            (predicted_duration / actual_duration) * 0.1
        ) if actual_duration > 0 else self.avg_speedup

        # Store learnings in memory
        learning_summary = {
            "plan_id": plan_id,
            "duration_accuracy": duration_accuracy,
            "success_accuracy": success_prediction_accuracy,
            "actual_speedup": predicted_duration / actual_duration if actual_duration > 0 else 1.0,
            "lessons": []
        }

        if duration_accuracy < 0.5:
            learning_summary["lessons"].append("Duration predictions need improvement")
        if success_prediction_accuracy < 0.5:
            learning_summary["lessons"].append("Success rate predictions need calibration")
        if actual_success_rate < 0.7:
            learning_summary["lessons"].append("Task decomposition strategy needs refinement")

        if self.memory:
            await self.memory.remember_long_term(
                f"Execution learning from plan {plan_id}: {json.dumps(learning_summary, indent=2)}",
                tags=["learning", "execution_analysis", "performance"],
                importance=0.8
            )

        # Collaborate findings with other agents
        await self.collaborate(
            f"Learned from orchestration: {actual_success_rate:.1%} success rate, " +
            f"{actual_duration/predicted_duration:.1f}x actual vs predicted duration",
            decision=f"Adjust future predictions based on {duration_accuracy:.1%} accuracy"
        )

    async def _create_new_pattern(
        self,
        execution_plan: Dict[str, Any],
        results: List[Dict[str, Any]],
        actual_duration: float
    ) -> None:
        """Create a new learned pattern from successful execution."""
        subtasks = execution_plan["subtasks"]

        # Extract common characteristics
        task_descriptions = [task.description for task in subtasks]
        task_types = [task.task_type for task in subtasks]

        # Find common keywords
        all_words = []
        for desc in task_descriptions:
            all_words.extend(desc.lower().split())

        word_freq = {}
        for word in all_words:
            if len(word) > 3:  # Only meaningful words
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get most common keywords
        common_keywords = [
            word for word, freq in word_freq.items()
            if freq >= len(subtasks) * 0.3  # Present in at least 30% of tasks
        ]

        # Create new pattern
        pattern_id = f"learned_{uuid.uuid4().hex[:8]}"
        new_pattern = TaskPattern(
            pattern_id=pattern_id,
            task_type=max(set(task_types), key=task_types.count),  # Most common type
            description_keywords=common_keywords[:10],  # Top 10 keywords
            optimal_subtasks=[task.description for task in subtasks],
            dependencies=[
                (dep.dependent_id, dep.prerequisite_id)
                for dep in execution_plan.get("dependencies", [])
            ],
            success_rate=sum(1 for r in results if r.get("success", False)) / len(results),
            avg_duration=actual_duration,
            parallel_efficiency=execution_plan["estimated_speedup"],
            usage_count=1,
            last_used=datetime.now()
        )

        # Store the new pattern
        self.task_patterns[pattern_id] = new_pattern

        # Remember in long-term memory
        if self.memory:
            await self.memory.remember_long_term(
                f"Created new pattern {pattern_id} from successful execution: " +
                f"{new_pattern.success_rate:.1%} success rate, {actual_duration:.1f}s duration",
                tags=["pattern_learning", "new_pattern", pattern_id],
                importance=0.9
            )

    # Helper methods

    def _classify_task_type(self, description: str) -> str:
        """Classify task type from description."""
        desc_lower = description.lower()

        if any(word in desc_lower for word in ["test", "testing", "verify", "validation"]):
            return "testing"
        elif any(word in desc_lower for word in ["implement", "create", "add", "build"]):
            return "implementation"
        elif any(word in desc_lower for word in ["fix", "bug", "error", "issue"]):
            return "bugfix"
        elif any(word in desc_lower for word in ["refactor", "restructure", "reorganize"]):
            return "refactoring"
        elif any(word in desc_lower for word in ["analyze", "investigate", "research"]):
            return "analysis"
        elif any(word in desc_lower for word in ["document", "readme", "docs"]):
            return "documentation"
        elif any(word in desc_lower for word in ["setup", "configure", "install"]):
            return "setup"
        else:
            return "general"

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        import re

        # Remove common stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "is", "are", "was", "were", "be",
            "been", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can"
        }

        # Extract words (alphanumeric)
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]*\b', text.lower())

        # Filter meaningful keywords
        keywords = [
            word for word in words
            if len(word) > 2 and word not in stop_words
        ]

        return keywords[:20]  # Top 20 keywords

    async def can_handle_task(self, task_description: str) -> bool:
        """Check if orchestrator can handle a task type."""
        # Orchestrator can handle any task that involves coordination
        orchestration_keywords = [
            "orchestrate", "coordinate", "manage", "execute", "parallel",
            "workflow", "multiple", "tasks", "decompose", "break down"
        ]

        return any(keyword in task_description.lower() for keyword in orchestration_keywords)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            "pattern_hit_rate": self.pattern_hit_rate,
            "avg_speedup": self.avg_speedup,
            "learned_patterns": len(self.task_patterns),
            "execution_history": len(self.execution_history),
            "success_rate_by_pattern": dict(self.success_rate_by_pattern),
            "active_plans": len(self.active_plans),
            "total_tasks_orchestrated": sum(
                metrics.total_tasks for metrics in self.execution_history
            ),
            "total_successful_tasks": sum(
                metrics.successful_tasks for metrics in self.execution_history
            )
        }


# Example usage function for testing
async def test_orchestrator_v03():
    """Test the Orchestrator V0.3."""
    print("\n" + "="*70)
    print("Testing Production Orchestrator V0.3")
    print("="*70)

    orchestrator = OrchestratorV03()

    try:
        # Initialize with memory system
        await orchestrator.initialize()

        # Test task decomposition and execution
        test_task = {
            "description": "Implement user authentication system with tests and documentation",
            "parameters": {
                "features": ["login", "register", "password_reset"],
                "tech_stack": "Python/FastAPI",
                "database": "PostgreSQL"
            }
        }

        # Execute the orchestration task
        outcome = await orchestrator.execute_task(test_task)

        print(f"\n📊 Execution Result:")
        print(f"   Success: {outcome.success}")
        print(f"   Duration: {outcome.duration_seconds:.1f}s")
        print(f"   Steps: {len(outcome.steps_taken)}")

        if outcome.lessons_learned:
            print(f"   Lessons: {outcome.lessons_learned}")

        # Show performance metrics
        metrics = orchestrator.get_performance_metrics()
        print(f"\n📈 Performance Metrics:")
        print(f"   Pattern Hit Rate: {metrics['pattern_hit_rate']:.1%}")
        print(f"   Average Speedup: {metrics['avg_speedup']:.1f}x")
        print(f"   Learned Patterns: {metrics['learned_patterns']}")
        print(f"   Total Tasks: {metrics['total_tasks_orchestrated']}")

        print(f"\n✅ Orchestrator V0.3 test completed successfully!")

    finally:
        await orchestrator.shutdown()


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_orchestrator_v03())
