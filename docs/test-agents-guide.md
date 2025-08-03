# Test Agents Guide

## Overview

The Test Solver and Test Writer agents provide automated test maintenance and creation capabilities for the Gadugi ecosystem. These agents integrate with the WorkflowMaster to ensure comprehensive test coverage and automatic resolution of test failures.

## Agents Overview

### Test Solver Agent

The Test Solver Agent analyzes and resolves failing tests through systematic failure analysis and targeted remediation.

**Key Features:**
- Systematic root cause analysis of test failures
- Automated resolution planning and implementation
- Support for multiple failure categories (assertions, dependencies, resources, timing)
- Intelligent skip logic with proper justification
- Integration with shared test instruction framework

### Test Writer Agent

The Test Writer Agent creates comprehensive tests for new functionality with TDD alignment and quality standards.

**Key Features:**
- Automated test generation for code coverage gaps
- TDD-aligned test creation that guides development
- Support for multiple test types (unit, integration, performance, security)
- Comprehensive fixture management and reuse
- Quality validation and enhancement

### Shared Test Instructions Framework

Both agents share a common instruction framework that ensures:
- Test idempotency and reliability
- Proper dependency management
- Resource cleanup and parallel safety
- Consistent test structure and documentation
- Valid skip justifications

## Usage

### Automatic Integration

The test agents are automatically invoked by the WorkflowMaster during the testing phase:

1. **Failing Test Detection**: WorkflowMaster detects failing tests and invokes Test Solver
2. **Coverage Gap Detection**: WorkflowMaster identifies uncovered code and invokes Test Writer
3. **Quality Validation**: Both agents ensure tests meet quality standards

### Manual Invocation

#### Test Solver Agent

```python
from test_solver_agent import TestSolverAgent

solver = TestSolverAgent()
result = solver.solve_test_failure('tests/test_module.py::test_failing_function')

print(f"Resolution: {result.resolution_applied}")
print(f"Final Status: {result.final_status}")
```

#### Test Writer Agent

```python
from test_writer_agent import TestWriterAgent, TestType

writer = TestWriterAgent()
result = writer.create_tests(
    code_path='src/module.py',
    context='User authentication system',
    test_type=TestType.UNIT
)

print(f"Tests Created: {len(result.tests_created)}")
print(f"Coverage: {result.coverage_analysis}")
```

## Test Solver Agent Details

### Systematic Failure Analysis Process

1. **Initial Assessment**
   - Collect failure information (error messages, tracebacks, environment)
   - Analyze test purpose and structure
   - Validate test follows shared instructions

2. **Root Cause Investigation**
   - Categorize failure type (assertion, runtime, dependency, etc.)
   - Perform systematic investigation based on category
   - Calculate confidence score for root cause analysis

3. **Resolution Strategy**
   - Create targeted fix plan for clear failures
   - Create investigation plan for unclear failures
   - Apply fixes systematically with validation

4. **Implementation and Validation**
   - Apply fixes while ensuring idempotency and parallel safety
   - Verify fixes resolve failures without regression
   - Document resolution process and recommendations

### Failure Categories

- **Assertion Errors**: Expected vs actual value mismatches
- **Runtime Errors**: Exceptions during test execution
- **Setup/Teardown Issues**: Problems with test environment preparation
- **Dependency Issues**: Missing or incompatible dependencies
- **Resource Issues**: File system, network, or external service problems
- **Timing Issues**: Race conditions or timeout problems

### Skip Scenarios

Tests are only skipped with explicit justification:

- **API Key Missing**: External API requires authentication
- **Platform Constraint**: OS or platform-specific functionality
- **Upstream Bug**: Known issues in dependencies
- **Infrastructure Dependency**: External services unavailable
- **Resource Constraint**: Hardware or environment limitations
- **Flaky Test**: Intermittent failures due to timing

## Test Writer Agent Details

### Test Creation Process

1. **Requirements Analysis**
   - Analyze code to understand testing requirements
   - Identify public methods, classes, and edge cases
   - Define comprehensive test scope

2. **Test Design**
   - Design test structure with proper organization
   - Plan fixture usage (existing and new)
   - Validate design against shared instructions

3. **Test Implementation**
   - Create test classes and individual test methods
   - Generate fixtures for resource management
   - Apply shared instruction enhancements

4. **Quality Assurance**
   - Validate test quality and structure
   - Analyze coverage and identify gaps
   - Document tests with clear intent and requirements

### Test Types Supported

- **Unit Tests**: Individual function and method testing
- **Integration Tests**: Component interaction testing
- **Performance Tests**: Response time and resource usage
- **Security Tests**: Input validation and access control
- **Error Handling Tests**: Exception and edge case testing

### Generated Test Structure

```python
class TestModuleName:
    """Comprehensive test suite for ModuleName."""
    
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup test environment and ensure cleanup."""
        # Setup code
        yield
        # Cleanup code
    
    def test_function_happy_path(self, shared_fixture):
        """
        Test function with valid inputs.
        
        Requirements:
        - Validates core functionality
        - Ensures proper return values
        - Verifies side effects
        """
        # Arrange
        test_input = create_valid_input()
        
        # Act
        result = target_function(test_input)
        
        # Assert
        assert result == expected_value
        assert validate_side_effects()
```

## Shared Test Instructions Framework

### Core Principles

1. **Purpose Analysis**: Every test must have a clear, documented purpose
2. **Idempotency**: Tests must produce consistent results when run multiple times
3. **Dependency Management**: External dependencies must be properly mocked or isolated
4. **Resource Cleanup**: All resources must be properly cleaned up
5. **Parallel Safety**: Tests must run reliably in parallel execution
6. **Fixture Reuse**: Leverage shared fixtures for consistency and efficiency

### Validation Framework

The shared instructions provide validation for:

```python
from shared_test_instructions import SharedTestInstructions

# Analyze test purpose
analysis = SharedTestInstructions.analyze_test_purpose(test_code, context)

# Validate test structure
is_valid, issues = SharedTestInstructions.validate_test_structure(test_code)

# Ensure idempotency
enhanced_code = SharedTestInstructions.ensure_test_idempotency(test_code)

# Validate parallel safety
is_safe, issues = SharedTestInstructions.validate_parallel_safety(test_code)

# Validate skip justification
is_valid, message = SharedTestInstructions.validate_skip_justification(
    reason, justification
)
```

## WorkflowMaster Integration

### Testing Phase Enhancement

The WorkflowMaster testing phase now includes:

1. **Failing Test Detection**: Automatic discovery of failing tests
2. **Test Solver Invocation**: Systematic resolution of failures
3. **Coverage Gap Analysis**: Identification of uncovered code
4. **Test Writer Invocation**: Generation of missing tests
5. **Quality Validation**: Comprehensive test suite validation

### Configuration

```python
config = {
    'autonomous_mode': True,
    'security_policy': 'testing',
    'test_solver_enabled': True,
    'test_writer_enabled': True
}

workflow_master = EnhancedWorkflowMaster(config)
```

### Execution Flow

```python
# WorkflowMaster automatically:
# 1. Detects failing tests
failing_tests = workflow_master.detect_failing_tests(workflow)
for test in failing_tests:
    result = workflow_master.test_solver.solve_test_failure(test)

# 2. Detects coverage gaps
coverage_gaps = workflow_master.detect_coverage_gaps(workflow)
for code_file in coverage_gaps:
    result = workflow_master.test_writer.create_tests(code_file)

# 3. Validates final test suite
final_result = workflow_master.run_test_suite(workflow)
```

## Best Practices

### For Test Solver

1. **Thorough Analysis**: Always analyze test purpose before fixing
2. **Conservative Fixes**: Make minimal changes to resolve issues
3. **Validation**: Run tests multiple times to ensure consistency
4. **Documentation**: Document all changes and reasoning
5. **Skip Justification**: Only skip with detailed, valid reasons

### For Test Writer

1. **Comprehensive Coverage**: Test happy paths, errors, and edge cases
2. **Clear Documentation**: Include purpose and requirements in tests
3. **Fixture Reuse**: Leverage existing fixtures when possible
4. **TDD Alignment**: Consider design implications when creating tests
5. **Quality Validation**: Ensure tests meet all shared instruction criteria

### For Integration

1. **Gradual Rollout**: Start with simple test scenarios
2. **Monitor Results**: Track agent performance and accuracy
3. **Feedback Loop**: Use results to improve agent algorithms
4. **Manual Override**: Provide manual controls for complex scenarios
5. **Continuous Improvement**: Regular updates based on usage patterns

## Troubleshooting

### Common Issues

#### Test Solver Issues

**Problem**: Agent skips tests that should be fixable
- **Solution**: Review confidence scoring algorithm
- **Check**: Error pattern recognition accuracy
- **Action**: Add more specific error patterns

**Problem**: Fixes introduce new failures
- **Solution**: Improve validation step
- **Check**: Regression testing coverage
- **Action**: Add rollback mechanisms

#### Test Writer Issues

**Problem**: Generated tests are too simplistic
- **Solution**: Enhance code analysis depth
- **Check**: Test requirement extraction
- **Action**: Add more sophisticated test patterns

**Problem**: Tests don't follow project conventions
- **Solution**: Improve pattern learning
- **Check**: Existing test analysis
- **Action**: Add convention detection

### Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Test Solver debugging
solver = TestSolverAgent()
result = solver.solve_test_failure(test_id)

# Test Writer debugging  
writer = TestWriterAgent()
result = writer.create_tests(code_file, context)
```

### Performance Optimization

1. **Parallel Execution**: Agents support concurrent operation
2. **Caching**: Results cached for repeated operations
3. **Incremental Analysis**: Only analyze changed code
4. **Resource Management**: Efficient memory and CPU usage

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**: Learn from successful patterns
2. **Advanced Code Analysis**: AST-based deep analysis
3. **Test Evolution**: Automatic test updates as code changes
4. **Performance Testing**: Automated benchmark generation
5. **Visual Test Reports**: Rich reporting and analytics

### Extensibility

The agent framework is designed for extension:

```python
class CustomTestSolverAgent(TestSolverAgent):
    """Custom test solver with project-specific logic."""
    
    def _analyze_failure_patterns(self, error_message, test_code, category):
        # Add custom analysis logic
        return super()._analyze_failure_patterns(error_message, test_code, category)

class CustomTestWriterAgent(TestWriterAgent):
    """Custom test writer with domain-specific patterns."""
    
    def _create_individual_test(self, test_method, code_analysis, tdd_context):
        # Add custom test generation logic
        return super()._create_individual_test(test_method, code_analysis, tdd_context)
```

## Contributing

To contribute to the test agents:

1. **Follow Shared Instructions**: All changes must adhere to the shared instruction framework
2. **Add Tests**: New features require comprehensive test coverage
3. **Document Changes**: Update documentation for any new capabilities
4. **Performance Testing**: Validate performance impact of changes
5. **Integration Testing**: Test with WorkflowMaster integration

## Support

For issues or questions:

1. **Check Logs**: Review agent execution logs for details
2. **Run Tests**: Validate basic functionality with test suite
3. **Check Configuration**: Verify agent and WorkflowMaster settings
4. **Review Documentation**: Ensure proper usage patterns
5. **Create Issues**: Report bugs or feature requests via GitHub

The Test Solver and Test Writer agents represent a significant advancement in automated test maintenance and creation, providing reliable, quality-focused testing support for the entire Gadugi ecosystem.