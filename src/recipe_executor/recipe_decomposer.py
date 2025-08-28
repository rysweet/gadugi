"""Recipe Decomposer Agent - Evaluates recipe complexity and splits complex recipes into sub-recipes."""

import logging
from typing import List, Optional, Tuple, cast
from dataclasses import dataclass, field
from pathlib import Path
import json

from .recipe_model import Recipe, Requirements, Design, Requirement
from .recipe_parser import RecipeParser

logger = logging.getLogger(__name__)


@dataclass
class ComplexityMetrics:
    """Metrics for evaluating recipe complexity."""
    
    functional_requirements_count: int
    non_functional_requirements_count: int
    component_count: int
    dependency_count: int
    interface_count: int
    estimated_loc: int  # Estimated lines of code
    complexity_score: float
    
    @property
    def is_complex(self) -> bool:
        """Determine if recipe should be decomposed based on thresholds."""
        return (
            self.complexity_score > 7.0 or
            self.functional_requirements_count > 10 or
            self.component_count > 5 or
            self.estimated_loc > 500
        )
    
    @property
    def decomposition_reason(self) -> str:
        """Get human-readable reason for decomposition."""
        reasons: List[str] = []
        if self.complexity_score > 7.0:
            reasons.append(f"High complexity score: {self.complexity_score:.1f}")
        if self.functional_requirements_count > 10:
            reasons.append(f"Too many requirements: {self.functional_requirements_count}")
        if self.component_count > 5:
            reasons.append(f"Too many components: {self.component_count}")
        if self.estimated_loc > 500:
            reasons.append(f"Estimated LOC too high: {self.estimated_loc}")
        return "; ".join(reasons) if reasons else "Within acceptable complexity"


@dataclass
class SubRecipe:
    """A decomposed sub-recipe."""
    
    name: str
    parent_recipe: str
    requirements: Requirements
    complexity_metrics: ComplexityMetrics
    design: Optional[Design] = None
    dependencies: List[str] = field(default_factory=lambda: cast(List[str], []))


class RecipeDecomposer:
    """
    Evaluates recipe complexity and decomposes complex recipes into manageable sub-recipes.
    
    This agent implements the Recipe Executor specification requirement for:
    - Evaluating recipe complexity using multiple metrics
    - Splitting complex recipes into sub-recipes
    - Maintaining dependency relationships
    - Ensuring each sub-recipe is independently testable
    """
    
    # Complexity thresholds
    MAX_FUNCTIONAL_REQUIREMENTS = 10
    MAX_COMPONENTS = 5
    MAX_ESTIMATED_LOC = 500
    MAX_COMPLEXITY_SCORE = 7.0
    
    def __init__(self, recipe_parser: Optional[RecipeParser] = None):
        """Initialize the decomposer with a recipe parser."""
        self.parser = recipe_parser or RecipeParser()
        
    def evaluate_complexity(self, recipe: Recipe) -> ComplexityMetrics:
        """
        Evaluate the complexity of a recipe using multiple metrics.
        
        Args:
            recipe: The recipe to evaluate
            
        Returns:
            ComplexityMetrics with detailed complexity analysis
        """
        functional_count = len(recipe.requirements.functional_requirements)
        non_functional_count = len(recipe.requirements.non_functional_requirements)
        
        # Component analysis
        component_count = 0
        interface_count = 0
        if recipe.design:
            component_count = len(recipe.design.components)
            for comp in recipe.design.components:
                # Handle different component types
                if hasattr(comp, 'methods'):
                    interface_count += len(comp.methods)
        
        # Dependency analysis
        deps = recipe.get_dependencies() if hasattr(recipe, 'get_dependencies') else []
        dependency_count = len(deps)
        
        # Estimate lines of code (rough heuristic)
        estimated_loc = self._estimate_lines_of_code(
            functional_count, component_count, interface_count
        )
        
        # Calculate overall complexity score (1-10 scale)
        complexity_score = self._calculate_complexity_score(
            functional_count,
            non_functional_count,
            component_count,
            dependency_count,
            interface_count,
            estimated_loc
        )
        
        metrics = ComplexityMetrics(
            functional_requirements_count=functional_count,
            non_functional_requirements_count=non_functional_count,
            component_count=component_count,
            dependency_count=dependency_count,
            interface_count=interface_count,
            estimated_loc=estimated_loc,
            complexity_score=complexity_score
        )
        
        logger.info(
            f"Recipe '{recipe.name}' complexity: "
            f"Score={metrics.complexity_score:.1f}, "
            f"Complex={metrics.is_complex}, "
            f"Reason='{metrics.decomposition_reason}'"
        )
        
        return metrics
    
    def should_decompose(self, recipe: Recipe) -> Tuple[bool, ComplexityMetrics]:
        """
        Determine if a recipe should be decomposed based on complexity.
        
        Args:
            recipe: The recipe to evaluate
            
        Returns:
            Tuple of (should_decompose, complexity_metrics)
        """
        metrics = self.evaluate_complexity(recipe)
        return metrics.is_complex, metrics
    
    def decompose_recipe(self, recipe: Recipe) -> List[SubRecipe]:
        """
        Decompose a complex recipe into manageable sub-recipes.
        
        This method:
        1. Groups related requirements
        2. Identifies natural boundaries (components/features)
        3. Creates sub-recipes with proper dependencies
        4. Ensures each sub-recipe is independently testable
        
        Args:
            recipe: The recipe to decompose
            
        Returns:
            List of sub-recipes that together implement the parent recipe
        """
        sub_recipes: List[SubRecipe] = []
        
        # Check if decomposition is needed
        should_decompose, metrics = self.should_decompose(recipe)
        if not should_decompose:
            logger.info(f"Recipe '{recipe.name}' does not need decomposition")
            return []
        
        logger.info(f"Decomposing recipe '{recipe.name}': {metrics.decomposition_reason}")
        
        # Strategy 1: Decompose by component (if design exists)
        if recipe.design and recipe.design.components:
            sub_recipes.extend(self._decompose_by_components(recipe))
        
        # Strategy 2: Decompose by feature groups (group related requirements)
        elif len(recipe.requirements.functional_requirements) > self.MAX_FUNCTIONAL_REQUIREMENTS:
            sub_recipes.extend(self._decompose_by_features(recipe))
        
        # Strategy 3: Decompose by layers (data, logic, presentation)
        else:
            sub_recipes.extend(self._decompose_by_layers(recipe))
        
        # Validate sub-recipes
        for sub_recipe in sub_recipes:
            sub_metrics = self.evaluate_complexity_for_sub_recipe(sub_recipe)
            if sub_metrics.is_complex:
                logger.warning(
                    f"Sub-recipe '{sub_recipe.name}' is still complex: "
                    f"{sub_metrics.decomposition_reason}"
                )
        
        logger.info(f"Created {len(sub_recipes)} sub-recipes from '{recipe.name}'")
        return sub_recipes
    
    def _decompose_by_components(self, recipe: Recipe) -> List[SubRecipe]:
        """Decompose recipe based on design components."""
        sub_recipes: List[SubRecipe] = []
        
        if not recipe.design:
            return sub_recipes
        
        for component in recipe.design.components:
            # Group requirements related to this component
            # Convert Requirement objects to strings for matching
            req_strings = [req.description for req in recipe.requirements.functional_requirements]
            related_reqs = self._find_related_requirements(
                component.name, 
                req_strings
            )
            
            # Convert back to Requirement objects
            related_req_objects = [
                req for req in recipe.requirements.functional_requirements 
                if req.description in related_reqs
            ]
            
            if related_req_objects:
                sub_recipe = SubRecipe(
                    name=f"{recipe.name}-{component.name.lower().replace(' ', '-')}",
                    parent_recipe=recipe.name,
                    requirements=Requirements(
                        purpose=f"Component {component.name} of {recipe.requirements.purpose}",
                        functional_requirements=related_req_objects,
                        non_functional_requirements=[],  # Inherit from parent
                        success_criteria=[]
                    ),
                    design=Design(
                        architecture="Component-based",
                        components=[component],
                        interfaces=[],
                        implementation_notes=""
                    ),
                    dependencies=[],
                    complexity_metrics=ComplexityMetrics(
                        functional_requirements_count=len(related_reqs),
                        non_functional_requirements_count=0,
                        component_count=1,
                        dependency_count=0,
                        interface_count=len(component.methods) if hasattr(component, 'methods') else 0,
                        estimated_loc=self._estimate_lines_of_code(len(related_req_objects), 1, 
                                                                   len(component.methods) if hasattr(component, 'methods') else 0),
                        complexity_score=3.0  # Simplified score for sub-recipe
                    )
                )
                sub_recipes.append(sub_recipe)
        
        return sub_recipes
    
    def _decompose_by_features(self, recipe: Recipe) -> List[SubRecipe]:
        """Decompose recipe by grouping related functional requirements."""
        sub_recipes: List[SubRecipe] = []
        requirements = recipe.requirements.functional_requirements
        
        # Simple clustering: group every N requirements
        chunk_size = self.MAX_FUNCTIONAL_REQUIREMENTS // 2
        for i in range(0, len(requirements), chunk_size):
            chunk = requirements[i:i+chunk_size]
            if chunk:
                sub_recipe = SubRecipe(
                    name=f"{recipe.name}-feature-{i//chunk_size + 1}",
                    parent_recipe=recipe.name,
                    requirements=Requirements(
                        purpose=f"Feature group {i//chunk_size + 1} of {recipe.requirements.purpose}",
                        functional_requirements=chunk,
                        non_functional_requirements=[],
                        success_criteria=[]
                    ),
                    design=None,  # Will be generated during implementation
                    dependencies=[],
                    complexity_metrics=ComplexityMetrics(
                        functional_requirements_count=len(chunk),
                        non_functional_requirements_count=0,
                        component_count=0,
                        dependency_count=0,
                        interface_count=0,
                        estimated_loc=self._estimate_lines_of_code(len(chunk), 0, 0),
                        complexity_score=2.0
                    )
                )
                sub_recipes.append(sub_recipe)
        
        return sub_recipes
    
    def _decompose_by_layers(self, recipe: Recipe) -> List[SubRecipe]:
        """Decompose recipe into architectural layers (data, logic, presentation)."""
        # Categorize requirements by layer
        data_reqs: List[Requirement] = []
        logic_reqs: List[Requirement] = []
        presentation_reqs: List[Requirement] = []
        
        for req in recipe.requirements.functional_requirements:
            req_lower = req.description.lower()
            if any(keyword in req_lower for keyword in ['data', 'storage', 'database', 'persist']):
                data_reqs.append(req)
            elif any(keyword in req_lower for keyword in ['ui', 'interface', 'display', 'view']):
                presentation_reqs.append(req)
            else:
                logic_reqs.append(req)
        
        sub_recipes: List[SubRecipe] = []
        
        # Create sub-recipe for each layer with requirements
        layers: List[Tuple[str, List[Requirement]]] = [
            ("data-layer", data_reqs),
            ("logic-layer", logic_reqs),
            ("presentation-layer", presentation_reqs)
        ]
        
        for layer_name, layer_reqs in layers:
            if layer_reqs:
                sub_recipe = SubRecipe(
                    name=f"{recipe.name}-{layer_name}",
                    parent_recipe=recipe.name,
                    requirements=Requirements(
                        purpose=f"{layer_name.replace('-', ' ').title()} of {recipe.requirements.purpose}",
                        functional_requirements=layer_reqs,
                        non_functional_requirements=[],
                        success_criteria=[]
                    ),
                    design=None,
                    dependencies=[],
                    complexity_metrics=ComplexityMetrics(
                        functional_requirements_count=len(layer_reqs),
                        non_functional_requirements_count=0,
                        component_count=0,
                        dependency_count=0,
                        interface_count=0,
                        estimated_loc=self._estimate_lines_of_code(len(layer_reqs), 0, 0),
                        complexity_score=2.5
                    )
                )
                sub_recipes.append(sub_recipe)
        
        return sub_recipes
    
    def _find_related_requirements(self, component_name: str, requirements: List[str]) -> List[str]:
        """Find requirements related to a specific component."""
        related: List[str] = []
        component_keywords = component_name.lower().split()
        
        for req in requirements:
            req_lower = req.lower()
            if any(keyword in req_lower for keyword in component_keywords):
                related.append(req)
        
        return related
    
    def _estimate_lines_of_code(self, req_count: int, comp_count: int, interface_count: int) -> int:
        """Estimate lines of code based on recipe metrics."""
        # Rough heuristic: 50 LOC per requirement, 100 per component, 20 per interface
        return (req_count * 50) + (comp_count * 100) + (interface_count * 20)
    
    def _calculate_complexity_score(
        self,
        func_reqs: int,
        non_func_reqs: int,
        components: int,
        dependencies: int,
        interfaces: int,
        estimated_loc: int
    ) -> float:
        """
        Calculate overall complexity score on a 1-10 scale.
        
        Weighted formula considering multiple factors.
        """
        score = 0.0
        
        # Functional requirements (weight: 30%)
        score += min(func_reqs / self.MAX_FUNCTIONAL_REQUIREMENTS, 1.0) * 3.0
        
        # Components (weight: 25%)
        score += min(components / self.MAX_COMPONENTS, 1.0) * 2.5
        
        # Estimated LOC (weight: 20%)
        score += min(estimated_loc / self.MAX_ESTIMATED_LOC, 1.0) * 2.0
        
        # Dependencies (weight: 15%)
        score += min(dependencies / 10, 1.0) * 1.5
        
        # Interfaces (weight: 10%)
        score += min(interfaces / 20, 1.0) * 1.0
        
        return min(score, 10.0)  # Cap at 10
    
    def evaluate_complexity_for_sub_recipe(self, sub_recipe: SubRecipe) -> ComplexityMetrics:
        """Evaluate complexity of a sub-recipe."""
        return sub_recipe.complexity_metrics
    
    def save_sub_recipes(self, sub_recipes: List[SubRecipe], output_dir: Path) -> None:
        """
        Save decomposed sub-recipes to disk for processing.
        
        Creates a sub-recipes directory with proper structure.
        """
        if not sub_recipes:
            return
        
        sub_recipe_dir = output_dir / "sub-recipes"
        sub_recipe_dir.mkdir(parents=True, exist_ok=True)
        
        for sub_recipe in sub_recipes:
            recipe_dir = sub_recipe_dir / sub_recipe.name
            recipe_dir.mkdir(exist_ok=True)
            
            # Write requirements.md
            req_file = recipe_dir / "requirements.md"
            req_content = f"# Requirements for {sub_recipe.name}\n\n"
            req_content += f"Parent Recipe: {sub_recipe.parent_recipe}\n\n"
            req_content += "## Functional Requirements\n\n"
            for req in sub_recipe.requirements.functional_requirements:
                req_content += f"- {req.description}\n"
            req_file.write_text(req_content)
            
            # Write design.md if available
            if sub_recipe.design:
                design_file = recipe_dir / "design.md"
                design_content = f"# Design for {sub_recipe.name}\n\n"
                design_content += f"Architecture: {sub_recipe.design.architecture}\n\n"
                design_content += "## Components\n\n"
                for comp in sub_recipe.design.components:
                    design_content += f"### {comp.name}\n"
                    design_content += f"{comp.description}\n\n"
                design_file.write_text(design_content)
            
            # Write components.json
            components_file = recipe_dir / "components.json"
            components_data = {
                "name": sub_recipe.name,
                "parent": sub_recipe.parent_recipe,
                "dependencies": sub_recipe.dependencies,
                "complexity_metrics": {
                    "functional_requirements": sub_recipe.complexity_metrics.functional_requirements_count,
                    "components": sub_recipe.complexity_metrics.component_count,
                    "estimated_loc": sub_recipe.complexity_metrics.estimated_loc,
                    "complexity_score": sub_recipe.complexity_metrics.complexity_score,
                    "is_complex": sub_recipe.complexity_metrics.is_complex
                }
            }
            components_file.write_text(json.dumps(components_data, indent=2))
        
        logger.info(f"Saved {len(sub_recipes)} sub-recipes to {sub_recipe_dir}")