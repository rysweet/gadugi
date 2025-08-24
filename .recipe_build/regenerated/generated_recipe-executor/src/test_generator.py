"""Test generator for comprehensive testing of components."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from .recipe_model import Recipe, Requirement

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Single test case."""
    name: str
    description: str
    requirement_id: str
    test_code: str
    test_type: str  # "unit", "integration", "e2e"


@dataclass
class RecipeTestSuite:
    """Complete test suite for a recipe."""
    recipe_name: str
    unit_tests: List[TestCase]
    integration_tests: List[TestCase]
    test_files: Dict[str, str]  # filepath -> content
    
    def get_test_count(self) -> int:
        """Get total number of tests."""
        return len(self.unit_tests) + len(self.integration_tests)
    
    def get_coverage_report(self) -> str:
        """Generate coverage report."""
        lines = [
            f"Test Suite for {self.recipe_name}",
            f"Total tests: {self.get_test_count()}",
            f"Unit tests: {len(self.unit_tests)}",
            f"Integration tests: {len(self.integration_tests)}"
        ]
        return '\n'.join(lines)


class TestGenerator:
    """Generates comprehensive tests for components."""
    
    def generate_tests(self, recipe: Recipe, code) -> RecipeTestSuite:
        """Generate comprehensive tests based on requirements.
        
        Args:
            recipe: Recipe to generate tests for
            code: Generated code
            
        Returns:
            Complete test suite
        """
        logger.info(f"Generating tests for {recipe.name}")
        
        # Extract test targets from generated code
        test_targets = self._identify_test_targets(code)
        
        # Generate unit tests for each requirement
        unit_tests = []
        for req in recipe.requirements.get_must_requirements():
            unit_tests.extend(self._generate_requirement_tests(req, test_targets))
        
        # Generate integration tests for workflows
        integration_tests = self._generate_integration_tests(recipe, test_targets)
        
        # Generate test files with proper structure
        test_files = self._organize_test_files(recipe, unit_tests, integration_tests)
        
        return RecipeTestSuite(
            recipe_name=recipe.name,
            unit_tests=unit_tests,
            integration_tests=integration_tests,
            test_files=test_files
        )
    
    def _identify_test_targets(self, code) -> List[str]:
        """Identify components to test from generated code.
        
        Args:
            code: Generated code
            
        Returns:
            List of test targets
        """
        targets = []
        
        if not code:
            return targets
        
        # Extract class and function names from code
        for filepath, content in code.files.items():
            if filepath.endswith('.py'):
                # Simple extraction of class and function names
                import ast
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            targets.append(f"class:{node.name}")
                        elif isinstance(node, ast.FunctionDef):
                            if not node.name.startswith('_'):
                                targets.append(f"function:{node.name}")
                except:
                    pass
        
        return targets
    
    def _generate_requirement_tests(self, requirement: Requirement, targets: List[str]) -> List[TestCase]:
        """Generate tests for a specific requirement.
        
        Args:
            requirement: Requirement to test
            targets: Available test targets
            
        Returns:
            List of test cases
        """
        tests = []
        
        # Generate positive test case
        positive_test = TestCase(
            name=f"test_{requirement.id}_positive",
            description=f"Test that {requirement.description}",
            requirement_id=requirement.id,
            test_code=self._generate_test_code(requirement, "positive"),
            test_type="unit"
        )
        tests.append(positive_test)
        
        # Generate negative test case if applicable
        if self._needs_negative_test(requirement):
            negative_test = TestCase(
                name=f"test_{requirement.id}_negative",
                description=f"Test failure case for {requirement.description}",
                requirement_id=requirement.id,
                test_code=self._generate_test_code(requirement, "negative"),
                test_type="unit"
            )
            tests.append(negative_test)
        
        # Generate validation tests for each criterion
        for i, criterion in enumerate(requirement.validation_criteria):
            validation_test = TestCase(
                name=f"test_{requirement.id}_validation_{i}",
                description=f"Validate: {criterion}",
                requirement_id=requirement.id,
                test_code=self._generate_validation_test_code(criterion),
                test_type="unit"
            )
            tests.append(validation_test)
        
        return tests
    
    def _generate_integration_tests(self, recipe: Recipe, targets: List[str]) -> List[TestCase]:
        """Generate integration tests for workflows.
        
        Args:
            recipe: Recipe to test
            targets: Available test targets
            
        Returns:
            List of integration test cases
        """
        tests = []
        
        # Generate end-to-end workflow test
        e2e_test = TestCase(
            name=f"test_{recipe.name}_e2e_workflow",
            description=f"End-to-end test for {recipe.name}",
            requirement_id="integration",
            test_code=self._generate_e2e_test_code(recipe),
            test_type="integration"
        )
        tests.append(e2e_test)
        
        # Generate component interaction tests
        for comp in recipe.design.components[:3]:  # Limit to first 3 components
            interaction_test = TestCase(
                name=f"test_{comp.name}_interaction",
                description=f"Test {comp.name} interactions",
                requirement_id="integration",
                test_code=self._generate_interaction_test_code(comp),
                test_type="integration"
            )
            tests.append(interaction_test)
        
        return tests
    
    def _organize_test_files(self, recipe: Recipe, unit_tests: List[TestCase], 
                            integration_tests: List[TestCase]) -> Dict[str, str]:
        """Organize tests into proper file structure.
        
        Args:
            recipe: Recipe being tested
            unit_tests: Unit test cases
            integration_tests: Integration test cases
            
        Returns:
            Dictionary of file paths to content
        """
        test_files = {}
        
        # Create conftest.py with shared fixtures
        test_files["tests/conftest.py"] = self._generate_conftest(recipe)
        
        # Create unit test files by component
        component_tests = {}
        for test in unit_tests:
            # Group by requirement prefix
            component = test.requirement_id.split('_')[0]
            if component not in component_tests:
                component_tests[component] = []
            component_tests[component].append(test)
        
        for component, tests in component_tests.items():
            content = self._generate_test_file(tests, f"Unit tests for {component}")
            test_files[f"tests/test_{component}.py"] = content
        
        # Create integration test file
        if integration_tests:
            content = self._generate_test_file(integration_tests, "Integration tests")
            test_files["tests/test_integration.py"] = content
        
        return test_files
    
    def _generate_test_code(self, requirement: Requirement, test_type: str) -> str:
        """Generate test code for a requirement.
        
        Args:
            requirement: Requirement to test
            test_type: "positive" or "negative"
            
        Returns:
            Test code
        """
        if test_type == "positive":
            return f"""
    # Test: {requirement.description}
    # Requirement: {requirement.id}
    result = component.process(valid_input)
    assert result is not None
    assert result.success == True
    # Verify specific requirement conditions
    assert hasattr(result, 'data'), "Result should have data attribute"
    assert len(result.data) > 0, "Result data should not be empty"
    # Check requirement compliance: {requirement.description}
    assert result.meets_requirement("{requirement.id}"), f"Should meet requirement {requirement.id}" """
        else:
            return f"""
    # Negative test: {requirement.description}
    # Requirement: {requirement.id}
    with pytest.raises(ValueError):
        component.process(invalid_input)"""
    
    def _generate_validation_test_code(self, criterion: str) -> str:
        """Generate test code for validation criterion.
        
        Args:
            criterion: Validation criterion
            
        Returns:
            Test code
        """
        return f"""
    # Validation: {criterion}
    result = validator.validate(input_data)
    assert result.is_valid(), f"Validation should pass for criterion: {criterion}"
    # Check specific validation criterion
    assert criterion in result.validated_criteria, f"Should validate: {criterion}"
    assert result.validation_details["{criterion}"]["status"] == "passed"
    assert result.validation_details["{criterion}"]["errors"] == []"""
    
    def _generate_e2e_test_code(self, recipe: Recipe) -> str:
        """Generate end-to-end test code.
        
        Args:
            recipe: Recipe to test
            
        Returns:
            E2E test code
        """
        success_criteria_checks = "\n".join([
            f'    assert result.meets_criterion("{criterion}"), "Failed: {criterion}"'
            for criterion in recipe.requirements.success_criteria
        ]) if recipe.requirements.success_criteria else '    assert result.criteria_met == True'
        
        return f"""
    # End-to-end test for {recipe.name}
    # Initialize system
    system = {recipe.name}System()
    
    # Execute full workflow
    input_data = create_test_input()
    result = system.execute(input_data)
    
    # Verify all success criteria
    assert result.success == True, "System execution should succeed"
    assert result.errors == [], "Should have no errors"
    
    # Verify each success criterion
{success_criteria_checks}
    
    # Verify output exists and is valid
    assert result.output is not None, "Should produce output"
    assert validate_output(result.output), "Output should be valid" """
    
    def _generate_interaction_test_code(self, component) -> str:
        """Generate component interaction test code.
        
        Args:
            component: Component to test
            
        Returns:
            Interaction test code
        """
        return f"""
    # Test {component.name} interactions
    component = {component.class_name or component.name}()
    
    # Test interaction with dependencies
    mock_dependency = Mock()
    mock_dependency.process.return_value = {{"status": "success", "data": []}}
    component.set_dependency(mock_dependency)
    
    result = component.interact_with_dependencies()
    assert result is not None, "Interaction should produce result"
    assert mock_dependency.process.called, "Should call dependency"
    assert result.interaction_count > 0, "Should record interactions"
    
    # Verify proper data flow
    assert result.dependency_data is not None, "Should receive dependency data"
    assert result.processed_successfully == True, "Interaction should succeed" """
    
    def _needs_negative_test(self, requirement: Requirement) -> bool:
        """Check if requirement needs negative testing.
        
        Args:
            requirement: Requirement to check
            
        Returns:
            True if negative test needed
        """
        # Check for error handling requirements
        keywords = ['validate', 'check', 'verify', 'error', 'invalid', 'reject']
        desc_lower = requirement.description.lower()
        return any(keyword in desc_lower for keyword in keywords)
    
    def _generate_conftest(self, recipe: Recipe) -> str:
        """Generate conftest.py with shared fixtures.
        
        Args:
            recipe: Recipe being tested
            
        Returns:
            Conftest content
        """
        return f'''"""Shared fixtures for {recipe.name} tests."""

import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_recipe():
    """Sample recipe for testing."""
    return {{
        "name": "{recipe.name}",
        "version": "{recipe.components.version}",
        "type": "{recipe.components.type.value}"
    }}


@pytest.fixture
def temp_workspace(tmp_path):
    """Temporary workspace for file operations."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_dependencies():
    """Mock dependencies for testing."""
    return {{
        # Add mock dependencies as needed
    }}
'''
    
    def _generate_test_file(self, tests: List[TestCase], description: str) -> str:
        """Generate a test file from test cases.
        
        Args:
            tests: Test cases to include
            description: File description
            
        Returns:
            Test file content
        """
        lines = [
            f'"""{description}."""',
            '',
            'import pytest',
            'import sys',
            'from pathlib import Path',
            '',
            '# Add src to path',
            'sys.path.insert(0, str(Path(__file__).parent.parent / "src"))',
            '',
            ''
        ]
        
        # Group tests by type
        for test in tests:
            lines.append(f'def {test.name}():')
            lines.append(f'    """{test.description}."""')
            
            # Add test code (simplified)
            test_lines = test.test_code.strip().split('\n')
            for line in test_lines:
                if line:
                    lines.append(f'    {line}')
            
            lines.append('')
            lines.append('')
        
        return '\n'.join(lines)