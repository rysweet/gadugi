"""Tests for Design Patterns functionality."""

import pytest
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.recipe_executor.pattern_manager import (
    PatternManager,
    DesignPattern,
    PatternConfig,
)
from src.recipe_executor.recipe_model import (
    Recipe,
    Requirements,
    Design,
    Components,
    ComponentType,
    Requirement,
    RequirementPriority,
    RecipeMetadata,
)


@pytest.fixture
def temp_patterns_dir():
    """Create a temporary patterns directory."""
    temp_dir = tempfile.mkdtemp()
    patterns_dir = Path(temp_dir) / "patterns"
    patterns_dir.mkdir()
    
    # Create a test pattern
    test_pattern_dir = patterns_dir / "test-pattern"
    test_pattern_dir.mkdir()
    
    # Write pattern.json
    pattern_config = {
        "name": "test-pattern",
        "version": "1.0.0",
        "description": "A test pattern",
        "target_types": ["service"],
        "auto_apply": False,
        "depends_on": []
    }
    with open(test_pattern_dir / "pattern.json", "w") as f:
        json.dump(pattern_config, f)
    
    # Write requirements.md
    requirements_content = """# Test Pattern Requirements

## Purpose
Test pattern for unit testing

## Functional Requirements
- Must provide testing functionality
- Should validate inputs

## Non-Functional Requirements
- Must be fast
- Should be reliable

## Success Criteria
- All tests pass
- Coverage > 80%
"""
    (test_pattern_dir / "requirements.md").write_text(requirements_content)
    
    # Write design.md
    design_content = """# Test Pattern Design

## Architecture
Simple test architecture

## Implementation Notes
Use pytest for testing
"""
    (test_pattern_dir / "design.md").write_text(design_content)
    
    # Create templates directory
    templates_dir = test_pattern_dir / "templates"
    templates_dir.mkdir()
    
    # Write a template file
    (templates_dir / "test_template.py").write_text("# Test template\nprint('hello')")
    
    yield patterns_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def pattern_manager(temp_patterns_dir):
    """Create a PatternManager with test patterns."""
    return PatternManager(patterns_root=temp_patterns_dir)


@pytest.fixture
def sample_recipe():
    """Create a sample recipe for testing."""
    requirements = Requirements(
        purpose="Test recipe",
        functional_requirements=[
            Requirement(
                id="fr-1",
                description="Test requirement",
                priority=RequirementPriority.MUST,
                validation_criteria=[],
                implemented=False
            )
        ],
        non_functional_requirements=[],
        success_criteria=["Tests pass"]
    )
    
    design = Design(
        architecture="Test architecture",
        components=[],
        interfaces=[],
        implementation_notes="Test implementation"
    )
    
    components = Components(
        name="test-recipe",
        version="1.0.0",
        type=ComponentType.SERVICE,
        description="A test recipe",
        metadata={}
    )
    
    return Recipe(
        name="test-recipe",
        path=Path("test-recipe"),
        requirements=requirements,
        design=design,
        components=components,
        metadata=RecipeMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    )


class TestPatternManager:
    """Test the PatternManager class."""
    
    def test_load_pattern(self, pattern_manager):
        """Test loading a pattern."""
        pattern = pattern_manager.load_pattern("test-pattern")
        
        assert pattern is not None
        assert pattern.name == "test-pattern"
        assert pattern.version == "1.0.0"
        assert pattern.description == "A test pattern"
        assert len(pattern.templates) == 1
        assert "test_template.py" in pattern.templates
    
    def test_load_nonexistent_pattern(self, pattern_manager):
        """Test loading a pattern that doesn't exist."""
        pattern = pattern_manager.load_pattern("nonexistent")
        assert pattern is None
    
    def test_pattern_caching(self, pattern_manager):
        """Test that patterns are cached after loading."""
        # Load pattern twice
        pattern1 = pattern_manager.load_pattern("test-pattern")
        pattern2 = pattern_manager.load_pattern("test-pattern")
        
        # Should be the same object (cached)
        assert pattern1 is pattern2
    
    def test_get_patterns_for_recipe_explicit(self, pattern_manager, sample_recipe):
        """Test getting patterns explicitly requested by recipe."""
        # Add pattern to recipe metadata
        sample_recipe.components.metadata["patterns"] = ["test-pattern"]
        
        patterns = pattern_manager.get_patterns_for_recipe(sample_recipe)
        
        assert len(patterns) == 1
        assert patterns[0].name == "test-pattern"
    
    def test_get_patterns_for_recipe_auto_apply(self, pattern_manager, sample_recipe, temp_patterns_dir):
        """Test auto-apply patterns based on recipe type."""
        # Create an auto-apply pattern
        auto_pattern_dir = temp_patterns_dir / "auto-pattern"
        auto_pattern_dir.mkdir()
        
        pattern_config = {
            "name": "auto-pattern",
            "version": "1.0.0",
            "description": "Auto-apply pattern",
            "target_types": ["service"],
            "auto_apply": True,
            "depends_on": []
        }
        with open(auto_pattern_dir / "pattern.json", "w") as f:
            json.dump(pattern_config, f)
        
        (auto_pattern_dir / "requirements.md").write_text("# Auto Pattern\n## Purpose\nAuto apply")
        (auto_pattern_dir / "design.md").write_text("# Auto Pattern Design")
        
        patterns = pattern_manager.get_patterns_for_recipe(sample_recipe)
        
        # Should find the auto-apply pattern
        assert len(patterns) == 1
        assert patterns[0].name == "auto-pattern"
    
    def test_apply_patterns_to_recipe(self, pattern_manager, sample_recipe):
        """Test applying patterns to a recipe."""
        pattern = pattern_manager.load_pattern("test-pattern")
        
        enhanced_recipe = pattern_manager.apply_patterns_to_recipe(
            sample_recipe, [pattern]
        )
        
        # Check that pattern was applied
        assert "applied_patterns" in enhanced_recipe.components.metadata
        applied = enhanced_recipe.components.metadata["applied_patterns"]
        assert len(applied) == 1
        assert applied[0]["name"] == "test-pattern"
        assert applied[0]["version"] == "1.0.0"
        
        # Check that requirements were merged
        assert len(enhanced_recipe.requirements.functional_requirements) > 1
    
    def test_get_pattern_templates(self, pattern_manager):
        """Test getting templates from patterns."""
        pattern = pattern_manager.load_pattern("test-pattern")
        
        templates = pattern_manager.get_pattern_templates([pattern])
        
        assert len(templates) == 1
        assert "test_template.py" in templates
        assert templates["test_template.py"] == "# Test template\nprint('hello')"
    
    def test_pattern_dependencies(self, pattern_manager, temp_patterns_dir):
        """Test resolving pattern dependencies."""
        # Create a pattern with dependencies
        dep_pattern_dir = temp_patterns_dir / "dep-pattern"
        dep_pattern_dir.mkdir()
        
        pattern_config = {
            "name": "dep-pattern",
            "version": "1.0.0",
            "description": "Pattern with dependencies",
            "depends_on": ["test-pattern"],
            "target_types": [],
            "auto_apply": False
        }
        with open(dep_pattern_dir / "pattern.json", "w") as f:
            json.dump(pattern_config, f)
        
        (dep_pattern_dir / "requirements.md").write_text("# Dep Pattern")
        (dep_pattern_dir / "design.md").write_text("# Dep Pattern Design")
        
        # Load pattern with dependencies
        pattern = pattern_manager.load_pattern("dep-pattern")
        
        # Resolve dependencies
        resolved = pattern_manager._resolve_pattern_dependencies([pattern])
        
        # Should have both patterns in correct order
        assert len(resolved) == 2
        assert resolved[0].name == "test-pattern"  # Dependency first
        assert resolved[1].name == "dep-pattern"


class TestDesignPattern:
    """Test the DesignPattern class."""
    
    def test_applies_to_explicit(self, sample_recipe):
        """Test pattern applies when explicitly requested."""
        pattern = DesignPattern(
            name="test",
            description="Test",
            version="1.0.0",
            requirements=sample_recipe.requirements,
            design=sample_recipe.design,
            templates={},
            depends_on=[],
            metadata={}
        )
        
        # Add pattern to recipe metadata
        sample_recipe.components.metadata["patterns"] = ["test"]
        
        assert pattern.applies_to(sample_recipe)
    
    def test_applies_to_by_type(self, sample_recipe):
        """Test pattern applies based on recipe type."""
        pattern = DesignPattern(
            name="test",
            description="Test",
            version="1.0.0",
            requirements=sample_recipe.requirements,
            design=sample_recipe.design,
            templates={},
            depends_on=[],
            metadata={"target_types": ["service"]}
        )
        
        assert pattern.applies_to(sample_recipe)
    
    def test_does_not_apply(self, sample_recipe):
        """Test pattern doesn't apply when conditions not met."""
        pattern = DesignPattern(
            name="test",
            description="Test",
            version="1.0.0",
            requirements=sample_recipe.requirements,
            design=sample_recipe.design,
            templates={},
            depends_on=[],
            metadata={"target_types": ["agent"]}  # Different type
        )
        
        assert not pattern.applies_to(sample_recipe)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])