"""Test to ensure no stub implementations are generated."""

import pytest
from pathlib import Path
import tempfile
from datetime import datetime

from src.recipe_executor.claude_code_generator import ClaudeCodeGenerator
from src.recipe_executor.stub_detector import StubDetector
from src.recipe_executor.recipe_model import (
    Recipe,
    Requirements,
    Design,
    Components,
    ComponentType,
    ComponentDesign,
    Requirement,
    RequirementPriority,
    RecipeMetadata,
    BuildContext,
)


@pytest.fixture
def sample_recipe():
    """Create a sample recipe for testing."""
    requirements = Requirements(
        purpose="Test recipe for stub detection",
        functional_requirements=[
            Requirement(
                id="fr-1",
                description="Must implement actual functionality",
                priority=RequirementPriority.MUST,
                validation_criteria=[],
                implemented=False
            )
        ],
        non_functional_requirements=[],
        success_criteria=["No stubs in generated code"]
    )
    
    design = Design(
        architecture="Simple test architecture",
        components=[
            ComponentDesign(
                name="TestComponent",
                description="A test component",
                class_name="TestComponent",
                methods=["process()", "validate()"],
                properties=["name", "data"]
            )
        ],
        interfaces=[],
        implementation_notes="Must generate real implementations"
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


class TestNoStubGeneration:
    """Ensure no stub implementations are generated."""
    
    def test_claude_generator_no_stubs(self, sample_recipe):
        """Test that ClaudeCodeGenerator doesn't generate stubs."""
        generator = ClaudeCodeGenerator(enforce_no_stubs=True)
        context = BuildContext(recipe=sample_recipe, dry_run=False)
        
        # Generate code
        result = generator.generate(sample_recipe, context)
        
        # Check that code was generated
        assert result is not None
        assert len(result.files) > 0
        
        # Use StubDetector to check for stubs
        detector = StubDetector()
        
        # Check each generated file for stubs
        for filepath, content in result.files.items():
            if filepath.endswith('.py'):
                stubs = detector.detect_stubs_in_code(content, filepath)
                assert len(stubs) == 0, f"Found stubs in {filepath}: {stubs}"
                
                # Specific checks for forbidden patterns
                assert "raise NotImplementedError" not in content, f"NotImplementedError found in {filepath}"
                assert "pass  # TODO" not in content, f"TODO with pass found in {filepath}"
                assert "# STUB" not in content, f"STUB comment found in {filepath}"
                assert "placeholder" not in content.lower(), f"Placeholder found in {filepath}"
    
    def test_generated_code_has_real_implementations(self, sample_recipe):
        """Test that generated code has actual implementations."""
        generator = ClaudeCodeGenerator(enforce_no_stubs=True)
        context = BuildContext(recipe=sample_recipe, dry_run=False)
        
        # Generate code
        result = generator.generate(sample_recipe, context)
        
        # Check that methods have real implementations
        for filepath, content in result.files.items():
            if filepath.endswith('.py') and 'test' not in filepath:
                # Check that methods don't just have 'pass'
                lines = content.split('\n')
                in_function = False
                function_body = []
                
                for line in lines:
                    if line.strip().startswith('def '):
                        in_function = True
                        function_body = []
                    elif in_function:
                        if line.strip() and not line.strip().startswith('"""') and not line.strip().startswith('#'):
                            function_body.append(line.strip())
                        # Check if we've reached the end of the function
                        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                            in_function = False
                            # Verify the function has more than just 'pass'
                            if function_body:
                                assert function_body != ['pass'], f"Function in {filepath} only contains 'pass'"
    
    def test_generated_code_returns_values(self, sample_recipe):
        """Test that generated methods return actual values."""
        generator = ClaudeCodeGenerator(enforce_no_stubs=True)
        context = BuildContext(recipe=sample_recipe, dry_run=False)
        
        # Generate code
        result = generator.generate(sample_recipe, context)
        
        # Check that methods return values (not None implicitly)
        for filepath, content in result.files.items():
            if filepath.endswith('.py') and 'test' not in filepath:
                # Look for methods that should return values
                if 'def process' in content or 'def validate' in content or 'def execute' in content:
                    # These methods should have explicit return statements
                    assert 'return ' in content, f"No return statements found in {filepath}"
                    # Should not just return None
                    assert not all(r.strip() == 'return None' for r in content.split('return ')[1:] if r), \
                        f"Methods in {filepath} only return None"
    
    def test_no_template_variables_left(self, sample_recipe):
        """Test that no template variables are left in generated code."""
        generator = ClaudeCodeGenerator(enforce_no_stubs=True)
        context = BuildContext(recipe=sample_recipe, dry_run=False)
        
        # Generate code
        result = generator.generate(sample_recipe, context)
        
        # Check for template variable patterns
        for filepath, content in result.files.items():
            assert '{{' not in content, f"Template variables {{ found in {filepath}"
            assert '}}' not in content, f"Template variables }} found in {filepath}"
            assert '{%' not in content, f"Template control structures found in {filepath}"
            assert 'TEMPLATE' not in content, f"TEMPLATE marker found in {filepath}"
            assert 'TODO: Implement' not in content, f"TODO: Implement found in {filepath}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])