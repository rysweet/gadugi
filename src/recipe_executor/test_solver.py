"""Test Solver Agent - Iteratively fixes failing tests until all pass (TDD Green phase)."""

import logging
import subprocess
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import time

from .recipe_model import Recipe, RecipeTestSuite as TestSuite, GeneratedCode as CodeArtifact
from .claude_code_generator import ClaudeCodeGenerator

logger = logging.getLogger(__name__)


@dataclass
class TestFailure:
    """Information about a failing test."""
    
    test_file: str
    test_name: str
    error_message: str
    stack_trace: str
    failure_type: str  # assertion, exception, import_error, syntax_error
    
    @property
    def is_assertion(self) -> bool:
        """Check if this is an assertion failure."""
        return self.failure_type == "assertion"
    
    @property
    def is_import_error(self) -> bool:
        """Check if this is an import error."""
        return self.failure_type == "import_error"


@dataclass
class TestRunResult:
    """Result of running a test suite."""
    
    passed: int
    failed: int
    skipped: int
    errors: int
    failures: List[TestFailure]
    coverage_percent: Optional[float] = None
    execution_time: float = 0.0
    
    @property
    def all_passed(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0 and self.errors == 0
    
    @property
    def success_rate(self) -> float:
        """Calculate test success rate."""
        total = self.passed + self.failed + self.errors
        return (self.passed / total * 100) if total > 0 else 0.0


@dataclass
class FixAttempt:
    """Record of an attempt to fix failing tests."""
    
    iteration: int
    failures_addressed: List[TestFailure]
    code_changes: Dict[str, str]  # file_path -> new_content
    result: TestRunResult
    success: bool
    fix_description: str


class TestSolver:
    """
    Iteratively fixes failing tests until all pass (TDD Green phase).
    
    This agent implements the Recipe Executor specification requirement for:
    - Running tests and analyzing failures
    - Generating fixes for failing tests
    - Iteratively applying fixes until all tests pass
    - Maintaining test-driven development discipline
    """
    
    MAX_ITERATIONS = 10
    ITERATION_DELAY = 2.0  # Seconds between iterations
    
    def __init__(self, generator: Optional[ClaudeCodeGenerator] = None):
        """Initialize the test solver with a code generator."""
        self.generator = generator or ClaudeCodeGenerator()
        self.fix_history: List[FixAttempt] = []
        
    def solve_tests(
        self,
        recipe: Recipe,
        test_suite: TestSuite,
        code_artifact: CodeArtifact,
        output_dir: Path
    ) -> Tuple[bool, CodeArtifact, List[FixAttempt]]:
        """
        Iteratively fix failing tests until all pass.
        
        This is the main TDD Green phase implementation.
        
        Args:
            recipe: The recipe being implemented
            test_suite: The test suite to make pass
            code_artifact: The initial code implementation
            output_dir: Directory containing the code and tests
            
        Returns:
            Tuple of (success, final_code_artifact, fix_attempts)
        """
        logger.info(f"Starting test solver for recipe '{recipe.name}'")
        
        current_code = code_artifact
        self.fix_history = []
        
        for iteration in range(1, self.MAX_ITERATIONS + 1):
            logger.info(f"Test solver iteration {iteration}/{self.MAX_ITERATIONS}")
            
            # Run tests
            test_result = self._run_tests(output_dir)
            
            # Log progress
            logger.info(
                f"Iteration {iteration}: "
                f"Passed={test_result.passed}, "
                f"Failed={test_result.failed}, "
                f"Errors={test_result.errors}, "
                f"Success Rate={test_result.success_rate:.1f}%"
            )
            
            # Check if all tests pass
            if test_result.all_passed:
                logger.info(f"✅ All tests passed after {iteration} iteration(s)!")
                return True, current_code, self.fix_history
            
            # Analyze failures
            failures_to_fix = self._prioritize_failures(test_result.failures)
            
            if not failures_to_fix:
                logger.warning("No actionable failures found to fix")
                break
            
            # Generate fixes
            logger.info(f"Attempting to fix {len(failures_to_fix)} failure(s)")
            fix_attempt = self._generate_fixes(
                iteration,
                recipe,
                current_code,
                failures_to_fix,
                output_dir
            )
            
            if fix_attempt.code_changes:
                # Apply fixes
                self._apply_fixes(fix_attempt.code_changes, output_dir)
                
                # Update current code artifact
                current_code = self._update_code_artifact(current_code, fix_attempt.code_changes)
                
                # Re-run tests to check if fixes worked
                fix_attempt.result = self._run_tests(output_dir)
                fix_attempt.success = fix_attempt.result.all_passed
                
                self.fix_history.append(fix_attempt)
                
                if fix_attempt.success:
                    logger.info(f"✅ All tests passed after fix attempt {iteration}!")
                    return True, current_code, self.fix_history
                
                # Log improvement
                improvement = fix_attempt.result.passed - test_result.passed
                if improvement > 0:
                    logger.info(f"✅ Fixed {improvement} test(s) in this iteration")
                elif improvement < 0:
                    logger.warning(f"⚠️ Regression: {-improvement} test(s) now failing")
                else:
                    logger.info("No improvement in this iteration")
            else:
                logger.warning("No fixes generated for this iteration")
                self.fix_history.append(fix_attempt)
            
            # Delay between iterations
            time.sleep(self.ITERATION_DELAY)
        
        # Max iterations reached
        final_result = self._run_tests(output_dir)
        logger.warning(
            f"Max iterations reached. Final state: "
            f"Passed={final_result.passed}, Failed={final_result.failed}"
        )
        
        return False, current_code, self.fix_history
    
    def _run_tests(self, output_dir: Path) -> TestRunResult:
        """Run tests and parse results."""
        try:
            # Run pytest with detailed output
            cmd = [
                "pytest",
                str(output_dir / "tests"),
                "-v",
                "--tb=short",
                "--no-header",
                "-q"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(output_dir)
            )
            
            # Parse test output
            return self._parse_pytest_output(result.stdout, result.stderr)
            
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return TestRunResult(
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                failures=[TestFailure(
                    test_file="unknown",
                    test_name="test_execution",
                    error_message=str(e),
                    stack_trace="",
                    failure_type="exception"
                )]
            )
    
    def _parse_pytest_output(self, stdout: str, stderr: str) -> TestRunResult:
        """Parse pytest output to extract test results."""
        passed = 0
        failed = 0
        skipped = 0
        errors = 0
        failures = []
        
        # Parse summary line (e.g., "3 passed, 2 failed, 1 skipped")
        summary_pattern = r"(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+skipped|(\d+)\s+error"
        
        for match in re.finditer(summary_pattern, stdout + stderr):
            if match.group(1):
                passed = int(match.group(1))
            elif match.group(2):
                failed = int(match.group(2))
            elif match.group(3):
                skipped = int(match.group(3))
            elif match.group(4):
                errors = int(match.group(4))
        
        # Parse individual failures
        failure_pattern = r"FAILED\s+([\w/]+\.py)::([\w]+)(?:\[[\w-]+\])?\s+-\s+(.+)"
        
        for match in re.finditer(failure_pattern, stdout):
            test_file = match.group(1)
            test_name = match.group(2)
            error_msg = match.group(3)
            
            # Determine failure type
            failure_type = "assertion"
            if "ImportError" in error_msg or "ModuleNotFoundError" in error_msg:
                failure_type = "import_error"
            elif "SyntaxError" in error_msg:
                failure_type = "syntax_error"
            elif "Exception" in error_msg or "Error" in error_msg:
                failure_type = "exception"
            
            failures.append(TestFailure(
                test_file=test_file,
                test_name=test_name,
                error_message=error_msg,
                stack_trace="",  # Would need more parsing for full trace
                failure_type=failure_type
            ))
        
        return TestRunResult(
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            failures=failures
        )
    
    def _prioritize_failures(self, failures: List[TestFailure]) -> List[TestFailure]:
        """
        Prioritize which failures to fix first.
        
        Priority order:
        1. Import errors (blocks everything)
        2. Syntax errors (blocks execution)
        3. Assertion failures (logic issues)
        4. Other exceptions
        """
        if not failures:
            return []
        
        # Group by failure type
        import_errors = [f for f in failures if f.is_import_error]
        syntax_errors = [f for f in failures if f.failure_type == "syntax_error"]
        assertions = [f for f in failures if f.is_assertion]
        others = [f for f in failures if f not in import_errors + syntax_errors + assertions]
        
        # Return in priority order, limiting to top 3 to avoid overwhelming fixes
        prioritized = import_errors + syntax_errors + assertions + others
        return prioritized[:3]
    
    def _generate_fixes(
        self,
        iteration: int,
        recipe: Recipe,
        current_code: CodeArtifact,
        failures: List[TestFailure],
        output_dir: Path
    ) -> FixAttempt:
        """Generate fixes for the given test failures."""
        logger.info(f"Generating fixes for {len(failures)} failure(s)")
        
        # Prepare context for fix generation
        fix_context = self._prepare_fix_context(failures, current_code)
        
        # Use Claude to generate fixes
        fix_prompt = self._create_fix_prompt(recipe, failures, fix_context)
        
        try:
            # Generate fixes using the code generator
            # This would typically call Claude API with the fix prompt
            code_changes = self._call_claude_for_fixes(fix_prompt, output_dir)
            
            fix_description = f"Addressed {len(failures)} test failure(s)"
            
            return FixAttempt(
                iteration=iteration,
                failures_addressed=failures,
                code_changes=code_changes,
                result=TestRunResult(0, 0, 0, 0, []),  # Will be updated after running tests
                success=False,
                fix_description=fix_description
            )
            
        except Exception as e:
            logger.error(f"Failed to generate fixes: {e}")
            return FixAttempt(
                iteration=iteration,
                failures_addressed=failures,
                code_changes={},
                result=TestRunResult(0, 0, 0, 0, []),
                success=False,
                fix_description=f"Failed to generate fixes: {e}"
            )
    
    def _prepare_fix_context(
        self,
        failures: List[TestFailure],
        current_code: CodeArtifact
    ) -> Dict[str, Any]:
        """Prepare context information for fix generation."""
        context = {
            "failures": [],
            "current_files": {}
        }
        
        # Add failure details
        for failure in failures:
            context["failures"].append({
                "test_file": failure.test_file,
                "test_name": failure.test_name,
                "error": failure.error_message,
                "type": failure.failure_type
            })
        
        # Add relevant code files
        for file_path, content in current_code.files.items():
            # Include files mentioned in failures
            if any(file_path in f.error_message for f in failures):
                context["current_files"][file_path] = content
        
        return context
    
    def _create_fix_prompt(
        self,
        recipe: Recipe,
        failures: List[TestFailure],
        context: Dict[str, Any]
    ) -> str:
        """Create a prompt for Claude to fix the failing tests."""
        prompt = f"""Fix the following test failures for the recipe '{recipe.name}':

## Test Failures
"""
        
        for i, failure in enumerate(failures, 1):
            prompt += f"""
### Failure {i}
- Test: {failure.test_name} in {failure.test_file}
- Error Type: {failure.failure_type}
- Error Message: {failure.error_message}
"""
        
        prompt += """
## Instructions
1. Analyze each test failure
2. Generate minimal code changes to fix the failures
3. Ensure fixes don't break other tests
4. Follow TDD principles - make tests pass with simplest solution
5. Return code changes as a JSON object: {"file_path": "new_content", ...}

## Current Code Context
"""
        
        for file_path, content in context.get("current_files", {}).items():
            prompt += f"\n### {file_path}\n```python\n{content[:500]}...\n```\n"
        
        return prompt
    
    def _call_claude_for_fixes(self, prompt: str, output_dir: Path) -> Dict[str, str]:
        """
        Call Claude API to generate fixes.
        
        This is a placeholder - actual implementation would use ClaudeCodeGenerator.
        """
        # For now, return empty changes
        # In real implementation, this would call Claude API
        logger.info("Would call Claude API with fix prompt")
        return {}
    
    def _apply_fixes(self, code_changes: Dict[str, str], output_dir: Path) -> None:
        """Apply code changes to files."""
        for file_path, new_content in code_changes.items():
            full_path = output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(new_content)
            logger.info(f"Applied fix to: {file_path}")
    
    def _update_code_artifact(
        self,
        artifact: CodeArtifact,
        changes: Dict[str, str]
    ) -> CodeArtifact:
        """Update code artifact with changes."""
        updated_files = artifact.files.copy()
        updated_files.update(changes)
        
        return CodeArtifact(
            files=updated_files,
            language=artifact.language,
            framework=artifact.framework
        )
    
    def get_fix_summary(self) -> str:
        """Generate a summary of all fix attempts."""
        if not self.fix_history:
            return "No fix attempts made"
        
        summary = f"Test Solver Summary:\n"
        summary += f"Total iterations: {len(self.fix_history)}\n\n"
        
        for attempt in self.fix_history:
            summary += f"Iteration {attempt.iteration}:\n"
            summary += f"  - Failures addressed: {len(attempt.failures_addressed)}\n"
            summary += f"  - Files changed: {len(attempt.code_changes)}\n"
            summary += f"  - Result: Passed={attempt.result.passed}, Failed={attempt.result.failed}\n"
            summary += f"  - Success: {'✅' if attempt.success else '❌'}\n"
            summary += f"  - Description: {attempt.fix_description}\n\n"
        
        final_attempt = self.fix_history[-1]
        if final_attempt.success:
            summary += f"✅ All tests passing after {len(self.fix_history)} iteration(s)!"
        else:
            summary += f"❌ {final_attempt.result.failed} test(s) still failing after {len(self.fix_history)} iteration(s)"
        
        return summary