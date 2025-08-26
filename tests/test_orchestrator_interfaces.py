"""Test that orchestrator interfaces match their dependencies.

This test would have caught the QualityGates.run_quality_checks error immediately.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.recipe_executor.orchestrator import RecipeOrchestrator
from src.recipe_executor.python_standards import QualityGates


class TestOrchestratorInterfaces(unittest.TestCase):
    """Test that orchestrator correctly uses its dependencies."""
    
    def test_quality_gates_has_expected_methods(self):
        """Test that QualityGates has methods orchestrator expects."""
        quality_gates = QualityGates()
        
        # This would have failed with AttributeError if method didn't exist
        self.assertTrue(hasattr(quality_gates, 'run_all_gates'))
        self.assertTrue(callable(getattr(quality_gates, 'run_all_gates')))
        
        # Verify it doesn't have the wrong method name
        self.assertFalse(hasattr(quality_gates, 'run_quality_checks'))
    
    def test_orchestrator_calls_quality_gates_correctly(self):
        """Test that orchestrator calls QualityGates with correct method."""
        orchestrator = RecipeOrchestrator()
        
        # Mock the quality gates
        mock_quality_gates = MagicMock()
        mock_quality_gates.run_all_gates.return_value = {
            'pyright': True,
            'ruff_format': True,
            'ruff_lint': True,
            'pytest': True
        }
        orchestrator.quality_gates = mock_quality_gates
        
        # Create a minimal recipe for testing
        from src.recipe_executor.recipe_model import (
            Recipe, Requirements, Design, Components, RecipeMetadata, ComponentType
        )
        from datetime import datetime
        
        test_recipe = Recipe(
            name="test",
            path=Path("/tmp/test"),
            metadata=RecipeMetadata(
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            requirements=Requirements(
                purpose="Test purpose",
                functional_requirements=[],
                non_functional_requirements=[]
            ),
            design=Design(
                architecture="Test architecture",
                components=[],
                interfaces=[]
            ),
            components=Components(
                name="test",
                version="1.0.0",
                type=ComponentType.LIBRARY
            )
        )
        
        # Mock other dependencies
        orchestrator.generator = MagicMock()
        orchestrator.generator.generate.return_value = (True, {"test.py": "print('test')"}, [])
        orchestrator.test_generator = MagicMock()
        orchestrator.test_generator.generate_tests.return_value = {}
        orchestrator.validator = MagicMock()
        orchestrator.validator.validate.return_value = MagicMock(passed=True)
        
        # Execute
        from src.recipe_executor.orchestrator import BuildOptions
        result = orchestrator.build_recipe(
            test_recipe,
            output_path=Path("/tmp/test"),
            options=BuildOptions()
        )
        
        # Verify quality gates was called with correct method
        mock_quality_gates.run_all_gates.assert_called_once()
        
        # This would have failed if we called run_quality_checks
        self.assertFalse(hasattr(mock_quality_gates, 'run_quality_checks'))


if __name__ == '__main__':
    unittest.main()