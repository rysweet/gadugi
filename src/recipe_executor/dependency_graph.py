"""Dependency graph construction and analysis for Recipe Executor."""

import logging
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from .recipe_model import Recipe, DependencyGraph, ComponentType

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes and manages recipe dependencies."""
    
    def __init__(self):
        """Initialize the dependency analyzer."""
        self.graphs: Dict[str, DependencyGraph] = {}
        self.recipe_cache: Dict[str, Recipe] = {}
        self.cycle_cache: Dict[str, List[List[str]]] = {}
        self.build_order_cache: Optional[List[str]] = None
    
    def analyze_recipe_dependencies(self, recipe: Recipe, all_recipes: Dict[str, Recipe]) -> DependencyGraph:
        """Analyze dependencies for a single recipe.
        
        Args:
            recipe: The recipe to analyze
            all_recipes: All available recipes
            
        Returns:
            DependencyGraph for the recipe
        """
        # Cache recipes
        self.recipe_cache = all_recipes
        
        # Create new graph
        graph = DependencyGraph()
        
        # Build graph starting from this recipe
        self._build_graph_recursive(recipe.name, graph, all_recipes, set())
        
        # Detect cycles
        cycles = graph.detect_cycles()
        if cycles:
            logger.warning(f"Found {len(cycles)} circular dependencies for recipe '{recipe.name}'")
            for cycle in cycles:
                logger.warning(f"  Cycle: {' -> '.join(cycle)}")
        
        # Calculate dependency depths
        for node_name in graph.nodes:
            graph.get_dependency_depth(node_name)
        
        # Store in cache
        self.graphs[recipe.name] = graph
        self.cycle_cache[recipe.name] = cycles
        
        return graph
    
    def _build_graph_recursive(
        self,
        recipe_name: str,
        graph: DependencyGraph,
        all_recipes: Dict[str, Recipe],
        visited: Set[str]
    ) -> None:
        """Recursively build dependency graph.
        
        Args:
            recipe_name: Current recipe being processed
            graph: Graph being built
            all_recipes: All available recipes
            visited: Set of visited recipes to prevent infinite loops
        """
        if recipe_name in visited:
            return
        
        visited.add(recipe_name)
        
        if recipe_name not in all_recipes:
            logger.warning(f"Recipe '{recipe_name}' not found in available recipes")
            return
        
        recipe = all_recipes[recipe_name]
        
        # Add node for this recipe
        if recipe_name not in graph.nodes:
            graph.add_node(recipe_name, recipe.components.type)
        
        # Process dependencies
        for dep_name in recipe.get_dependencies():
            # Add dependency node
            if dep_name in all_recipes:
                dep_recipe = all_recipes[dep_name]
                if dep_name not in graph.nodes:
                    graph.add_node(dep_name, dep_recipe.components.type)
                
                # Add edge
                graph.add_edge(recipe_name, dep_name)
                
                # Recursively process dependency's dependencies
                self._build_graph_recursive(dep_name, graph, all_recipes, visited)
            else:
                logger.warning(f"Dependency '{dep_name}' not found for recipe '{recipe_name}'")
    
    def analyze_all_recipes(self, recipes: Dict[str, Recipe]) -> Dict[str, DependencyGraph]:
        """Analyze dependencies for all recipes.
        
        Args:
            recipes: All recipes to analyze
            
        Returns:
            Dictionary of recipe_name -> DependencyGraph
        """
        self.recipe_cache = recipes
        self.graphs = {}
        self.cycle_cache = {}
        
        for recipe_name, recipe in recipes.items():
            graph = self.analyze_recipe_dependencies(recipe, recipes)
            self.graphs[recipe_name] = graph
        
        logger.info(f"Analyzed dependencies for {len(self.graphs)} recipes")
        
        return self.graphs
    
    def get_build_order(self, recipes: Dict[str, Recipe]) -> List[str]:
        """Get the order in which recipes should be built.
        
        Args:
            recipes: All recipes
            
        Returns:
            List of recipe names in build order
        """
        if self.build_order_cache:
            return self.build_order_cache
        
        # Create a global dependency graph
        global_graph = DependencyGraph()
        
        # Add all recipes as nodes
        for recipe_name, recipe in recipes.items():
            global_graph.add_node(recipe_name, recipe.components.type)
        
        # Add all edges
        for recipe_name, recipe in recipes.items():
            for dep_name in recipe.get_dependencies():
                if dep_name in recipes:
                    global_graph.add_edge(recipe_name, dep_name)
        
        # Check for cycles
        cycles = global_graph.detect_cycles()
        if cycles:
            raise ValueError(f"Cannot determine build order due to circular dependencies: {cycles}")
        
        # Get topological order (get_build_order returns List[List[str]], we need List[str])
        try:
            build_order_layers = global_graph.get_build_order()
            # Flatten the layers into a single list
            build_order = [recipe for layer in build_order_layers for recipe in layer]
            self.build_order_cache = build_order
            logger.info(f"Determined build order for {len(build_order)} recipes")
            return build_order
        except ValueError as e:
            logger.error(f"Failed to determine build order: {e}")
            raise
    
    def find_affected_recipes(self, changed_recipe: str, all_recipes: Dict[str, Recipe]) -> Set[str]:
        """Find all recipes affected by a change in one recipe.
        
        Args:
            changed_recipe: The recipe that changed
            all_recipes: All available recipes
            
        Returns:
            Set of affected recipe names
        """
        affected: Set[str] = set()
        
        # Ensure we have analyzed all recipes
        if not self.graphs:
            self.analyze_all_recipes(all_recipes)
        
        # Find all recipes that depend on the changed recipe
        for _, graph in self.graphs.items():
            if changed_recipe in graph.nodes:
                node = graph.nodes[changed_recipe]
                # Add all dependents
                affected.update(node.dependents)
        
        logger.info(f"Recipe '{changed_recipe}' affects {len(affected)} other recipes")
        
        return affected
    
    def find_transitive_dependencies(self, recipe_name: str, all_recipes: Dict[str, Recipe]) -> Set[str]:
        """Find all transitive dependencies of a recipe.
        
        Args:
            recipe_name: The recipe to analyze
            all_recipes: All available recipes
            
        Returns:
            Set of all transitive dependency names
        """
        if recipe_name not in all_recipes:
            logger.warning(f"Recipe '{recipe_name}' not found")
            return set()
        
        dependencies: Set[str] = set()
        to_process = deque([recipe_name])
        processed: Set[str] = set()
        
        while to_process:
            current = to_process.popleft()
            
            if current in processed:
                continue
            
            processed.add(current)
            
            if current in all_recipes:
                recipe = all_recipes[current]
                for dep in recipe.get_dependencies():
                    dependencies.add(dep)
                    if dep not in processed:
                        to_process.append(dep)
        
        logger.debug(f"Recipe '{recipe_name}' has {len(dependencies)} transitive dependencies")
        
        return dependencies
    
    def validate_no_missing_dependencies(self, recipes: Dict[str, Recipe]) -> Tuple[bool, Dict[str, List[str]]]:
        """Validate that all recipe dependencies exist.
        
        Args:
            recipes: All recipes to validate
            
        Returns:
            Tuple of (all_valid, dict of recipe_name -> missing_dependencies)
        """
        missing_deps: Dict[str, List[str]] = {}
        all_recipe_names = set(recipes.keys())
        
        for recipe_name, recipe in recipes.items():
            recipe_deps = set(recipe.get_dependencies())
            missing = recipe_deps - all_recipe_names
            
            if missing:
                missing_deps[recipe_name] = list(missing)
                logger.warning(f"Recipe '{recipe_name}' has missing dependencies: {missing}")
        
        all_valid = len(missing_deps) == 0
        
        if all_valid:
            logger.info("All recipe dependencies are satisfied")
        else:
            logger.error(f"{len(missing_deps)} recipes have missing dependencies")
        
        return all_valid, missing_deps
    
    def get_dependency_metrics(self, recipe_name: str) -> Dict[str, int]:
        """Get dependency metrics for a recipe.
        
        Args:
            recipe_name: The recipe to analyze
            
        Returns:
            Dictionary of metrics
        """
        if recipe_name not in self.graphs:
            return {
                "direct_dependencies": 0,
                "transitive_dependencies": 0,
                "dependency_depth": 0,
                "dependent_count": 0
            }
        
        graph = self.graphs[recipe_name]
        node = graph.nodes.get(recipe_name)
        
        if not node:
            return {
                "direct_dependencies": 0,
                "transitive_dependencies": 0,
                "dependency_depth": 0,
                "dependent_count": 0
            }
        
        # Count transitive dependencies
        all_deps = self.find_transitive_dependencies(recipe_name, self.recipe_cache)
        
        return {
            "direct_dependencies": len(node.dependencies),
            "transitive_dependencies": len(all_deps),
            "dependency_depth": graph.get_dependency_depth(recipe_name),
            "dependent_count": len(node.dependents)
        }
    
    def suggest_dependency_optimizations(self, recipes: Dict[str, Recipe]) -> List[str]:
        """Suggest optimizations for dependency structure.
        
        Args:
            recipes: All recipes to analyze
            
        Returns:
            List of optimization suggestions
        """
        suggestions: List[str] = []
        
        # Analyze all recipes first
        if not self.graphs:
            self.analyze_all_recipes(recipes)
        
        # Check for deep dependency chains
        max_depth_threshold = 5
        for recipe_name, graph in self.graphs.items():
            for node_name in graph.nodes:
                depth = graph.get_dependency_depth(node_name)
                if depth > max_depth_threshold:
                    suggestions.append(
                        f"Recipe '{node_name}' has dependency depth {depth} (threshold: {max_depth_threshold}). "
                        "Consider flattening the dependency hierarchy."
                    )
        
        # Check for recipes with too many direct dependencies
        max_direct_deps = 7
        for recipe_name, recipe in recipes.items():
            dep_count = len(recipe.get_dependencies())
            if dep_count > max_direct_deps:
                suggestions.append(
                    f"Recipe '{recipe_name}' has {dep_count} direct dependencies (threshold: {max_direct_deps}). "
                    "Consider creating intermediate recipes to group related dependencies."
                )
        
        # Check for circular dependency risks
        for recipe_name, cycles in self.cycle_cache.items():
            if cycles:
                suggestions.append(
                    f"Recipe '{recipe_name}' has circular dependencies: {cycles}. "
                    "Refactor to eliminate cycles."
                )
        
        # Check for common dependencies that could be extracted
        dep_counts: Dict[str, int] = defaultdict(int)
        for recipe in recipes.values():
            for dep in recipe.get_dependencies():
                dep_counts[dep] += 1
        
        common_threshold = len(recipes) * 0.5  # Used by 50% of recipes
        for dep, count in dep_counts.items():
            if count >= common_threshold:
                suggestions.append(
                    f"Dependency '{dep}' is used by {count} recipes ({count/len(recipes)*100:.0f}%). "
                    "Consider making it a core component."
                )
        
        if not suggestions:
            suggestions.append("No dependency optimizations needed - structure looks good!")
        
        logger.info(f"Generated {len(suggestions)} dependency optimization suggestions")
        
        return suggestions
    
    def export_dependency_graph(self, recipe_name: str, format: str = "dot") -> str:
        """Export dependency graph in various formats.
        
        Args:
            recipe_name: The recipe to export
            format: Export format (currently only 'dot' for GraphViz)
            
        Returns:
            String representation of the graph
        """
        if recipe_name not in self.graphs:
            logger.warning(f"No dependency graph found for recipe '{recipe_name}'")
            return ""
        
        graph = self.graphs[recipe_name]
        
        if format == "dot":
            lines = ["digraph dependencies {"]
            lines.append('  rankdir=LR;')
            lines.append('  node [shape=box];')
            
            # Add nodes with type coloring
            for node_name, node in graph.nodes.items():
                color = self._get_node_color(node.recipe_type)
                lines.append(f'  "{node_name}" [fillcolor={color}, style=filled];')
            
            # Add edges
            for from_node, to_node in graph.edges:
                lines.append(f'  "{from_node}" -> "{to_node}";')
            
            lines.append("}")
            
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _get_node_color(self, component_type: ComponentType) -> str:
        """Get color for node based on component type.
        
        Args:
            component_type: The component type
            
        Returns:
            Color string for GraphViz
        """
        colors = {
            ComponentType.SERVICE: "lightblue",
            ComponentType.AGENT: "lightgreen",
            ComponentType.LIBRARY: "lightyellow",
            ComponentType.TOOL: "lightcoral",
            ComponentType.CORE: "lightgray"
        }
        return colors.get(component_type, "white")