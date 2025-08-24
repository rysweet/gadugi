"""Dependency resolver for recipe build ordering."""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .recipe_model import Recipe


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected.
    
    Circular dependencies prevent topological sorting and would cause
    infinite loops in the build process. This error provides details
    about the dependency cycle that was detected.
    """
    
    def __init__(self, cycle: List[str], message: Optional[str] = None):
        """Initialize the circular dependency error.
        
        Args:
            cycle: List of recipe names forming the circular dependency
            message: Optional custom error message
        """
        self.cycle = cycle
        
        if message is None:
            # Create a clear visualization of the cycle
            cycle_str = " -> ".join(cycle)
            if cycle and cycle[0] != cycle[-1]:
                cycle_str += f" -> {cycle[0]}"  # Complete the cycle visually
            message = f"Circular dependency detected: {cycle_str}"
        
        super().__init__(message)
        
    def __str__(self) -> str:
        """Return string representation of the error."""
        return super().__str__()


class MissingDependencyError(Exception):
    """Raised when a required dependency is missing.
    
    This error occurs when a recipe declares a dependency on another
    recipe that doesn't exist in the build context.
    """
    
    def __init__(self, recipe_name: str, missing_dep: str, available_recipes: Optional[List[str]] = None):
        """Initialize the missing dependency error.
        
        Args:
            recipe_name: Name of the recipe with the missing dependency
            missing_dep: Name of the missing dependency
            available_recipes: Optional list of available recipes for suggestions
        """
        self.recipe_name = recipe_name
        self.missing_dep = missing_dep
        self.available_recipes = available_recipes or []
        
        message = f"Recipe '{recipe_name}' depends on '{missing_dep}' which was not found"
        
        # Try to suggest similar recipe names if available
        if self.available_recipes:
            similar = self._find_similar_names(missing_dep, self.available_recipes)
            if similar:
                message += f"\n  Did you mean one of: {', '.join(similar)}?"
            else:
                message += f"\n  Available recipes: {', '.join(sorted(self.available_recipes[:5]))}"
                if len(self.available_recipes) > 5:
                    message += f" (and {len(self.available_recipes) - 5} more)"
        
        super().__init__(message)
    
    def _find_similar_names(self, target: str, candidates: List[str], max_results: int = 3) -> List[str]:
        """Find recipe names similar to the target.
        
        Args:
            target: The target name to match
            candidates: List of candidate names
            max_results: Maximum number of suggestions
            
        Returns:
            List of similar names
        """
        # Simple similarity check based on common prefixes/substrings
        similar = []
        target_lower = target.lower()
        
        # First check for exact substring matches
        for candidate in candidates:
            if target_lower in candidate.lower() or candidate.lower() in target_lower:
                similar.append(candidate)
                if len(similar) >= max_results:
                    break
        
        # If no matches, check for common prefixes
        if not similar:
            for candidate in candidates:
                if candidate.lower().startswith(target_lower[:3]) or target_lower.startswith(candidate.lower()[:3]):
                    similar.append(candidate)
                    if len(similar) >= max_results:
                        break
        
        return similar[:max_results]
        
    def __str__(self) -> str:
        """Return string representation of the error."""
        return super().__str__()


@dataclass
class DependencyNode:
    """Node in the dependency graph."""
    recipe: Recipe
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    visited: bool = False
    in_stack: bool = False
    
    def add_dependency(self, dep_name: str):
        """Add a dependency to this node."""
        self.dependencies.add(dep_name)
    
    def add_dependent(self, dep_name: str):
        """Add a dependent (reverse dependency) to this node."""
        self.dependents.add(dep_name)
    
    def get_dependency_count(self) -> int:
        """Get number of dependencies."""
        return len(self.dependencies)
    
    def has_dependencies(self) -> bool:
        """Check if node has any dependencies."""
        return len(self.dependencies) > 0


@dataclass
class DependencyGraph:
    """Graph representing recipe dependencies."""
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    
    def add_node(self, recipe: Recipe):
        """Add a recipe node to the graph."""
        if recipe.name not in self.nodes:
            self.nodes[recipe.name] = DependencyNode(recipe=recipe)
    
    def add_edge(self, from_recipe: str, to_recipe: str):
        """Add a dependency edge (from depends on to)."""
        if from_recipe in self.nodes and to_recipe in self.nodes:
            self.nodes[from_recipe].add_dependency(to_recipe)
            self.nodes[to_recipe].add_dependent(from_recipe)
    
    def get_node(self, name: str) -> Optional[DependencyNode]:
        """Get a node by recipe name."""
        return self.nodes.get(name)
    
    def get_roots(self) -> List[DependencyNode]:
        """Get nodes with no dependencies (can be built first)."""
        return [node for node in self.nodes.values() if not node.has_dependencies()]
    
    def get_leaves(self) -> List[DependencyNode]:
        """Get nodes with no dependents (nothing depends on them)."""
        return [node for node in self.nodes.values() if len(node.dependents) == 0]
    
    def reset_visited(self):
        """Reset visited flags for traversal."""
        for node in self.nodes.values():
            node.visited = False
            node.in_stack = False


@dataclass
class ParallelGroup:
    """Group of recipes that can be built in parallel."""
    level: int
    recipes: List[Recipe]
    
    def get_recipe_names(self) -> List[str]:
        """Get list of recipe names in this group."""
        return [r.name for r in self.recipes]
    
    def size(self) -> int:
        """Get number of recipes in this group."""
        return len(self.recipes)


class DependencyResolver:
    """Resolves and orders recipe dependencies with parallel execution support."""
    
    def __init__(self):
        """Initialize the resolver."""
        self.graph = DependencyGraph()
        self.build_order: List[Recipe] = []
        self.cycles: List[List[str]] = []
    
    def resolve(self, recipes: Dict[str, Recipe]) -> List[Recipe]:
        """Return recipes in build order using topological sort.
        
        Args:
            recipes: Dictionary of recipe name to Recipe object
            
        Returns:
            List of recipes in build order
            
        Raises:
            CircularDependencyError: If circular dependencies detected
            MissingDependencyError: If required dependency not found
        """
        # Build the dependency graph
        self._build_dependency_graph(recipes)
        
        # Check for circular dependencies
        cycles = self._detect_cycles()
        if cycles:
            cycle_str = ' → '.join(cycles[0] + [cycles[0][0]])
            raise CircularDependencyError(f"Circular dependency detected: {cycle_str}")
        
        # Perform topological sort
        build_order = self._topological_sort()
        
        return build_order
    
    def get_parallel_groups(self, recipes: List[Recipe]) -> List[ParallelGroup]:
        """Group recipes that can be built in parallel.
        
        Args:
            recipes: List of all recipes
            
        Returns:
            List of parallel groups ordered by dependency level
        """
        # Build dependency graph if not already built
        if not self.graph.nodes:
            recipe_dict = {r.name: r for r in recipes}
            self._build_dependency_graph(recipe_dict)
        
        # Calculate levels using BFS from roots
        levels = self._calculate_levels()
        
        # Group recipes by level
        groups = []
        for level in sorted(levels.keys()):
            group_recipes = [self.graph.nodes[name].recipe for name in levels[level]]
            groups.append(ParallelGroup(level=level, recipes=group_recipes))
        
        return groups
    
    def find_build_path(self, target: str, recipes: Dict[str, Recipe]) -> List[Recipe]:
        """Find minimal build path to build a target recipe.
        
        Args:
            target: Name of target recipe to build
            recipes: All available recipes
            
        Returns:
            Minimal list of recipes needed to build target
        """
        if target not in recipes:
            raise MissingDependencyError(f"Target recipe '{target}' not found")
        
        # Build graph
        self._build_dependency_graph(recipes)
        
        # Find all dependencies of target
        required = self._find_all_dependencies(target)
        required.add(target)
        
        # Filter and sort required recipes
        required_recipes = [recipes[name] for name in required if name in recipes]
        
        # Sort in build order
        return self._topological_sort_subset(required_recipes)
    
    def _build_dependency_graph(self, recipes: Dict[str, Recipe]):
        """Build directed acyclic graph from recipe dependencies.
        
        Args:
            recipes: Dictionary of recipe name to Recipe
            
        Raises:
            MissingDependencyError: If a dependency is not found
        """
        self.graph = DependencyGraph()
        
        # Add all nodes first
        for name, recipe in recipes.items():
            self.graph.add_node(recipe)
        
        # Add edges for dependencies
        for name, recipe in recipes.items():
            for dep in recipe.get_dependencies():
                if dep not in recipes:
                    raise MissingDependencyError(
                        f"Recipe '{name}' depends on missing recipe '{dep}'"
                    )
                # Edge from recipe to dependency (recipe depends on dep)
                self.graph.add_edge(name, dep)
    
    def _detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies using DFS.
        
        Returns:
            List of cycles found (each cycle is a list of recipe names)
        """
        self.cycles = []
        self.graph.reset_visited()
        
        for node_name in self.graph.nodes:
            if not self.graph.nodes[node_name].visited:
                path = []
                self._dfs_detect_cycle(node_name, path)
        
        return self.cycles
    
    def _dfs_detect_cycle(self, node_name: str, path: List[str]):
        """DFS helper for cycle detection.
        
        Args:
            node_name: Current node being visited
            path: Current path in DFS
        """
        node = self.graph.nodes[node_name]
        node.visited = True
        node.in_stack = True
        path.append(node_name)
        
        for dep_name in node.dependencies:
            dep_node = self.graph.nodes[dep_name]
            
            if not dep_node.visited:
                self._dfs_detect_cycle(dep_name, path)
            elif dep_node.in_stack:
                # Found a cycle
                cycle_start = path.index(dep_name)
                cycle = path[cycle_start:]
                self.cycles.append(cycle)
        
        path.pop()
        node.in_stack = False
    
    def _topological_sort(self) -> List[Recipe]:
        """Perform topological sort using Kahn's algorithm.
        
        Returns:
            List of recipes in build order
        """
        # Calculate in-degrees
        in_degree = defaultdict(int)
        for node in self.graph.nodes.values():
            for dep in node.dependencies:
                in_degree[dep] += 1
        
        # Find nodes with no incoming edges
        queue = deque()
        for name, node in self.graph.nodes.items():
            if in_degree[name] == 0:
                queue.append(name)
        
        sorted_recipes = []
        
        while queue:
            # Get node with no dependencies
            current = queue.popleft()
            sorted_recipes.append(self.graph.nodes[current].recipe)
            
            # Remove edges from current node
            for dep in self.graph.nodes[current].dependencies:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        
        # Check if all nodes were processed
        if len(sorted_recipes) != len(self.graph.nodes):
            # Cycle exists (shouldn't happen if cycle detection worked)
            unprocessed = set(self.graph.nodes.keys()) - set(r.name for r in sorted_recipes)
            raise CircularDependencyError(f"Could not process recipes: {unprocessed}")
        
        return sorted_recipes
    
    def _topological_sort_subset(self, recipes: List[Recipe]) -> List[Recipe]:
        """Topological sort for a subset of recipes.
        
        Args:
            recipes: Subset of recipes to sort
            
        Returns:
            Sorted list of recipes
        """
        # Create subgraph with only required recipes
        recipe_names = set(r.name for r in recipes)
        in_degree = defaultdict(int)
        
        for recipe in recipes:
            for dep in recipe.get_dependencies():
                if dep in recipe_names:
                    in_degree[dep] += 1
        
        # Kahn's algorithm on subset
        queue = deque()
        for recipe in recipes:
            if in_degree[recipe.name] == 0:
                queue.append(recipe)
        
        sorted_recipes = []
        processed = set()
        
        while queue:
            current = queue.popleft()
            sorted_recipes.append(current)
            processed.add(current.name)
            
            # Check dependents
            node = self.graph.get_node(current.name)
            if node:
                for dependent in node.dependents:
                    if dependent in recipe_names and dependent not in processed:
                        # Check if all dependencies of dependent are processed
                        dep_recipe = next((r for r in recipes if r.name == dependent), None)
                        if dep_recipe:
                            deps_satisfied = all(
                                dep in processed or dep not in recipe_names
                                for dep in dep_recipe.get_dependencies()
                            )
                            if deps_satisfied:
                                queue.append(dep_recipe)
        
        return sorted_recipes
    
    def _calculate_levels(self) -> Dict[int, List[str]]:
        """Calculate dependency levels for parallel execution.
        
        Returns:
            Dictionary of level to list of recipe names at that level
        """
        levels = defaultdict(list)
        node_levels = {}
        
        # BFS to assign levels
        queue = deque()
        
        # Start with roots (no dependencies)
        for node in self.graph.get_roots():
            queue.append((node.recipe.name, 0))
            node_levels[node.recipe.name] = 0
        
        while queue:
            current_name, level = queue.popleft()
            levels[level].append(current_name)
            
            # Process dependents
            current_node = self.graph.get_node(current_name)
            if current_node:
                for dependent_name in current_node.dependents:
                    if dependent_name not in node_levels:
                        # Check if all dependencies have been assigned levels
                        dependent_node = self.graph.get_node(dependent_name)
                        if dependent_node:
                            deps_done = all(
                                dep in node_levels 
                                for dep in dependent_node.dependencies
                            )
                            if deps_done:
                                # Assign level as max dependency level + 1
                                dep_levels = [
                                    node_levels[dep] 
                                    for dep in dependent_node.dependencies
                                ]
                                new_level = max(dep_levels) + 1 if dep_levels else 0
                                node_levels[dependent_name] = new_level
                                queue.append((dependent_name, new_level))
        
        return levels
    
    def _find_all_dependencies(self, recipe_name: str) -> Set[str]:
        """Find all transitive dependencies of a recipe.
        
        Args:
            recipe_name: Name of recipe to analyze
            
        Returns:
            Set of all dependency names
        """
        dependencies = set()
        visited = set()
        
        def dfs(name: str):
            if name in visited:
                return
            visited.add(name)
            
            node = self.graph.get_node(name)
            if node:
                for dep in node.dependencies:
                    dependencies.add(dep)
                    dfs(dep)
        
        dfs(recipe_name)
        return dependencies
    
    def analyze_impact(self, changed_recipe: str) -> Set[str]:
        """Analyze which recipes are impacted by a change.
        
        Args:
            changed_recipe: Name of recipe that changed
            
        Returns:
            Set of recipe names that depend on the changed recipe
        """
        impacted = set()
        
        def dfs(name: str):
            node = self.graph.get_node(name)
            if node:
                for dependent in node.dependents:
                    if dependent not in impacted:
                        impacted.add(dependent)
                        dfs(dependent)
        
        dfs(changed_recipe)
        return impacted
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the dependency graph.
        
        Returns:
            Dictionary with various statistics
        """
        if not self.graph.nodes:
            return {
                "total_recipes": 0,
                "root_recipes": 0,
                "leaf_recipes": 0,
                "max_depth": 0,
                "avg_dependencies": 0
            }
        
        roots = self.graph.get_roots()
        leaves = self.graph.get_leaves()
        
        # Calculate max depth
        levels = self._calculate_levels()
        max_depth = max(levels.keys()) if levels else 0
        
        # Calculate average dependencies
        total_deps = sum(len(node.dependencies) for node in self.graph.nodes.values())
        avg_deps = total_deps / len(self.graph.nodes) if self.graph.nodes else 0
        
        return {
            "total_recipes": len(self.graph.nodes),
            "root_recipes": len(roots),
            "leaf_recipes": len(leaves),
            "max_depth": max_depth,
            "avg_dependencies": round(avg_deps, 2),
            "parallel_groups": len(levels)
        }