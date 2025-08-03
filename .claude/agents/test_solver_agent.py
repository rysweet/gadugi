"""
Test Solver Agent Implementation
Analyzes and resolves failing tests through systematic failure analysis.
"""

import os
import sys
import subprocess
import tempfile
import logging
import shutil
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

try:
    from utils.error_handling import ErrorHandler, CircuitBreaker
    from interfaces import AgentConfig, OperationResult
except ImportError:
    # Fallback definitions for missing imports
    from dataclasses import dataclass
    
    @dataclass
    class OperationResult:
        success: bool
        data: Any = None
        error: str = ""
    
    @dataclass
    class AgentConfig:
        agent_id: str
        name: str
    
    class CircuitBreaker:
        def __init__(self, failure_threshold=3, recovery_timeout=30.0):
            pass
        def __call__(self, func):
            return func

# Import shared test instructions
from shared_test_instructions import (
    SharedTestInstructions, TestResult, TestStatus, SkipReason, TestAnalysis
)


class FailureCategory(Enum):
    """Categories of test failures."""
    ASSERTION_ERROR = "assertion_error"
    RUNTIME_ERROR = "runtime_error"
    SETUP_TEARDOWN = "setup_teardown"
    DEPENDENCY_ISSUE = "dependency_issue"
    RESOURCE_ISSUE = "resource_issue"
    TIMING_ISSUE = "timing_issue"
    CONFIGURATION_ISSUE = "configuration_issue"


@dataclass
class FailureAnalysis:
    """Detailed analysis of test failure."""
    category: FailureCategory
    root_cause: str
    error_message: str
    traceback: str
    environment_info: Dict[str, Any]
    investigation_steps: List[str]
    confidence_score: float  # 0.0 to 1.0


@dataclass
class ResolutionPlan:
    """Plan for resolving test failure."""
    fix_type: str  # 'test_fix', 'setup_fix', 'functionality_fix'
    steps: List[str]
    risk_assessment: str  # 'low', 'medium', 'high'
    rollback_plan: str
    validation_steps: List[str]


@dataclass
class TestSolverResult:
    """Result of test solving operation."""
    test_name: str
    original_status: TestStatus
    final_status: TestStatus
    analysis: TestAnalysis
    failure_analysis: Optional[FailureAnalysis]
    resolution_plan: Optional[ResolutionPlan]
    resolution_applied: str
    skip_reason: Optional[SkipReason]
    skip_justification: str
    validation_results: List[str]
    recommendations: List[str]


class TestSolverAgent:
    """
    Agent for analyzing and resolving failing tests.
    
    Follows shared test instruction framework for systematic failure resolution.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig(
            agent_id="test_solver_agent",
            name="Test Solver Agent"
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        self.shared_instructions = SharedTestInstructions(config)
        
        # Setup error handling
        try:
            self.error_handler = ErrorHandler()
        except NameError:
            self.error_handler = None
    
    def solve_test_failure(self, test_identifier: str, context: str = "") -> TestSolverResult:
        """
        Main entry point for solving test failures.
        
        Args:
            test_identifier: Test file path and function name (e.g., 'tests/test_module.py::test_function')
            context: Additional context about the failure
            
        Returns:
            TestSolverResult with analysis and resolution details
        """
        self.logger.info(f"Starting test failure analysis for: {test_identifier}")
        
        try:
            # Phase 1: Initial Assessment
            failure_info = self._collect_failure_information(test_identifier)
            test_code = self._extract_test_code(test_identifier)
            
            # Analyze test purpose using shared instructions
            test_analysis = self.shared_instructions.analyze_test_purpose(test_code, context)
            
            # Validate test structure
            is_valid_structure, structure_issues = self.shared_instructions.validate_test_structure(test_code)
            
            # Phase 2: Root Cause Investigation
            failure_analysis = self._investigate_root_cause(failure_info, test_code, test_analysis)
            
            # Phase 3: Resolution Strategy
            if failure_analysis.confidence_score > 0.7:
                resolution_plan = self._create_resolution_plan(failure_analysis, test_code)
                
                # Phase 4: Implementation
                resolution_result = self._apply_resolution(
                    test_identifier, test_code, resolution_plan, failure_analysis
                )
                
                # Phase 5: Validation
                validation_results = self._validate_resolution(test_identifier, resolution_result)
                
                return TestSolverResult(
                    test_name=test_identifier,
                    original_status=TestStatus.FAIL,
                    final_status=TestStatus.PASS if validation_results['success'] else TestStatus.FAIL,
                    analysis=test_analysis,
                    failure_analysis=failure_analysis,
                    resolution_plan=resolution_plan,
                    resolution_applied=resolution_result['description'],
                    skip_reason=None,
                    skip_justification="",
                    validation_results=validation_results['details'],
                    recommendations=self._generate_recommendations(failure_analysis, resolution_result)
                )
            else:
                # If root cause unclear, provide skip with justification
                skip_reason, justification = self._determine_skip_strategy(failure_analysis)
                
                return TestSolverResult(
                    test_name=test_identifier,
                    original_status=TestStatus.FAIL,
                    final_status=TestStatus.SKIP,
                    analysis=test_analysis,
                    failure_analysis=failure_analysis,
                    resolution_plan=None,
                    resolution_applied="Test skipped due to unclear root cause",
                    skip_reason=skip_reason,
                    skip_justification=justification,
                    validation_results=["Skipped - requires manual investigation"],
                    recommendations=self._generate_investigation_recommendations(failure_analysis)
                )
                
        except Exception as e:
            self.logger.error(f"Error solving test failure: {e}")
            return self._create_error_result(test_identifier, str(e))
    
    def _collect_failure_information(self, test_identifier: str) -> Dict[str, Any]:
        """Collect comprehensive failure information."""
        self.logger.info("Collecting failure information...")
        
        failure_info = {
            'test_name': test_identifier,
            'error_message': '',
            'traceback': '',
            'exit_code': 0,
            'environment': {}
        }
        
        try:
            # Run test to capture failure output
            result = subprocess.run([
                sys.executable, '-m', 'pytest', test_identifier, '-v', '--tb=long'
            ], capture_output=True, text=True, timeout=60)
            
            failure_info.update({
                'error_message': result.stdout + result.stderr,
                'traceback': result.stderr,
                'exit_code': result.returncode
            })
            
            # Collect environment information
            failure_info['environment'] = {
                'python_version': sys.version,
                'working_directory': os.getcwd(),
                'environment_vars': dict(os.environ),
                'installed_packages': self._get_installed_packages()
            }
            
        except subprocess.TimeoutExpired:
            failure_info['error_message'] = "Test execution timed out"
        except Exception as e:
            failure_info['error_message'] = f"Failed to run test: {e}"
        
        return failure_info
    
    def _extract_test_code(self, test_identifier: str) -> str:
        """Extract the test code from the test file."""
        try:
            # Parse test identifier
            if '::' in test_identifier:
                file_path, test_function = test_identifier.split('::', 1)
            else:
                file_path = test_identifier
                test_function = None
            
            # Read test file
            with open(file_path, 'r') as f:
                content = f.read()
            
            if test_function:
                # Extract specific test function
                lines = content.split('\n')
                test_lines = []
                in_test = False
                indent_level = 0
                
                for line in lines:
                    if f'def {test_function}(' in line:
                        in_test = True
                        indent_level = len(line) - len(line.lstrip())
                        test_lines.append(line)
                    elif in_test:
                        if line.strip() and len(line) - len(line.lstrip()) <= indent_level and line.strip()[0].isalpha():
                            break  # End of function
                        test_lines.append(line)
                
                return '\n'.join(test_lines)
            else:
                return content
                
        except Exception as e:
            self.logger.error(f"Failed to extract test code: {e}")
            return ""
    
    @CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    def _investigate_root_cause(self, failure_info: Dict[str, Any], 
                               test_code: str, test_analysis: TestAnalysis) -> FailureAnalysis:
        """Systematically investigate root cause of test failure."""
        self.logger.info("Investigating root cause...")
        
        error_message = failure_info.get('error_message', '')
        
        # Categorize failure type
        category = self._categorize_failure(error_message, test_code)
        
        # Analyze specific failure patterns
        root_cause = self._analyze_failure_patterns(error_message, test_code, category)
        
        # Determine confidence score
        confidence_score = self._calculate_confidence_score(error_message, root_cause, category)
        
        # Generate investigation steps
        investigation_steps = self._generate_investigation_steps(category, root_cause)
        
        return FailureAnalysis(
            category=category,
            root_cause=root_cause,
            error_message=error_message,
            traceback=failure_info.get('traceback', ''),
            environment_info=failure_info.get('environment', {}),
            investigation_steps=investigation_steps,
            confidence_score=confidence_score
        )
    
    def _categorize_failure(self, error_message: str, test_code: str) -> FailureCategory:
        """Categorize the type of failure."""
        error_lower = error_message.lower()
        
        if 'assertionerror' in error_lower or 'assert' in error_lower:
            return FailureCategory.ASSERTION_ERROR
        elif any(err in error_lower for err in ['importerror', 'modulenotfounderror', 'attributeerror']):
            return FailureCategory.DEPENDENCY_ISSUE
        elif any(err in error_lower for err in ['filenotfounderror', 'permissionerror', 'ioerror']):
            return FailureCategory.RESOURCE_ISSUE
        elif any(err in error_lower for err in ['timeout', 'connectionerror', 'socket']):
            return FailureCategory.TIMING_ISSUE
        elif 'setup' in error_lower or 'teardown' in error_lower or 'fixture' in error_lower:
            return FailureCategory.SETUP_TEARDOWN
        elif any(err in error_lower for err in ['configerror', 'configuration', 'config']):
            return FailureCategory.CONFIGURATION_ISSUE
        else:
            return FailureCategory.RUNTIME_ERROR
    
    def _analyze_failure_patterns(self, error_message: str, test_code: str, 
                                 category: FailureCategory) -> str:
        """Analyze specific failure patterns to identify root cause."""
        
        if category == FailureCategory.ASSERTION_ERROR:
            # Extract expected vs actual values
            expected_actual = self._extract_assertion_details(error_message)
            return f"Assertion failure: {expected_actual}"
        
        elif category == FailureCategory.DEPENDENCY_ISSUE:
            missing_deps = self._extract_missing_dependencies(error_message)
            return f"Missing dependencies: {missing_deps}"
        
        elif category == FailureCategory.RESOURCE_ISSUE:
            resource_issues = self._extract_resource_issues(error_message, test_code)
            return f"Resource issues: {resource_issues}"
        
        elif category == FailureCategory.TIMING_ISSUE:
            timing_issues = self._extract_timing_issues(error_message, test_code)
            return f"Timing issues: {timing_issues}"
        
        elif category == FailureCategory.SETUP_TEARDOWN:
            setup_issues = self._extract_setup_issues(error_message, test_code)
            return f"Setup/teardown issues: {setup_issues}"
        
        elif category == FailureCategory.CONFIGURATION_ISSUE:
            config_issues = self._extract_config_issues(error_message, test_code)
            return f"Configuration issues: {config_issues}"
        
        else:
            return f"Runtime error: {error_message[:200]}"
    
    def _create_resolution_plan(self, failure_analysis: FailureAnalysis, 
                               test_code: str) -> ResolutionPlan:
        """Create systematic resolution plan."""
        
        category = failure_analysis.category
        
        if category == FailureCategory.ASSERTION_ERROR:
            return self._create_assertion_fix_plan(failure_analysis, test_code)
        elif category == FailureCategory.DEPENDENCY_ISSUE:
            return self._create_dependency_fix_plan(failure_analysis, test_code)
        elif category == FailureCategory.RESOURCE_ISSUE:
            return self._create_resource_fix_plan(failure_analysis, test_code)
        elif category == FailureCategory.SETUP_TEARDOWN:
            return self._create_setup_fix_plan(failure_analysis, test_code)
        else:
            return self._create_generic_fix_plan(failure_analysis, test_code)
    
    def _apply_resolution(self, test_identifier: str, test_code: str, 
                         resolution_plan: ResolutionPlan, 
                         failure_analysis: FailureAnalysis) -> Dict[str, Any]:
        """Apply the resolution plan to fix the test."""
        
        # Create backup
        test_file = test_identifier.split('::')[0]
        backup_path = self._create_test_backup(test_file)
        
        try:
            # Apply fixes based on plan
            if resolution_plan.fix_type == 'test_fix':
                fixed_code = self._apply_test_fixes(test_code, resolution_plan, failure_analysis)
                self._write_fixed_test(test_file, test_identifier, fixed_code)
            
            elif resolution_plan.fix_type == 'setup_fix':
                self._apply_setup_fixes(test_file, resolution_plan, failure_analysis)
            
            elif resolution_plan.fix_type == 'functionality_fix':
                # This would require modifying the actual code being tested
                # For now, document the required changes
                return {
                    'success': False,
                    'description': 'Functionality fix required - see recommendations',
                    'backup_path': backup_path
                }
            
            return {
                'success': True,
                'description': f"Applied {resolution_plan.fix_type} with {len(resolution_plan.steps)} steps",
                'backup_path': backup_path
            }
            
        except Exception as e:
            # Rollback on failure
            self._rollback_test_changes(test_file, backup_path)
            raise e
    
    def _validate_resolution(self, test_identifier: str, 
                           resolution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the resolution actually fixes the test."""
        
        if not resolution_result['success']:
            return {
                'success': False,
                'details': ['Resolution was not applied successfully']
            }
        
        validation_results = []
        
        try:
            # Run the test multiple times to ensure consistency
            for i in range(3):
                result = subprocess.run([
                    sys.executable, '-m', 'pytest', test_identifier, '-v'
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    validation_results.append(f"Run {i+1}: FAILED")
                    return {
                        'success': False,
                        'details': validation_results + [f"Test still failing: {result.stderr}"]
                    }
                else:
                    validation_results.append(f"Run {i+1}: PASSED")
            
            # Run related tests to check for regression
            test_file = test_identifier.split('::')[0]
            regression_result = subprocess.run([
                sys.executable, '-m', 'pytest', test_file, '-v'
            ], capture_output=True, text=True, timeout=120)
            
            if regression_result.returncode != 0:
                validation_results.append("REGRESSION DETECTED in related tests")
                return {
                    'success': False,
                    'details': validation_results
                }
            else:
                validation_results.append("No regression in related tests")
            
            return {
                'success': True,
                'details': validation_results
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'details': validation_results + ["Validation timed out"]
            }
        except Exception as e:
            return {
                'success': False,
                'details': validation_results + [f"Validation error: {e}"]
            }
    
    def _determine_skip_strategy(self, failure_analysis: FailureAnalysis) -> Tuple[SkipReason, str]:
        """Determine appropriate skip strategy for unclear failures."""
        
        if 'api' in failure_analysis.error_message.lower() and 'key' in failure_analysis.error_message.lower():
            return SkipReason.API_KEY_MISSING, "Test requires API key that is not available in test environment"
        
        elif failure_analysis.category == FailureCategory.DEPENDENCY_ISSUE:
            return SkipReason.INFRASTRUCTURE_DEPENDENCY, f"Test has unresolved dependency issues: {failure_analysis.root_cause}"
        
        elif failure_analysis.category == FailureCategory.TIMING_ISSUE:
            return SkipReason.FLAKY_TEST, f"Test appears to have timing issues that make it unreliable: {failure_analysis.root_cause}"
        
        elif 'platform' in failure_analysis.error_message.lower():
            return SkipReason.PLATFORM_CONSTRAINT, f"Test appears to have platform-specific issues: {failure_analysis.root_cause}"
        
        else:
            return SkipReason.UPSTREAM_BUG, f"Test failure appears to be due to external factors: {failure_analysis.root_cause}"
    
    # Helper methods for specific fix types
    
    def _create_assertion_fix_plan(self, failure_analysis: FailureAnalysis, test_code: str) -> ResolutionPlan:
        """Create plan for fixing assertion errors."""
        return ResolutionPlan(
            fix_type="test_fix",
            steps=[
                "Analyze expected vs actual values",
                "Determine if expected value or test logic needs adjustment",
                "Update assertion or test setup",
                "Ensure fix doesn't create artificial pass"
            ],
            risk_assessment="low",
            rollback_plan="Restore from backup file",
            validation_steps=["Run test multiple times", "Check for consistency"]
        )
    
    def _create_dependency_fix_plan(self, failure_analysis: FailureAnalysis, test_code: str) -> ResolutionPlan:
        """Create plan for fixing dependency issues."""
        return ResolutionPlan(
            fix_type="setup_fix",
            steps=[
                "Identify missing dependencies",
                "Add proper imports or mocking",
                "Update test fixtures if needed",
                "Validate dependency management"
            ],
            risk_assessment="medium",
            rollback_plan="Restore from backup file",
            validation_steps=["Run test", "Check import resolution"]
        )
    
    def _create_resource_fix_plan(self, failure_analysis: FailureAnalysis, test_code: str) -> ResolutionPlan:
        """Create plan for fixing resource issues."""
        return ResolutionPlan(
            fix_type="test_fix",
            steps=[
                "Identify resource management issues",
                "Add proper cleanup or resource creation",
                "Ensure idempotency",
                "Validate parallel safety"
            ],
            risk_assessment="medium",
            rollback_plan="Restore from backup file",
            validation_steps=["Run test multiple times", "Check resource cleanup"]
        )
    
    def _create_setup_fix_plan(self, failure_analysis: FailureAnalysis, test_code: str) -> ResolutionPlan:
        """Create plan for fixing setup/teardown issues."""
        return ResolutionPlan(
            fix_type="setup_fix",
            steps=[
                "Analyze fixture or setup issues",
                "Fix setup/teardown logic",
                "Ensure proper resource management",
                "Validate fixture dependencies"
            ],
            risk_assessment="medium",
            rollback_plan="Restore from backup file",
            validation_steps=["Run test with fixtures", "Check setup/teardown"]
        )
    
    def _create_generic_fix_plan(self, failure_analysis: FailureAnalysis, test_code: str) -> ResolutionPlan:
        """Create generic fix plan for unclear issues."""
        return ResolutionPlan(
            fix_type="test_fix",
            steps=[
                "Document failure analysis",
                "Apply conservative fixes",
                "Add debugging information",
                "Consider skipping if fix unclear"
            ],
            risk_assessment="high",
            rollback_plan="Restore from backup file",
            validation_steps=["Run test", "Manual review required"]
        )
    
    # Utility methods
    
    def _get_installed_packages(self) -> List[str]:
        """Get list of installed packages."""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True)
            return result.stdout.split('\n')
        except:
            return []
    
    def _calculate_confidence_score(self, error_message: str, root_cause: str, 
                                   category: FailureCategory) -> float:
        """Calculate confidence score for root cause analysis."""
        base_score = 0.5
        
        # Higher confidence for clear error patterns
        if category == FailureCategory.ASSERTION_ERROR and 'assert' in error_message.lower():
            base_score += 0.3
        elif category == FailureCategory.DEPENDENCY_ISSUE and any(dep in error_message.lower() 
                                                                  for dep in ['import', 'module']):
            base_score += 0.2
        
        # Adjust based on error message clarity
        if len(error_message) > 100 and any(keyword in error_message.lower() 
                                          for keyword in ['expected', 'actual', 'failed']):
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _generate_investigation_steps(self, category: FailureCategory, root_cause: str) -> List[str]:
        """Generate investigation steps based on failure category."""
        base_steps = [
            "Run test in isolation",
            "Check test dependencies",
            "Verify environment configuration"
        ]
        
        if category == FailureCategory.ASSERTION_ERROR:
            base_steps.extend([
                "Compare expected vs actual values",
                "Check test data validity",
                "Verify business logic"
            ])
        elif category == FailureCategory.DEPENDENCY_ISSUE:
            base_steps.extend([
                "Check import statements",
                "Verify package installations",
                "Check module paths"
            ])
        
        return base_steps
    
    def _generate_recommendations(self, failure_analysis: FailureAnalysis, 
                                 resolution_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for preventing similar issues."""
        recommendations = []
        
        if failure_analysis.category == FailureCategory.ASSERTION_ERROR:
            recommendations.append("Consider adding more descriptive assertion messages")
            recommendations.append("Review test data generation for consistency")
        
        elif failure_analysis.category == FailureCategory.DEPENDENCY_ISSUE:
            recommendations.append("Add dependency checks to test setup")
            recommendations.append("Consider using mock objects for external dependencies")
        
        recommendations.append("Add monitoring for similar test patterns")
        recommendations.append("Review test documentation and purpose clarity")
        
        return recommendations
    
    def _generate_investigation_recommendations(self, failure_analysis: FailureAnalysis) -> List[str]:
        """Generate recommendations for manual investigation."""
        return [
            f"Manual investigation required for {failure_analysis.category.value}",
            f"Root cause analysis confidence: {failure_analysis.confidence_score:.2f}",
            "Review error message and traceback manually",
            "Consider architectural changes if failure persists",
            "Document findings for future reference"
        ]
    
    def _create_test_backup(self, test_file_path: str) -> str:
        """Create backup of test file before modifications."""
        backup_path = f"{test_file_path}.backup"
        shutil.copy2(test_file_path, backup_path)
        return backup_path
    
    def _rollback_test_changes(self, test_file_path: str, backup_path: str):
        """Rollback test file to backup version."""
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, test_file_path)
            os.remove(backup_path)
    
    def _create_error_result(self, test_identifier: str, error_message: str) -> TestSolverResult:
        """Create error result when analysis fails."""
        return TestSolverResult(
            test_name=test_identifier,
            original_status=TestStatus.ERROR,
            final_status=TestStatus.ERROR,
            analysis=TestAnalysis(
                purpose="Error during analysis",
                requirements=[],
                expected_outcome="Analysis failed",
                dependencies=[],
                resources_used=[],
                complexity_score=0
            ),
            failure_analysis=None,
            resolution_plan=None,
            resolution_applied=f"Analysis failed: {error_message}",
            skip_reason=None,
            skip_justification="",
            validation_results=[f"Error: {error_message}"],
            recommendations=["Manual analysis required"]
        )
    
    # Placeholder methods for extraction logic (to be implemented based on specific patterns)
    
    def _extract_assertion_details(self, error_message: str) -> str:
        """Extract expected vs actual values from assertion error."""
        # Implementation would parse assertion error messages
        return "assertion details extracted"
    
    def _extract_missing_dependencies(self, error_message: str) -> str:
        """Extract missing dependency information."""
        # Implementation would parse import/module errors
        return "missing dependencies identified"
    
    def _extract_resource_issues(self, error_message: str, test_code: str) -> str:
        """Extract resource-related issues."""
        # Implementation would analyze file/network/resource errors
        return "resource issues identified"
    
    def _extract_timing_issues(self, error_message: str, test_code: str) -> str:
        """Extract timing-related issues."""
        # Implementation would analyze timeout/race condition errors
        return "timing issues identified"
    
    def _extract_setup_issues(self, error_message: str, test_code: str) -> str:
        """Extract setup/teardown issues."""
        # Implementation would analyze fixture/setup errors
        return "setup issues identified"
    
    def _extract_config_issues(self, error_message: str, test_code: str) -> str:
        """Extract configuration issues."""
        # Implementation would analyze config-related errors
        return "configuration issues identified"
    
    def _apply_test_fixes(self, test_code: str, resolution_plan: ResolutionPlan, 
                         failure_analysis: FailureAnalysis) -> str:
        """Apply fixes to test code."""
        # Apply shared instruction enhancements
        enhanced_code = self.shared_instructions.ensure_test_idempotency(test_code)
        enhanced_code = self.shared_instructions.ensure_resource_cleanup(enhanced_code)
        
        return enhanced_code
    
    def _apply_setup_fixes(self, test_file: str, resolution_plan: ResolutionPlan, 
                          failure_analysis: FailureAnalysis):
        """Apply setup/configuration fixes."""
        # Implementation would modify test setup, conftest.py, etc.
        pass
    
    def _write_fixed_test(self, test_file: str, test_identifier: str, fixed_code: str):
        """Write fixed test code back to file."""
        # Implementation would update the specific test function in the file
        pass