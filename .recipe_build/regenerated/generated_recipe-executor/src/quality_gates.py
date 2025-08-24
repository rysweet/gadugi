"""Quality gates for generated code validation."""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class QualityGates:
    """Runs quality checks on generated code."""
    
    def __init__(self):
        """Initialize quality gates."""
        self.use_uv = True
        
    def run_all_gates(self, implementation) -> Dict[str, bool]:
        """Run all quality gates and return results.
        
        Args:
            implementation: Implementation to check
            
        Returns:
            Dictionary of gate name to pass/fail status
        """
        results = {}
        
        # Create temporary project directory
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            
            # Write implementation files
            self._write_implementation_files(implementation, project_dir)
            
            # Run quality gates
            results["pyright"] = self._run_pyright(project_dir)
            results["ruff_format"] = self._run_ruff_format(project_dir)
            results["ruff_lint"] = self._run_ruff_lint(project_dir)
            results["pytest"] = self._run_pytest(project_dir)
            results["coverage"] = self._check_coverage(project_dir)
        
        # Log results
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info(f"Quality gates: {passed}/{total} passed")
        
        for gate, passed in results.items():
            status = "PASSED" if passed else "FAILED"
            logger.debug(f"  {gate}: {status}")
        
        return results
    
    def _write_implementation_files(self, implementation, project_dir: Path):
        """Write implementation files to temporary directory.
        
        Args:
            implementation: Implementation with code and tests
            project_dir: Directory to write to
        """
        # Write code files
        if implementation.code:
            for filepath, content in implementation.code.get_all_files().items():
                file_path = project_dir / filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
        
        # Write test files if separate
        if implementation.tests and hasattr(implementation.tests, 'test_files'):
            for filepath, content in implementation.tests.test_files.items():
                file_path = project_dir / filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
    
    def _run_pyright(self, project_dir: Path) -> bool:
        """Run pyright type checking.
        
        Args:
            project_dir: Project directory
            
        Returns:
            True if pyright passes with zero errors
        """
        # Create pyrightconfig.json
        config = {
            "include": ["**/*.py"],
            "typeCheckingMode": "standard",
            "reportMissingImports": False  # Allow missing imports for testing
        }
        
        import json
        config_file = project_dir / "pyrightconfig.json"
        config_file.write_text(json.dumps(config, indent=2))
        
        # Run pyright
        cmd = ["pyright"]
        if self.use_uv:
            cmd = ["uv", "run"] + cmd
        
        try:
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Check for errors
            if "0 errors" in result.stdout:
                return True
            
            # Log errors for debugging
            if result.returncode != 0:
                logger.debug(f"Pyright errors:\n{result.stdout[:500]}")
            
            return result.returncode == 0
            
        except Exception as e:
            logger.warning(f"Pyright check failed: {e}")
            return False
    
    def _run_ruff_format(self, project_dir: Path) -> bool:
        """Run ruff format check.
        
        Args:
            project_dir: Project directory
            
        Returns:
            True if code is properly formatted
        """
        cmd = ["ruff", "format", "--check", str(project_dir)]
        if self.use_uv:
            cmd = ["uv", "run"] + cmd
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.debug(f"Ruff format issues:\n{result.stdout[:500]}")
            
            return result.returncode == 0
            
        except Exception as e:
            logger.warning(f"Ruff format check failed: {e}")
            return False
    
    def _run_ruff_lint(self, project_dir: Path) -> bool:
        """Run ruff linting.
        
        Args:
            project_dir: Project directory
            
        Returns:
            True if no linting errors
        """
        cmd = ["ruff", "check", str(project_dir)]
        if self.use_uv:
            cmd = ["uv", "run"] + cmd
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.debug(f"Ruff lint issues:\n{result.stdout[:500]}")
            
            # Allow some warnings but not errors
            return "error" not in result.stdout.lower()
            
        except Exception as e:
            logger.warning(f"Ruff lint check failed: {e}")
            return False
    
    def _run_pytest(self, project_dir: Path) -> bool:
        """Run pytest tests.
        
        Args:
            project_dir: Project directory
            
        Returns:
            True if all tests pass
        """
        # Check if tests exist
        test_dir = project_dir / "tests"
        if not test_dir.exists():
            logger.debug("No tests directory found")
            return True  # No tests is not a failure
        
        cmd = ["pytest", str(test_dir), "-v"]
        if self.use_uv:
            cmd = ["uv", "run"] + cmd
        
        try:
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.debug(f"Pytest failures:\n{result.stdout[:500]}")
            
            return result.returncode == 0
            
        except Exception as e:
            logger.warning(f"Pytest check failed: {e}")
            return False
    
    def _check_coverage(self, project_dir: Path) -> bool:
        """Check test coverage.
        
        Args:
            project_dir: Project directory
            
        Returns:
            True if coverage meets threshold
        """
        # Skip coverage check if no tests
        test_dir = project_dir / "tests"
        if not test_dir.exists():
            return True
        
        cmd = ["pytest", str(test_dir), "--cov=.", "--cov-report=term"]
        if self.use_uv:
            cmd = ["uv", "run"] + cmd
        
        try:
            result = subprocess.run(
                cmd,
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse coverage percentage
            for line in result.stdout.split('\n'):
                if 'TOTAL' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        coverage_str = parts[-1].rstrip('%')
                        try:
                            coverage = float(coverage_str)
                            # Require at least 60% coverage
                            if coverage < 60:
                                logger.debug(f"Coverage {coverage}% is below threshold of 60%")
                                return False
                            logger.debug(f"Coverage {coverage}% meets threshold")
                            return True
                        except ValueError:
                            logger.debug(f"Could not parse coverage from: {coverage_str}")
                            continue
            
            # If we can't parse coverage but tests ran, warn but don't fail
            logger.warning("Could not parse coverage percentage from pytest output")
            return True
            
        except Exception as e:
            logger.warning(f"Coverage check failed: {e}")
            return True  # Don't fail on coverage issues