"""Test for GeneratedCode framework attribute bug found during self-hosting."""

import pytest
from pathlib import Path
import tempfile
from recipe_executor.recipe_model import GeneratedCode, Recipe, RecipeTestSuite
from recipe_executor.tdd_pipeline import TDDPipeline, CodeArtifact


def test_generated_code_has_framework_attribute():
    """Test that GeneratedCode has framework attribute needed by TDD pipeline."""
    # This should fail initially, proving the bug exists
    code = GeneratedCode(
        recipe_name="test-recipe",
        files={"test.py": "print('hello')"},
        language="python"
    )
    
    # The TDD pipeline expects this attribute to exist
    assert hasattr(code, 'framework'), "GeneratedCode should have 'framework' attribute"


def test_tdd_pipeline_refactor_phase_with_generated_code():
    """Test that TDD pipeline can handle GeneratedCode in refactor phase."""
    # Create a GeneratedCode instance
    code = GeneratedCode(
        recipe_name="test-recipe",
        files={"main.py": "def hello(): return 'world'"},
        language="python"
    )
    
    # Create TDD pipeline
    pipeline = TDDPipeline()
    
    # Try to apply refactoring (this is where the bug occurs)
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Write the code files
        for filepath, content in code.files.items():
            full_path = output_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
        
        # This should work without AttributeError
        try:
            # The _apply_refactoring method tries to access code.framework
            refactored = pipeline._apply_refactoring(code, output_dir)
            assert refactored is not None
            assert isinstance(refactored, CodeArtifact)
        except AttributeError as e:
            if "'GeneratedCode' object has no attribute 'framework'" in str(e):
                pytest.fail(f"Bug confirmed: {e}")
            raise


def test_code_artifact_compatibility():
    """Test that CodeArtifact (alias for GeneratedCode) works with framework field."""
    # CodeArtifact is imported as an alias in tdd_pipeline.py
    # It expects a framework field when creating new instances
    
    # This should work after fix
    artifact = CodeArtifact(
        recipe_name="test",
        files={"test.py": "pass"},
        language="python",
        framework=None  # Should be optional with default None
    )
    
    assert hasattr(artifact, 'framework')
    assert artifact.framework is None or isinstance(artifact.framework, str)


if __name__ == "__main__":
    # Run the tests to demonstrate the bug
    print("Running tests to demonstrate framework attribute bug...")
    pytest.main([__file__, "-v"])