"""Recipe data models for the Recipe Executor."""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any, List, Dict, cast
from enum import Enum
from datetime import datetime


class ComponentType(Enum):
    """Types of components that can be built from recipes."""

    SERVICE = "service"
    AGENT = "agent"
    LIBRARY = "library"
    TOOL = "tool"
    CORE = "core"


class RequirementPriority(Enum):
    """Priority levels for requirements."""

    MUST = "must"
    SHOULD = "should"
    COULD = "could"
    WONT = "wont"


@dataclass
class Requirement:
    """A single functional or non-functional requirement."""

    id: str
    description: str
    priority: RequirementPriority
    validation_criteria: List[str] = field(default_factory=lambda: cast(List[str], []))
    implemented: bool = False


@dataclass
class Requirements:
    """Parsed requirements from requirements.md."""

    purpose: str
    functional_requirements: List[Requirement]
    non_functional_requirements: List[Requirement]
    success_criteria: List[str]

    def get_all_requirements(self) -> List[Requirement]:
        """Get all requirements regardless of type."""
        return self.functional_requirements + self.non_functional_requirements

    def get_must_requirements(self) -> List[Requirement]:
        """Get only MUST requirements."""
        return [r for r in self.get_all_requirements() if r.priority == RequirementPriority.MUST]


@dataclass
class ComponentDesign:
    """Design specification for a single component."""

    name: str
    description: str
    class_name: Optional[str] = None
    methods: List[str] = field(default_factory=lambda: cast(List[str], []))
    properties: List[str] = field(default_factory=lambda: cast(List[str], []))
    code_snippet: Optional[str] = None


@dataclass
class Interface:
    """Interface specification between components."""

    name: str
    description: str
    methods: List[str] = field(default_factory=lambda: cast(List[str], []))
    events: List[str] = field(default_factory=lambda: cast(List[str], []))
    data_types: List[str] = field(default_factory=lambda: cast(List[str], []))


@dataclass
class Design:
    """Parsed design from design.md."""

    architecture: str
    components: List[ComponentDesign]
    interfaces: List[Interface]
    implementation_notes: str
    code_blocks: List[str] = field(default_factory=lambda: cast(List[str], []))

    def get_component_by_name(self, name: str) -> Optional[ComponentDesign]:
        """Find a component by name."""
        for component in self.components:
            if component.name == name:
                return component
        return None


@dataclass
class Components:
    """Recipe dependencies from components.json."""

    name: str
    version: str
    type: ComponentType
    dependencies: List[str] = field(
        default_factory=lambda: cast(List[str], [])
    )  # Other recipe names this depends on
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=lambda: cast(Dict[str, Any], {}))

    def is_self_hosting(self) -> bool:
        """Check if this recipe is self-hosting."""
        return self.metadata.get("self_hosting", False)

    def requires_bootstrap(self) -> bool:
        """Check if bootstrap is required."""
        return self.metadata.get("bootstrap_required", False)


@dataclass
class DesignPattern:
    """Represents a reusable design pattern with templates."""

    name: str
    description: str
    template: str  # Code template as string
    category: str = "structural"  # e.g., "creational", "structural", "behavioral"
    template_path: Optional[Path] = None
    applicable_types: List[ComponentType] = field(default_factory=lambda: cast(List[ComponentType], []))  # Renamed from applicable_to
    applicable_to: List[ComponentType] = field(default_factory=lambda: cast(List[ComponentType], []))  # Keep for compatibility
    required_methods: List[str] = field(default_factory=lambda: cast(List[str], []))  # Added for test compatibility
    required_properties: List[str] = field(default_factory=lambda: cast(List[str], []))  # Added for test compatibility
    required_components: List[str] = field(default_factory=lambda: cast(List[str], []))
    design_decisions: Dict[str, str] = field(default_factory=lambda: cast(Dict[str, str], {}))
    code_templates: Dict[str, str] = field(default_factory=lambda: cast(Dict[str, str], {}))
    
    def __post_init__(self):
        """Ensure compatibility between applicable_types and applicable_to."""
        if self.applicable_types and not self.applicable_to:
            self.applicable_to = self.applicable_types
        elif self.applicable_to and not self.applicable_types:
            self.applicable_types = self.applicable_to
    
    def is_applicable(self, component_type: ComponentType) -> bool:
        """Check if pattern is applicable to given component type."""
        if not self.applicable_to and not self.applicable_types:
            return True  # No restrictions, applicable to all
        return component_type in (self.applicable_to or self.applicable_types)
    
    def get_template(self, key: Optional[str] = None) -> Optional[str]:
        """Get a specific code template."""
        if key is None:
            return self.template
        return self.code_templates.get(key)


@dataclass
class RecipeComplexity:
    """Complexity analysis and decomposition recommendations."""
    
    recipe_name: str
    complexity_score: float = 0.0  # 0-100 scale
    component_count: int = 0
    dependency_count: int = 0
    requirement_count: int = 0
    interface_count: int = 0
    cyclomatic_complexity: int = 0
    cognitive_complexity: int = 0
    decomposition_recommended: bool = False
    decomposition_suggestions: List[str] = field(default_factory=lambda: cast(List[str], []))
    complexity_factors: Dict[str, float] = field(default_factory=lambda: cast(Dict[str, float], {}))
    metrics: Optional['ComplexityMetrics'] = None  # Added for test compatibility
    decomposition_strategy: str = "component-based"
    sub_recipes: List[str] = field(default_factory=lambda: cast(List[str], []))
    estimated_effort_hours: float = 0.0
    risk_level: str = "low"
    
    def calculate_overall_score(self) -> float:
        """Calculate overall complexity score."""
        # Weight different factors
        weights = {
            "components": 0.2,
            "dependencies": 0.25,
            "requirements": 0.15,
            "interfaces": 0.15,
            "cyclomatic": 0.15,
            "cognitive": 0.1
        }
        
        # Normalize and weight factors
        score = 0.0
        score += min(self.component_count / 10, 10) * weights["components"] * 10
        score += min(self.dependency_count / 5, 10) * weights["dependencies"] * 10
        score += min(self.requirement_count / 20, 10) * weights["requirements"] * 10
        score += min(self.interface_count / 5, 10) * weights["interfaces"] * 10
        score += min(self.cyclomatic_complexity / 50, 10) * weights["cyclomatic"] * 10
        score += min(self.cognitive_complexity / 30, 10) * weights["cognitive"] * 10
        
        self.complexity_score = min(score, 100)
        return self.complexity_score
    
    def should_decompose(self) -> bool:
        """Determine if recipe should be decomposed."""
        # First check explicit recommendation
        if self.decomposition_recommended:
            return True
        # Recommend decomposition if:
        # - Complexity score > 70
        # - More than 15 components
        # - More than 10 dependencies
        # - Cyclomatic complexity > 50
        if self.complexity_score > 70:
            return True
        if self.component_count > 15:
            return True
        if self.dependency_count > 10:
            return True
        if self.cyclomatic_complexity > 50:
            return True
        # Check metrics if provided
        if self.metrics and self.metrics.is_complex:
            return True
        return False
    
    def generate_decomposition_suggestions(self) -> List[str]:
        """Generate suggestions for decomposing the recipe."""
        suggestions: List[str] = []
        
        if self.component_count > 10:
            suggestions.append(
                f"Split into {self.component_count // 5} sub-recipes, "
                "grouping related components together"
            )
        
        if self.dependency_count > 8:
            suggestions.append(
                "Extract common dependencies into a shared base recipe"
            )
        
        if self.requirement_count > 20:
            suggestions.append(
                "Group requirements by feature area and create focused recipes"
            )
        
        if self.cyclomatic_complexity > 40:
            suggestions.append(
                "Simplify complex logic by extracting utility functions"
            )
        
        if self.interface_count > 8:
            suggestions.append(
                "Define common interface patterns in a separate library recipe"
            )
        
        self.decomposition_suggestions = suggestions
        return suggestions


@dataclass
class DependencyNode:
    """Node in the dependency graph."""
    
    name: str
    recipe_type: ComponentType
    dependencies: set[str] = field(default_factory=lambda: cast(set[str], set()))
    dependents: set[str] = field(default_factory=lambda: cast(set[str], set()))
    depth: int = 0
    visited: bool = False
    in_progress: bool = False  # For cycle detection


@dataclass
class DependencyGraph:
    """Dependency relationships with circular detection."""
    
    nodes: Dict[str, DependencyNode] = field(default_factory=lambda: cast(Dict[str, DependencyNode], {}))
    edges: List[tuple[str, str]] = field(default_factory=lambda: cast(List[tuple[str, str]], []))  # (from, to) pairs
    cycles: List[List[str]] = field(default_factory=lambda: cast(List[List[str]], []))
    topological_order: List[str] = field(default_factory=lambda: cast(List[str], []))
    recipes: Dict[str, 'Recipe'] = field(default_factory=lambda: cast(Dict[str, 'Recipe'], {}))  # Store recipes
    
    def add_node(self, name: str, recipe_type: ComponentType) -> None:
        """Add a node to the dependency graph."""
        if name not in self.nodes:
            self.nodes[name] = DependencyNode(name=name, recipe_type=recipe_type)
    
    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add a dependency edge."""
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError(f"Both nodes must exist before adding edge: {from_node} -> {to_node}")
        
        self.nodes[from_node].dependencies.add(to_node)
        self.nodes[to_node].dependents.add(from_node)
        self.edges.append((from_node, to_node))
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        self.cycles = []
        visited: set[str] = set()
        rec_stack: List[str] = []
        
        def dfs_cycle_detect(node_name: str) -> bool:
            """DFS helper for cycle detection."""
            if node_name in rec_stack:
                # Found a cycle
                cycle_start_idx = rec_stack.index(node_name)
                cycle: List[str] = rec_stack[cycle_start_idx:] + [node_name]
                self.cycles.append(cycle)
                return True
            
            if node_name in visited:
                return False
            
            visited.add(node_name)
            rec_stack.append(node_name)
            
            node = self.nodes[node_name]
            for dep in node.dependencies:
                dfs_cycle_detect(dep)
            
            rec_stack.pop()
            return False
        
        # Check all nodes for cycles
        for node_name in self.nodes:
            if node_name not in visited:
                dfs_cycle_detect(node_name)
        
        return self.cycles
    
    def get_topological_order(self) -> List[str]:
        """Get topological order of dependencies."""
        if self.cycles:
            raise ValueError("Cannot compute topological order with circular dependencies")
        
        # Kahn's algorithm
        in_degree = {node: len(self.nodes[node].dependencies) for node in self.nodes}
        queue = [node for node in self.nodes if in_degree[node] == 0]
        result: List[str] = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for dependent in self.nodes[node].dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        if len(result) != len(self.nodes):
            raise ValueError("Graph has cycles or disconnected components")
        
        self.topological_order = result
        return result
    
    def add_recipe(self, recipe: 'Recipe') -> None:
        """Add a recipe to the dependency graph."""
        self.recipes[recipe.name] = recipe
        self.add_node(recipe.name, recipe.components.type)
        
        # Add edges for dependencies
        for dep in recipe.get_dependencies():
            if dep in self.nodes:
                self.add_edge(recipe.name, dep)
    
    def has_circular_dependency(self) -> tuple[bool, List[str]]:
        """Check for circular dependencies."""
        cycles = self.detect_cycles()
        if cycles:
            return True, cycles[0] if cycles else []
        return False, []
    
    def get_build_order(self) -> List[List[str]]:
        """Get the order in which recipes should be built (as layers)."""
        if self.cycles:
            return []
        
        # Build layers based on dependency depth
        depths: Dict[str, int] = {}
        for node_name in self.nodes:
            depths[node_name] = self.get_dependency_depth(node_name)
        
        # Group by depth
        layers: Dict[int, List[str]] = {}
        for node, depth in depths.items():
            if depth not in layers:
                layers[depth] = []
            layers[depth].append(node)
        
        # Return as list of layers, sorted by depth
        return [layers[d] for d in sorted(layers.keys())]
    
    def get_dependency_depth(self, node_name: str, visited: Optional[set[str]] = None) -> int:
        """Calculate the maximum dependency depth for a node."""
        if node_name not in self.nodes:
            return -1
        
        if visited is None:
            visited = set()
        
        # Check for cycles
        if node_name in visited:
            return 0  # Stop recursion on cycle
        
        visited.add(node_name)
        
        node = self.nodes[node_name]
        if not node.dependencies:
            node.depth = 0
            return 0
        
        max_depth = 0
        for dep in node.dependencies:
            dep_depth = self.get_dependency_depth(dep, visited.copy())
            max_depth = max(max_depth, dep_depth + 1)
        
        node.depth = max_depth
        return max_depth


@dataclass
class BuildState:
    """Tracks build state for incremental builds."""
    
    recipe_name: str
    last_build_time: Optional[datetime] = None
    last_checksum: Optional[str] = None
    dependencies_checksums: Dict[str, str] = field(default_factory=lambda: cast(Dict[str, str], {}))
    generated_files: List[str] = field(default_factory=lambda: cast(List[str], []))
    output_files: List[str] = field(default_factory=lambda: cast(List[str], []))  # Added for test compatibility
    build_successful: bool = False
    success: bool = False  # Alias for build_successful
    build_errors: List[str] = field(default_factory=lambda: cast(List[str], []))
    requires_rebuild: bool = True
    affected_by: List[str] = field(default_factory=lambda: cast(List[str], []))  # Dependencies that changed
    
    def __post_init__(self):
        """Synchronize success with build_successful."""
        if self.success:
            self.build_successful = self.success
        if self.output_files and not self.generated_files:
            self.generated_files = self.output_files
    
    def needs_rebuild(self, current_checksum: str) -> bool:
        """Check if rebuild is needed based on checksum."""
        return self.last_checksum != current_checksum
    
    def update_checksum(self, new_checksum: str) -> bool:
        """Update checksum and return if changed."""
        changed = self.last_checksum != new_checksum
        self.last_checksum = new_checksum
        return changed
    
    def mark_successful_build(self) -> None:
        """Mark the build as successful."""
        self.build_successful = True
        self.last_build_time = datetime.now()
        self.build_errors = []
        self.requires_rebuild = False
    
    def mark_failed_build(self, errors: List[str]) -> None:
        """Mark the build as failed."""
        self.build_successful = False
        self.build_errors = errors
        self.requires_rebuild = True
    
    def check_dependency_changes(self, dep_checksums: Dict[str, str]) -> List[str]:
        """Check which dependencies have changed."""
        changed: List[str] = []
        for dep_name, checksum in dep_checksums.items():
            if dep_name not in self.dependencies_checksums:
                changed.append(dep_name)
            elif self.dependencies_checksums[dep_name] != checksum:
                changed.append(dep_name)
        
        self.affected_by = changed
        if changed:
            self.requires_rebuild = True
        
        return changed


@dataclass
class RecipeMetadata:
    """Metadata about a recipe."""

    created_at: datetime
    updated_at: datetime
    author: str = "Recipe Executor"
    tags: List[str] = field(default_factory=lambda: cast(List[str], []))
    build_count: int = 0
    last_build: Optional[datetime] = None
    checksum: Optional[str] = None
    supplementary_docs: Dict[str, str] = field(default_factory=lambda: cast(Dict[str, str], {}))


@dataclass
class Recipe:
    """Represents a complete recipe with all components."""

    name: str
    path: Path
    requirements: Requirements
    design: Design
    components: Components
    metadata: RecipeMetadata
    pattern: Optional[DesignPattern] = None
    complexity: Optional[RecipeComplexity] = None
    dependency_graph: Optional[DependencyGraph] = None
    build_state: Optional[BuildState] = None

    def __post_init__(self):
        """Validate recipe consistency."""
        if self.name != self.components.name:
            raise ValueError(f"Recipe name mismatch: {self.name} != {self.components.name}")
        
        # Initialize complexity if not provided
        if not self.complexity:
            self.complexity = self.calculate_complexity()
        
        # Initialize build state
        if not self.build_state:
            self.build_state = BuildState(recipe_name=self.name)

    def get_dependencies(self) -> List[str]:
        """Get list of recipe dependencies."""
        return self.components.dependencies

    def get_output_path(self) -> Path:
        """Get output path for generated code."""
        # Convention: code goes to src/{recipe_name}/
        return Path("src") / self.name.replace("-", "_")

    def is_valid(self) -> bool:
        """Check if recipe is valid and complete."""
        # Check that we have all required parts
        if not self.requirements or not self.design or not self.components:
            return False

        # Check that we have at least one requirement
        if not self.requirements.get_all_requirements():
            return False

        # Check that we have at least one component in design
        if not self.design.components:
            return False

        return True
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for change detection."""
        # Create a deterministic string representation
        content_parts = [
            self.name,
            self.components.version,
            str(self.components.type.value),
            json.dumps(sorted(self.get_dependencies())),
            self.requirements.purpose,
            str(len(self.requirements.get_all_requirements())),
            str(len(self.design.components)),
            str(len(self.design.interfaces)),
        ]
        
        # Add requirement IDs
        for req in sorted(self.requirements.get_all_requirements(), key=lambda r: r.id):
            content_parts.append(f"{req.id}:{req.description}:{req.priority.value}")
        
        # Add component names
        for comp in sorted(self.design.components, key=lambda c: c.name):
            content_parts.append(f"{comp.name}:{comp.description}")
        
        # Calculate SHA256 hash
        content = "\n".join(content_parts)
        checksum = hashlib.sha256(content.encode()).hexdigest()
        
        # Update metadata
        self.metadata.checksum = checksum
        return checksum
    
    def has_changed_since(self, last_checksum: Optional[str]) -> bool:
        """Check if recipe has changed since last checksum."""
        if not last_checksum:
            return True
        
        current_checksum = self.calculate_checksum()
        return current_checksum != last_checksum
    
    def validate_dependencies(self, available_recipes: Optional[List[str]] = None) -> tuple[bool, List[str]]:
        """Validate that all dependencies exist."""
        if available_recipes is None:
            # If no list provided, assume all dependencies are valid
            return True, []
        
        missing: List[str] = []
        for dep in self.get_dependencies():
            if dep not in available_recipes:
                missing.append(dep)
        
        return len(missing) == 0, missing
    
    def has_self_overwrite_risk(self) -> bool:
        """Check if recipe has self-overwrite risk."""
        valid, _ = self.validate_no_self_overwrite()
        return not valid
    
    def detect_circular_dependencies(self, all_recipes: Dict[str, 'Recipe']) -> List[List[str]]:
        """Detect circular dependencies using DFS."""
        if not self.dependency_graph:
            self.dependency_graph = DependencyGraph()
            self._build_dependency_graph(all_recipes)
        
        cycles = self.dependency_graph.detect_cycles()
        return cycles
    
    def _build_dependency_graph(self, all_recipes: Dict[str, 'Recipe']) -> None:
        """Build the dependency graph for this recipe."""
        if not self.dependency_graph:
            self.dependency_graph = DependencyGraph()
        
        # Add this recipe as a node
        self.dependency_graph.add_node(self.name, self.components.type)
        
        # Recursively add dependencies
        visited: set[str] = set()
        to_visit: List[tuple[str, str]] = [(self.name, dep) for dep in self.get_dependencies()]
        
        while to_visit:
            parent, dep_name = to_visit.pop(0)
            
            if dep_name not in visited:
                visited.add(dep_name)
                
                if dep_name in all_recipes:
                    dep_recipe = all_recipes[dep_name]
                    self.dependency_graph.add_node(dep_name, dep_recipe.components.type)
                    self.dependency_graph.add_edge(parent, dep_name)
                    
                    # Add transitive dependencies
                    for trans_dep in dep_recipe.get_dependencies():
                        to_visit.append((dep_name, trans_dep))
    
    def merge_with_pattern(self, pattern: DesignPattern) -> None:
        """Merge pattern requirements with recipe requirements."""
        if not pattern.is_applicable(self.components.type):
            raise ValueError(
                f"Pattern {pattern.name} is not applicable to {self.components.type.value}"
            )
        
        self.pattern = pattern
        
        # Add pattern's required components to design
        for comp_name in pattern.required_components:
            if not self.design.get_component_by_name(comp_name):
                # Add component from pattern
                pattern_comp = ComponentDesign(
                    name=comp_name,
                    description=f"Required by {pattern.name} pattern",
                )
                self.design.components.append(pattern_comp)
        
        # Merge design decisions
        for decision_key, decision_value in pattern.design_decisions.items():
            # Store in metadata
            self.metadata.supplementary_docs[f"pattern_{decision_key}"] = decision_value
    
    def calculate_complexity(self) -> RecipeComplexity:
        """Calculate and return recipe complexity."""
        complexity = RecipeComplexity(
            recipe_name=self.name,
            complexity_score=0.0,
            component_count=len(self.design.components),
            dependency_count=len(self.get_dependencies()),
            requirement_count=len(self.requirements.get_all_requirements()),
            interface_count=len(self.design.interfaces),
            cyclomatic_complexity=self._estimate_cyclomatic_complexity(),
            cognitive_complexity=self._estimate_cognitive_complexity(),
            decomposition_recommended=False,
        )
        
        # Calculate overall score
        complexity.calculate_overall_score()
        
        # Check if decomposition is needed
        complexity.decomposition_recommended = complexity.should_decompose()
        
        # Generate suggestions if needed
        if complexity.decomposition_recommended:
            complexity.generate_decomposition_suggestions()
        
        self.complexity = complexity
        return complexity
    
    def _estimate_cyclomatic_complexity(self) -> int:
        """Estimate cyclomatic complexity based on design."""
        # Rough estimate based on components and their interactions
        base_complexity = len(self.design.components)
        
        # Add complexity for each method in components
        for comp in self.design.components:
            base_complexity += len(comp.methods) * 2
        
        # Add complexity for interfaces
        base_complexity += len(self.design.interfaces) * 3
        
        return base_complexity
    
    def _estimate_cognitive_complexity(self) -> int:
        """Estimate cognitive complexity based on requirements."""
        # Base on requirement complexity
        base = 0
        
        for req in self.requirements.get_all_requirements():
            if req.priority == RequirementPriority.MUST:
                base += 3
            elif req.priority == RequirementPriority.SHOULD:
                base += 2
            else:
                base += 1
            
            # Add for validation criteria
            base += len(req.validation_criteria)
        
        return base
    
    def is_self_hosting(self) -> bool:
        """Check if recipe would overwrite itself."""
        if "recipe-executor" in self.name or "recipe_executor" in self.name:
            return True
        
        output_path = self.get_output_path()
        
        # Check if output would overwrite recipe executor
        if "recipe_executor" in str(output_path):
            return True
        
        # Check components metadata
        return self.components.is_self_hosting()
    
    def validate_no_self_overwrite(self) -> tuple[bool, str]:
        """Validate that recipe won't overwrite Recipe Executor."""
        if self.is_self_hosting():
            if not self.components.metadata.get("self_hosting_allowed", False):
                return False, (
                    f"Recipe '{self.name}' would overwrite Recipe Executor. "
                    "Set 'self_hosting_allowed: true' in metadata to allow this."
                )
        
        # Check output path doesn't conflict
        output_path = self.get_output_path()
        protected_paths = [
            Path("src/recipe_executor"),
            Path("tests/recipe_executor"),
        ]
        
        for protected in protected_paths:
            try:
                output_path.relative_to(protected)
                return False, (
                    f"Recipe output path {output_path} would overwrite "
                    f"protected path {protected}"
                )
            except ValueError:
                # Not a subpath, which is good
                pass
        
        return True, "No self-overwrite detected"
    
    def get_affected_by_changes(self, changed_recipes: List[str]) -> bool:
        """Check if this recipe is affected by changes in other recipes."""
        # Direct dependency changed
        for dep in self.get_dependencies():
            if dep in changed_recipes:
                return True
        
        # Check if any transitive dependency changed
        if self.dependency_graph:
            for node_name in self.dependency_graph.nodes:
                if node_name in changed_recipes:
                    # Check if we depend on this node
                    node = self.dependency_graph.nodes[node_name]
                    if self.name in node.dependents:
                        return True
        
        return False
    
    def split_into_sub_recipes(self, max_components: int = 5) -> List['Recipe']:
        """Split recipe into smaller sub-recipes."""
        if not self.complexity or not self.complexity.decomposition_recommended:
            return [self]
        
        sub_recipes: List['Recipe'] = []
        
        # Group components by related functionality
        component_groups = self._group_related_components(max_components)
        
        for i, group in enumerate(component_groups):
            # Create sub-recipe
            sub_name = f"{self.name}-part{i+1}"
            sub_requirements = Requirements(
                purpose=f"Part {i+1} of {self.requirements.purpose}",
                functional_requirements=[],
                non_functional_requirements=self.requirements.non_functional_requirements.copy(),
                success_criteria=[],
            )
            
            sub_design = Design(
                architecture=self.design.architecture,
                components=group,
                interfaces=[],
                implementation_notes=self.design.implementation_notes,
            )
            
            sub_components = Components(
                name=sub_name,
                version=self.components.version,
                type=self.components.type,
                dependencies=self.components.dependencies.copy() if i == 0 else [self.name],
            )
            
            sub_metadata = RecipeMetadata(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                tags=self.metadata.tags + ["sub-recipe", f"part-{i+1}"],
            )
            
            sub_recipe = Recipe(
                name=sub_name,
                path=self.path.parent / sub_name,
                requirements=sub_requirements,
                design=sub_design,
                components=sub_components,
                metadata=sub_metadata,
            )
            
            sub_recipes.append(sub_recipe)
        
        return sub_recipes
    
    def _group_related_components(self, max_per_group: int) -> List[List[ComponentDesign]]:
        """Group related components together."""
        groups: List[List[ComponentDesign]] = []
        current_group: List[ComponentDesign] = []
        
        for comp in self.design.components:
            if len(current_group) >= max_per_group:
                groups.append(current_group)
                current_group = []
            
            current_group.append(comp)
        
        if current_group:
            groups.append(current_group)
        
        return groups


@dataclass
class BuildContext:
    """Context for building a recipe."""

    recipe: Recipe
    dependencies: Dict[str, Any] = field(default_factory=lambda: cast(Dict[str, Any], {}))
    options: Dict[str, Any] = field(default_factory=lambda: cast(Dict[str, Any], {}))
    environment: Dict[str, str] = field(default_factory=lambda: cast(Dict[str, str], {}))
    dry_run: bool = False
    verbose: bool = False
    force_rebuild: bool = False

    def get_dependency(self, name: str) -> Any:
        """Get a built dependency by name."""
        return self.dependencies.get(name)

    def has_dependency(self, name: str) -> bool:
        """Check if a dependency is available."""
        return name in self.dependencies


@dataclass
class GeneratedCode:
    """Code generated from a recipe."""

    recipe_name: str
    files: Dict[str, str]  # filepath -> content
    language: str = "python"
    framework: Optional[str] = None  # Framework used (e.g., "pytest", "unittest", None)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_file(self, path: str) -> Optional[str]:
        """Get generated file content by path."""
        return self.files.get(path)

    def add_file(self, path: str, content: str):
        """Add a generated file."""
        self.files[path] = content


@dataclass
class RecipeTestSuite:
    """Generated test suite for a recipe."""

    recipe_name: str
    unit_tests: List[str]
    integration_tests: List[str]
    test_files: Dict[str, str]  # filepath -> content

    def get_all_tests(self) -> List[str]:
        """Get all test names."""
        return self.unit_tests + self.integration_tests


@dataclass
class ValidationResult:
    """Result of validating generated code against requirements."""

    recipe_name: str
    passed: bool
    requirements_coverage: Dict[str, bool]  # requirement_id -> covered
    design_compliance: Dict[str, bool]  # component_name -> compliant
    quality_gates: Dict[str, bool]  # gate_name -> passed
    errors: List[str] = field(default_factory=lambda: cast(List[str], []))
    warnings: List[str] = field(default_factory=lambda: cast(List[str], []))

    def get_coverage_percentage(self) -> float:
        """Calculate requirement coverage percentage."""
        if not self.requirements_coverage:
            return 0.0
        covered = sum(1 for covered in self.requirements_coverage.values() if covered)
        return (covered / len(self.requirements_coverage)) * 100

    def get_failed_requirements(self) -> List[str]:
        """Get list of uncovered requirements."""
        return [req_id for req_id, covered in self.requirements_coverage.items() if not covered]


@dataclass
class BuildResult:
    """Result of building one or more recipes."""

    results: List["SingleBuildResult"]
    success: bool
    total_time: float
    timestamp: datetime = field(default_factory=datetime.now)

    def get_failed_recipes(self) -> List[str]:
        """Get list of recipes that failed to build."""
        return [r.recipe.name for r in self.results if not r.success]

    def get_successful_recipes(self) -> List[str]:
        """Get list of successfully built recipes."""
        return [r.recipe.name for r in self.results if r.success]


@dataclass
class SingleBuildResult:
    """Result of building a single recipe."""

    recipe: Recipe
    code: Optional[GeneratedCode]
    tests: Optional[RecipeTestSuite]
    validation: Optional[ValidationResult]
    quality_result: Dict[str, bool]  # tool_name -> passed
    success: bool
    build_time: float
    errors: List[str] = field(default_factory=lambda: cast(List[str], []))

    def get_quality_failures(self) -> List[str]:
        """Get list of failed quality gates."""
        return [tool for tool, passed in self.quality_result.items() if not passed]


@dataclass
class ComplexityMetrics:
    """Metrics for assessing recipe complexity."""
    
    functional_requirements_count: int = 0
    non_functional_requirements_count: int = 0
    component_count: int = 0
    dependency_count: int = 0
    interface_count: int = 0
    estimated_loc: int = 0
    complexity_score: float = 0.0
    
    @property
    def is_complex(self) -> bool:
        """Check if the recipe is considered complex."""
        return (
            self.complexity_score > 7.0 or
            self.component_count > 10 or
            self.dependency_count > 5 or
            self.estimated_loc > 1000
        )
    
    @property
    def decomposition_reason(self) -> str:
        """Get reason for decomposition recommendation."""
        reasons: List[str] = []
        if self.complexity_score > 7.0:
            reasons.append("High complexity score")
        if self.component_count > 10:
            reasons.append("Too many components")
        if self.dependency_count > 5:
            reasons.append("Too many dependencies")
        if self.estimated_loc > 1000:
            reasons.append("Large estimated codebase")
        return "; ".join(reasons) if reasons else "No decomposition needed"
    
    @property
    def requires_decomposition(self) -> bool:
        """Check if decomposition is required."""
        return self.is_complex


@dataclass
class SubRecipe:
    """A sub-recipe created from decomposing a complex recipe."""
    
    name: str
    parent_recipe: str = ""  # Changed from parent_recipe_name for test compatibility
    parent_recipe_name: str = ""  # Keep both for compatibility
    components: List[ComponentDesign] = field(default_factory=lambda: cast(List[ComponentDesign], []))
    requirements: Optional[Requirements] = None  # Changed to Requirements type
    design: Optional[Design] = None  # Added for test compatibility
    dependencies: List[str] = field(default_factory=lambda: cast(List[str], []))
    complexity_metrics: Optional[ComplexityMetrics] = None  # Added for test
    
    def __post_init__(self):
        """Ensure parent_recipe and parent_recipe_name are synchronized."""
        if self.parent_recipe and not self.parent_recipe_name:
            self.parent_recipe_name = self.parent_recipe
        elif self.parent_recipe_name and not self.parent_recipe:
            self.parent_recipe = self.parent_recipe_name
    
    def to_recipe(self, parent_recipe: Recipe) -> Recipe:
        """Convert SubRecipe to full Recipe."""
        if isinstance(self.requirements, Requirements):
            sub_requirements = self.requirements
        else:
            sub_requirements = Requirements(
                purpose=f"Sub-recipe of {parent_recipe.requirements.purpose}",
                functional_requirements=[],
                non_functional_requirements=parent_recipe.requirements.non_functional_requirements,
                success_criteria=[]
            )
        
        sub_design = Design(
            architecture=parent_recipe.design.architecture,
            components=self.components,
            interfaces=[],
            implementation_notes=""
        )
        
        sub_components = Components(
            name=self.name,
            version=parent_recipe.components.version,
            type=parent_recipe.components.type,
            dependencies=self.dependencies
        )
        
        sub_metadata = RecipeMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=["sub-recipe", f"parent:{self.parent_recipe_name}"]
        )
        
        return Recipe(
            name=self.name,
            path=parent_recipe.path.parent / self.name,
            requirements=sub_requirements,
            design=sub_design,
            components=sub_components,
            metadata=sub_metadata
        )


@dataclass
class ParallelBuildResult:
    """Result of building recipes in parallel."""
    
    recipe_names: List[str] = field(default_factory=lambda: cast(List[str], []))
    success_count: int = 0
    failure_count: int = 0
    total_time: float = 0.0
    individual_results: List[SingleBuildResult] = field(default_factory=lambda: cast(List[SingleBuildResult], []))
    results: Dict[str, SingleBuildResult] = field(default_factory=lambda: cast(Dict[str, SingleBuildResult], {}))  # Added for test
    parallel_groups: List[List[str]] = field(default_factory=lambda: cast(List[List[str]], []))  # Added for test
    parallel_speedup: float = 1.0
    
    def __post_init__(self):
        """Synchronize results formats."""
        # Convert individual_results to results dict if needed
        if self.individual_results and not self.results:
            for result in self.individual_results:
                self.results[result.recipe.name] = result
        # Convert results dict to individual_results if needed
        elif self.results and not self.individual_results:
            self.individual_results = list(self.results.values())
        
        # Update counts based on results
        if self.results:
            self.success_count = sum(1 for r in self.results.values() if r.success)
            self.failure_count = len(self.results) - self.success_count
            self.recipe_names = list(self.results.keys())
    
    @property
    def success(self) -> bool:
        """Check if all recipes built successfully."""
        return self.failure_count == 0
    
    def get_failed_recipes(self) -> List[str]:
        """Get names of failed recipes."""
        return [r.recipe.name for r in self.individual_results if not r.success]
    
    def get_successful_recipes(self) -> List[str]:
        """Get names of successful recipes."""
        return [r.recipe.name for r in self.individual_results if r.success]
