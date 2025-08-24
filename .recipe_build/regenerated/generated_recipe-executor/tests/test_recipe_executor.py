"""Tests for Recipe Executor core functionality."""

import json
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from src.recipe_model import (
    ComponentType,
    Components,
    Design,
    Recipe,
    RecipeMetadata,
    Requirement,
    RequirementPriority,
    Requirements,
)
from src.recipe_parser import RecipeParser
from src.recipe_validator import RecipeValidator
from src.dependency_resolver import DependencyResolver


@pytest.fixture
def sample_recipe_dir(tmp_path):
    """Create a sample recipe directory structure."""
    recipe_dir = tmp_path / "sample-recipe"
    recipe_dir.mkdir()
    
    # Create requirements.md
    requirements = """# Sample Recipe Requirements

## Purpose
A sample recipe for testing the Recipe Executor.

## Functional Requirements
- MUST parse input files correctly
- MUST validate data structures
- SHOULD support caching for performance
- COULD provide detailed logging

## Success Criteria
- All input files are parsed without errors
- Validation catches all invalid inputs
- Performance meets requirements
"""
    (recipe_dir / "requirements.md").write_text(requirements)
    
    # Create design.md
    design = """# Sample Recipe Design

## Architecture
Multi-layer architecture with clear separation of concerns.

## Components

- **Parser**: Handles file parsing
  - Class: `FileParser`
  - Methods: `parse`, `validate`
  
- **Validator**: Validates data
  - Class: `DataValidator`
  - Methods: `validate`, `check_rules`

- **Cache**: Caching layer
  - Class: `CacheManager`
  - Methods: `get`, `set`, `clear`

## Implementation Notes
Use Python type hints throughout for better type safety.

## Language
Python
"""
    (recipe_dir / "design.md").write_text(design)
    
    # Create components.json
    components = {
        "name": "sample-recipe",
        "version": "1.0.0",
        "type": "LIBRARY",
        "dependencies": [],
        "description": "Sample recipe for testing",
        "metadata": {
            "author": "test",
            "tags": ["sample", "test"]
        }
    }
    (recipe_dir / "components.json").write_text(json.dumps(components, indent=2))
    
    return recipe_dir


@pytest.fixture
def complex_recipe_dir(tmp_path):
    """Create a complex recipe for decomposition testing."""
    recipe_dir = tmp_path / "complex-recipe"
    recipe_dir.mkdir()
    
    # Create requirements with many items
    requirements = """# Complex Recipe Requirements

## Purpose
A complex recipe requiring decomposition.

## Functional Requirements
"""
    # Add 25 requirements to trigger complexity
    for i in range(25):
        requirements += f"- MUST implement feature {i+1}\n"
    
    requirements += "\n## Success Criteria\n- All features implemented\n"
    
    (recipe_dir / "requirements.md").write_text(requirements)
    
    # Create design with many components
    design = """# Complex Recipe Design

## Architecture
Complex multi-tier architecture.

## Components
"""
    # Add 15 components to trigger complexity
    for i in range(15):
        design += f"""
- **Component{i+1}**: Does something
  - Class: `Component{i+1}`
  - Methods: `method1`, `method2`, `method3`, `method4`, `method5`
"""
    
    design += "\n## Language\nPython\n"
    
    (recipe_dir / "design.md").write_text(design)
    
    # Create components.json with dependencies
    components = {
        "name": "complex-recipe",
        "version": "1.0.0",
        "type": "SERVICE",
        "dependencies": ["dep1", "dep2", "dep3", "dep4", "dep5", "dep6"],
        "description": "Complex recipe",
        "metadata": {}
    }
    (recipe_dir / "components.json").write_text(json.dumps(components, indent=2))
    
    return recipe_dir


class TestRecipeParser:
    """Test recipe parsing functionality."""
    
    def test_parse_valid_recipe(self, sample_recipe_dir):
        """Test parsing a valid recipe."""
        parser = RecipeParser()
        recipe = parser.parse_recipe(sample_recipe_dir)
        
        assert recipe.name == "sample-recipe"
        assert recipe.components.version == "1.0.0"
        assert recipe.components.type == ComponentType.LIBRARY
        assert len(recipe.requirements.functional_requirements) == 4
        assert len(recipe.design.components) == 3
    
    def test_parse_requirements(self, sample_recipe_dir):
        """Test parsing requirements with priorities."""
        parser = RecipeParser()
        recipe = parser.parse_recipe(sample_recipe_dir)
        
        reqs = recipe.requirements.functional_requirements
        assert reqs[0].priority == RequirementPriority.MUST
        assert reqs[1].priority == RequirementPriority.MUST
        assert reqs[2].priority == RequirementPriority.SHOULD
        assert reqs[3].priority == RequirementPriority.COULD
    
    def test_parse_design_components(self, sample_recipe_dir):
        """Test parsing design components."""
        parser = RecipeParser()
        recipe = parser.parse_recipe(sample_recipe_dir)
        
        components = recipe.design.components
        assert len(components) == 3
        assert components[0].name == "Parser"
        assert components[0].class_name == "FileParser"
        assert "parse" in components[0].methods
    
    def test_missing_files(self, tmp_path):
        """Test error handling for missing files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        parser = RecipeParser()
        with pytest.raises(Exception) as exc_info:
            parser.parse_recipe(empty_dir)
        assert "Missing required files" in str(exc_info.value)


class TestRecipeValidator:
    """Test recipe validation functionality."""
    
    def test_validate_valid_recipe(self, sample_recipe_dir):
        """Test validating a valid recipe."""
        parser = RecipeParser()
        recipe = parser.parse_recipe(sample_recipe_dir)
        
        validator = RecipeValidator()
        result = validator.validate(recipe)
        
        assert result.valid
        assert len(result.get_errors()) == 0
    
    def test_validate_separation(self, tmp_path):
        """Test WHAT/HOW separation validation."""
        recipe_dir = tmp_path / "bad-recipe"
        recipe_dir.mkdir()
        
        # Requirements with HOW details
        requirements = """# Requirements
## Functional Requirements
- MUST use PostgreSQL for data storage
- MUST implement using Django framework
"""
        (recipe_dir / "requirements.md").write_text(requirements)
        
        # Design with WHAT details
        design = """# Design
## Components
- Component1: MUST validate all inputs
- Component2: system shall process data
"""
        (recipe_dir / "design.md").write_text(design)
        
        # Components.json
        components = {
            "name": "bad-recipe",
            "version": "1.0.0",
            "type": "LIBRARY",
            "dependencies": []
        }
        (recipe_dir / "components.json").write_text(json.dumps(components))
        
        parser = RecipeParser()
        recipe = parser.parse_recipe(recipe_dir)
        
        validator = RecipeValidator()
        result = validator.validate_separation(recipe)
        
        assert not result.valid
        assert len(result.get_errors()) > 0
        
        # Check for specific violations
        error_messages = [e.message for e in result.get_errors()]
        assert any("PostgreSQL" in msg for msg in error_messages)


class TestDependencyResolver:
    """Test dependency resolution functionality."""
    
    def test_simple_dependency_chain(self):
        """Test resolving a simple dependency chain."""
        # Create mock recipes
        recipes = {}
        
        # Recipe A depends on B
        recipe_a = self._create_mock_recipe("A", ["B"])
        recipe_b = self._create_mock_recipe("B", [])
        
        recipes["A"] = recipe_a
        recipes["B"] = recipe_b
        
        resolver = DependencyResolver()
        build_order = resolver.resolve(recipes)
        
        assert len(build_order) == 2
        assert build_order[0].name == "B"  # B built first
        assert build_order[1].name == "A"  # Then A
    
    def test_parallel_groups(self):
        """Test identifying parallel execution groups."""
        recipes = {}
        
        # A and B have no dependencies (can build in parallel)
        # C depends on both A and B
        recipe_a = self._create_mock_recipe("A", [])
        recipe_b = self._create_mock_recipe("B", [])
        recipe_c = self._create_mock_recipe("C", ["A", "B"])
        
        recipes["A"] = recipe_a
        recipes["B"] = recipe_b
        recipes["C"] = recipe_c
        
        resolver = DependencyResolver()
        build_order = resolver.resolve(recipes)
        parallel_groups = resolver.get_parallel_groups(build_order)
        
        assert len(parallel_groups) == 2
        assert parallel_groups[0].size() == 2  # A and B in parallel
        assert parallel_groups[1].size() == 1  # C alone
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        recipes = {}
        
        # Create circular dependency: A -> B -> C -> A
        recipe_a = self._create_mock_recipe("A", ["B"])
        recipe_b = self._create_mock_recipe("B", ["C"])
        recipe_c = self._create_mock_recipe("C", ["A"])
        
        recipes["A"] = recipe_a
        recipes["B"] = recipe_b
        recipes["C"] = recipe_c
        
        resolver = DependencyResolver()
        with pytest.raises(Exception) as exc_info:
            resolver.resolve(recipes)
        assert "Circular dependency" in str(exc_info.value)
    
    def test_missing_dependency(self):
        """Test handling of missing dependencies."""
        recipes = {}
        
        # A depends on B, but B doesn't exist
        recipe_a = self._create_mock_recipe("A", ["B"])
        recipes["A"] = recipe_a
        
        resolver = DependencyResolver()
        with pytest.raises(Exception) as exc_info:
            resolver.resolve(recipes)
        assert "missing recipe" in str(exc_info.value).lower()
    
    def _create_mock_recipe(self, name: str, dependencies: list) -> Recipe:
        """Create a mock recipe for testing."""
        from datetime import datetime
        
        return Recipe(
            name=name,
            path=Path(f"/mock/{name}"),
            requirements=Requirements(
                purpose="Mock",
                functional_requirements=[],
                non_functional_requirements=[],
                success_criteria=[]
            ),
            design=Design(
                architecture="Mock",
                components=[],
                interfaces=[],
                implementation_notes="",
                code_blocks=[]
            ),
            components=Components(
                name=name,
                version="1.0.0",
                type=ComponentType.LIBRARY,
                dependencies=dependencies,
                description="Mock"
            ),
            metadata=RecipeMetadata(
                created_at=datetime.now(),
                last_modified=datetime.now(),
                checksum="mock"
            )
        )


class TestRecipeComplexity:
    """Test recipe complexity analysis."""
    
    def test_simple_recipe_complexity(self, sample_recipe_dir):
        """Test complexity scoring for simple recipe."""
        from src.recipe_decomposer import RecipeDecomposer
        
        parser = RecipeParser()
        recipe = parser.parse_recipe(sample_recipe_dir)
        
        decomposer = RecipeDecomposer()
        result = decomposer.evaluate_complexity(recipe)
        
        assert result.score < 5  # Should be simple
        assert not result.needs_decomposition
        assert result.get_severity() in ["simple", "moderate"]
    
    def test_complex_recipe_decomposition(self, complex_recipe_dir):
        """Test complexity analysis for complex recipe."""
        from src.recipe_decomposer import RecipeDecomposer
        
        parser = RecipeParser()
        recipe = parser.parse_recipe(complex_recipe_dir)
        
        decomposer = RecipeDecomposer()
        result = decomposer.evaluate_complexity(recipe)
        
        assert result.score >= 5  # Should be complex
        assert result.needs_decomposition
        assert result.get_severity() in ["complex", "very_complex"]
        assert result.strategy is not None
        assert len(result.reasons) > 0