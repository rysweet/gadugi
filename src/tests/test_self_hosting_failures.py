"""Tests for Recipe Executor self-hosting failures found during regeneration."""

import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from recipe_executor.intelligent_stub_detector import IntelligentStubDetector
from recipe_executor.python_standards import QualityGates
from recipe_executor.component_registry import ComponentRegistry


class TestQualityGatesRuffFailure:
    """Test for quality gates ruff formatting failure with uv run."""
    
    def test_ruff_format_with_uv_run_fails_on_temp_files(self):
        """Test that demonstrates the ruff formatting failure with uv run on temp files."""
        # This test should fail initially, proving the bug exists
        quality_gates = QualityGates()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello( ):\n    return   'world'")
            temp_file = f.name
        
        try:
            # This should fail with the same error we saw in the log
            # "Command '['uv', 'run', 'ruff', 'format', '/tmp/...'] returned non-zero exit status 2"
            result = subprocess.run(
                ['uv', 'run', 'ruff', 'format', temp_file],
                capture_output=True,
                text=True,
                cwd=Path.cwd()  # Run from project root
            )
            
            # The bug: uv run fails when the temp file is outside the project
            assert result.returncode == 0, f"Ruff format with uv run failed: {result.stderr}"
            
        finally:
            Path(temp_file).unlink(missing_ok=True)
    
    def test_quality_gates_format_check_handles_uv_projects(self):
        """Test that quality gates properly handle uv projects."""
        quality_gates = QualityGates()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create a minimal Python file
            test_file = tmpdir_path / "test.py"
            test_file.write_text("def hello():\n    return 'world'\n")
            
            # The bug: quality gates don't handle uv projects correctly for temp directories
            # This should work but currently fails
            result = quality_gates.check_ruff_format(tmpdir_path)
            assert result, "Quality gates should handle temp directories correctly"


class TestArtifactCheckPathIssue:
    """Test for artifact check looking for components in wrong paths."""
    
    def test_component_registry_checks_correct_paths(self):
        """Test that component registry looks for files in the correct location."""
        registry = ComponentRegistry()
        
        # Create a mock file structure like our generated code
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create the structure Claude generated
            src_dir = tmpdir_path / "src" / "recipe_executor"
            src_dir.mkdir(parents=True)
            
            # Create some component files
            (src_dir / "recipe_model.py").write_text("# Recipe model")
            (src_dir / "orchestrator.py").write_text("# Orchestrator")
            (src_dir / "__main__.py").write_text("# Main")
            
            # The bug: registry looks for files at wrong paths
            # It was looking for "src/recipe_model.py" but files are at "src/recipe_executor/recipe_model.py"
            files = {
                "src/recipe_executor/recipe_model.py": "# Recipe model",
                "src/recipe_executor/orchestrator.py": "# Orchestrator", 
                "src/recipe_executor/__main__.py": "# Main"
            }
            
            is_complete, missing = registry.validate_completeness(files)
            
            # This should pass but the bug makes it fail
            assert is_complete, f"Component registry should find files at correct paths. Missing: {missing}"
    
    def test_component_registry_expected_paths_match_actual(self):
        """Test that expected component paths match what Claude actually generates."""
        registry = ComponentRegistry()
        
        # Get the expected components
        expected = registry.get_required_components()
        
        # Check that paths are consistent
        for component, expected_path in expected.items():
            # The bug: expected paths don't match actual generation paths
            # Expected: "src/recipe_model.py"
            # Actual: "src/recipe_executor/recipe_model.py"
            assert "recipe_executor" in expected_path or expected_path.startswith("tests/"), \
                f"Component {component} has incorrect expected path: {expected_path}"


class TestIntelligentStubDetectorPaths:
    """Test for intelligent stub detector path issues."""
    
    def test_stub_detector_handles_generated_paths(self):
        """Test that stub detector correctly handles generated file paths."""
        
        # Mock the Claude interaction
        with patch('subprocess.run') as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '{"has_stubs": false, "stub_count": 0}'
            mock_run.return_value = mock_result
            
            detector = IntelligentStubDetector()
            
            # Test with the actual generated file structure
            files = {
                "src/recipe_executor/recipe_model.py": "class Recipe: pass",
                "src/recipe_executor/orchestrator.py": "class Orchestrator: pass"
            }
            
            has_stubs, count, _ = detector.detect_stubs_with_claude(files, "recipe-executor")
            
            # This should work correctly
            assert not has_stubs, "Detector should handle generated paths correctly"
    
    def test_refactoring_uses_correct_output_dir(self):
        """Test that refactoring phase uses correct output directory."""
        from recipe_executor.tdd_pipeline import TDDPipeline
        from recipe_executor.recipe_model import GeneratedCode
        
        pipeline = TDDPipeline()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create test files
            (output_dir / "test.py").write_text("def test(): pass")
            
            code = GeneratedCode(
                recipe_name="test",
                files={"test.py": "def test(): pass"},
                language="python",
                framework=None
            )
            
            # The bug: refactoring doesn't handle output_dir correctly for quality gates
            quality_results = {"pyright": True}
            
            # This should work but might fail due to path issues
            try:
                result = pipeline._apply_refactoring(code, quality_results, output_dir)
                assert result is not None, "Refactoring should succeed"
            except Exception as e:
                pytest.fail(f"Refactoring failed with path issues: {e}")


def test_self_hosting_integration():
    """Integration test for complete self-hosting process."""
    from recipe_executor.self_hosting import SelfHostingManager
    
    manager = SelfHostingManager()
    
    # This is the ultimate test - can we self-host successfully?
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "self_host"
        
        # This should succeed end-to-end but currently fails
        result = manager.regenerate_self(
            output_dir=output_dir,
            validate_only=False,
            allow_overwrite=False
        )
        
        assert result.success, f"Self-hosting should succeed. Summary: {result.summary}"
        assert result.files_generated > 0, "Should generate files"
        assert len(result.missing_components) == 0, f"Should have no missing components: {result.missing_components}"


if __name__ == "__main__":
    print("Running self-hosting failure tests...")
    pytest.main([__file__, "-v", "--tb=short"])