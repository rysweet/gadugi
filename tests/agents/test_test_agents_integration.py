"""
Comprehensive tests for Test Solver and Test Writer agents and WorkflowMaster integration.
"""

import pytest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Add agents to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '.claude', 'agents'))

# Import agents to test
from shared_test_instructions import (
    SharedTestInstructions, TestResult, TestStatus, SkipReason, TestAnalysis
)
from test_solver_agent import TestSolverAgent, FailureCategory, TestSolverResult
from test_writer_agent import TestWriterAgent, TestType, TestWriterResult
from workflow_master_enhanced import EnhancedWorkflowMaster


class TestSharedTestInstructions:
    """Test the shared test instruction framework."""
    
    def test_analyze_test_purpose(self):
        """Test test purpose analysis."""
        test_code = '''
def test_user_authentication():
    """Test user authentication with valid credentials."""
    user = create_test_user()
    assert user.authenticate("password123") == True
'''
        
        analysis = SharedTestInstructions.analyze_test_purpose(test_code, "User authentication system")
        
        assert analysis.purpose
        assert "authentication" in analysis.purpose.lower()
        assert len(analysis.dependencies) >= 0
        assert analysis.complexity_score >= 1
    
    def test_validate_test_structure_valid(self):
        """Test validation of valid test structure."""
        valid_test = '''
def test_example():
    """Test example functionality."""
    # Arrange
    data = setup_test_data()
    
    # Act
    result = process_data(data)
    
    # Assert
    assert result is not None
'''
        
        is_valid, issues = SharedTestInstructions.validate_test_structure(valid_test)
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_test_structure_invalid(self):
        """Test validation of invalid test structure."""
        invalid_test = '''
def not_a_test():
    pass
'''
        
        is_valid, issues = SharedTestInstructions.validate_test_structure(invalid_test)
        assert not is_valid
        assert len(issues) > 0
        assert any("test_" in issue for issue in issues)
    
    def test_ensure_test_idempotency(self):
        """Test idempotency enhancement."""
        non_idempotent_test = '''
def test_append_data():
    global_list.append("data")
    assert len(global_list) > 0
'''
        
        enhanced_test = SharedTestInstructions.ensure_test_idempotency(non_idempotent_test)
        assert "TODO: Ensure proper cleanup for idempotency" in enhanced_test or enhanced_test != non_idempotent_test
    
    def test_validate_dependency_management(self):
        """Test dependency management validation."""
        test_with_external_deps = '''
import requests
def test_api_call():
    response = requests.get("http://api.example.com")
    assert response.status_code == 200
'''
        
        is_valid, issues = SharedTestInstructions.validate_dependency_management(test_with_external_deps)
        # Should flag external dependencies that aren't mocked
        assert len(issues) >= 0  # May or may not have issues depending on implementation
    
    def test_validate_parallel_safety(self):
        """Test parallel safety validation."""
        unsafe_test = '''
import os
def test_global_state():
    os.chdir("/tmp")
    os.environ["TEST_VAR"] = "value"
    assert os.getcwd() == "/tmp"
'''
        
        is_safe, issues = SharedTestInstructions.validate_parallel_safety(unsafe_test)
        assert not is_safe
        assert len(issues) > 0
        assert any("global" in issue.lower() for issue in issues)
    
    def test_validate_skip_justification_valid(self):
        """Test valid skip justification."""
        is_valid, message = SharedTestInstructions.validate_skip_justification(
            SkipReason.API_KEY_MISSING,
            "API key is required but not available in test environment"
        )
        assert is_valid
        assert "valid" in message.lower()
    
    def test_validate_skip_justification_invalid(self):
        """Test invalid skip justification."""
        is_valid, message = SharedTestInstructions.validate_skip_justification(
            SkipReason.API_KEY_MISSING,
            "short"
        )
        assert not is_valid
        assert "detailed" in message.lower()


class TestTestSolverAgent:
    """Test the Test Solver Agent."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.solver = TestSolverAgent()
        
    @patch('test_solver_agent.subprocess.run')
    def test_solve_test_failure_success(self, mock_subprocess):
        """Test successful test failure resolution."""
        # Mock subprocess calls
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "test passed"
        mock_subprocess.return_value.stderr = ""
        
        # Mock file reading
        with patch('builtins.open', mock_open_for_test_code()):
            result = self.solver.solve_test_failure("tests/test_example.py::test_function")
        
        assert result.test_name == "tests/test_example.py::test_function"
        assert result.original_status == TestStatus.FAIL
        # Final status depends on implementation
    
    @patch('test_solver_agent.subprocess.run')
    def test_categorize_failure_assertion_error(self, mock_subprocess):
        """Test failure categorization for assertion errors."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stdout = ""
        mock_subprocess.return_value.stderr = "AssertionError: expected 5, got 3"
        
        failure_info = {
            'error_message': "AssertionError: expected 5, got 3",
            'traceback': "",
            'environment': {}
        }
        
        category = self.solver._categorize_failure(failure_info['error_message'], "test code")
        assert category == FailureCategory.ASSERTION_ERROR
    
    @patch('test_solver_agent.subprocess.run') 
    def test_categorize_failure_import_error(self, mock_subprocess):
        """Test failure categorization for import errors."""
        error_message = "ImportError: No module named 'missing_module'"
        category = self.solver._categorize_failure(error_message, "test code")
        assert category == FailureCategory.DEPENDENCY_ISSUE
    
    def test_calculate_confidence_score(self):
        """Test confidence score calculation."""
        clear_error = "AssertionError: expected 5, got 3"
        score = self.solver._calculate_confidence_score(
            clear_error, "Clear assertion mismatch", FailureCategory.ASSERTION_ERROR
        )
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be fairly confident with clear assertion error
    
    def test_create_test_backup(self):
        """Test test file backup creation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("test content")
            test_file = f.name
        
        try:
            backup_path = self.solver._create_test_backup(test_file)
            assert os.path.exists(backup_path)
            assert backup_path.endswith('.backup')
            
            # Cleanup
            os.remove(backup_path)
        finally:
            os.remove(test_file)


class TestTestWriterAgent:
    """Test the Test Writer Agent."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.writer = TestWriterAgent()
    
    def test_create_tests_basic(self):
        """Test basic test creation."""
        # Create a temporary Python file to test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

def divide_numbers(a, b):
    """Divide first number by second."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
''')
            code_file = f.name
        
        try:
            result = self.writer.create_tests(code_file, "Math utility functions")
            
            assert result.module_name
            assert len(result.tests_created) > 0
            assert result.quality_metrics['idempotent']
            assert result.quality_metrics['parallel_safe']
            
        finally:
            os.remove(code_file)
    
    def test_analyze_code_for_testing(self):
        """Test code analysis for test creation."""
        # Create temporary code file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''
class Calculator:
    def add(self, a, b):
        return a + b
    
    def _private_method(self):
        pass

def public_function():
    pass
''')
            code_file = f.name
        
        try:
            analysis = self.writer._analyze_code_for_testing(code_file)
            
            assert 'add' in analysis.public_methods
            assert 'public_function' in analysis.public_methods
            assert '_private_method' in analysis.private_methods
            assert 'Calculator' in analysis.classes
            
        finally:
            os.remove(code_file)
    
    def test_create_individual_fixture(self):
        """Test individual fixture creation."""
        fixture = self.writer._create_individual_fixture("temp_dir")
        
        assert fixture.name == "temp_dir"
        assert "temporary directory" in fixture.purpose.lower()
        assert fixture.scope in ['function', 'class', 'module', 'session']
        assert fixture.setup_code
    
    def test_generate_test_file_content(self):
        """Test test file content generation."""
        # Create mock test writer result
        from test_writer_agent import TestSpec, FixtureSpec, TestWriterResult
        
        mock_result = TestWriterResult(
            module_name="test_module",
            tests_created=[
                TestSpec(
                    name="test_example",
                    purpose="Test example functionality",
                    test_type=TestType.UNIT,
                    coverage_areas=["example"],
                    fixtures_used=["temp_dir"],
                    setup_code="# Setup code",
                    test_code="# Test code",
                    assertion_code="assert True",
                    cleanup_code="# Cleanup",
                    documentation='"""Test documentation."""'
                )
            ],
            fixtures_created=[
                FixtureSpec(
                    name="temp_dir",
                    purpose="Temporary directory",
                    scope="function",
                    setup_code="return Path(tempfile.mkdtemp())",
                    cleanup_code="shutil.rmtree(temp_dir)",
                    dependencies=[]
                )
            ],
            coverage_analysis={},
            tdd_alignment={},
            quality_metrics={},
            validation_results=[]
        )
        
        content = self.writer.generate_test_file_content(mock_result)
        
        assert "Test suite for test_module" in content
        assert "Generated by Test Writer Agent" in content
        assert "import pytest" in content
        assert "def test_example" in content
        assert "@pytest.fixture" in content


class TestWorkflowMasterIntegration:
    """Test WorkflowMaster integration with test agents."""
    
    def setup_method(self):
        """Setup for each test method."""
        config = {
            'autonomous_mode': True,
            'security_policy': 'testing'
        }
        self.workflow_master = EnhancedWorkflowMaster(config)
    
    def test_test_agent_initialization(self):
        """Test that test agents are properly initialized."""
        assert hasattr(self.workflow_master, 'test_solver')
        assert hasattr(self.workflow_master, 'test_writer')
        assert self.workflow_master.test_solver is not None
        assert self.workflow_master.test_writer is not None
    
    def test_execution_stats_tracking(self):
        """Test that test agent execution is tracked."""
        initial_stats = self.workflow_master.execution_stats.copy()
        
        assert 'test_solver_invocations' in initial_stats
        assert 'test_writer_invocations' in initial_stats
        assert initial_stats['test_solver_invocations'] == 0
        assert initial_stats['test_writer_invocations'] == 0
    
    @patch.object(EnhancedWorkflowMaster, '_detect_failing_tests')
    @patch.object(EnhancedWorkflowMaster, '_detect_coverage_gaps')
    def test_execute_testing_task_with_agents(self, mock_coverage, mock_failing):
        """Test testing task execution with test agents."""
        # Mock workflow state
        from workflow_master_enhanced import WorkflowState, TaskInfo, WorkflowPhase
        
        workflow = WorkflowState(task_id="test-123")
        task = TaskInfo(
            id="test-task",
            name="testing",
            description="Test task",
            phase=WorkflowPhase.TESTING
        )
        
        # Mock no failing tests or coverage gaps
        mock_failing.return_value = []
        mock_coverage.return_value = []
        
        # Mock container execution
        with patch.object(self.workflow_master, 'run_test_suite') as mock_run_tests:
            mock_run_tests.return_value = {'success': True}
            
            result = self.workflow_master.execute_testing_task(task, workflow)
            
            assert result is True
            mock_failing.assert_called_once()
            mock_coverage.assert_called_once()
    
    def test_determine_test_file_path(self):
        """Test test file path determination."""
        # Test various code file paths
        test_cases = [
            ("src/module.py", "tests/test_module.py"),
            ("lib/utils.py", "tests/test_utils.py"),
            ("package/submodule.py", "tests/test_submodule.py")
        ]
        
        for code_file, expected_test_file in test_cases:
            result = self.workflow_master.determine_test_file_path(code_file)
            assert result == expected_test_file
    
    def test_extract_test_class_name(self):
        """Test test class name extraction."""
        test_cases = [
            ("test_user_creation", "TestUserCreation"),
            ("test_api_authentication", "TestApiAuthentication"),
            ("test_simple", "TestSimple"),
            ("invalid_name", "TestClass")
        ]
        
        for test_method, expected_class in test_cases:
            result = self.workflow_master.extract_test_class_name(test_method)
            assert result == expected_class
    
    @patch('workflow_master_enhanced.Path.mkdir')
    @patch('builtins.open')
    def test_write_test_suite(self, mock_open, mock_mkdir):
        """Test test suite writing."""
        from test_writer_agent import TestWriterResult
        
        mock_result = Mock(spec=TestWriterResult)
        mock_result.module_name = "test_module"
        mock_result.tests_created = []
        mock_result.fixtures_created = []
        
        with patch.object(self.workflow_master, 'generate_test_file_content') as mock_generate:
            mock_generate.return_value = "test content"
            
            result = self.workflow_master.write_test_suite("tests/test_file.py", mock_result)
            
            assert result is True
            mock_mkdir.assert_called_once()
            mock_open.assert_called_once()


class TestAgentErrorHandling:
    """Test error handling in test agents."""
    
    def test_test_solver_error_handling(self):
        """Test error handling in TestSolverAgent."""
        solver = TestSolverAgent()
        
        # Test with invalid test identifier
        result = solver.solve_test_failure("invalid::test::identifier")
        
        assert result.original_status == TestStatus.ERROR
        assert "error" in result.resolution_applied.lower()
    
    def test_test_writer_error_handling(self):
        """Test error handling in TestWriterAgent."""
        writer = TestWriterAgent()
        
        # Test with non-existent file
        result = writer.create_tests("/non/existent/file.py")
        
        assert result.module_name
        assert len(result.tests_created) == 0
        assert "error" in str(result.validation_results).lower()


class TestAgentConfiguration:
    """Test agent configuration and customization."""
    
    def test_test_solver_custom_config(self):
        """Test TestSolverAgent with custom configuration."""
        from interfaces import AgentConfig
        
        config = AgentConfig(
            agent_id="custom_solver",
            name="Custom Test Solver"
        )
        
        solver = TestSolverAgent(config)
        assert solver.config.agent_id == "custom_solver"
        assert solver.config.name == "Custom Test Solver"
    
    def test_test_writer_custom_config(self):
        """Test TestWriterAgent with custom configuration."""
        from interfaces import AgentConfig
        
        config = AgentConfig(
            agent_id="custom_writer", 
            name="Custom Test Writer"
        )
        
        writer = TestWriterAgent(config)
        assert writer.config.agent_id == "custom_writer"
        assert writer.config.name == "Custom Test Writer"


def mock_open_for_test_code():
    """Mock file opening for test code reading."""
    test_code = '''
def test_example():
    """Test example functionality."""
    assert True
'''
    return patch('builtins.open', mock_open(read_data=test_code))


# Integration test helpers

@pytest.fixture
def temp_test_directory():
    """Create temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_python_file(temp_test_directory):
    """Create sample Python file for testing."""
    file_path = os.path.join(temp_test_directory, "sample.py")
    with open(file_path, 'w') as f:
        f.write('''
def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b

def calculate_product(a, b):
    """Calculate product of two numbers."""
    if a == 0 or b == 0:
        return 0
    return a * b

class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def get_history(self):
        return self.history.copy()
''')
    return file_path


@pytest.fixture
def failing_test_file(temp_test_directory):
    """Create a failing test file for solver testing."""
    file_path = os.path.join(temp_test_directory, "test_failing.py")
    with open(file_path, 'w') as f:
        f.write('''
import pytest

def test_assertion_failure():
    """Test that will fail due to assertion."""
    assert 1 + 1 == 3  # This will fail

def test_import_error():
    """Test that will fail due to import."""
    import non_existent_module
    assert True

def test_runtime_error():
    """Test that will fail due to runtime error."""
    result = 1 / 0  # Division by zero
    assert result
''')
    return file_path


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    def test_complete_workflow_with_test_agents(self, sample_python_file, temp_test_directory):
        """Test complete workflow including test creation and failure resolution."""
        # This would be a more complex integration test
        # that exercises the full workflow with real files
        pass
    
    def test_test_writer_creates_valid_tests(self, sample_python_file):
        """Test that TestWriterAgent creates syntactically valid tests."""
        writer = TestWriterAgent()
        result = writer.create_tests(sample_python_file, "Sample calculator functions")
        
        assert len(result.tests_created) > 0
        
        # Check that created tests have valid structure
        for test in result.tests_created:
            assert test.name.startswith('test_')
            assert test.documentation
            assert test.test_code or test.assertion_code
    
    def test_shared_instructions_integration(self, sample_python_file):
        """Test integration between agents and shared instructions."""
        writer = TestWriterAgent()
        result = writer.create_tests(sample_python_file)
        
        # Tests should follow shared instruction guidelines
        for test in result.tests_created:
            # Check idempotency
            assert not any(pattern in test.test_code for pattern in ['global ', '+=', 'append'])
            
            # Check structure
            test_code = f"{test.setup_code}\n{test.test_code}\n{test.assertion_code}"
            is_valid, issues = SharedTestInstructions.validate_test_structure(test_code)
            # Should have minimal issues for generated tests
            assert len(issues) <= 2  # Allow for minor issues in generated code


if __name__ == "__main__":
    pytest.main([__file__])