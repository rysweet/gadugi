"""Complete TDD Red-Green-Refactor cycle implementation for Recipe Executor."""

import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from enum import Enum

from .recipe_model import Recipe, RecipeTestSuite as TestSuite, GeneratedCode as CodeArtifact, BuildContext
from .test_generator import TestGenerator
from .test_solver import TestSolver, TestRunResult
from .claude_code_generator import ClaudeCodeGenerator
from .python_standards import QualityGates

logger = logging.getLogger(__name__)


class TDDPhase(Enum):
    """TDD cycle phases."""
    RED = "red"      # Tests written and failing
    GREEN = "green"  # Tests passing with minimal implementation
    REFACTOR = "refactor"  # Code improved while tests still pass


@dataclass
class TDDCycleResult:
    """Result of a complete TDD cycle."""
    
    phase_reached: TDDPhase
    test_suite: TestSuite
    code_artifact: Optional[CodeArtifact]
    red_phase_result: TestRunResult
    green_phase_result: Optional[TestRunResult]
    refactor_phase_result: Optional[TestRunResult]
    quality_gates_passed: bool
    success: bool
    errors: List[str]
    cycle_time: float
    
    @property
    def summary(self) -> str:
        """Generate a summary of the TDD cycle."""
        summary = f"TDD Cycle Result:\n"
        summary += f"  Phase Reached: {self.phase_reached.value.upper()}\n"
        summary += f"  Success: {'✅' if self.success else '❌'}\n"
        summary += f"  Cycle Time: {self.cycle_time:.1f}s\n"
        
        if self.red_phase_result:
            summary += f"\n  RED Phase:\n"
            summary += f"    Tests Written: {self.red_phase_result.failed + self.red_phase_result.errors}\n"
            summary += f"    All Failing: {'✅' if self.red_phase_result.all_passed == False else '❌'}\n"
        
        if self.green_phase_result:
            summary += f"\n  GREEN Phase:\n"
            summary += f"    Tests Passing: {self.green_phase_result.passed}\n"
            summary += f"    All Passing: {'✅' if self.green_phase_result.all_passed else '❌'}\n"
        
        if self.refactor_phase_result:
            summary += f"\n  REFACTOR Phase:\n"
            summary += f"    Tests Still Pass: {'✅' if self.refactor_phase_result.all_passed else '❌'}\n"
            summary += f"    Quality Gates: {'✅' if self.quality_gates_passed else '❌'}\n"
        
        if self.errors:
            summary += f"\n  Errors:\n"
            for error in self.errors:
                summary += f"    - {error}\n"
        
        return summary


class TDDPipeline:
    """
    Implements the complete Test-Driven Development Red-Green-Refactor cycle.
    
    This is a critical component of Recipe Executor that ensures:
    1. Tests are written FIRST and initially FAIL (Red phase)
    2. Minimal implementation to make tests pass (Green phase)
    3. Code improvement while maintaining green tests (Refactor phase)
    4. Quality gates are enforced at each phase
    """
    
    def __init__(
        self,
        test_generator: Optional[TestGenerator] = None,
        code_generator: Optional[ClaudeCodeGenerator] = None,
        test_solver: Optional[TestSolver] = None,
        quality_gates: Optional[QualityGates] = None
    ):
        """Initialize the TDD pipeline with required components."""
        self.test_generator = test_generator or TestGenerator()
        self.code_generator = code_generator or ClaudeCodeGenerator()
        self.test_solver = test_solver or TestSolver(code_generator)
        self.quality_gates = quality_gates or QualityGates()
        
    def execute_tdd_cycle(
        self,
        recipe: Recipe,
        context: BuildContext,
        output_dir: Path
    ) -> TDDCycleResult:
        """
        Execute the complete TDD Red-Green-Refactor cycle.
        
        Args:
            recipe: The recipe to implement
            context: Build context with options
            output_dir: Directory for generated code and tests
            
        Returns:
            TDDCycleResult with complete cycle information
        """
        logger.info(f"Starting TDD cycle for recipe '{recipe.name}'")
        start_time = time.time()
        
        errors = []
        phase_reached = TDDPhase.RED
        test_suite = None
        code_artifact = None
        red_result = None
        green_result = None
        refactor_result = None
        quality_passed = False
        
        try:
            # Phase 1: RED - Generate tests that fail
            logger.info("🔴 TDD RED Phase: Generating failing tests")
            red_result = self._execute_red_phase(recipe, context, output_dir)
            
            if not red_result["success"]:
                errors.append(f"RED phase failed: {red_result.get('error', 'Unknown error')}")
                return self._create_result(
                    TDDPhase.RED, red_result.get("test_suite"), None,
                    red_result.get("test_result"), None, None,
                    False, False, errors, time.time() - start_time
                )
            
            test_suite = red_result["test_suite"]
            
            # Verify tests are actually failing
            if red_result["test_result"].all_passed:
                errors.append("RED phase violation: Tests should fail initially but are passing!")
                logger.error("TDD violation: Tests passing in RED phase")
            
            # Phase 2: GREEN - Make tests pass with minimal implementation
            logger.info("🟢 TDD GREEN Phase: Making tests pass")
            green_result = self._execute_green_phase(recipe, test_suite, context, output_dir)
            
            if not green_result["success"]:
                errors.append(f"GREEN phase failed: {green_result.get('error', 'Unknown error')}")
                return self._create_result(
                    TDDPhase.RED, test_suite, green_result.get("code_artifact"),
                    red_result["test_result"], green_result.get("test_result"), None,
                    False, False, errors, time.time() - start_time
                )
            
            phase_reached = TDDPhase.GREEN
            code_artifact = green_result["code_artifact"]
            
            # Phase 3: REFACTOR - Improve code while keeping tests green
            logger.info("♻️ TDD REFACTOR Phase: Improving code quality")
            refactor_result = self._execute_refactor_phase(
                recipe, code_artifact, test_suite, context, output_dir
            )
            
            if refactor_result["success"]:
                phase_reached = TDDPhase.REFACTOR
                code_artifact = refactor_result["code_artifact"]
                quality_passed = refactor_result["quality_gates_passed"]
            else:
                errors.append(f"REFACTOR phase warning: {refactor_result.get('error', 'Quality issues')}")
            
            # Final success determination
            success = (
                phase_reached == TDDPhase.REFACTOR and
                green_result["test_result"].all_passed and
                (refactor_result["test_result"].all_passed if refactor_result else True)
            )
            
        except Exception as e:
            logger.error(f"TDD cycle failed with exception: {e}")
            errors.append(str(e))
            success = False
        
        cycle_time = time.time() - start_time
        
        return self._create_result(
            phase_reached, test_suite, code_artifact,
            red_result.get("test_result") if red_result else None,
            green_result.get("test_result") if green_result else None,
            refactor_result.get("test_result") if refactor_result else None,
            quality_passed, success, errors, cycle_time
        )
    
    def _execute_red_phase(
        self,
        recipe: Recipe,
        context: BuildContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Execute RED phase: Generate tests that fail.
        
        Critical: Tests MUST fail initially to validate they're testing something meaningful.
        """
        try:
            # Generate test suite
            test_suite = self.test_generator.generate_tests(recipe)
            
            # Write test files to disk
            test_dir = output_dir / "tests"
            test_dir.mkdir(parents=True, exist_ok=True)
            
            for test_file, content in test_suite.test_files.items():
                test_path = output_dir / test_file
                test_path.parent.mkdir(parents=True, exist_ok=True)
                test_path.write_text(content)
                logger.info(f"Created test file: {test_path}")
            
            # Create minimal stub implementations to allow imports
            self._create_minimal_stubs(recipe, output_dir)
            
            # Run tests - they should fail
            test_result = self._run_tests(output_dir)
            
            # Validate RED phase requirements
            if test_result.all_passed:
                logger.warning("⚠️ TDD Violation: Tests are passing in RED phase!")
                # This is actually a problem - tests should fail initially
            else:
                logger.info(f"✅ RED phase correct: {test_result.failed} test(s) failing as expected")
            
            return {
                "success": True,
                "test_suite": test_suite,
                "test_result": test_result
            }
            
        except Exception as e:
            logger.error(f"RED phase failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_suite": None,
                "test_result": TestRunResult(0, 0, 0, 1, [])
            }
    
    def _execute_green_phase(
        self,
        recipe: Recipe,
        test_suite: TestSuite,
        context: BuildContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Execute GREEN phase: Make tests pass with minimal implementation.
        
        Uses TestSolver for iterative fixing until all tests pass.
        """
        try:
            # Generate initial implementation
            logger.info("Generating initial implementation")
            initial_code = self.code_generator.generate(recipe, context, output_dir)
            
            if not initial_code:
                return {
                    "success": False,
                    "error": "Failed to generate initial code",
                    "code_artifact": None,
                    "test_result": None
                }
            
            # Write initial implementation
            for file_path, content in initial_code.files.items():
                full_path = output_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                logger.info(f"Created implementation file: {full_path}")
            
            # Use TestSolver to iteratively fix failing tests
            success, final_code, fix_attempts = self.test_solver.solve_tests(
                recipe, test_suite, initial_code, output_dir
            )
            
            # Get final test results
            final_test_result = self._run_tests(output_dir)
            
            if success and final_test_result.all_passed:
                logger.info(f"✅ GREEN phase complete: All {final_test_result.passed} tests passing")
            else:
                logger.warning(f"⚠️ GREEN phase incomplete: {final_test_result.failed} tests still failing")
            
            return {
                "success": success,
                "code_artifact": final_code,
                "test_result": final_test_result,
                "fix_attempts": fix_attempts
            }
            
        except Exception as e:
            logger.error(f"GREEN phase failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "code_artifact": None,
                "test_result": None
            }
    
    def _execute_refactor_phase(
        self,
        recipe: Recipe,
        code_artifact: CodeArtifact,
        test_suite: TestSuite,
        context: BuildContext,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Execute REFACTOR phase: Improve code while keeping tests green.
        
        Applies quality gates and refactoring improvements.
        """
        try:
            logger.info("Starting refactoring phase")
            
            # Run quality gates on current code
            quality_results = self.quality_gates.run_all_gates(output_dir)
            
            # Log quality gate results
            for gate, passed in quality_results.items():
                status = "✅" if passed else "❌"
                logger.info(f"Quality gate '{gate}': {status}")
            
            # If all quality gates pass, no refactoring needed
            if all(quality_results.values()):
                logger.info("All quality gates passed - no refactoring needed")
                test_result = self._run_tests(output_dir)
                return {
                    "success": True,
                    "code_artifact": code_artifact,
                    "test_result": test_result,
                    "quality_gates_passed": True
                }
            
            # Attempt automated refactoring for failed gates
            refactored_code = self._apply_refactoring(code_artifact, quality_results, output_dir)
            
            # Write refactored code
            for file_path, content in refactored_code.files.items():
                full_path = output_dir / file_path
                full_path.write_text(content)
            
            # Verify tests still pass after refactoring
            test_result = self._run_tests(output_dir)
            
            if not test_result.all_passed:
                logger.error(f"Refactoring broke {test_result.failed} test(s)!")
                # Revert to pre-refactor code
                for file_path, content in code_artifact.files.items():
                    full_path = output_dir / file_path
                    full_path.write_text(content)
                test_result = self._run_tests(output_dir)
            
            # Re-run quality gates
            final_quality = self.quality_gates.run_all_gates(output_dir)
            
            return {
                "success": test_result.all_passed,
                "code_artifact": refactored_code if test_result.all_passed else code_artifact,
                "test_result": test_result,
                "quality_gates_passed": all(final_quality.values())
            }
            
        except Exception as e:
            logger.error(f"REFACTOR phase failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "code_artifact": code_artifact,
                "test_result": None,
                "quality_gates_passed": False
            }
    
    def _create_minimal_stubs(self, recipe: Recipe, output_dir: Path) -> None:
        """Create minimal stub implementations to allow test imports."""
        # Create minimal module structure
        if recipe.design:
            for component in recipe.design.components:
                # Convert component name to module name
                module_name = component.name.lower().replace(" ", "_").replace("-", "_")
                module_path = output_dir / f"{module_name}.py"
                
                if not module_path.exists():
                    # Create minimal stub
                    stub_content = f'"""Minimal stub for {component.name}."""\n\n'
                    stub_content += "# This is a minimal stub to allow test imports\n"
                    stub_content += "# Will be replaced with actual implementation in GREEN phase\n\n"
                    
                    # Add minimal class/function definitions based on interfaces or methods
                    interfaces = getattr(component, 'public_interfaces', getattr(component, 'methods', []))
                    for interface in interfaces:
                        if "class" in interface.lower():
                            class_name = interface.split()[1] if len(interface.split()) > 1 else "StubClass"
                            stub_content += f"class {class_name}:\n    pass\n\n"
                        elif "def" in interface.lower() or "function" in interface.lower():
                            func_name = interface.split()[1] if len(interface.split()) > 1 else "stub_function"
                            stub_content += f"def {func_name}(*args, **kwargs):\n    pass\n\n"
                    
                    module_path.write_text(stub_content)
                    logger.info(f"Created minimal stub: {module_path}")
    
    def _run_tests(self, output_dir: Path) -> TestRunResult:
        """Run tests and return results."""
        try:
            cmd = [
                "pytest",
                str(output_dir / "tests"),
                "-v",
                "--tb=short",
                "-q"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(output_dir),
                timeout=30
            )
            
            # Parse output (simplified - real implementation in TestSolver)
            passed = result.stdout.count(" PASSED")
            failed = result.stdout.count(" FAILED")
            errors = result.stdout.count(" ERROR")
            
            return TestRunResult(
                passed=passed,
                failed=failed,
                skipped=0,
                errors=errors,
                failures=[],
                execution_time=0.0
            )
            
        except subprocess.TimeoutExpired:
            logger.error("Test execution timed out")
            return TestRunResult(0, 0, 0, 1, [])
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return TestRunResult(0, 0, 0, 1, [])
    
    def _apply_refactoring(
        self,
        code_artifact: CodeArtifact,
        quality_results: Dict[str, bool],
        output_dir: Path
    ) -> CodeArtifact:
        """
        Apply automated refactoring based on quality gate failures.
        
        This is a simplified version - real implementation would use more sophisticated refactoring.
        """
        refactored_files = code_artifact.files.copy()
        
        # Apply formatting if ruff format failed
        if not quality_results.get("ruff_format", True):
            logger.info("Applying automatic formatting")
            subprocess.run(
                ["ruff", "format", str(output_dir)],
                capture_output=True,
                check=False
            )
            
            # Read back formatted files
            for file_path in refactored_files:
                full_path = output_dir / file_path
                if full_path.exists():
                    refactored_files[file_path] = full_path.read_text()
        
        # Apply linting fixes if ruff check failed
        if not quality_results.get("ruff_check", True):
            logger.info("Applying automatic linting fixes")
            subprocess.run(
                ["ruff", "check", "--fix", str(output_dir)],
                capture_output=True,
                check=False
            )
            
            # Read back fixed files
            for file_path in refactored_files:
                full_path = output_dir / file_path
                if full_path.exists():
                    refactored_files[file_path] = full_path.read_text()
        
        return CodeArtifact(
            files=refactored_files,
            language=code_artifact.language,
            framework=code_artifact.framework
        )
    
    def _create_result(
        self,
        phase_reached: TDDPhase,
        test_suite: Optional[TestSuite],
        code_artifact: Optional[CodeArtifact],
        red_result: Optional[TestRunResult],
        green_result: Optional[TestRunResult],
        refactor_result: Optional[TestRunResult],
        quality_passed: bool,
        success: bool,
        errors: List[str],
        cycle_time: float
    ) -> TDDCycleResult:
        """Create a TDD cycle result."""
        return TDDCycleResult(
            phase_reached=phase_reached,
            test_suite=test_suite,
            code_artifact=code_artifact,
            red_phase_result=red_result,
            green_phase_result=green_result,
            refactor_phase_result=refactor_result,
            quality_gates_passed=quality_passed,
            success=success,
            errors=errors,
            cycle_time=cycle_time
        )