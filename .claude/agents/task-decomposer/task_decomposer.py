from typing import Any, Dict, List, Optional, Tuple

import hashlib
import json
import logging

"""Task Decomposer Agent - Intelligently decomposes complex tasks into manageable subtasks."""

from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SubTask:
    """Represents a single subtask within a decomposition."""

    id: str
    name: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_time: Optional[int] = None
    complexity: str = "medium"
    can_parallelize: bool = True
    resource_requirements: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert SubTask to dictionary representation."""
        return asdict(self)

@dataclass
class DecompositionResult:
    """Result of task decomposition operation."""

    original_task: str
    subtasks: List[SubTask]
    dependency_graph: Dict[str, List[str]]
    parallelization_score: float
    estimated_total_time: int
    decomposition_pattern: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert DecompositionResult to dictionary representation."""
        return {
            "original_task": self.original_task,
            "subtasks": [task.to_dict() for task in self.subtasks],
            "dependency_graph": self.dependency_graph,
            "parallelization_score": self.parallelization_score,
            "estimated_total_time": self.estimated_total_time,
            "decomposition_pattern": self.decomposition_pattern,
        }

class PatternDatabase:
    """Simulated pattern database for learning and retrieval."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize pattern database."""
        self.storage_path = storage_path or Path(".decomposer_patterns.json")
        self.patterns: Dict[str, Any] = self._load_patterns()

    def _load_patterns(self) -> Dict[str, Any]:
        """Load patterns from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
        return self._get_default_patterns()

    def _get_default_patterns(self) -> Dict[str, Any]:
        """Get default decomposition patterns."""
        return {
            "feature_implementation": {
                "triggers": ["implement", "create", "build", "develop", "add"],
                "subtasks": ["design", "implement", "test", "document", "review"],
                "avg_parallelization": 0.6,
                "success_rate": 0.85,
            },
            "bug_fix": {
                "triggers": ["fix", "resolve", "debug", "patch", "repair"],
                "subtasks": ["reproduce", "diagnose", "fix", "test", "verify"],
                "avg_parallelization": 0.3,
                "success_rate": 0.9,
            },
            "refactoring": {
                "triggers": ["refactor", "optimize", "improve", "enhance", "clean"],
                "subtasks": ["analyze", "plan", "refactor", "test", "validate"],
                "avg_parallelization": 0.5,
                "success_rate": 0.8,
            },
            "testing": {
                "triggers": ["test", "validate", "verify", "check", "ensure"],
                "subtasks": ["setup", "execute", "analyze", "report", "cleanup"],
                "avg_parallelization": 0.7,
                "success_rate": 0.95,
            },
            "documentation": {
                "triggers": ["document", "write", "describe", "explain"],
                "subtasks": ["outline", "draft", "review", "revise", "publish"],
                "avg_parallelization": 0.8,
                "success_rate": 0.9,
            },
        }

    def save_patterns(self) -> None:
        """Save patterns to storage."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")

    def find_matching_pattern(self, task_description: str) -> Optional[str]:
        """Find a matching pattern for the given task description."""
        task_lower = task_description.lower()
        for pattern_name, pattern_data in self.patterns.items():
            for trigger in pattern_data["triggers"]:
                if trigger in task_lower:
                    return pattern_name
        return None

    def update_pattern_metrics(
        self, pattern_name: str, success: bool, parallelization_score: float
    ) -> None:
        """Update pattern success metrics."""
        if pattern_name in self.patterns:
            pattern = self.patterns[pattern_name]
            # Update success rate with exponential moving average
            alpha = 0.1
            current_rate = pattern.get("success_rate", 0.5)
            pattern["success_rate"] = (
                alpha * (1.0 if success else 0.0) + (1 - alpha) * current_rate
            )

            # Update parallelization score
            current_parallel = pattern.get("avg_parallelization", 0.5)
            pattern["avg_parallelization"] = (
                alpha * parallelization_score + (1 - alpha) * current_parallel
            )

            self.save_patterns()

class TaskDecomposer:
    """Intelligently decomposes complex tasks into manageable subtasks."""

    def __init__(self, patterns_db: Optional[PatternDatabase] = None):
        """Initialize the TaskDecomposer."""
        self.patterns_db = patterns_db or PatternDatabase()
        self.subtask_counter = 0

    def _generate_subtask_id(self, task_name: str) -> str:
        """Generate unique subtask ID."""
        self.subtask_counter += 1
        task_hash = hashlib.md5(task_name.encode()).hexdigest()[:8]
        return f"subtask_{task_hash}_{self.subtask_counter:03d}"

    async def decompose_task(
        self, task_description: str, context: Optional[Dict[str, Any]] = None
    ) -> DecompositionResult:
        """
        Main decomposition logic.

        Args:
            task_description: Description of the task to decompose
            context: Optional additional context for decomposition

        Returns:
            DecompositionResult containing subtasks and analysis
        """
        # Find matching pattern
        pattern_name = self.patterns_db.find_matching_pattern(task_description)

        # Generate subtasks based on pattern or default analysis
        subtasks = await self._generate_subtasks(
            task_description, pattern_name, context
        )

        # Analyze dependencies
        dependency_graph = await self.analyze_dependencies(subtasks)

        # Estimate parallelization potential
        parallelization_score = await self.estimate_parallelization(
            subtasks, dependency_graph
        )

        # Calculate total estimated time
        estimated_total_time = self._calculate_total_time(
            subtasks, dependency_graph, parallelization_score
        )

        return DecompositionResult(
            original_task=task_description,
            subtasks=subtasks,
            dependency_graph=dependency_graph,
            parallelization_score=parallelization_score,
            estimated_total_time=estimated_total_time,
            decomposition_pattern=pattern_name,
        )

    async def _generate_subtasks(
        self,
        task_description: str,
        pattern_name: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> List[SubTask]:
        """Generate subtasks based on pattern or task analysis."""
        subtasks = []

        if pattern_name and pattern_name in self.patterns_db.patterns:
            # Use pattern-based decomposition
            pattern = self.patterns_db.patterns[pattern_name]
            for i, subtask_type in enumerate(pattern["subtasks"]):
                subtask_id = self._generate_subtask_id(subtask_type)
                subtasks.append(
                    SubTask(
                        id=subtask_id,
                        name=f"{subtask_type.capitalize()} for {self._extract_task_target(task_description)}",
                        description=f"{subtask_type.capitalize()} phase of: {task_description}",
                        dependencies=[subtasks[i - 1].id] if i > 0 else [],
                        estimated_time=self._estimate_subtask_time(subtask_type),
                        complexity=self._estimate_complexity(subtask_type),
                        can_parallelize=i == 0 or subtask_type in ["test", "document"],
                    )
                )
        else:
            # Default decomposition for unknown patterns
            subtasks = await self._default_decomposition(task_description, context)

        return subtasks

    async def _default_decomposition(
        self, task_description: str, context: Optional[Dict[str, Any]]
    ) -> List[SubTask]:
        """Default decomposition strategy when no pattern matches."""
        subtasks = []

        # Basic phases for any task
        phases = [
            ("analysis", "Analyze requirements and constraints", "low", 30),
            ("design", "Design solution approach", "medium", 60),
            ("implementation", "Implement core functionality", "high", 120),
            ("testing", "Test and validate implementation", "medium", 60),
            ("integration", "Integrate with existing system", "medium", 45),
            ("documentation", "Document changes and usage", "low", 30),
        ]

        for i, (phase, description, complexity, time) in enumerate(phases):
            subtask_id = self._generate_subtask_id(phase)
            dependencies = []

            # Set up dependencies
            if phase == "design":
                dependencies = [subtasks[0].id]  # Depends on analysis
            elif phase in ["implementation", "testing"]:
                dependencies = [subtasks[i - 1].id]  # Sequential dependency
            elif phase == "integration":
                dependencies = [st.id for st in subtasks if st.name.startswith("Test")]
            elif phase == "documentation":
                dependencies = []  # Can run in parallel

            subtasks.append(
                SubTask(
                    id=subtask_id,
                    name=f"{phase.capitalize()} phase",
                    description=f"{description} for: {task_description[:100]}",
                    dependencies=dependencies,
                    estimated_time=time,
                    complexity=complexity,
                    can_parallelize=phase in ["documentation", "analysis"],
                )
            )

        return subtasks

    def _extract_task_target(self, task_description: str) -> str:
        """Extract the main target/object from task description."""
        # Simple extraction - take first few meaningful words after action verb
        words = task_description.split()
        if len(words) > 3:
            return " ".join(words[1:4])
        return "task"

    def _estimate_subtask_time(self, subtask_type: str) -> int:
        """Estimate time for a subtask type in minutes."""
        time_estimates = {
            "design": 60,
            "implement": 120,
            "test": 60,
            "document": 30,
            "review": 45,
            "reproduce": 15,
            "diagnose": 45,
            "fix": 90,
            "verify": 30,
            "analyze": 45,
            "plan": 30,
            "refactor": 90,
            "validate": 30,
            "setup": 15,
            "execute": 60,
            "report": 20,
            "cleanup": 10,
            "outline": 20,
            "draft": 60,
            "revise": 30,
            "publish": 15,
        }
        return time_estimates.get(subtask_type, 60)

    def _estimate_complexity(self, subtask_type: str) -> str:
        """Estimate complexity for a subtask type."""
        complexity_map = {
            "design": "medium",
            "implement": "high",
            "test": "medium",
            "document": "low",
            "review": "medium",
            "reproduce": "low",
            "diagnose": "high",
            "fix": "high",
            "verify": "low",
            "analyze": "medium",
            "plan": "medium",
            "refactor": "high",
            "validate": "medium",
            "setup": "low",
            "execute": "medium",
            "report": "low",
            "cleanup": "low",
            "outline": "low",
            "draft": "medium",
            "revise": "medium",
            "publish": "low",
        }
        return complexity_map.get(subtask_type, "medium")

    async def analyze_dependencies(
        self, subtasks: List[SubTask]
    ) -> Dict[str, List[str]]:
        """
        Identify dependencies between subtasks.

        Args:
            subtasks: List of subtasks to analyze

        Returns:
            Dictionary mapping subtask IDs to their dependencies
        """
        dependency_graph = {}

        for subtask in subtasks:
            dependency_graph[subtask.id] = subtask.dependencies.copy()

        # Detect implicit dependencies based on task names
        for subtask in subtasks:
            # Testing depends on implementation
            if "test" in subtask.name.lower():
                for other in subtasks:
                    if (
                        "implement" in other.name.lower()
                        and other.id not in dependency_graph[subtask.id]
                    ):
                        dependency_graph[subtask.id].append(other.id)

            # Documentation can depend on implementation but not block it
            if "document" in subtask.name.lower():
                # Remove documentation from critical path
                dependency_graph[subtask.id] = []

            # Review depends on implementation and testing
            if "review" in subtask.name.lower():
                for other in subtasks:
                    if (
                        "implement" in other.name.lower()
                        or "test" in other.name.lower()
                    ) and other.id not in dependency_graph[subtask.id]:
                        dependency_graph[subtask.id].append(other.id)

        return dependency_graph

    async def estimate_parallelization(
        self, subtasks: List[SubTask], dependencies: Dict[str, List[str]]
    ) -> float:
        """
        Calculate parallelization potential (0-1 scale).

        Args:
            subtasks: List of subtasks
            dependencies: Dependency graph

        Returns:
            Score between 0 (fully sequential) and 1 (fully parallel)
        """
        if not subtasks:
            return 0.0

        # Calculate critical path length
        critical_path_length = await self._find_critical_path_length(
            subtasks, dependencies
        )

        # Calculate total work if done sequentially
        total_sequential_time = sum(task.estimated_time or 60 for task in subtasks)

        # Calculate parallelization score
        if total_sequential_time == 0:
            return 0.0

        # The more we can reduce time through parallelization, the higher the score
        parallelization_score = 1.0 - (critical_path_length / total_sequential_time)

        # Account for subtasks that can be parallelized
        parallelizable_count = sum(1 for task in subtasks if task.can_parallelize)
        parallelization_factor = parallelizable_count / len(subtasks)

        # Weighted average of time reduction and parallelizable tasks
        final_score = (parallelization_score * 0.7) + (parallelization_factor * 0.3)

        return min(max(final_score, 0.0), 1.0)

    async def _find_critical_path_length(
        self, subtasks: List[SubTask], dependencies: Dict[str, List[str]]
    ) -> int:
        """Find the length of the critical path through the dependency graph."""
        # Create a mapping of task IDs to tasks
        task_map = {task.id: task for task in subtasks}

        # Memoization for path lengths
        memo: Dict[str, int] = {}

        def get_max_path_length(task_id: str) -> int:
            """Recursively find maximum path length from this task."""
            if task_id in memo:
                return memo[task_id]

            task = task_map.get(task_id)
            if not task:
                return 0

            task_time = task.estimated_time or 60

            # If no dependencies, this task's time is its path length
            if task_id not in dependencies or not dependencies[task_id]:
                memo[task_id] = task_time
                return task_time

            # Find maximum path length through dependencies
            max_dep_length = 0
            for dep_id in dependencies[task_id]:
                dep_length = get_max_path_length(dep_id)
                max_dep_length = max(max_dep_length, dep_length)

            total_length = task_time + max_dep_length
            memo[task_id] = total_length
            return total_length

        # Find maximum path length across all tasks
        max_path_length = 0
        for task in subtasks:
            path_length = get_max_path_length(task.id)
            max_path_length = max(max_path_length, path_length)

        return max_path_length

    def _calculate_total_time(
        self,
        subtasks: List[SubTask],
        dependencies: Dict[str, List[str]],
        parallelization_score: float,
    ) -> int:
        """Calculate total estimated time considering parallelization."""
        if not subtasks:
            return 0

        total_sequential_time = sum(task.estimated_time or 60 for task in subtasks)

        # Adjust time based on parallelization potential
        # Higher parallelization score means more time savings
        time_reduction_factor = parallelization_score * 0.5  # Max 50% time reduction
        estimated_time = int(total_sequential_time * (1 - time_reduction_factor))

        return max(estimated_time, 30)  # Minimum 30 minutes for any task

    async def learn_pattern(
        self, result: DecompositionResult, success_metrics: Dict[str, Any]
    ) -> None:
        """
        Store successful decomposition patterns for future use.

        Args:
            result: The decomposition result
            success_metrics: Metrics about the success of this decomposition
        """
        if result.decomposition_pattern:
            # Update existing pattern metrics
            success = success_metrics.get("success", True)
            self.patterns_db.update_pattern_metrics(
                result.decomposition_pattern, success, result.parallelization_score
            )
        else:
            # Potentially learn a new pattern
            await self._learn_new_pattern(result, success_metrics)

    async def _learn_new_pattern(
        self, result: DecompositionResult, success_metrics: Dict[str, Any]
    ) -> None:
        """Learn a new decomposition pattern from successful execution."""
        # Extract key words from the original task
        task_words = result.original_task.lower().split()

        # Find action verbs that could be triggers
        common_verbs = {
            "implement",
            "create",
            "build",
            "fix",
            "test",
            "refactor",
            "optimize",
            "document",
        }
        triggers = [word for word in task_words if word in common_verbs]

        if triggers and success_metrics.get("success", False):
            # Create a new pattern entry
            pattern_name = (
                f"learned_{hashlib.md5(result.original_task.encode()).hexdigest()[:8]}"
            )

            subtask_types = []
            for subtask in result.subtasks:
                # Extract subtask type from name
                subtask_type = subtask.name.split()[0].lower()
                if subtask_type not in subtask_types:
                    subtask_types.append(subtask_type)

            self.patterns_db.patterns[pattern_name] = {
                "triggers": triggers,
                "subtasks": subtask_types,
                "avg_parallelization": result.parallelization_score,
                "success_rate": 1.0 if success_metrics.get("success") else 0.0,
                "learned_from": result.original_task[:100],
            }

            self.patterns_db.save_patterns()
            logger.info(f"Learned new pattern: {pattern_name}")

    async def find_similar_patterns(self, task_description: str) -> List[str]:
        """
        Retrieve similar decomposition patterns from history.

        Args:
            task_description: Task to find patterns for

        Returns:
            List of similar pattern names
        """
        similar_patterns = []
        task_lower = task_description.lower()

        # Score each pattern based on trigger word matches
        pattern_scores: List[Tuple[str, float]] = []

        for pattern_name, pattern_data in self.patterns_db.patterns.items():
            score = 0.0
            for trigger in pattern_data["triggers"]:
                if trigger in task_lower:
                    score += 1.0

            # Boost score by success rate
            score *= pattern_data.get("success_rate", 0.5)

            if score > 0:
                pattern_scores.append((pattern_name, score))

        # Sort by score and return top patterns
        pattern_scores.sort(key=lambda x: x[1], reverse=True)
        similar_patterns = [name for name, _ in pattern_scores[:3]]

        return similar_patterns
