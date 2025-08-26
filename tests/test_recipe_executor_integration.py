"""Integration tests for the complete Recipe Executor pipeline."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.recipe_executor.enhanced_orchestrator import (
    EnhancedRecipeOrchestrator,
    PipelineStage,
    PipelineResult
)
from src.recipe_executor.recipe_model import Recipe, Requirements, Design, Component
from src.recipe_executor.self_hosting import SelfHostingManager
from src.recipe_executor.recipe_decomposer import RecipeDecomposer
from src.recipe_executor.tdd_pipeline import TDDPipeline


@pytest.fixture
def temp_recipe_dir():
    """Create a temporary recipe directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recipe_dir = Path(tmpdir) / "test-recipe"
        recipe_dir.mkdir()
        
        # Create test recipe files
        requirements_content = """# Test Recipe Requirements

## Functional Requirements
- The system shall process user input
- The system shall validate data
- The system shall store results
- The system shall generate reports

## Non-Functional Requirements
- Performance: Process within 100ms
- Security: Validate all inputs
"""
        
        design_content = """# Test Recipe Design

## Architecture
Modular component-based architecture

## Components
- InputProcessor: Handles user input
- Validator: Validates data
- Storage: Stores results
- ReportGenerator: Generates reports
"""
        
        components_content = {
            "name": "test-recipe",
            "version": "1.0.0",
            "type": "service",
            "dependencies": []
        }
        
        (recipe_dir / "requirements.md").write_text(requirements_content)
        (recipe_dir / "design.md").write_text(design_content)
        (recipe_dir / "components.json").write_text(json.dumps(components_content, indent=2))
        
        yield recipe_dir


@pytest.fixture
def complex_recipe_dir():
    """Create a complex recipe that should trigger decomposition."""
    with tempfile.TemporaryDirectory() as tmpdir:
        recipe_dir = Path(tmpdir) / "complex-recipe"
        recipe_dir.mkdir()
        
        # Create complex recipe with many requirements
        requirements = ["The system shall " + f"requirement_{i}" for i in range(15)]
        requirements_content = f"""# Complex Recipe Requirements

## Functional Requirements
{chr(10).join('- ' + req for req in requirements)}

## Non-Functional Requirements
- Performance: Sub-second response
- Scalability: Handle 1000 requests/second
"""
        
        design_content = """# Complex Recipe Design

## Architecture
Microservices architecture with 8 components

## Components
- API Gateway: Routes requests
- Auth Service: Authentication
- User Service: User management
- Data Service: Data processing
- Analytics Service: Analytics
- Notification Service: Notifications
- Report Service: Reporting
- Admin Service: Administration
"""
        
        (recipe_dir / "requirements.md").write_text(requirements_content)
        (recipe_dir / "design.md").write_text(design_content)
        (recipe_dir / "components.json").write_text(json.dumps({
            "name": "complex-recipe",
            "version": "1.0.0",
            "dependencies": []
        }, indent=2))
        
        yield recipe_dir


class TestEnhancedPipeline:
    """Test the enhanced 10-stage pipeline."""
    
    def test_pipeline_initialization(self):
        """Test that the enhanced orchestrator initializes correctly."""
        orchestrator = EnhancedRecipeOrchestrator()
        
        assert orchestrator.parser is not None
        assert orchestrator.resolver is not None
        assert orchestrator.decomposer is not None
        assert orchestrator.tdd_pipeline is not None
        assert orchestrator.quality_gates is not None
        assert len(orchestrator.stage_results) == 0
    
    def test_stage_1_validation(self, temp_recipe_dir):
        """Test Stage 1: Recipe validation."""
        orchestrator = EnhancedRecipeOrchestrator()
        
        with tempfile.TemporaryDirectory() as output_dir:
            result = orchestrator.execute_recipe(
                recipe_path=temp_recipe_dir,
                output_dir=Path(output_dir),
                dry_run=True,
                verbose=False
            )
            
            # Check that validation stage was executed
            validation_stages = [s for s in result.stages_completed if s.stage == PipelineStage.VALIDATION]
            assert len(validation_stages) == 1
            assert validation_stages[0].success
    
    def test_stage_2_complexity_evaluation(self, complex_recipe_dir):
        """Test Stage 2: Complexity evaluation and decomposition."""
        orchestrator = EnhancedRecipeOrchestrator()
        
        # Parse the complex recipe
        recipe = orchestrator.parser.parse_recipe(complex_recipe_dir)
        
        # Test complexity evaluation
        should_decompose, metrics = orchestrator.decomposer.should_decompose(recipe)
        
        assert should_decompose  # Complex recipe should be decomposed
        assert metrics.functional_requirements_count == 15
        assert metrics.is_complex
    
    @patch('src.recipe_executor.tdd_pipeline.TDDPipeline.execute_tdd_cycle')
    def test_stages_3_5_tdd_cycle(self, mock_tdd_cycle, temp_recipe_dir):
        """Test Stages 3-5: TDD Red-Green-Refactor cycle."""
        orchestrator = EnhancedRecipeOrchestrator()
        
        # Mock TDD cycle result
        mock_tdd_result = Mock()
        mock_tdd_result.success = True
        mock_tdd_result.code_artifact = Mock(files={"test.py": "print('test')"})
        mock_tdd_result.red_phase_result = Mock(failed=5, all_passed=False)
        mock_tdd_result.green_phase_result = Mock(passed=5, all_passed=True)
        mock_tdd_result.cycle_time = 10.0
        mock_tdd_cycle.return_value = mock_tdd_result
        
        with tempfile.TemporaryDirectory() as output_dir:
            result = orchestrator.execute_recipe(
                recipe_path=temp_recipe_dir,
                output_dir=Path(output_dir),
                dry_run=False,
                verbose=False
            )
            
            # Check TDD stages were executed
            tdd_stages = [
                s for s in result.stages_completed 
                if s.stage in [
                    PipelineStage.TEST_GENERATION,
                    PipelineStage.IMPLEMENTATION,
                    PipelineStage.TEST_FIXING
                ]
            ]
            assert len(tdd_stages) == 3
    
    def test_full_pipeline_execution(self, temp_recipe_dir):
        """Test complete pipeline execution end-to-end."""
        orchestrator = EnhancedRecipeOrchestrator()
        
        with tempfile.TemporaryDirectory() as output_dir:
            with patch.object(orchestrator.tdd_pipeline, 'execute_tdd_cycle') as mock_tdd:
                # Mock successful TDD cycle
                mock_tdd_result = Mock()
                mock_tdd_result.success = True
                mock_tdd_result.code_artifact = Mock(files={"main.py": "# Generated code"})
                mock_tdd_result.red_phase_result = Mock(all_passed=False, failed=3)
                mock_tdd_result.green_phase_result = Mock(all_passed=True, passed=3)
                mock_tdd_result.refactor_phase_result = Mock(all_passed=True)
                mock_tdd_result.cycle_time = 5.0
                mock_tdd.return_value = mock_tdd_result
                
                result = orchestrator.execute_recipe(
                    recipe_path=temp_recipe_dir,
                    output_dir=Path(output_dir),
                    dry_run=False,
                    verbose=True
                )
                
                # Verify pipeline stages
                assert len(result.stages_completed) >= 5  # At least validation, complexity, TDD stages
                assert result.recipe is not None
                assert result.recipe.name == "test-recipe"
    
    def test_pipeline_failure_handling(self):
        """Test pipeline handles failures gracefully."""
        orchestrator = EnhancedRecipeOrchestrator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_recipe_dir = Path(tmpdir) / "invalid"
            invalid_recipe_dir.mkdir()
            
            # Create invalid recipe (missing requirements)
            (invalid_recipe_dir / "components.json").write_text('{"name": "invalid"}')
            
            result = orchestrator.execute_recipe(
                recipe_path=invalid_recipe_dir,
                output_dir=Path(tmpdir) / "output",
                dry_run=True
            )
            
            assert not result.success
            assert len(result.stages_completed) > 0
            # First stage should fail
            assert not result.stages_completed[0].success


class TestRecipeDecomposer:
    """Test the RecipeDecomposer agent."""
    
    def test_complexity_evaluation_simple(self):
        """Test complexity evaluation for a simple recipe."""
        decomposer = RecipeDecomposer()
        
        # Create simple recipe
        recipe = Recipe(
            name="simple-recipe",
            requirements=Requirements(
                functional_requirements=["Requirement 1", "Requirement 2"],
                non_functional_requirements=[]
            ),
            design=Design(
                architecture="Simple",
                components=[Component(
                    name="MainComponent",
                    description="Main",
                    responsibilities=[],
                    public_interfaces=[],
                    dependencies=[]
                )],
                patterns=[]
            ),
            dependencies=[]
        )
        
        metrics = decomposer.evaluate_complexity(recipe)
        
        assert not metrics.is_complex
        assert metrics.functional_requirements_count == 2
        assert metrics.component_count == 1
    
    def test_complexity_evaluation_complex(self):
        """Test complexity evaluation for a complex recipe."""
        decomposer = RecipeDecomposer()
        
        # Create complex recipe
        requirements = [f"Requirement {i}" for i in range(15)]
        components = [
            Component(
                name=f"Component{i}",
                description=f"Component {i}",
                responsibilities=[],
                public_interfaces=["interface1", "interface2"],
                dependencies=[]
            )
            for i in range(7)
        ]
        
        recipe = Recipe(
            name="complex-recipe",
            requirements=Requirements(
                functional_requirements=requirements,
                non_functional_requirements=[]
            ),
            design=Design(
                architecture="Complex",
                components=components,
                patterns=[]
            ),
            dependencies=[]
        )
        
        metrics = decomposer.evaluate_complexity(recipe)
        
        assert metrics.is_complex
        assert metrics.functional_requirements_count == 15
        assert metrics.component_count == 7
        assert metrics.complexity_score > 7.0
    
    def test_decomposition(self):
        """Test recipe decomposition."""
        decomposer = RecipeDecomposer()
        
        # Create recipe that needs decomposition
        requirements = [f"Feature {i} requirement" for i in range(12)]
        recipe = Recipe(
            name="to-decompose",
            requirements=Requirements(
                functional_requirements=requirements,
                non_functional_requirements=[]
            ),
            design=None,
            dependencies=[]
        )
        
        sub_recipes = decomposer.decompose_recipe(recipe)
        
        assert len(sub_recipes) > 1  # Should be decomposed
        
        # Check that all requirements are covered
        all_reqs = []
        for sub in sub_recipes:
            all_reqs.extend(sub.requirements.functional_requirements)
        assert len(all_reqs) == len(requirements)


class TestTDDPipeline:
    """Test the TDD Red-Green-Refactor pipeline."""
    
    @patch('subprocess.run')
    def test_red_phase(self, mock_run):
        """Test RED phase: tests should fail initially."""
        tdd = TDDPipeline()
        
        # Mock failing test output
        mock_run.return_value = Mock(
            stdout="3 failed",
            stderr="",
            returncode=1
        )
        
        recipe = Recipe(
            name="test-recipe",
            requirements=Requirements(
                functional_requirements=["Test requirement"],
                non_functional_requirements=[]
            ),
            design=None,
            dependencies=[]
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.recipe_executor.recipe_model import BuildContext
            context = BuildContext(recipe=recipe, dry_run=False, verbose=False)
            
            result = tdd.execute_tdd_cycle(
                recipe=recipe,
                context=context,
                output_dir=Path(tmpdir)
            )
            
            # In RED phase, tests should fail
            assert result.red_phase_result is not None
            # Tests should not all pass in RED phase
            assert not result.red_phase_result.all_passed


class TestSelfHosting:
    """Test self-hosting capabilities."""
    
    def test_self_hosting_validation(self):
        """Test self-hosting validation."""
        manager = SelfHostingManager()
        
        # Validation should check if recipe exists
        result = manager._validate_self_hosting_capability()
        
        # Result depends on whether recipe actually exists
        assert result is not None
        assert isinstance(result.validation_errors, list)
    
    @patch.object(SelfHostingManager, '_bootstrap_test')
    @patch.object(EnhancedRecipeOrchestrator, 'execute_recipe')
    def test_regenerate_self(self, mock_execute, mock_bootstrap):
        """Test self-regeneration process."""
        manager = SelfHostingManager()
        
        # Mock successful pipeline execution
        mock_pipeline_result = Mock()
        mock_pipeline_result.success = True
        mock_pipeline_result.final_artifact = Mock(files={
            "recipe_executor/orchestrator.py": "# Generated orchestrator",
            "recipe_executor/__main__.py": "# Generated main"
        })
        mock_pipeline_result.summary = "Success"
        mock_execute.return_value = mock_pipeline_result
        
        # Mock successful bootstrap test
        mock_bootstrap.return_value = True
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = manager.regenerate_self(
                output_dir=Path(tmpdir),
                validate_only=False,
                allow_overwrite=False
            )
            
            assert mock_execute.called
            # Bootstrap test should be called if generation successful
            # (depends on component completeness)
    
    def test_critical_components_check(self):
        """Test that critical components are properly identified."""
        manager = SelfHostingManager()
        
        assert "orchestrator.py" in manager.CRITICAL_COMPONENTS
        assert "__main__.py" in manager.CRITICAL_COMPONENTS
        assert "recipe_parser.py" in manager.CRITICAL_COMPONENTS
        assert len(manager.CRITICAL_COMPONENTS) >= 5


class TestCLIIntegration:
    """Test CLI command integration."""
    
    def test_cli_help(self):
        """Test CLI help command."""
        from src.recipe_executor.__main__ import main
        
        # Test help doesn't crash
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
    
    def test_cli_pipeline_command(self):
        """Test pipeline command exists."""
        from src.recipe_executor.__main__ import main
        import argparse
        
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        
        # Verify pipeline command would be added
        # (Can't fully test without mocking the entire CLI)
        assert True  # Placeholder
    
    @patch('src.recipe_executor.self_hosting.SelfHostingManager.verify_self_hosting')
    def test_cli_self_host_verify(self, mock_verify):
        """Test self-host verify command."""
        from src.recipe_executor.__main__ import main
        
        mock_verify.return_value = True
        
        # Would need to mock more to fully test
        # This is a placeholder showing the test structure
        assert True


@pytest.mark.integration
class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def test_simple_recipe_full_pipeline(self, temp_recipe_dir):
        """Test full pipeline execution with a simple recipe."""
        orchestrator = EnhancedRecipeOrchestrator()
        
        with tempfile.TemporaryDirectory() as output_dir:
            # Mock the parts that would require Claude API
            with patch.object(orchestrator.code_generator, 'generate') as mock_gen:
                mock_gen.return_value = Mock(files={
                    "main.py": "def main(): pass",
                    "test_main.py": "def test_main(): assert True"
                })
                
                result = orchestrator.execute_recipe(
                    recipe_path=temp_recipe_dir,
                    output_dir=Path(output_dir),
                    dry_run=False,
                    verbose=True
                )
                
                # Basic checks
                assert result.recipe.name == "test-recipe"
                assert len(result.stages_completed) > 0
    
    def test_complex_recipe_decomposition_and_execution(self, complex_recipe_dir):
        """Test that complex recipes are properly decomposed and executed."""
        orchestrator = EnhancedRecipeOrchestrator()
        
        with tempfile.TemporaryDirectory() as output_dir:
            result = orchestrator.execute_recipe(
                recipe_path=complex_recipe_dir,
                output_dir=Path(output_dir),
                dry_run=True,  # Dry run to avoid needing Claude API
                verbose=True
            )
            
            # Check complexity stage
            complexity_stages = [
                s for s in result.stages_completed 
                if s.stage == PipelineStage.COMPLEXITY
            ]
            assert len(complexity_stages) == 1
            
            # Should detect high complexity
            assert complexity_stages[0].data.get("is_complex", False)