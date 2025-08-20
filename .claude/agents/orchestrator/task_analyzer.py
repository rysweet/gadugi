"""Task analyzer for dependency detection and optimization."""

import ast
import logging
import re
from dataclasses import dataclass
from pathlib import   # type: ignore
from typing import Any, Dict, List, Optional, Set, Tuple  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class TaskDependency:
    """Represents a dependency between tasks."""

    dependent_id: str
    prerequisite_id: str
    dependency_type: str  # "file", "import", "explicit", "resource"
    confidence: float = 1.0  # 0.0 to 1.0
    reason: str = ""


class TaskAnalyzer:
    """Analyzer for task dependencies and optimization opportunities."""

    def __init__(self):
        """Initialize the task analyzer."""
        self.file_dependencies: Dict[str, Set[str]] = {}
        self.import_graph: Dict[str, Set[str]] = {}
        self.resource_locks: Dict[str, str] = {}

    async def analyze_dependencies(
        self,
        tasks: List[Any],
    ) -> List[TaskDependency]:
        """Analyze tasks for implicit dependencies.

        Args:
            tasks: List of tasks to analyze

        Returns:
            List of discovered dependencies
        """
        dependencies = []

        # Analyze file dependencies
        file_deps = self._analyze_file_dependencies(tasks)
        dependencies.extend(file_deps)

        # Analyze import dependencies
        import_deps = self._analyze_import_dependencies(tasks)
        dependencies.extend(import_deps)

        # Analyze resource conflicts
        resource_deps = self._analyze_resource_conflicts(tasks)
        dependencies.extend(resource_deps)

        # Remove duplicate dependencies
        unique_deps = self._deduplicate_dependencies(dependencies)

        logger.info(f"Discovered {len(unique_deps)} dependencies among {len(tasks)} tasks")
        return unique_deps

    def _analyze_file_dependencies(self, tasks: List[Any]) -> List[TaskDependency]:
        """Analyze file-based dependencies between tasks.

        Args:
            tasks: List of tasks

        Returns:
            File dependencies
        """
        dependencies = []
        file_map: Dict[str, List[str]] = {}  # file -> task IDs that modify it

        for task in tasks:
            task_id = task.id if hasattr(task, "id") else str(task)

            # Extract files from task parameters or description
            files = self._extract_files_from_task(task)

            for file_path in files:
                if file_path in file_map:
                    # Create dependencies with all previous tasks that modify this file
                    for prev_task_id in file_map[file_path]:
                        dep = TaskDependency(
                            dependent_id=task_id,
                            prerequisite_id=prev_task_id,
                            dependency_type="file",
                            confidence=0.9,
                            reason=f"Both tasks modify {file_path}",
                        )
                        dependencies.append(dep)

                # Add this task to the file map
                if file_path not in file_map:
                    file_map[file_path] = []
                file_map[file_path].append(task_id)

        return dependencies

    def _analyze_import_dependencies(self, tasks: List[Any]) -> List[TaskDependency]:
        """Analyze Python import dependencies between tasks.

        Args:
            tasks: List of tasks

        Returns:
            Import dependencies
        """
        dependencies = []
        module_creators: Dict[str, str] = {}  # module -> task ID that creates it
        module_users: Dict[str, List[str]] = {}  # module -> task IDs that use it

        for task in tasks:
            task_id = task.id if hasattr(task, "id") else str(task)

            # Check if task creates a module
            created_modules = self._extract_created_modules(task)
            for module in created_modules:
                module_creators[module] = task_id

            # Check if task imports modules
            imported_modules = self._extract_imported_modules(task)
            for module in imported_modules:
                if module not in module_users:
                    module_users[module] = []
                module_users[module].append(task_id)

        # Create dependencies: module users depend on module creators
        for module, user_ids in module_users.items():
            if module in module_creators:
                creator_id = module_creators[module]
                for user_id in user_ids:
                    if user_id != creator_id:
                        dep = TaskDependency(
                            dependent_id=user_id,
                            prerequisite_id=creator_id,
                            dependency_type="import",
                            confidence=0.95,
                            reason=f"Imports module {module}",
                        )
                        dependencies.append(dep)

        return dependencies

    def _analyze_resource_conflicts(self, tasks: List[Any]) -> List[TaskDependency]:
        """Analyze resource conflicts that require serialization.

        Args:
            tasks: List of tasks

        Returns:
            Resource dependencies
        """
        dependencies = []
        resource_users: Dict[str, List[Tuple[str, int]]] = {}  # resource -> [(task_id, priority)]

        for i, task in enumerate(tasks):
            task_id = task.id if hasattr(task, "id") else str(task)
            priority = task.priority if hasattr(task, "priority") else 0

            # Extract resources (databases, APIs, exclusive files)
            resources = self._extract_resources(task)

            for resource in resources:
                if resource not in resource_users:
                    resource_users[resource] = []
                resource_users[resource].append((task_id, priority))

        # Create dependencies for exclusive resources
        for resource, users in resource_users.items():
            if len(users) > 1:
                # Sort by priority (higher priority executes first)
                users.sort(key=lambda x: x[1], reverse=True)

                # Create chain of dependencies
                for i in range(1, len(users)):
                    dep = TaskDependency(
                        dependent_id=users[i][0],
                        prerequisite_id=users[i-1][0],
                        dependency_type="resource",
                        confidence=0.8,
                        reason=f"Exclusive access to {resource}",
                    )
                    dependencies.append(dep)

        return dependencies

    def _extract_files_from_task(self, task: Any) -> Set[str]:
        """Extract file paths mentioned in a task.

        Args:
            task: Task to analyze

        Returns:
            Set of file paths
        """
        files = set()

        # Check task parameters
        if hasattr(task, "parameters"):
            files.update(self._find_files_in_dict(task.parameters))

        # Check task description
        if hasattr(task, "description"):
            # Look for file paths in description
            path_pattern = r'["\']?([a-zA-Z0-9_\-/]+\.[a-zA-Z0-9]+)["\']?'
            matches = re.findall(path_pattern, task.description)
            files.update(matches)

        return files

    def _find_files_in_dict(self, data: Dict[str, Any]) -> Set[str]:
        """Recursively find file paths in a dictionary.

        Args:
            data: Dictionary to search

        Returns:
            Set of file paths
        """
        files = set()

        for key, value in data.items():
            if key in ["file", "filepath", "path", "filename"]:
                if isinstance(value, str):
                    files.add(value)
                elif isinstance(value, list):
                    files.update(str(v) for v in value if isinstance(v, str))
            elif isinstance(value, dict):
                files.update(self._find_files_in_dict(value))

        return files

    def _extract_created_modules(self, task: Any) -> Set[str]:
        """Extract Python modules created by a task.

        Args:
            task: Task to analyze

        Returns:
            Set of module names
        """
        modules = set()

        if hasattr(task, "name"):
            # Heuristic: tasks that "create" or "implement" likely create modules
            if any(word in task.name.lower() for word in ["create", "implement", "add"]):
                # Try to extract module name from task name
                words = re.findall(r'\w+', task.name)
                for word in words:
                    if word.lower() not in ["create", "implement", "add", "the", "a", "an"]:
                        modules.add(word.lower())

        return modules

    def _extract_imported_modules(self, task: Any) -> Set[str]:
        """Extract Python modules imported by a task.

        Args:
            task: Task to analyze

        Returns:
            Set of module names
        """
        modules = set()

        if hasattr(task, "parameters") and "code" in task.parameters:
            # Parse Python code for imports
            try:
                tree = ast.parse(task.parameters["code"])
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            modules.add(alias.name.split(".")[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            modules.add(node.module.split(".")[0])
            except:
                pass  # Ignore parsing errors

        return modules

    def _extract_resources(self, task: Any) -> Set[str]:
        """Extract exclusive resources used by a task.

        Args:
            task: Task to analyze

        Returns:
            Set of resource identifiers
        """
        resources = set()

        # Check for database operations
        if hasattr(task, "parameters"):
            params = task.parameters

            # Database resources
            if "database" in params or "db" in params:
                resources.add("database")

            # API endpoints
            if "api" in params or "endpoint" in params:
                api = params.get("api") or params.get("endpoint")
                if api:
                    resources.add(f"api:{api}")

            # Exclusive file locks
            if "exclusive" in params and params["exclusive"]:
                files = self._extract_files_from_task(task)
                for file in files:
                    resources.add(f"file_lock:{file}")

        return resources

    def _deduplicate_dependencies(
        self,
        dependencies: List[TaskDependency],
    ) -> List[TaskDependency]:
        """Remove duplicate dependencies, keeping highest confidence.

        Args:
            dependencies: List of dependencies

        Returns:
            Deduplicated list
        """
        dep_map: Dict[Tuple[str, str], TaskDependency] = {}

        for dep in dependencies:
            key = (dep.dependent_id, dep.prerequisite_id)

            if key not in dep_map or dep.confidence > dep_map[key].confidence:
                dep_map[key] = dep

        return list(dep_map.values())

    def optimize_execution_order(
        self,
        tasks: List[Any],
        dependencies: List[TaskDependency],
    ) -> List[List[str]]:
        """Optimize task execution order for maximum parallelism.

        Args:
            tasks: List of tasks
            dependencies: List of dependencies

        Returns:
            Optimized execution order (batches of parallel tasks)
        """
        # Build adjacency list
        task_ids = [task.id if hasattr(task, "id") else str(task) for task in tasks]
        adj_list: Dict[str, Set[str]] = {tid: set() for tid in task_ids}
        in_degree: Dict[str, int] = {tid: 0 for tid in task_ids}

        for dep in dependencies:
            if dep.dependent_id in adj_list and dep.prerequisite_id in task_ids:
                adj_list[dep.prerequisite_id].add(dep.dependent_id)
                in_degree[dep.dependent_id] += 1

        # Topological sort with level extraction
        execution_order = []
        queue = [tid for tid in task_ids if in_degree[tid] == 0]

        while queue:
            # Current level (can execute in parallel)
            current_level = queue[:]
            execution_order.append(current_level)
            queue = []

            # Process current level
            for task_id in current_level:
                for dependent in adj_list[task_id]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        # Check for cycles
        if sum(in_degree.values()) > 0:
            logger.warning("Dependency cycle detected, some tasks may not execute")

        return execution_order
