"""Dependency resolution for Recipe Executor using only standard library."""

from typing import Optional, Set, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict, deque

from .recipe_model import Recipe


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected."""
    
    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")


class MissingDependencyError(Exception):
    """Raised when a required dependency is missing."""
    pass


@dataclass
class DependencyGraph:
    """Represents the dependency graph of recipes using only stdlib."""
    
    # Adjacency list representation
    forward_edges: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))  # dependency -> dependents
    backward_edges: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))  # dependent -> dependencies
    recipes: Dict[str, Recipe] = field(default_factory=dict)
    
    def add_recipe(self, recipe: Recipe) -> None:
        """Add a recipe to the graph."""
        self.recipes[recipe.name] = recipe
        
        # Ensure node exists even if it has no dependencies
        if recipe.name not in self.forward_edges:
            self.forward_edges[recipe.name] = set()
        
        # Add edges for dependencies
        for dep in recipe.get_dependencies():
            self.backward_edges[recipe.name].add(dep)
            self.forward_edges[dep].add(recipe.name)
    
    def get_build_order(self) -> List[str]:
        """Get recipes in build order using Kahn's algorithm (topological sort)."""
        # Count incoming edges for each node
        in_degree = {}
        for node in self.forward_edges:
            in_degree[node] = len(self.backward_edges.get(node, set()))
        
        # Find all nodes with no incoming edges
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result = []
        
        while queue:
            # Remove a node with no incoming edges
            node = queue.popleft()
            result.append(node)
            
            # Remove edges from this node
            for neighbor in self.forward_edges.get(node, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(in_degree):
            cycles = self.get_cycles()
            if cycles:
                raise CircularDependencyError(cycles[0])
            else:
                raise CircularDependencyError(["Unknown cycle detected"])
        
        return result
    
    def get_dependencies(self, recipe_name: str) -> Set[str]:
        """Get all dependencies of a recipe (transitive)."""
        visited = set()
        to_visit = deque([recipe_name])
        dependencies = set()
        
        while to_visit:
            current = to_visit.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            # Add direct dependencies
            for dep in self.backward_edges.get(current, set()):
                dependencies.add(dep)
                if dep not in visited:
                    to_visit.append(dep)
        
        return dependencies
    
    def get_dependents(self, recipe_name: str) -> Set[str]:
        """Get all recipes that depend on this one (transitive)."""
        visited = set()
        to_visit = deque([recipe_name])
        dependents = set()
        
        while to_visit:
            current = to_visit.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            # Add direct dependents
            for dep in self.forward_edges.get(current, set()):
                dependents.add(dep)
                if dep not in visited:
                    to_visit.append(dep)
        
        return dependents
    
    def get_cycles(self) -> List[List[str]]:
        """Detect cycles in the graph using DFS."""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = defaultdict(lambda: WHITE)
        parent = {}
        cycles = []
        
        def dfs(node: str, path: List[str]) -> None:
            """DFS to detect cycles."""
            color[node] = GRAY
            path.append(node)
            
            for neighbor in self.forward_edges.get(node, set()):
                if color[neighbor] == GRAY:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                elif color[neighbor] == WHITE:
                    parent[neighbor] = node
                    dfs(neighbor, path.copy())
            
            color[node] = BLACK
        
        # Run DFS from all unvisited nodes
        for node in self.forward_edges:
            if color[node] == WHITE:
                dfs(node, [])
        
        return cycles
    
    def validate_dependencies(self) -> List[str]:
        """Validate that all dependencies exist."""
        errors = []
        
        for recipe_name, deps in self.backward_edges.items():
            for dep in deps:
                if dep not in self.recipes and dep not in self.forward_edges:
                    errors.append(f"Recipe '{recipe_name}' depends on missing recipe '{dep}'")
        
        return errors
    
    def get_parallel_groups(self) -> List[List[str]]:
        """Get recipes grouped by level for parallel execution."""
        # Build order gives us the sequence, but we can parallelize within levels
        in_degree = {}
        for node in self.forward_edges:
            in_degree[node] = len(self.backward_edges.get(node, set()))
        
        groups = []
        remaining = set(self.forward_edges.keys())
        
        while remaining:
            # Find all nodes with satisfied dependencies
            current_group = []
            for node in remaining:
                deps = self.backward_edges.get(node, set())
                if all(dep not in remaining for dep in deps):
                    current_group.append(node)
            
            if not current_group:
                # No progress possible - there must be a cycle
                raise CircularDependencyError(list(remaining))
            
            groups.append(current_group)
            remaining -= set(current_group)
        
        return groups


class DependencyResolver:
    """Resolve dependencies between recipes."""
    
    def __init__(self):
        """Initialize dependency resolver."""
        self.graph = DependencyGraph()
    
    def add_recipe(self, recipe: Recipe) -> None:
        """Add a recipe to be resolved."""
        self.graph.add_recipe(recipe)
    
    def resolve(self) -> List[str]:
        """Resolve dependencies and return build order."""
        # Validate first
        errors = self.graph.validate_dependencies()
        if errors:
            raise MissingDependencyError(f"Dependency validation failed: {errors}")
        
        # Return topological order
        return self.graph.get_build_order()
    
    def get_parallel_groups(self) -> List[List[str]]:
        """Get recipes grouped for parallel execution."""
        return self.graph.get_parallel_groups()
    
    def validate(self) -> bool:
        """Validate the dependency graph."""
        try:
            errors = self.graph.validate_dependencies()
            if errors:
                return False
            
            # Try to get build order to check for cycles
            self.graph.get_build_order()
            return True
        except CircularDependencyError:
            return False