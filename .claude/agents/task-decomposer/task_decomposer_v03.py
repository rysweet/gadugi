"""
Task Decomposer v0.3 Agent with Learning Capabilities
======================================================

A production-ready task decomposer that learns optimal task breakdown patterns
and continuously improves its decomposition strategies based on execution results.
"""

import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..base.v03_agent import V03Agent, AgentCapabilities, TaskOutcome


@dataclass
class DecompositionStrategy:
    """Represents a learned decomposition strategy."""
    name: str
    pattern: str
    success_rate: float
    avg_parallelization: float
    avg_completion_time: float
    usage_count: int
    last_used: datetime
    complexity_level: str
    triggers: List[str] = field(default_factory=list)
    subtask_template: List[str] = field(default_factory=list)


@dataclass
class SubTask:
    """Enhanced subtask with learning metadata."""
    id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_time: Optional[int] = None
    complexity: str = "medium"
    can_parallelize: bool = True
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 1-10 scale
    confidence: float = 0.7  # Confidence in estimates
    agent_hint: Optional[str] = None  # Suggested agent for execution


@dataclass
class DecompositionResult:
    """Enhanced decomposition result with learning context."""
    original_task: str
    subtasks: List[SubTask]
    dependency_graph: Dict[str, List[str]]
    parallelization_score: float
    estimated_total_time: int
    decomposition_pattern: Optional[str] = None
    confidence_score: float = 0.7
    strategy_used: Optional[str] = None
    learning_context: Dict[str, Any] = field(default_factory=dict)
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class ExecutionFeedback:
    """Feedback from task execution for learning."""
    decomposition_id: str
    actual_completion_time: float
    success_rate: float
    parallelization_achieved: float
    bottlenecks: List[str]
    improvements: List[str]
    agent_performance: Dict[str, float]
    user_satisfaction: float = 0.8


class TaskDecomposerV03(V03Agent):
    """
    V0.3 Task Decomposer with advanced learning capabilities.

    Features:
    - Pattern recognition from successful decompositions
    - Complexity analysis for optimal task breakdown
    - Parallelization optimization
    - Agent assignment hints
    - Continuous learning from execution feedback
    """

    def __init__(self):
        capabilities = AgentCapabilities(
            can_parallelize=True,
            can_create_prs=False,
            can_write_code=False,
            can_review_code=True,
            can_test=False,
            can_document=True,
            expertise_areas=[
                "task_decomposition",
                "dependency_analysis",
                "parallelization",
                "complexity_analysis",
                "pattern_recognition"
            ],
            max_parallel_tasks=8
        )

        super().__init__(
            agent_id="task_decomposer_v03",
            agent_type="TaskDecomposer",
            capabilities=capabilities
        )

        # Learning state
        self.strategies: Dict[str, DecompositionStrategy] = {}
        self.execution_history: List[ExecutionFeedback] = []
        self.pattern_confidence_threshold = 0.6
        self.subtask_counter = 0

        # Performance tracking
        self.total_decompositions = 0
        self.successful_decompositions = 0
        self.avg_parallelization_achieved = 0.0

    async def initialize(self, mcp_url: str = "http://localhost:8000") -> None:
        """Initialize with memory system and load learned patterns."""
        await super().initialize(mcp_url)

        # Load existing strategies from memory
        await self._load_learned_strategies()

        print(f"🧠 Loaded {len(self.strategies)} learned decomposition strategies")

    async def _load_learned_strategies(self) -> None:
        """Load previously learned decomposition strategies."""
        try:
            # Try to recall strategy patterns from memory
            if not self.memory:
                return
            strategy_memories = await self.memory.recall_memories(
                memory_type="procedural",
                limit=50
            )

            strategies_found = 0
            for memory in strategy_memories:
                content = memory.get('content', '')
                if 'decomposition_strategy:' in content:
                    try:
                        # Extract strategy data from memory
                        strategy_data = json.loads(
                            content.split('decomposition_strategy:')[1]
                        )

                        strategy = DecompositionStrategy(
                            name=strategy_data['name'],
                            pattern=strategy_data['pattern'],
                            success_rate=strategy_data['success_rate'],
                            avg_parallelization=strategy_data['avg_parallelization'],
                            avg_completion_time=strategy_data['avg_completion_time'],
                            usage_count=strategy_data['usage_count'],
                            last_used=datetime.fromisoformat(strategy_data['last_used']),
                            complexity_level=strategy_data['complexity_level'],
                            triggers=strategy_data['triggers'],
                            subtask_template=strategy_data['subtask_template']
                        )

                        self.strategies[strategy.name] = strategy
                        strategies_found += 1

                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"  ⚠️ Failed to parse strategy from memory: {e}")

            if strategies_found > 0:
                print(f"  📚 Restored {strategies_found} learned strategies from memory")
            else:
                # Initialize with default strategies
                await self._initialize_default_strategies()

        except Exception as e:
            print(f"  ℹ️ No previous strategies found, starting fresh: {e}")
            await self._initialize_default_strategies()

    async def _initialize_default_strategies(self) -> None:
        """Initialize with proven decomposition strategies."""
        default_strategies = [
            DecompositionStrategy(
                name="feature_implementation",
                pattern="implement|create|build|develop|add",
                success_rate=0.85,
                avg_parallelization=0.65,
                avg_completion_time=180.0,
                usage_count=0,
                last_used=datetime.now(),
                complexity_level="medium",
                triggers=["implement", "create", "build", "develop", "add"],
                subtask_template=[
                    "requirements_analysis",
                    "architecture_design",
                    "implementation",
                    "unit_testing",
                    "integration_testing",
                    "documentation",
                    "code_review"
                ]
            ),
            DecompositionStrategy(
                name="bug_fix_workflow",
                pattern="fix|resolve|debug|patch|repair",
                success_rate=0.92,
                avg_parallelization=0.35,
                avg_completion_time=90.0,
                usage_count=0,
                last_used=datetime.now(),
                complexity_level="high",
                triggers=["fix", "resolve", "debug", "patch", "repair"],
                subtask_template=[
                    "issue_reproduction",
                    "root_cause_analysis",
                    "solution_design",
                    "implementation",
                    "testing",
                    "verification",
                    "documentation"
                ]
            ),
            DecompositionStrategy(
                name="refactoring_workflow",
                pattern="refactor|optimize|improve|enhance|clean",
                success_rate=0.78,
                avg_parallelization=0.55,
                avg_completion_time=150.0,
                usage_count=0,
                last_used=datetime.now(),
                complexity_level="high",
                triggers=["refactor", "optimize", "improve", "enhance", "clean"],
                subtask_template=[
                    "code_analysis",
                    "refactoring_plan",
                    "implementation",
                    "testing",
                    "performance_validation",
                    "documentation"
                ]
            ),
            DecompositionStrategy(
                name="testing_workflow",
                pattern="test|validate|verify|check|ensure",
                success_rate=0.95,
                avg_parallelization=0.8,
                avg_completion_time=120.0,
                usage_count=0,
                last_used=datetime.now(),
                complexity_level="medium",
                triggers=["test", "validate", "verify", "check", "ensure"],
                subtask_template=[
                    "test_planning",
                    "test_case_creation",
                    "test_execution",
                    "result_analysis",
                    "reporting"
                ]
            )
        ]

        for strategy in default_strategies:
            self.strategies[strategy.name] = strategy

    async def execute_task(self, task: Dict[str, Any]) -> TaskOutcome:
        """Execute task decomposition with learning."""
        start_time = datetime.now()
        task_id = "unknown"  # Initialize with default value

        try:
            task_description = task.get('description', '')
            context = task.get('context', {})

            # Start task in memory
            task_id = await self.start_task(f"Decompose: {task_description}")

            # Remember the decomposition request
            if self.memory:
                await self.memory.remember_short_term(
                    f"Starting decomposition: {task_description}",
                    tags=["decomposition", "start"]
                )

            # Perform decomposition
            result = await self.decompose_task(task_description, context)

            # Store the result
            await self._store_decomposition_result(result)

            duration = (datetime.now() - start_time).total_seconds()

            # Remember success
            if self.memory:
                await self.memory.remember_long_term(
                    f"Successfully decomposed task into {len(result.subtasks)} subtasks. "
                    f"Parallelization score: {result.parallelization_score:.2f}",
                    tags=["success", "decomposition", result.strategy_used or "unknown"],
                    importance=0.8
                )

            return TaskOutcome(
                success=True,
                task_id=task_id,
                task_type="decomposition",
                steps_taken=[
                    f"Analyzed task: {task_description[:50]}...",
                    f"Applied strategy: {result.strategy_used}",
                    f"Generated {len(result.subtasks)} subtasks",
                    f"Calculated dependencies and parallelization"
                ],
                duration_seconds=duration,
                lessons_learned=f"Decomposed with {result.parallelization_score:.1%} parallelization potential"
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            if self.memory:
                await self.memory.remember_long_term(
                    f"Failed decomposition: {str(e)}",
                    tags=["failure", "decomposition", "error"],
                    importance=0.9
                )

            return TaskOutcome(
                success=False,
                task_id=task_id,
                task_type="decomposition",
                steps_taken=["Attempted task analysis", "Error encountered"],
                duration_seconds=duration,
                error=str(e),
                lessons_learned=f"Decomposition failed: {str(e)}"
            )

    async def decompose_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> DecompositionResult:
        """
        Main decomposition logic with learning integration.
        """
        # Analyze task complexity
        complexity_analysis = await self._analyze_task_complexity(task_description, context)

        # Find best matching strategy
        strategy = await self._select_best_strategy(task_description, complexity_analysis)

        # Generate subtasks using selected strategy
        subtasks = await self._generate_smart_subtasks(
            task_description, strategy, complexity_analysis, context
        )

        # Analyze dependencies with learning
        dependency_graph = await self._analyze_dependencies_smart(subtasks)

        # Calculate parallelization potential
        parallelization_score = await self._estimate_parallelization_optimized(
            subtasks, dependency_graph, strategy
        )

        # Estimate total time with confidence intervals
        estimated_total_time, confidence = await self._estimate_time_with_confidence(
            subtasks, dependency_graph, parallelization_score, strategy
        )

        # Generate optimization suggestions
        optimizations = await self._generate_optimization_suggestions(
            subtasks, dependency_graph, parallelization_score
        )

        result = DecompositionResult(
            original_task=task_description,
            subtasks=subtasks,
            dependency_graph=dependency_graph,
            parallelization_score=parallelization_score,
            estimated_total_time=estimated_total_time,
            decomposition_pattern=strategy.name if strategy else None,
            confidence_score=confidence,
            strategy_used=strategy.name if strategy else "adaptive",
            learning_context={
                "complexity_level": complexity_analysis["level"],
                "pattern_matches": complexity_analysis["patterns"],
                "confidence_factors": complexity_analysis["confidence_factors"]
            },
            optimization_suggestions=optimizations
        )

        # Update strategy usage
        if strategy:
            strategy.usage_count += 1
            strategy.last_used = datetime.now()
            await self._update_strategy_in_memory(strategy)

        self.total_decompositions += 1

        return result

    async def _analyze_task_complexity(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze task complexity using learned patterns."""
        # Get relevant knowledge about complexity analysis
        complexity_knowledge = await self.get_relevant_knowledge("complexity analysis")

        task_lower = task_description.lower()
        words = task_lower.split()

        # Complexity indicators
        high_complexity_indicators = [
            "implement", "build", "create", "develop", "design", "architect",
            "integration", "system", "complex", "advanced", "multiple", "scalable"
        ]

        medium_complexity_indicators = [
            "update", "modify", "enhance", "improve", "optimize", "refactor"
        ]

        low_complexity_indicators = [
            "fix", "patch", "correct", "adjust", "tweak", "document"
        ]

        # Calculate complexity score
        high_score = sum(1 for word in words if word in high_complexity_indicators)
        medium_score = sum(1 for word in words if word in medium_complexity_indicators)
        low_score = sum(1 for word in words if word in low_complexity_indicators)

        # Determine complexity level
        if high_score > medium_score and high_score > low_score:
            complexity_level = "high"
        elif medium_score > low_score:
            complexity_level = "medium"
        else:
            complexity_level = "low"

        # Additional context analysis
        context_factors = []
        if context:
            if context.get("dependencies", []):
                context_factors.append("has_dependencies")
            if context.get("time_constraint"):
                context_factors.append("time_constrained")
            if context.get("parallel_capable", True):
                context_factors.append("parallelizable")

        # Pattern matching against known task types
        patterns = []
        for strategy_name, strategy in self.strategies.items():
            for trigger in strategy.triggers:
                if trigger in task_lower:
                    patterns.append({
                        "strategy": strategy_name,
                        "trigger": trigger,
                        "success_rate": strategy.success_rate
                    })

        return {
            "level": complexity_level,
            "score": {
                "high": high_score,
                "medium": medium_score,
                "low": low_score
            },
            "patterns": patterns,
            "context_factors": context_factors,
            "confidence_factors": [
                f"Word analysis confidence: {max(high_score, medium_score, low_score) / len(words):.2f}",
                f"Pattern matches: {len(patterns)}",
                f"Context richness: {len(context_factors)}"
            ]
        }

    async def _select_best_strategy(
        self,
        task_description: str,
        complexity_analysis: Dict[str, Any]
    ) -> Optional[DecompositionStrategy]:
        """Select the best decomposition strategy based on learning."""
        task_lower = task_description.lower()

        # Score strategies based on multiple factors
        strategy_scores: List[Tuple[DecompositionStrategy, float]] = []

        for strategy in self.strategies.values():
            score = 0.0

            # Pattern matching score
            pattern_matches = sum(1 for trigger in strategy.triggers if trigger in task_lower)
            score += pattern_matches * 2.0

            # Success rate bonus
            score += strategy.success_rate * 1.5

            # Usage frequency bonus (but not too much to avoid over-fitting)
            usage_bonus = min(strategy.usage_count * 0.1, 0.5)
            score += usage_bonus

            # Complexity level matching
            if strategy.complexity_level == complexity_analysis["level"]:
                score += 1.0

            # Recency bonus
            days_since_use = (datetime.now() - strategy.last_used).days
            if days_since_use < 7:
                score += 0.5
            elif days_since_use < 30:
                score += 0.2

            if score > 0:
                strategy_scores.append((strategy, score))

        # Sort by score and select best
        strategy_scores.sort(key=lambda x: x[1], reverse=True)

        if strategy_scores and strategy_scores[0][1] > self.pattern_confidence_threshold:
            best_strategy = strategy_scores[0][0]

            # Remember the selection reasoning
            if self.memory:
                await self.memory.remember_short_term(
                    f"Selected strategy '{best_strategy.name}' with score {strategy_scores[0][1]:.2f} "
                    f"for task: {task_description[:50]}...",
                    tags=["strategy_selection", best_strategy.name]
                )

            return best_strategy

        return None

    async def _generate_smart_subtasks(
        self,
        task_description: str,
        strategy: Optional[DecompositionStrategy],
        complexity_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[SubTask]:
        """Generate subtasks using strategy template and adaptive logic."""
        subtasks = []

        if strategy and strategy.subtask_template:
            # Use strategy template as base
            for i, subtask_type in enumerate(strategy.subtask_template):
                subtask_id = self._generate_subtask_id(subtask_type)

                # Generate smart task name and description
                task_target = self._extract_task_target(task_description)

                subtask = SubTask(
                    id=subtask_id,
                    name=f"{subtask_type.replace('_', ' ').title()} - {task_target}",
                    description=f"Execute {subtask_type} phase for: {task_description[:80]}...",
                    dependencies=self._calculate_dependencies(i, subtasks, subtask_type),
                    estimated_time=self._estimate_smart_time(subtask_type, complexity_analysis),
                    complexity=self._map_complexity(subtask_type, complexity_analysis["level"]),
                    can_parallelize=self._can_parallelize(subtask_type, i),
                    priority=self._calculate_priority(subtask_type, i),
                    confidence=strategy.success_rate,
                    agent_hint=self._suggest_agent(subtask_type)
                )

                subtasks.append(subtask)
        else:
            # Adaptive decomposition without strategy template
            subtasks = await self._adaptive_decomposition(
                task_description, complexity_analysis, context
            )

        return subtasks

    async def _adaptive_decomposition(
        self,
        task_description: str,
        complexity_analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[SubTask]:
        """Adaptive decomposition when no clear pattern matches."""
        base_phases = [
            "analysis_and_planning",
            "design",
            "implementation",
            "testing",
            "integration",
            "documentation"
        ]

        # Adjust phases based on complexity
        if complexity_analysis["level"] == "high":
            base_phases.insert(1, "architecture_design")
            base_phases.insert(-1, "performance_testing")
            base_phases.insert(-1, "security_review")
        elif complexity_analysis["level"] == "low":
            # Remove some phases for simple tasks
            base_phases = [p for p in base_phases if p not in ["design", "integration"]]

        subtasks = []
        for i, phase in enumerate(base_phases):
            subtask_id = self._generate_subtask_id(phase)

            subtask = SubTask(
                id=subtask_id,
                name=f"{phase.replace('_', ' ').title()}",
                description=f"Execute {phase} for: {task_description[:80]}...",
                dependencies=self._calculate_dependencies(i, subtasks, phase),
                estimated_time=self._estimate_smart_time(phase, complexity_analysis),
                complexity=complexity_analysis["level"],
                can_parallelize=phase in ["documentation", "testing"] or i == 0,
                priority=5,
                confidence=0.6,  # Lower confidence for adaptive
                agent_hint=self._suggest_agent(phase)
            )

            subtasks.append(subtask)

        return subtasks

    def _generate_subtask_id(self, subtask_type: str) -> str:
        """Generate unique subtask ID."""
        self.subtask_counter += 1
        task_hash = hashlib.md5(subtask_type.encode()).hexdigest()[:6]
        return f"st_{task_hash}_{self.subtask_counter:03d}"

    def _calculate_dependencies(
        self,
        index: int,
        existing_subtasks: List[SubTask],
        subtask_type: str
    ) -> List[str]:
        """Calculate smart dependencies based on subtask type and position."""
        dependencies = []

        # Standard sequential dependency
        if index > 0 and subtask_type not in ["documentation", "analysis_and_planning"]:
            dependencies.append(existing_subtasks[index - 1].id)

        # Smart dependencies based on type
        if subtask_type in ["testing", "integration_testing"]:
            # Testing depends on implementation phases
            for subtask in existing_subtasks:
                if "implementation" in subtask.name.lower():
                    if subtask.id not in dependencies:
                        dependencies.append(subtask.id)

        elif subtask_type in ["code_review", "security_review"]:
            # Reviews depend on implementation and testing
            for subtask in existing_subtasks:
                if any(keyword in subtask.name.lower()
                      for keyword in ["implementation", "testing"]):
                    if subtask.id not in dependencies:
                        dependencies.append(subtask.id)

        return dependencies

    def _estimate_smart_time(
        self,
        subtask_type: str,
        complexity_analysis: Dict[str, Any]
    ) -> int:
        """Estimate time with complexity adjustment."""
        base_estimates = {
            "analysis_and_planning": 45,
            "requirements_analysis": 30,
            "architecture_design": 90,
            "design": 60,
            "implementation": 180,
            "unit_testing": 60,
            "integration_testing": 90,
            "testing": 75,
            "performance_testing": 60,
            "security_review": 45,
            "code_review": 30,
            "documentation": 45,
            "integration": 60,
            "deployment": 30
        }

        base_time = base_estimates.get(subtask_type, 60)

        # Adjust for complexity
        if complexity_analysis["level"] == "high":
            multiplier = 1.5
        elif complexity_analysis["level"] == "low":
            multiplier = 0.7
        else:
            multiplier = 1.0

        return int(base_time * multiplier)

    def _map_complexity(self, subtask_type: str, overall_complexity: str) -> str:
        """Map subtask type to complexity level."""
        high_complexity_types = [
            "architecture_design", "implementation", "integration",
            "performance_testing", "security_review"
        ]

        low_complexity_types = [
            "documentation", "analysis_and_planning", "code_review"
        ]

        if subtask_type in high_complexity_types:
            return "high" if overall_complexity == "high" else "medium"
        elif subtask_type in low_complexity_types:
            return "low"
        else:
            return overall_complexity

    def _can_parallelize(self, subtask_type: str, index: int) -> bool:
        """Determine if subtask can be parallelized."""
        always_parallel = [
            "documentation", "analysis_and_planning", "code_review"
        ]

        never_parallel = [
            "implementation", "integration", "deployment"
        ]

        if subtask_type in always_parallel:
            return True
        elif subtask_type in never_parallel:
            return False
        else:
            # Testing can often be parallelized
            return "testing" in subtask_type

    def _calculate_priority(self, subtask_type: str, index: int) -> int:
        """Calculate priority (1-10, higher is more important)."""
        high_priority_types = [
            "analysis_and_planning", "architecture_design",
            "implementation", "security_review"
        ]

        if subtask_type in high_priority_types:
            return 8
        elif "testing" in subtask_type:
            return 7
        elif subtask_type in ["documentation", "code_review"]:
            return 5
        else:
            return 6

    def _suggest_agent(self, subtask_type: str) -> Optional[str]:
        """Suggest best agent type for subtask."""
        agent_mapping = {
            "implementation": "code-writer",
            "code_review": "CodeReviewer",
            "testing": "TestWriter",
            "unit_testing": "TestWriter",
            "integration_testing": "TestWriter",
            "performance_testing": "TestWriter",
            "documentation": "ReadmeAgent",
            "security_review": "CodeReviewer",
            "architecture_design": "architect",
            "design": "architect"
        }

        return agent_mapping.get(subtask_type)

    def _extract_task_target(self, task_description: str) -> str:
        """Extract the main target/object from task description."""
        words = task_description.split()

        # Skip action words and get the meat of the task
        skip_words = {
            "implement", "create", "build", "develop", "add", "fix",
            "resolve", "debug", "patch", "repair", "refactor", "optimize"
        }

        meaningful_words = [w for w in words if w.lower() not in skip_words]

        if len(meaningful_words) >= 3:
            return " ".join(meaningful_words[:3])
        elif meaningful_words:
            return " ".join(meaningful_words)
        else:
            return "task"

    async def _analyze_dependencies_smart(
        self,
        subtasks: List[SubTask]
    ) -> Dict[str, List[str]]:
        """Enhanced dependency analysis with pattern learning."""
        dependency_graph = {}

        # Start with explicit dependencies
        for subtask in subtasks:
            dependency_graph[subtask.id] = subtask.dependencies.copy()

        # Apply learned dependency patterns
        await self._apply_dependency_patterns(subtasks, dependency_graph)

        # Validate and optimize dependency graph
        await self._optimize_dependency_graph(subtasks, dependency_graph)

        return dependency_graph

    async def _apply_dependency_patterns(
        self,
        subtasks: List[SubTask],
        dependency_graph: Dict[str, List[str]]
    ) -> None:
        """Apply learned dependency patterns."""
        # Get knowledge about dependency patterns
        dependency_knowledge = await self.get_relevant_knowledge("dependency patterns")

        for subtask in subtasks:
            subtask_name = subtask.name.lower()

            # Pattern: Testing always depends on implementation
            if "test" in subtask_name:
                for other in subtasks:
                    if ("implement" in other.name.lower() or
                        "code" in other.name.lower()) and \
                       other.id != subtask.id and \
                       other.id not in dependency_graph[subtask.id]:
                        dependency_graph[subtask.id].append(other.id)

            # Pattern: Reviews depend on implementation
            if "review" in subtask_name:
                for other in subtasks:
                    if ("implement" in other.name.lower() or
                        "develop" in other.name.lower()) and \
                       other.id != subtask.id and \
                       other.id not in dependency_graph[subtask.id]:
                        dependency_graph[subtask.id].append(other.id)

            # Pattern: Integration depends on individual components
            if "integration" in subtask_name:
                for other in subtasks:
                    if ("implement" in other.name.lower() or
                        "unit_test" in other.name.lower()) and \
                       other.id != subtask.id and \
                       other.id not in dependency_graph[subtask.id]:
                        dependency_graph[subtask.id].append(other.id)

    async def _optimize_dependency_graph(
        self,
        subtasks: List[SubTask],
        dependency_graph: Dict[str, List[str]]
    ) -> None:
        """Optimize dependency graph to maximize parallelization."""
        # Remove unnecessary dependencies that don't add value
        subtask_map = {st.id: st for st in subtasks}

        for subtask_id, deps in dependency_graph.items():
            subtask = subtask_map[subtask_id]

            # If subtask can parallelize, remove non-critical dependencies
            if subtask.can_parallelize:
                critical_deps = []
                for dep_id in deps:
                    dep_subtask = subtask_map.get(dep_id)
                    if dep_subtask and self._is_critical_dependency(subtask, dep_subtask):
                        critical_deps.append(dep_id)

                dependency_graph[subtask_id] = critical_deps

    def _is_critical_dependency(self, subtask: SubTask, dependency: SubTask) -> bool:
        """Determine if a dependency is critical or can be relaxed."""
        # Implementation must complete before testing
        if "test" in subtask.name.lower() and "implement" in dependency.name.lower():
            return True

        # Architecture/design must complete before implementation
        if "implement" in subtask.name.lower() and \
           ("design" in dependency.name.lower() or "architect" in dependency.name.lower()):
            return True

        # Analysis must complete before design
        if "design" in subtask.name.lower() and "analysis" in dependency.name.lower():
            return True

        # Otherwise, dependency might be relaxable
        return False

    async def _estimate_parallelization_optimized(
        self,
        subtasks: List[SubTask],
        dependency_graph: Dict[str, List[str]],
        strategy: Optional[DecompositionStrategy]
    ) -> float:
        """Enhanced parallelization estimation with learning."""
        if not subtasks:
            return 0.0

        # Calculate based on dependency analysis
        critical_path_time = await self._calculate_critical_path(subtasks, dependency_graph)
        total_sequential_time = sum(st.estimated_time or 60 for st in subtasks)

        if total_sequential_time == 0:
            return 0.0

        # Base parallelization score
        base_score = 1.0 - (critical_path_time / total_sequential_time)

        # Adjust based on parallelizable tasks
        parallelizable_count = sum(1 for st in subtasks if st.can_parallelize)
        parallelization_factor = parallelizable_count / len(subtasks)

        # Use strategy learning if available
        if strategy:
            learned_factor = strategy.avg_parallelization
            # Weighted average of calculated and learned values
            final_score = (base_score * 0.6) + (learned_factor * 0.4)
        else:
            final_score = (base_score * 0.7) + (parallelization_factor * 0.3)

        return min(max(final_score, 0.0), 1.0)

    async def _calculate_critical_path(
        self,
        subtasks: List[SubTask],
        dependency_graph: Dict[str, List[str]]
    ) -> int:
        """Calculate critical path length through dependency graph."""
        subtask_map = {st.id: st for st in subtasks}
        memo: Dict[str, int] = {}

        def get_path_length(subtask_id: str) -> int:
            if subtask_id in memo:
                return memo[subtask_id]

            subtask = subtask_map.get(subtask_id)
            if not subtask:
                return 0

            subtask_time = subtask.estimated_time or 60
            dependencies = dependency_graph.get(subtask_id, [])

            if not dependencies:
                memo[subtask_id] = subtask_time
                return subtask_time

            max_dep_time = max(get_path_length(dep) for dep in dependencies)
            total_time = subtask_time + max_dep_time
            memo[subtask_id] = total_time
            return total_time

        return max(get_path_length(st.id) for st in subtasks)

    async def _estimate_time_with_confidence(
        self,
        subtasks: List[SubTask],
        dependency_graph: Dict[str, List[str]],
        parallelization_score: float,
        strategy: Optional[DecompositionStrategy]
    ) -> Tuple[int, float]:
        """Estimate total time with confidence interval."""
        critical_path_time = await self._calculate_critical_path(subtasks, dependency_graph)

        # Adjust for parallelization potential
        time_savings = parallelization_score * 0.4  # Conservative estimate
        estimated_time = int(critical_path_time * (1 - time_savings))

        # Calculate confidence based on multiple factors
        confidence_factors = []

        # Strategy confidence
        if strategy:
            confidence_factors.append(strategy.success_rate * 0.4)

        # Subtask confidence average
        subtask_confidences = [st.confidence for st in subtasks if st.confidence]
        if subtask_confidences:
            confidence_factors.append(sum(subtask_confidences) / len(subtask_confidences) * 0.3)

        # Dependency clarity confidence
        clear_dependencies = sum(1 for deps in dependency_graph.values() if deps)
        dep_confidence = clear_dependencies / len(subtasks) * 0.3
        confidence_factors.append(dep_confidence)

        # Overall confidence
        overall_confidence = sum(confidence_factors) if confidence_factors else 0.6
        overall_confidence = min(max(overall_confidence, 0.3), 0.95)

        return estimated_time, overall_confidence

    async def _generate_optimization_suggestions(
        self,
        subtasks: List[SubTask],
        dependency_graph: Dict[str, List[str]],
        parallelization_score: float
    ) -> List[str]:
        """Generate suggestions for optimizing the decomposition."""
        suggestions = []

        # Parallelization suggestions
        if parallelization_score < 0.5:
            suggestions.append(
                "Consider breaking down implementation tasks into smaller, "
                "more independent components to increase parallelization"
            )

        # Dependency optimization
        highly_dependent_tasks = [
            st.id for st in subtasks
            if len(dependency_graph.get(st.id, [])) > 2
        ]

        if highly_dependent_tasks:
            suggestions.append(
                f"Tasks with many dependencies might benefit from refactoring: "
                f"{len(highly_dependent_tasks)} tasks have 3+ dependencies"
            )

        # Time distribution analysis
        time_estimates = [st.estimated_time or 60 for st in subtasks]
        if time_estimates:
            max_time = max(time_estimates)
            avg_time = sum(time_estimates) / len(time_estimates)

            if max_time > avg_time * 2:
                suggestions.append(
                    "Consider breaking down the longest task to better balance workload"
                )

        # Agent specialization suggestions
        agent_counts = {}
        for st in subtasks:
            if st.agent_hint:
                agent_counts[st.agent_hint] = agent_counts.get(st.agent_hint, 0) + 1

        if len(agent_counts) > 3:
            suggestions.append(
                f"Tasks require {len(agent_counts)} different agent types - "
                f"consider consolidating similar tasks for better efficiency"
            )

        return suggestions

    async def _store_decomposition_result(self, result: DecompositionResult) -> None:
        """Store decomposition result in memory for learning."""
        # Store as procedural memory
        steps = [f"{st.name}: {st.description[:50]}..." for st in result.subtasks]

        # Store as procedural memory - using learn_procedure instead of store_procedure
        if self.memory:
            procedure_id = await self.memory.learn_procedure(
                procedure_name=f"decomposition_{result.strategy_used or 'adaptive'}",
                steps=steps,
                context=f"Decomposed '{result.original_task}' into {len(result.subtasks)} "
                       f"subtasks with {result.parallelization_score:.1%} parallelization"
            )
        else:
            procedure_id = None

        # Store detailed result as long-term memory
        detailed_result = {
            "original_task": result.original_task,
            "subtask_count": len(result.subtasks),
            "parallelization_score": result.parallelization_score,
            "estimated_time": result.estimated_total_time,
            "strategy_used": result.strategy_used,
            "confidence": result.confidence_score,
            "optimizations": result.optimization_suggestions
        }

        if self.memory:
            await self.memory.remember_long_term(
                f"decomposition_result: {json.dumps(detailed_result)}",
                tags=["decomposition", "result", result.strategy_used or "adaptive"],
                importance=0.8
            )

    async def _update_strategy_in_memory(self, strategy: DecompositionStrategy) -> None:
        """Update strategy information in memory."""
        strategy_data = {
            "name": strategy.name,
            "pattern": strategy.pattern,
            "success_rate": strategy.success_rate,
            "avg_parallelization": strategy.avg_parallelization,
            "avg_completion_time": strategy.avg_completion_time,
            "usage_count": strategy.usage_count,
            "last_used": strategy.last_used.isoformat(),
            "complexity_level": strategy.complexity_level,
            "triggers": strategy.triggers,
            "subtask_template": strategy.subtask_template
        }

        if self.memory:
            await self.memory.remember_long_term(
                f"decomposition_strategy: {json.dumps(strategy_data)}",
                tags=["strategy", "learning", strategy.name],
                importance=0.9
            )

    async def learn_from_execution(self, feedback: ExecutionFeedback) -> None:
        """Learn from execution feedback to improve future decompositions."""
        # Update performance metrics
        self.total_decompositions += 1
        if feedback.success_rate > 0.8:
            self.successful_decompositions += 1

        # Update average parallelization achieved
        alpha = 0.1  # Learning rate
        self.avg_parallelization_achieved = (
            alpha * feedback.parallelization_achieved +
            (1 - alpha) * self.avg_parallelization_achieved
        )

        # Store feedback as learning experience
        if self.memory:
            await self.memory.remember_long_term(
                f"execution_feedback: {json.dumps(asdict(feedback))}",
                tags=["feedback", "learning", "execution"],
                importance=0.9
            )

        # Learn from specific aspects
        await self._learn_from_bottlenecks(feedback.bottlenecks)
        await self._learn_from_improvements(feedback.improvements)
        await self._update_agent_performance_knowledge(feedback.agent_performance)

        # Update relevant strategies
        strategy_name = None
        if self.memory:
            decomposition_memories = await self.memory.recall_memories(
                memory_type="semantic",
                limit=10
            )
        else:
            decomposition_memories = []

        for memory in decomposition_memories:
            if feedback.decomposition_id in memory.get('content', ''):
                # Extract strategy name from memory
                content = memory.get('content', '')
                if 'strategy_used' in content:
                    try:
                        data = json.loads(content.split('decomposition_result:')[1])
                        strategy_name = data.get('strategy_used')
                        break
                    except:
                        continue

        if strategy_name and strategy_name in self.strategies:
            await self._update_strategy_performance(
                strategy_name, feedback.success_rate, feedback.parallelization_achieved
            )

        print(f"📈 Learned from execution: {feedback.success_rate:.1%} success, "
              f"{feedback.parallelization_achieved:.1%} parallelization achieved")

    async def _learn_from_bottlenecks(self, bottlenecks: List[str]) -> None:
        """Learn patterns from identified bottlenecks."""
        if self.memory:
            for bottleneck in bottlenecks:
                await self.memory.remember_long_term(
                    f"bottleneck_pattern: {bottleneck}",
                    tags=["bottleneck", "learning", "optimization"],
                    importance=0.8
                )

    async def _learn_from_improvements(self, improvements: List[str]) -> None:
        """Learn patterns from successful improvements."""
        if self.memory:
            for improvement in improvements:
                await self.memory.remember_long_term(
                    f"improvement_pattern: {improvement}",
                    tags=["improvement", "learning", "optimization"],
                    importance=0.7
                )

    async def _update_agent_performance_knowledge(
        self,
        agent_performance: Dict[str, float]
    ) -> None:
        """Update knowledge about agent performance for different task types."""
        if self.memory:
            for agent_type, performance in agent_performance.items():
                await self.memory.remember_long_term(
                    f"agent_performance: {agent_type} scored {performance:.2f}",
                    tags=["agent_performance", agent_type, "learning"],
                    importance=0.6
                )

    async def _update_strategy_performance(
        self,
        strategy_name: str,
        success_rate: float,
        parallelization_achieved: float
    ) -> None:
        """Update strategy performance metrics."""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]

            # Update with exponential moving average
            alpha = 0.2
            strategy.success_rate = (
                alpha * success_rate + (1 - alpha) * strategy.success_rate
            )
            strategy.avg_parallelization = (
                alpha * parallelization_achieved +
                (1 - alpha) * strategy.avg_parallelization
            )

            # Save updated strategy
            await self._update_strategy_in_memory(strategy)

    async def get_decomposition_insights(self) -> Dict[str, Any]:
        """Get insights about decomposition patterns and performance."""
        # Calculate performance metrics
        success_rate = (
            self.successful_decompositions / self.total_decompositions
            if self.total_decompositions > 0 else 0.0
        )

        # Get strategy performance
        strategy_performance = {}
        for name, strategy in self.strategies.items():
            strategy_performance[name] = {
                "success_rate": strategy.success_rate,
                "usage_count": strategy.usage_count,
                "avg_parallelization": strategy.avg_parallelization,
                "last_used": strategy.last_used.isoformat()
            }

        # Get recent learning
        if self.memory:
            recent_memories = await self.memory.recall_memories(
                memory_type="semantic",
                limit=20
            )
        else:
            recent_memories = []

        learning_insights = []
        for memory in recent_memories:
            content = memory.get('content', '')
            if any(keyword in content for keyword in ['bottleneck', 'improvement', 'feedback']):
                learning_insights.append(content[:100] + "...")

        return {
            "performance_metrics": {
                "total_decompositions": self.total_decompositions,
                "success_rate": success_rate,
                "avg_parallelization_achieved": self.avg_parallelization_achieved
            },
            "strategy_performance": strategy_performance,
            "learning_insights": learning_insights[:10],
            "capabilities": {
                "strategies_learned": len(self.strategies),
                "pattern_confidence_threshold": self.pattern_confidence_threshold,
                "max_parallel_tasks": self.capabilities.max_parallel_tasks
            }
        }

    async def can_handle_task(self, task_description: str) -> bool:
        """Check if this agent can handle the task."""
        # Task decomposer can handle any task that needs decomposition
        decomposition_keywords = [
            "decompose", "break down", "split", "divide", "subtask",
            "complex", "multi-step", "workflow", "process"
        ]

        task_lower = task_description.lower()

        # Direct decomposition requests
        if any(keyword in task_lower for keyword in decomposition_keywords):
            return True

        # Complex tasks that would benefit from decomposition
        complexity_indicators = [
            "implement", "build", "create", "develop", "system",
            "integration", "multiple", "comprehensive", "full"
        ]

        if any(indicator in task_lower for indicator in complexity_indicators):
            return True

        # Always available as a general decomposition service
        return True


# Example usage and testing
async def test_task_decomposer_v03():
    """Test the enhanced task decomposer."""
    print("\n" + "="*60)
    print("Testing Task Decomposer v0.3 with Learning")
    print("="*60)

    # Create and initialize decomposer
    decomposer = TaskDecomposerV03()

    try:
        await decomposer.initialize()

        # Test complex task decomposition
        task = {
            "description": "Implement a microservices-based e-commerce platform with user authentication, payment processing, and inventory management",
            "context": {
                "time_constraint": "3 months",
                "team_size": 5,
                "parallel_capable": True,
                "dependencies": ["database", "payment_gateway"]
            }
        }

        print(f"\n📋 Decomposing complex task...")
        outcome = await decomposer.execute_task(task)

        print(f"✅ Decomposition completed: {outcome.success}")
        print(f"🎯 Steps taken: {len(outcome.steps_taken)}")

        # Simulate execution feedback
        feedback = ExecutionFeedback(
            decomposition_id="test_123",
            actual_completion_time=150.0,
            success_rate=0.9,
            parallelization_achieved=0.7,
            bottlenecks=["database_setup", "payment_integration"],
            improvements=["parallel_testing", "automated_deployment"],
            agent_performance={
                "code-writer": 0.85,
                "TestWriter": 0.90,
                "CodeReviewer": 0.88
            }
        )

        print(f"\n📊 Learning from execution feedback...")
        await decomposer.learn_from_execution(feedback)

        # Get insights
        insights = await decomposer.get_decomposition_insights()
        print(f"\n🧠 Current insights:")
        print(f"  Success rate: {insights['performance_metrics']['success_rate']:.1%}")
        print(f"  Strategies learned: {insights['capabilities']['strategies_learned']}")

        print(f"\n✅ Test completed successfully!")

    finally:
        await decomposer.shutdown()


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_task_decomposer_v03())
