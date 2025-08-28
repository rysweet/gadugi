"""Recipe complexity evaluation and analysis."""

import logging
from typing import Dict, List
from dataclasses import dataclass

from .recipe_model import (
    Recipe,
    RecipeComplexity,
    RequirementPriority,
    ComponentType,
)

logger = logging.getLogger(__name__)


@dataclass
class ComplexityMetrics:
    """Detailed complexity metrics for a recipe."""
    
    lines_of_code_estimate: int = 0
    test_complexity: int = 0
    integration_points: int = 0
    external_dependencies: int = 0
    data_structures: int = 0
    algorithms_complexity: int = 0
    error_handling_paths: int = 0
    configuration_complexity: int = 0
    deployment_complexity: int = 0
    maintenance_burden: float = 0.0
    
    def calculate_total_score(self) -> float:
        """Calculate total complexity score."""
        # Weight different factors
        weights = {
            "loc": 0.15,
            "test": 0.10,
            "integration": 0.15,
            "external": 0.10,
            "data": 0.10,
            "algorithms": 0.15,
            "errors": 0.05,
            "config": 0.05,
            "deploy": 0.05,
            "maintenance": 0.10
        }
        
        # Normalize and calculate
        score = 0.0
        score += min(self.lines_of_code_estimate / 1000, 10) * weights["loc"] * 10
        score += min(self.test_complexity / 100, 10) * weights["test"] * 10
        score += min(self.integration_points / 10, 10) * weights["integration"] * 10
        score += min(self.external_dependencies / 10, 10) * weights["external"] * 10
        score += min(self.data_structures / 20, 10) * weights["data"] * 10
        score += min(self.algorithms_complexity / 50, 10) * weights["algorithms"] * 10
        score += min(self.error_handling_paths / 20, 10) * weights["errors"] * 10
        score += min(self.configuration_complexity / 10, 10) * weights["config"] * 10
        score += min(self.deployment_complexity / 10, 10) * weights["deploy"] * 10
        score += self.maintenance_burden * weights["maintenance"] * 10
        
        return min(score, 100.0)


class ComplexityAnalyzer:
    """Analyzes recipe complexity and provides decomposition recommendations."""
    
    def __init__(self):
        """Initialize the complexity analyzer."""
        self.complexity_cache: Dict[str, RecipeComplexity] = {}
        self.metrics_cache: Dict[str, ComplexityMetrics] = {}
        self.decomposition_strategies: Dict[str, List[str]] = {}
    
    def analyze_recipe(self, recipe: Recipe) -> RecipeComplexity:
        """Analyze the complexity of a recipe.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            RecipeComplexity analysis
        """
        # Check cache
        if recipe.name in self.complexity_cache:
            return self.complexity_cache[recipe.name]
        
        # Calculate detailed metrics
        metrics = self._calculate_detailed_metrics(recipe)
        self.metrics_cache[recipe.name] = metrics
        
        # Create complexity analysis
        complexity = RecipeComplexity(
            recipe_name=recipe.name,
            complexity_score=0.0,
            component_count=len(recipe.design.components),
            dependency_count=len(recipe.get_dependencies()),
            requirement_count=len(recipe.requirements.get_all_requirements()),
            interface_count=len(recipe.design.interfaces),
            cyclomatic_complexity=self._calculate_cyclomatic_complexity(recipe),
            cognitive_complexity=self._calculate_cognitive_complexity(recipe),
            decomposition_recommended=False,
        )
        
        # Calculate complexity factors
        complexity.complexity_factors = {
            "structural": self._calculate_structural_complexity(recipe),
            "behavioral": self._calculate_behavioral_complexity(recipe),
            "data": self._calculate_data_complexity(recipe),
            "integration": self._calculate_integration_complexity(recipe),
            "quality": self._calculate_quality_complexity(recipe),
        }
        
        # Calculate overall score
        complexity.calculate_overall_score()
        
        # Add detailed metrics score
        detailed_score = metrics.calculate_total_score()
        complexity.complexity_score = (complexity.complexity_score + detailed_score) / 2
        
        # Determine if decomposition is needed
        complexity.decomposition_recommended = complexity.should_decompose()
        
        # Generate decomposition suggestions
        if complexity.decomposition_recommended:
            suggestions = complexity.generate_decomposition_suggestions()
            # Add analyzer-specific suggestions
            suggestions.extend(self._generate_advanced_suggestions(recipe, complexity))
            complexity.decomposition_suggestions = suggestions
        
        # Cache the result
        self.complexity_cache[recipe.name] = complexity
        
        logger.info(f"Recipe '{recipe.name}' complexity: {complexity.complexity_score:.1f}, "
                   f"decomposition: {complexity.decomposition_recommended}")
        
        return complexity
    
    def _calculate_detailed_metrics(self, recipe: Recipe) -> ComplexityMetrics:
        """Calculate detailed complexity metrics.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            ComplexityMetrics with detailed analysis
        """
        metrics = ComplexityMetrics()
        
        # Estimate lines of code
        metrics.lines_of_code_estimate = self._estimate_lines_of_code(recipe)
        
        # Test complexity
        metrics.test_complexity = self._estimate_test_complexity(recipe)
        
        # Integration points
        metrics.integration_points = len(recipe.design.interfaces) * 2
        metrics.integration_points += len(recipe.get_dependencies()) * 3
        
        # External dependencies (rough estimate)
        metrics.external_dependencies = len(recipe.components.metadata.get("external_deps", []))
        
        # Data structures
        metrics.data_structures = self._count_data_structures(recipe)
        
        # Algorithm complexity
        metrics.algorithms_complexity = self._estimate_algorithm_complexity(recipe)
        
        # Error handling
        metrics.error_handling_paths = self._count_error_paths(recipe)
        
        # Configuration complexity
        metrics.configuration_complexity = len(recipe.components.metadata.get("config_options", {}))
        
        # Deployment complexity
        metrics.deployment_complexity = self._estimate_deployment_complexity(recipe)
        
        # Maintenance burden
        metrics.maintenance_burden = self._calculate_maintenance_burden(recipe)
        
        return metrics
    
    def _estimate_lines_of_code(self, recipe: Recipe) -> int:
        """Estimate lines of code for the recipe.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Estimated lines of code
        """
        # Base estimate per component
        loc_per_component = 200
        loc_per_method = 30
        loc_per_interface = 100
        
        loc = len(recipe.design.components) * loc_per_component
        
        # Add for methods
        for component in recipe.design.components:
            loc += len(component.methods) * loc_per_method
        
        # Add for interfaces
        loc += len(recipe.design.interfaces) * loc_per_interface
        
        # Add for requirements (validation code)
        loc += len(recipe.requirements.get_all_requirements()) * 20
        
        return loc
    
    def _estimate_test_complexity(self, recipe: Recipe) -> int:
        """Estimate test complexity.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Test complexity score
        """
        # Base complexity
        complexity = 0
        
        # Unit tests per component
        complexity += len(recipe.design.components) * 5
        
        # Integration tests per interface
        complexity += len(recipe.design.interfaces) * 8
        
        # Tests for requirements
        must_reqs = recipe.requirements.get_must_requirements()
        complexity += len(must_reqs) * 3
        
        # Additional complexity for validation criteria
        for req in recipe.requirements.get_all_requirements():
            complexity += len(req.validation_criteria) * 2
        
        return complexity
    
    def _count_data_structures(self, recipe: Recipe) -> int:
        """Count data structures in the recipe.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Number of data structures
        """
        count = 0
        
        # Count properties as potential data structures
        for component in recipe.design.components:
            count += len(component.properties)
        
        # Count data types in interfaces
        for interface in recipe.design.interfaces:
            count += len(interface.data_types)
        
        return count
    
    def _estimate_algorithm_complexity(self, recipe: Recipe) -> int:
        """Estimate algorithmic complexity.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Algorithm complexity score
        """
        # Based on component methods and their likely complexity
        complexity = 0
        
        for component in recipe.design.components:
            for method in component.methods:
                # Heuristic based on method name
                if any(keyword in method.lower() for keyword in ["sort", "search", "optimize", "calculate"]):
                    complexity += 10
                elif any(keyword in method.lower() for keyword in ["process", "transform", "analyze"]):
                    complexity += 7
                else:
                    complexity += 3
        
        return complexity
    
    def _count_error_paths(self, recipe: Recipe) -> int:
        """Count error handling paths.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Number of error paths
        """
        # Estimate based on components and interfaces
        error_paths = 0
        
        # Each component likely has error handling
        error_paths += len(recipe.design.components) * 2
        
        # Each interface method may have error conditions
        for interface in recipe.design.interfaces:
            error_paths += len(interface.methods)
        
        # Dependencies may fail
        error_paths += len(recipe.get_dependencies())
        
        return error_paths
    
    def _estimate_deployment_complexity(self, recipe: Recipe) -> int:
        """Estimate deployment complexity.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Deployment complexity score
        """
        complexity = 0
        
        # Service components are more complex to deploy
        if recipe.components.type == ComponentType.SERVICE:
            complexity += 5
        
        # Dependencies add deployment complexity
        complexity += len(recipe.get_dependencies())
        
        # External dependencies add more complexity
        complexity += len(recipe.components.metadata.get("external_deps", [])) * 2
        
        # Configuration adds complexity
        complexity += len(recipe.components.metadata.get("config_options", {}))
        
        return complexity
    
    def _calculate_maintenance_burden(self, recipe: Recipe) -> float:
        """Calculate maintenance burden.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Maintenance burden score (0-1)
        """
        burden = 0.0
        
        # Complex recipes are harder to maintain
        if len(recipe.design.components) > 10:
            burden += 0.2
        
        # Many dependencies increase maintenance
        if len(recipe.get_dependencies()) > 5:
            burden += 0.2
        
        # Many interfaces mean more contracts to maintain
        if len(recipe.design.interfaces) > 5:
            burden += 0.2
        
        # High requirement count means more to validate
        if len(recipe.requirements.get_all_requirements()) > 20:
            burden += 0.2
        
        # Self-hosting recipes are complex to maintain
        if recipe.is_self_hosting():
            burden += 0.2
        
        return min(burden, 1.0)
    
    def _calculate_cyclomatic_complexity(self, recipe: Recipe) -> int:
        """Calculate cyclomatic complexity.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Cyclomatic complexity value
        """
        # Base complexity
        complexity = 1
        
        # Add for each component (potential decision point)
        complexity += len(recipe.design.components)
        
        # Add for each method (likely contains branches)
        for component in recipe.design.components:
            complexity += len(component.methods) * 2
        
        # Add for interfaces (contract branches)
        complexity += len(recipe.design.interfaces) * 2
        
        # Add for dependencies (potential failure branches)
        complexity += len(recipe.get_dependencies())
        
        # Add for validation criteria (conditional checks)
        for req in recipe.requirements.get_all_requirements():
            complexity += len(req.validation_criteria)
        
        return complexity
    
    def _calculate_cognitive_complexity(self, recipe: Recipe) -> int:
        """Calculate cognitive complexity.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Cognitive complexity value
        """
        complexity = 0
        
        # Requirements add cognitive load
        for req in recipe.requirements.get_all_requirements():
            if req.priority == RequirementPriority.MUST:
                complexity += 3
            elif req.priority == RequirementPriority.SHOULD:
                complexity += 2
            else:
                complexity += 1
            
            # Validation criteria add to understanding
            complexity += len(req.validation_criteria)
        
        # Components add cognitive load
        complexity += len(recipe.design.components) * 2
        
        # Interfaces require understanding contracts
        complexity += len(recipe.design.interfaces) * 3
        
        # Dependencies require understanding external behavior
        complexity += len(recipe.get_dependencies()) * 2
        
        return complexity
    
    def _calculate_structural_complexity(self, recipe: Recipe) -> float:
        """Calculate structural complexity factor.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Structural complexity (0-1)
        """
        factors: List[float] = []
        
        # Component count factor
        factors.append(min(len(recipe.design.components) / 15, 1.0))
        
        # Interface count factor
        factors.append(min(len(recipe.design.interfaces) / 10, 1.0))
        
        # Dependency depth factor
        factors.append(min(len(recipe.get_dependencies()) / 10, 1.0))
        
        return sum(factors) / len(factors) if factors else 0.0
    
    def _calculate_behavioral_complexity(self, recipe: Recipe) -> float:
        """Calculate behavioral complexity factor.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Behavioral complexity (0-1)
        """
        total_methods = 0
        total_events = 0
        
        for component in recipe.design.components:
            total_methods += len(component.methods)
        
        for interface in recipe.design.interfaces:
            total_methods += len(interface.methods)
            total_events += len(interface.events)
        
        # Normalize
        method_factor = min(total_methods / 50, 1.0)
        event_factor = min(total_events / 20, 1.0)
        
        return (method_factor + event_factor) / 2
    
    def _calculate_data_complexity(self, recipe: Recipe) -> float:
        """Calculate data complexity factor.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Data complexity (0-1)
        """
        total_properties = 0
        total_data_types = 0
        
        for component in recipe.design.components:
            total_properties += len(component.properties)
        
        for interface in recipe.design.interfaces:
            total_data_types += len(interface.data_types)
        
        # Normalize
        property_factor = min(total_properties / 30, 1.0)
        type_factor = min(total_data_types / 20, 1.0)
        
        return (property_factor + type_factor) / 2
    
    def _calculate_integration_complexity(self, recipe: Recipe) -> float:
        """Calculate integration complexity factor.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Integration complexity (0-1)
        """
        # Dependencies
        dep_factor = min(len(recipe.get_dependencies()) / 10, 1.0)
        
        # Interfaces
        interface_factor = min(len(recipe.design.interfaces) / 8, 1.0)
        
        # External dependencies
        external = len(recipe.components.metadata.get("external_deps", []))
        external_factor = min(external / 5, 1.0)
        
        return (dep_factor + interface_factor + external_factor) / 3
    
    def _calculate_quality_complexity(self, recipe: Recipe) -> float:
        """Calculate quality assurance complexity factor.
        
        Args:
            recipe: The recipe to analyze
            
        Returns:
            Quality complexity (0-1)
        """
        # Requirements with validation criteria
        validated_reqs = sum(
            1 for req in recipe.requirements.get_all_requirements()
            if req.validation_criteria
        )
        validation_factor = min(validated_reqs / 20, 1.0)
        
        # Must requirements
        must_factor = min(len(recipe.requirements.get_must_requirements()) / 15, 1.0)
        
        # Success criteria
        criteria_factor = min(len(recipe.requirements.success_criteria) / 10, 1.0)
        
        return (validation_factor + must_factor + criteria_factor) / 3
    
    def _generate_advanced_suggestions(self, recipe: Recipe, complexity: RecipeComplexity) -> List[str]:
        """Generate advanced decomposition suggestions.
        
        Args:
            recipe: The recipe being analyzed
            complexity: The complexity analysis
            
        Returns:
            List of advanced suggestions
        """
        suggestions: List[str] = []
        
        # Get detailed metrics
        metrics = self.metrics_cache.get(recipe.name)
        
        if metrics:
            # Lines of code suggestion
            if metrics.lines_of_code_estimate > 2000:
                suggestions.append(
                    f"Estimated {metrics.lines_of_code_estimate} lines of code. "
                    "Consider splitting into modules of 500-800 lines each."
                )
            
            # Test complexity suggestion
            if metrics.test_complexity > 100:
                suggestions.append(
                    f"Test complexity score is {metrics.test_complexity}. "
                    "Create separate test recipes for unit, integration, and e2e tests."
                )
            
            # Integration points suggestion
            if metrics.integration_points > 15:
                suggestions.append(
                    f"Recipe has {metrics.integration_points} integration points. "
                    "Consider creating an integration layer recipe."
                )
            
            # Maintenance burden suggestion
            if metrics.maintenance_burden > 0.6:
                suggestions.append(
                    f"High maintenance burden ({metrics.maintenance_burden:.1%}). "
                    "Simplify by extracting stable components into separate recipes."
                )
        
        # Complexity factor suggestions
        for factor_name, factor_value in complexity.complexity_factors.items():
            if factor_value > 0.7:
                suggestions.append(
                    f"High {factor_name} complexity ({factor_value:.1%}). "
                    f"Focus decomposition on reducing {factor_name} aspects."
                )
        
        # Pattern-based suggestions
        if recipe.components.type == ComponentType.SERVICE:
            suggestions.append(
                "Service recipe detected. Consider separating API, business logic, "
                "and data access layers into distinct recipes."
            )
        elif recipe.components.type == ComponentType.AGENT:
            suggestions.append(
                "Agent recipe detected. Consider separating sensing, planning, "
                "and acting components into distinct recipes."
            )
        
        return suggestions
    
    def suggest_decomposition_strategy(self, recipe: Recipe) -> List[str]:
        """Suggest a specific decomposition strategy.
        
        Args:
            recipe: The recipe to decompose
            
        Returns:
            List of strategy steps
        """
        complexity = self.analyze_recipe(recipe)
        
        if not complexity.decomposition_recommended:
            return ["No decomposition needed - recipe complexity is manageable."]
        
        strategy: List[str] = []
        
        # Determine primary decomposition approach
        if complexity.component_count > 15:
            strategy.append("1. Component-based decomposition:")
            strategy.append("   - Group related components by functionality")
            strategy.append("   - Create sub-recipes for each component group")
            strategy.append("   - Define clear interfaces between sub-recipes")
        
        elif complexity.dependency_count > 10:
            strategy.append("1. Dependency-based decomposition:")
            strategy.append("   - Extract common dependencies into a base recipe")
            strategy.append("   - Create specialized recipes for different dependency sets")
            strategy.append("   - Use dependency injection for flexibility")
        
        elif complexity.requirement_count > 25:
            strategy.append("1. Feature-based decomposition:")
            strategy.append("   - Group requirements by feature area")
            strategy.append("   - Create focused recipes for each feature")
            strategy.append("   - Maintain traceability between features and requirements")
        
        else:
            strategy.append("1. Layered decomposition:")
            strategy.append("   - Separate into presentation, business, and data layers")
            strategy.append("   - Create recipes for each architectural layer")
            strategy.append("   - Define clear layer boundaries and interactions")
        
        # Add common steps
        strategy.extend([
            "2. Create integration recipe to combine sub-recipes",
            "3. Define clear contracts between sub-recipes",
            "4. Implement incremental build support",
            "5. Add comprehensive integration tests",
            "6. Document the decomposition rationale"
        ])
        
        # Cache the strategy
        self.decomposition_strategies[recipe.name] = strategy
        
        return strategy