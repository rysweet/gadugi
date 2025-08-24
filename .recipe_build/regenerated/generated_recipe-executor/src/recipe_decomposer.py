"""Recipe decomposer for handling complex recipes."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .recipe_model import Recipe, ComponentDesign, Requirement


@dataclass
class FunctionalArea:
    """Represents a functional area in a recipe."""
    name: str
    description: str
    requirements: List[Requirement]
    components: List[ComponentDesign]
    dependencies: Set[str] = field(default_factory=set)
    
    def get_requirement_count(self) -> int:
        """Get total number of requirements."""
        return len(self.requirements)
    
    def get_component_count(self) -> int:
        """Get total number of components."""
        return len(self.components)
    
    def is_independent(self) -> bool:
        """Check if this area has no dependencies."""
        return len(self.dependencies) == 0


@dataclass
class DecompositionStrategy:
    """Strategy for decomposing a complex recipe."""
    approach: str  # "functional", "layered", "component"
    reason: str
    suggested_splits: List[str]
    estimated_sub_recipes: int
    
    def get_description(self) -> str:
        """Get human-readable description of strategy."""
        descriptions = {
            "functional": "Split by functional areas (e.g., auth, data, UI)",
            "layered": "Split by architectural layers (e.g., API, business, data)",
            "component": "Split by major components or services"
        }
        return descriptions.get(self.approach, self.approach)


@dataclass
class ComplexityResult:
    """Result of complexity evaluation."""
    score: int
    needs_decomposition: bool
    reasons: List[str]
    strategy: Optional[DecompositionStrategy]
    functional_areas: List[FunctionalArea] = field(default_factory=list)
    
    def get_severity(self) -> str:
        """Get complexity severity level."""
        if self.score <= 2:
            return "simple"
        elif self.score <= 4:
            return "moderate"
        elif self.score <= 7:
            return "complex"
        else:
            return "very_complex"


@dataclass
class SubRecipe:
    """A sub-recipe created from decomposition."""
    name: str
    parent_recipe: str
    functional_area: FunctionalArea
    path: Path
    dependencies: List[str]
    
    def create_files(self) -> bool:
        """Create the sub-recipe files."""
        # Create directory
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Create requirements.md
        self._create_requirements_file()
        
        # Create design.md
        self._create_design_file()
        
        # Create components.json
        self._create_components_file()
        
        return True
    
    def _create_requirements_file(self):
        """Create requirements.md for sub-recipe."""
        content = f"""# {self.name} Requirements

## Purpose
{self.functional_area.description}

## Functional Requirements
"""
        for req in self.functional_area.requirements:
            content += f"- {req.priority.value} {req.description}\n"
            for criterion in req.validation_criteria:
                content += f"  - {criterion}\n"
        
        content += "\n## Success Criteria\n"
        content += f"- All {len(self.functional_area.requirements)} requirements implemented\n"
        content += "- All tests passing\n"
        content += "- Integration with parent recipe validated\n"
        
        (self.path / "requirements.md").write_text(content)
    
    def _create_design_file(self):
        """Create design.md for sub-recipe."""
        content = f"""# {self.name} Design

## Architecture
Component of {self.parent_recipe} handling {self.functional_area.name}.

## Components
"""
        for comp in self.functional_area.components:
            content += f"\n### {comp.name}\n"
            content += f"{comp.description}\n\n"
            if comp.methods:
                content += "Methods:\n"
                for method in comp.methods:
                    content += f"- `{method}`\n"
        
        content += "\n## Language\nPython\n"
        
        (self.path / "design.md").write_text(content)
    
    def _create_components_file(self):
        """Create components.json for sub-recipe."""
        data = {
            "name": self.name,
            "version": "1.0.0",
            "type": "LIBRARY",
            "dependencies": self.dependencies,
            "description": f"Sub-component of {self.parent_recipe}: {self.functional_area.description}",
            "metadata": {
                "parent_recipe": self.parent_recipe,
                "functional_area": self.functional_area.name
            }
        }
        
        with open(self.path / "components.json", 'w') as f:
            json.dump(data, f, indent=2)


class RecipeDecomposer:
    """Evaluates complexity and decomposes recipes."""
    
    THRESHOLDS = {
        'max_components': 10,
        'max_requirements': 20,
        'max_functional_areas': 3,
        'max_dependencies': 5,
        'max_code_blocks': 15,
        'max_interfaces': 8
    }
    
    def __init__(self):
        """Initialize the decomposer."""
        self.complexity_weights = {
            'requirements': 0.3,
            'components': 0.25,
            'dependencies': 0.15,
            'functional_areas': 0.2,
            'code_complexity': 0.1
        }
    
    def evaluate_complexity(self, recipe: Recipe) -> ComplexityResult:
        """Determine if recipe needs decomposition.
        
        Args:
            recipe: Recipe to evaluate
            
        Returns:
            ComplexityResult with score and recommendation
        """
        score = 0
        reasons = []
        
        # Evaluate requirements complexity
        req_score, req_reason = self._evaluate_requirements(recipe)
        score += req_score
        if req_reason:
            reasons.append(req_reason)
        
        # Evaluate component complexity
        comp_score, comp_reason = self._evaluate_components(recipe)
        score += comp_score
        if comp_reason:
            reasons.append(comp_reason)
        
        # Evaluate dependency complexity
        dep_score, dep_reason = self._evaluate_dependencies(recipe)
        score += dep_score
        if dep_reason:
            reasons.append(dep_reason)
        
        # Identify functional areas
        functional_areas = self._identify_functional_areas(recipe)
        if len(functional_areas) > self.THRESHOLDS['max_functional_areas']:
            score += 4
            reasons.append(f"Mixed concerns: {len(functional_areas)} functional areas")
        
        # Evaluate code complexity
        code_score, code_reason = self._evaluate_code_complexity(recipe)
        score += code_score
        if code_reason:
            reasons.append(code_reason)
        
        # Determine if decomposition is needed
        needs_decomposition = score >= 5
        
        # Suggest strategy if decomposition needed
        strategy = None
        if needs_decomposition:
            strategy = self._suggest_strategy(recipe, functional_areas)
        
        return ComplexityResult(
            score=score,
            needs_decomposition=needs_decomposition,
            reasons=reasons,
            strategy=strategy,
            functional_areas=functional_areas
        )
    
    def decompose(self, recipe: Recipe, strategy: DecompositionStrategy) -> List[SubRecipe]:
        """Decompose a complex recipe into sub-recipes.
        
        Args:
            recipe: Recipe to decompose
            strategy: Strategy to use for decomposition
            
        Returns:
            List of sub-recipes created
        """
        sub_recipes = []
        
        if strategy.approach == "functional":
            sub_recipes = self._decompose_by_function(recipe)
        elif strategy.approach == "layered":
            sub_recipes = self._decompose_by_layer(recipe)
        elif strategy.approach == "component":
            sub_recipes = self._decompose_by_component(recipe)
        else:
            # Default to functional decomposition
            sub_recipes = self._decompose_by_function(recipe)
        
        # Create files for each sub-recipe
        for sub_recipe in sub_recipes:
            sub_recipe.create_files()
        
        return sub_recipes
    
    def _evaluate_requirements(self, recipe: Recipe) -> Tuple[int, Optional[str]]:
        """Evaluate requirements complexity.
        
        Args:
            recipe: Recipe to evaluate
            
        Returns:
            Tuple of (score, reason)
        """
        req_count = len(recipe.requirements.get_all())
        must_count = len(recipe.requirements.get_must_requirements())
        
        if req_count > self.THRESHOLDS['max_requirements']:
            return 3, f"Too many requirements: {req_count}"
        elif req_count > self.THRESHOLDS['max_requirements'] // 2:
            return 2, f"Many requirements: {req_count}"
        elif must_count > 10:
            return 1, f"Many MUST requirements: {must_count}"
        
        return 0, None
    
    def _evaluate_components(self, recipe: Recipe) -> Tuple[int, Optional[str]]:
        """Evaluate component complexity.
        
        Args:
            recipe: Recipe to evaluate
            
        Returns:
            Tuple of (score, reason)
        """
        comp_count = len(recipe.design.components)
        
        if comp_count > self.THRESHOLDS['max_components']:
            return 3, f"Too many components: {comp_count}"
        elif comp_count > self.THRESHOLDS['max_components'] // 2:
            return 2, f"Many components: {comp_count}"
        
        # Check component complexity
        complex_components = 0
        for comp in recipe.design.components:
            if len(comp.methods) > 10:
                complex_components += 1
        
        if complex_components > 3:
            return 2, f"Complex components: {complex_components} with >10 methods"
        elif complex_components > 1:
            return 1, f"Some complex components: {complex_components}"
        
        return 0, None
    
    def _evaluate_dependencies(self, recipe: Recipe) -> Tuple[int, Optional[str]]:
        """Evaluate dependency complexity.
        
        Args:
            recipe: Recipe to evaluate
            
        Returns:
            Tuple of (score, reason)
        """
        dep_count = len(recipe.get_dependencies())
        
        if dep_count > self.THRESHOLDS['max_dependencies']:
            return 2, f"Too many dependencies: {dep_count}"
        elif dep_count > self.THRESHOLDS['max_dependencies'] // 2:
            return 1, f"Several dependencies: {dep_count}"
        
        return 0, None
    
    def _evaluate_code_complexity(self, recipe: Recipe) -> Tuple[int, Optional[str]]:
        """Evaluate code complexity from design.
        
        Args:
            recipe: Recipe to evaluate
            
        Returns:
            Tuple of (score, reason)
        """
        code_blocks = len(recipe.design.code_blocks)
        
        if code_blocks > self.THRESHOLDS['max_code_blocks']:
            return 2, f"Many code examples: {code_blocks}"
        elif code_blocks > self.THRESHOLDS['max_code_blocks'] // 2:
            return 1, f"Several code examples: {code_blocks}"
        
        # Check for very long code blocks
        long_blocks = sum(1 for block in recipe.design.code_blocks if len(block.split('\n')) > 50)
        if long_blocks > 2:
            return 1, f"Long code blocks: {long_blocks}"
        
        return 0, None
    
    def _identify_functional_areas(self, recipe: Recipe) -> List[FunctionalArea]:
        """Identify distinct functional areas in recipe.
        
        Args:
            recipe: Recipe to analyze
            
        Returns:
            List of functional areas identified
        """
        areas = []
        area_map: Dict[str, FunctionalArea] = {}
        
        # Analyze requirements to identify areas
        for req in recipe.requirements.get_all():
            # Extract area from requirement description
            area_name = self._extract_area_from_requirement(req)
            
            if area_name not in area_map:
                area_map[area_name] = FunctionalArea(
                    name=area_name,
                    description=f"Handles {area_name} functionality",
                    requirements=[],
                    components=[]
                )
            
            area_map[area_name].requirements.append(req)
        
        # Map components to areas
        for comp in recipe.design.components:
            area_name = self._extract_area_from_component(comp)
            
            if area_name in area_map:
                area_map[area_name].components.append(comp)
            else:
                # Create new area for unmapped component
                area_map[area_name] = FunctionalArea(
                    name=area_name,
                    description=f"Handles {area_name} functionality",
                    requirements=[],
                    components=[comp]
                )
        
        # Identify dependencies between areas
        for area in area_map.values():
            for comp in area.components:
                for dep in comp.dependencies:
                    # Check if dependency is in another area
                    for other_area in area_map.values():
                        if area != other_area:
                            for other_comp in other_area.components:
                                if dep == other_comp.name:
                                    area.dependencies.add(other_area.name)
        
        return list(area_map.values())
    
    def _extract_area_from_requirement(self, req: Requirement) -> str:
        """Extract functional area from requirement.
        
        Args:
            req: Requirement to analyze
            
        Returns:
            Functional area name
        """
        desc = req.description.lower()
        
        # Common functional areas
        if any(word in desc for word in ['parse', 'read', 'load', 'extract']):
            return "input_processing"
        elif any(word in desc for word in ['validate', 'check', 'verify']):
            return "validation"
        elif any(word in desc for word in ['generate', 'create', 'build']):
            return "generation"
        elif any(word in desc for word in ['test', 'verify', 'assert']):
            return "testing"
        elif any(word in desc for word in ['review', 'analyze', 'evaluate']):
            return "analysis"
        elif any(word in desc for word in ['save', 'store', 'cache', 'persist']):
            return "storage"
        elif any(word in desc for word in ['api', 'endpoint', 'service']):
            return "api"
        elif any(word in desc for word in ['ui', 'interface', 'display']):
            return "ui"
        else:
            return "core"
    
    def _extract_area_from_component(self, comp: ComponentDesign) -> str:
        """Extract functional area from component.
        
        Args:
            comp: Component to analyze
            
        Returns:
            Functional area name
        """
        name = comp.name.lower()
        
        # Map component names to areas
        if 'parser' in name:
            return "input_processing"
        elif 'validator' in name:
            return "validation"
        elif 'generator' in name:
            return "generation"
        elif 'test' in name:
            return "testing"
        elif 'review' in name or 'analyzer' in name:
            return "analysis"
        elif 'manager' in name or 'cache' in name:
            return "storage"
        elif 'orchestrator' in name or 'coordinator' in name:
            return "orchestration"
        else:
            return "core"
    
    def _suggest_strategy(self, recipe: Recipe, functional_areas: List[FunctionalArea]) -> DecompositionStrategy:
        """Suggest decomposition strategy based on analysis.
        
        Args:
            recipe: Recipe to decompose
            functional_areas: Identified functional areas
            
        Returns:
            Suggested decomposition strategy
        """
        # Analyze characteristics to determine best approach
        distinct_areas = len(functional_areas)
        avg_components_per_area = sum(len(a.components) for a in functional_areas) / max(distinct_areas, 1)
        has_layers = any('layer' in recipe.design.architecture.lower() for _ in [1])
        
        if distinct_areas > 3 and avg_components_per_area < 3:
            # Many small areas - use functional decomposition
            return DecompositionStrategy(
                approach="functional",
                reason=f"Recipe has {distinct_areas} distinct functional areas",
                suggested_splits=[area.name for area in functional_areas],
                estimated_sub_recipes=distinct_areas
            )
        elif has_layers and len(recipe.design.components) > 8:
            # Layered architecture - use layer decomposition
            return DecompositionStrategy(
                approach="layered",
                reason="Recipe has layered architecture",
                suggested_splits=["presentation", "business", "data"],
                estimated_sub_recipes=3
            )
        else:
            # Component-based decomposition
            major_components = [c for c in recipe.design.components if len(c.methods) > 5]
            return DecompositionStrategy(
                approach="component",
                reason=f"Recipe has {len(major_components)} major components",
                suggested_splits=[c.name for c in major_components[:5]],
                estimated_sub_recipes=min(len(major_components), 5)
            )
    
    def _decompose_by_function(self, recipe: Recipe) -> List[SubRecipe]:
        """Decompose recipe by functional areas.
        
        Args:
            recipe: Recipe to decompose
            
        Returns:
            List of sub-recipes
        """
        functional_areas = self._identify_functional_areas(recipe)
        sub_recipes = []
        
        for area in functional_areas:
            if area.get_requirement_count() > 0 or area.get_component_count() > 0:
                sub_recipe = SubRecipe(
                    name=f"{recipe.name}-{area.name}",
                    parent_recipe=recipe.name,
                    functional_area=area,
                    path=recipe.path.parent / f"{recipe.name}-{area.name}",
                    dependencies=list(area.dependencies)
                )
                sub_recipes.append(sub_recipe)
        
        return sub_recipes
    
    def _decompose_by_layer(self, recipe: Recipe) -> List[SubRecipe]:
        """Decompose recipe by architectural layers.
        
        Args:
            recipe: Recipe to decompose
            
        Returns:
            List of sub-recipes
        """
        # Create layer-based functional areas
        layers = {
            "api": FunctionalArea("api", "API and presentation layer", [], []),
            "business": FunctionalArea("business", "Business logic layer", [], []),
            "data": FunctionalArea("data", "Data and persistence layer", [], [])
        }
        
        # Distribute requirements and components to layers
        for req in recipe.requirements.get_all():
            layer = self._identify_layer_for_requirement(req)
            layers[layer].requirements.append(req)
        
        for comp in recipe.design.components:
            layer = self._identify_layer_for_component(comp)
            layers[layer].components.append(comp)
        
        # Create sub-recipes for non-empty layers
        sub_recipes = []
        for layer_name, area in layers.items():
            if area.requirements or area.components:
                sub_recipe = SubRecipe(
                    name=f"{recipe.name}-{layer_name}",
                    parent_recipe=recipe.name,
                    functional_area=area,
                    path=recipe.path.parent / f"{recipe.name}-{layer_name}",
                    dependencies=[]
                )
                sub_recipes.append(sub_recipe)
        
        return sub_recipes
    
    def _decompose_by_component(self, recipe: Recipe) -> List[SubRecipe]:
        """Decompose recipe by major components.
        
        Args:
            recipe: Recipe to decompose
            
        Returns:
            List of sub-recipes
        """
        sub_recipes = []
        
        # Group related components
        component_groups = self._group_related_components(recipe.design.components)
        
        for group_name, components in component_groups.items():
            # Find requirements related to these components
            related_reqs = self._find_related_requirements(recipe.requirements.get_all(), components)
            
            area = FunctionalArea(
                name=group_name,
                description=f"Component group: {group_name}",
                requirements=related_reqs,
                components=components
            )
            
            sub_recipe = SubRecipe(
                name=f"{recipe.name}-{group_name}",
                parent_recipe=recipe.name,
                functional_area=area,
                path=recipe.path.parent / f"{recipe.name}-{group_name}",
                dependencies=[]
            )
            sub_recipes.append(sub_recipe)
        
        return sub_recipes
    
    def _identify_layer_for_requirement(self, req: Requirement) -> str:
        """Identify architectural layer for requirement.
        
        Args:
            req: Requirement to classify
            
        Returns:
            Layer name
        """
        desc = req.description.lower()
        
        if any(word in desc for word in ['api', 'endpoint', 'route', 'http']):
            return "api"
        elif any(word in desc for word in ['store', 'database', 'persist', 'cache']):
            return "data"
        else:
            return "business"
    
    def _identify_layer_for_component(self, comp: ComponentDesign) -> str:
        """Identify architectural layer for component.
        
        Args:
            comp: Component to classify
            
        Returns:
            Layer name
        """
        name = comp.name.lower()
        
        if any(word in name for word in ['api', 'handler', 'controller', 'route']):
            return "api"
        elif any(word in name for word in ['store', 'repository', 'dao', 'cache']):
            return "data"
        else:
            return "business"
    
    def _group_related_components(self, components: List[ComponentDesign]) -> Dict[str, List[ComponentDesign]]:
        """Group related components together.
        
        Args:
            components: List of components to group
            
        Returns:
            Dictionary of group name to components
        """
        groups = {}
        
        for comp in components:
            # Simple grouping by component name similarity
            group_name = comp.name.split('_')[0] if '_' in comp.name else comp.name[:5]
            
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append(comp)
        
        return groups
    
    def _find_related_requirements(self, requirements: List[Requirement], 
                                  components: List[ComponentDesign]) -> List[Requirement]:
        """Find requirements related to given components.
        
        Args:
            requirements: All requirements
            components: Components to match
            
        Returns:
            Related requirements
        """
        related = []
        component_names = [c.name.lower() for c in components]
        
        for req in requirements:
            desc = req.description.lower()
            # Check if requirement mentions any component
            for comp_name in component_names:
                if comp_name in desc:
                    related.append(req)
                    break
        
        return related