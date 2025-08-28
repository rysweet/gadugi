#!/usr/bin/env python3
"""Test Executor - Single-purpose executor for running tests.

This executor runs tests directly without delegating to other agents.
It follows the NO DELEGATION principle - all operations use direct subprocess calls.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_executor import BaseExecutor


class TestExecutor(BaseExecutor):
    """Single-purpose executor for running tests.
    
    CRITICAL: This executor MUST NOT call or delegate to other agents.
    All operations must be direct subprocess calls only.
    """
    
    def __init__(self):
        """Initialize the test executor."""
        self.test_results = []
        
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution entry point for running tests.
        
        Args:
            params: Dictionary containing:
                - test_framework: 'pytest' | 'unittest' | 'jest' | 'mocha'
                - test_path: Path to test file or directory
                - options: Additional test options (coverage, verbose, etc.)
                - working_dir: Working directory for test execution
                
        Returns:
            Dictionary with:
                - success: Boolean indicating if tests passed
                - framework: Test framework used
                - tests_run: Number of tests executed
                - tests_passed: Number of tests that passed
                - tests_failed: Number of tests that failed
                - output: Test output
                - error: Error message if execution failed
        """
        framework = params.get('test_framework', 'pytest')
        test_path = params.get('test_path', 'tests/')
        options = params.get('options', {})
        working_dir = params.get('working_dir', '.')
        
        try:
            if framework == 'pytest':
                return self._run_pytest(test_path, options, working_dir)
            elif framework == 'unittest':
                return self._run_unittest(test_path, options, working_dir)
            elif framework == 'jest':
                return self._run_jest(test_path, options, working_dir)
            elif framework == 'mocha':
                return self._run_mocha(test_path, options, working_dir)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported test framework: {framework}'
                }
        except Exception as e:
            return {
                'success': False,
                'framework': framework,
                'error': str(e)
            }
    
    def _run_pytest(self, test_path: str, options: Dict, working_dir: str) -> Dict[str, Any]:
        """Run pytest tests.
        
        Direct subprocess execution - no agent delegation.
        """
        cmd = ['pytest', test_path]
        
        # Add common pytest options
        if options.get('verbose'):
            cmd.append('-v')
        if options.get('coverage'):
            cmd.extend(['--cov', options.get('coverage_path', '.')])
            cmd.append('--cov-report=term')
        if options.get('markers'):
            cmd.extend(['-m', options['markers']])
        
        # Check for UV project
        uv_project = Path(working_dir) / 'pyproject.toml'
        if uv_project.exists() and (Path(working_dir) / 'uv.lock').exists():
            # Use UV to run pytest
            cmd = ['uv', 'run'] + cmd
        
        # Execute tests
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True
        )
        
        # Parse pytest output
        output_lines = result.stdout.split('\n')
        summary_line = self._find_pytest_summary(output_lines)
        
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        
        if summary_line:
            # Parse summary like "5 passed, 2 failed in 1.23s"
            import re
            passed_match = re.search(r'(\d+) passed', summary_line)
            failed_match = re.search(r'(\d+) failed', summary_line)
            
            if passed_match:
                tests_passed = int(passed_match.group(1))
            if failed_match:
                tests_failed = int(failed_match.group(1))
            tests_run = tests_passed + tests_failed
        
        # Log the test execution
        self._log_test_run('pytest', test_path, result.returncode == 0)
        
        return {
            'success': result.returncode == 0,
            'framework': 'pytest',
            'tests_run': tests_run,
            'tests_passed': tests_passed,
            'tests_failed': tests_failed,
            'output': result.stdout,
            'error_output': result.stderr if result.returncode != 0 else None,
            'exit_code': result.returncode
        }
    
    def _run_unittest(self, test_path: str, options: Dict, working_dir: str) -> Dict[str, Any]:
        """Run Python unittest tests.
        
        Direct subprocess execution - no agent delegation.
        """
        cmd = [sys.executable, '-m', 'unittest']
        
        if options.get('verbose'):
            cmd.append('-v')
        
        # Add test path or discover tests
        if Path(test_path).is_file():
            cmd.append(test_path)
        else:
            cmd.extend(['discover', '-s', test_path])
        
        # Execute tests
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True
        )
        
        # Parse unittest output
        output_lines = result.stdout.split('\n')
        tests_run = 0
        tests_failed = 0
        
        for line in output_lines:
            if 'Ran' in line and 'test' in line:
                import re
                match = re.search(r'Ran (\d+) test', line)
                if match:
                    tests_run = int(match.group(1))
            if 'FAILED' in line:
                match = re.search(r'failures=(\d+)', line)  # type: ignore[assignment]
                if match:
                    tests_failed = int(match.group(1))
        
        tests_passed = tests_run - tests_failed
        
        # Log the test execution
        self._log_test_run('unittest', test_path, result.returncode == 0)
        
        return {
            'success': result.returncode == 0,
            'framework': 'unittest',
            'tests_run': tests_run,
            'tests_passed': tests_passed,
            'tests_failed': tests_failed,
            'output': result.stdout,
            'error_output': result.stderr if result.returncode != 0 else None,
            'exit_code': result.returncode
        }
    
    def _run_jest(self, test_path: str, options: Dict, working_dir: str) -> Dict[str, Any]:
        """Run Jest tests for JavaScript/TypeScript.
        
        Direct subprocess execution - no agent delegation.
        """
        cmd = ['npx', 'jest', test_path]
        
        if options.get('coverage'):
            cmd.append('--coverage')
        if options.get('watch'):
            cmd.append('--watch')
        if options.get('verbose'):
            cmd.append('--verbose')
        
        # Execute tests
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True
        )
        
        # Basic Jest output parsing
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        
        if 'Tests:' in result.stdout:
            import re
            # Parse Jest summary
            passed_match = re.search(r'(\d+) passed', result.stdout)
            failed_match = re.search(r'(\d+) failed', result.stdout)
            total_match = re.search(r'(\d+) total', result.stdout)
            
            if total_match:
                tests_run = int(total_match.group(1))
            if passed_match:
                tests_passed = int(passed_match.group(1))
            if failed_match:
                tests_failed = int(failed_match.group(1))
        
        # Log the test execution
        self._log_test_run('jest', test_path, result.returncode == 0)
        
        return {
            'success': result.returncode == 0,
            'framework': 'jest',
            'tests_run': tests_run,
            'tests_passed': tests_passed,
            'tests_failed': tests_failed,
            'output': result.stdout,
            'error_output': result.stderr if result.returncode != 0 else None,
            'exit_code': result.returncode
        }
    
    def _run_mocha(self, test_path: str, options: Dict, working_dir: str) -> Dict[str, Any]:
        """Run Mocha tests for JavaScript.
        
        Direct subprocess execution - no agent delegation.
        """
        cmd = ['npx', 'mocha', test_path]
        
        if options.get('reporter'):
            cmd.extend(['--reporter', options['reporter']])
        if options.get('timeout'):
            cmd.extend(['--timeout', str(options['timeout'])])
        
        # Execute tests
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True
        )
        
        # Basic Mocha output parsing
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if 'passing' in line:
                import re
                match = re.search(r'(\d+) passing', line)
                if match:
                    tests_passed = int(match.group(1))
            if 'failing' in line:
                match = re.search(r'(\d+) failing', line)  # type: ignore[assignment]
                if match:
                    tests_failed = int(match.group(1))
        
        tests_run = tests_passed + tests_failed
        
        # Log the test execution
        self._log_test_run('mocha', test_path, result.returncode == 0)
        
        return {
            'success': result.returncode == 0,
            'framework': 'mocha',
            'tests_run': tests_run,
            'tests_passed': tests_passed,
            'tests_failed': tests_failed,
            'output': result.stdout,
            'error_output': result.stderr if result.returncode != 0 else None,
            'exit_code': result.returncode
        }
    
    def _find_pytest_summary(self, output_lines: List[str]) -> Optional[str]:
        """Find the pytest summary line in output."""
        for line in output_lines:
            if 'passed' in line or 'failed' in line:
                if 'in' in line and 's' in line:  # timing info
                    return line
        return None
    
    def _log_test_run(self, framework: str, test_path: str, success: bool):
        """Log a test execution for audit purposes."""
        self.test_results.append({
            'timestamp': datetime.now().isoformat(),
            'framework': framework,
            'test_path': test_path,
            'success': success
        })
    
    def get_test_results(self) -> List[Dict[str, Any]]:
        """Get the log of all test executions."""
        return self.test_results.copy()


# Single-purpose function interface for direct usage
def execute_tests(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute tests without creating an instance.
    
    This is the primary interface for CLAUDE.md orchestration.
    No agent delegation - direct subprocess execution only.
    
    Args:
        params: Test execution parameters
        
    Returns:
        Test execution results
    """
    executor = TestExecutor()
    return executor.execute(params)