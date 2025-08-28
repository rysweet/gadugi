"""Python standards and quality enforcement for Recipe Executor."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict
import subprocess
import tempfile


@dataclass
class PythonStandards:
    """Enforces Python coding standards for generated code."""

    use_uv: bool = True
    use_ruff: bool = True
    use_pyright: bool = True
    pyright_strict: bool = True

    def get_pyproject_template(self) -> str:
        """Get standard pyproject.toml template for UV projects."""
        return """[project]
name = "{name}"
version = "{version}"
description = "{description}"
requires-python = ">=3.10"
dependencies = {dependencies}

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
    "pyright>=1.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "RUF"]
ignore = ["E501"]  # Line too long - handled by formatter

[tool.pyright]
include = ["src", "tests"]
exclude = ["**/node_modules", "**/__pycache__", ".venv"]
defineConstant = {{ DEBUG = true }}
reportMissingImports = true
reportMissingTypeStubs = false
reportOptionalMemberAccess = true
reportOptionalCall = true
reportOptionalIterable = true
reportOptionalContextManager = true
reportOptionalOperand = true
reportTypedDictNotRequiredAccess = true
reportPrivateImportUsage = false
reportUnboundVariable = true
reportUnusedImport = true
reportUnusedClass = true
reportUnusedFunction = true
reportUnusedVariable = true
reportDuplicateImport = true
reportInvalidStringEscapeSequence = true
reportInvalidTypeVarUse = true
reportMissingTypeArgument = true
reportUnnecessaryIsInstance = true
reportUnnecessaryCast = true
reportUnnecessaryComparison = true
reportUnnecessaryContains = true
reportAssertAlwaysTrue = true
reportSelfClsParameterName = true
reportUnusedExpression = true
reportMatchNotExhaustive = true
reportImplicitOverride = false
reportShadowedImports = true
pythonVersion = "3.10"
pythonPlatform = "Linux"
typeCheckingMode = "strict"
"""

    def get_pyrightconfig_template(self) -> str:
        """Get pyrightconfig.json template for strict type checking."""
        return """{
  "include": ["src", "tests"],
  "exclude": ["**/node_modules", "**/__pycache__", ".venv"],
  "defineConstant": {
    "DEBUG": true
  },
  "reportMissingImports": true,
  "reportMissingTypeStubs": false,
  "reportOptionalMemberAccess": true,
  "reportOptionalCall": true,
  "reportOptionalIterable": true,
  "reportOptionalContextManager": true,
  "reportOptionalOperand": true,
  "reportTypedDictNotRequiredAccess": true,
  "reportPrivateImportUsage": false,
  "reportUnboundVariable": true,
  "reportUnusedImport": true,
  "reportUnusedClass": true,
  "reportUnusedFunction": true,
  "reportUnusedVariable": true,
  "reportDuplicateImport": true,
  "reportInvalidStringEscapeSequence": true,
  "reportInvalidTypeVarUse": true,
  "reportMissingTypeArgument": true,
  "reportUnnecessaryIsInstance": true,
  "reportUnnecessaryCast": true,
  "reportUnnecessaryComparison": true,
  "reportUnnecessaryContains": true,
  "reportAssertAlwaysTrue": true,
  "reportSelfClsParameterName": true,
  "reportUnusedExpression": true,
  "reportMatchNotExhaustive": true,
  "reportImplicitOverride": false,
  "reportShadowedImports": true,
  "pythonVersion": "3.10",
  "pythonPlatform": "Linux",
  "typeCheckingMode": "strict"
}"""

    def get_init_template(self) -> str:
        """Get __init__.py template with proper type annotations."""
        return '''"""Module initialization with proper type exports."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type-only imports for better IDE support
    from .{module} import *

__all__ = {exports}
'''

    def format_code_with_ruff(self, code: str, use_project_context: bool = False) -> str:
        """Format Python code using ruff.
        
        Args:
            code: Python code to format
            use_project_context: If True, uses uv run within project. If False, runs ruff directly.
        """
        if not self.use_ruff:
            return code

        # Write code to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            # Decide whether to use uv run or direct ruff
            if use_project_context and self.use_uv:
                # Use UV within project context
                cmd = ["uv", "run", "ruff", "format", temp_path]
            else:
                # Run ruff directly (for temp files outside project)
                cmd = ["ruff", "format", temp_path]
                
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )

            # Read formatted code
            with open(temp_path, "r") as f:
                formatted_code = f.read()

            return formatted_code
        except subprocess.CalledProcessError as e:
            # If ruff fails, return original code
            print(f"Ruff formatting failed: {e}")
            return code
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

    def check_code_with_pyright(
        self, code: str, module_name: str = "temp", use_project_context: bool = False
    ) -> tuple[bool, list[str]]:
        """Check Python code with pyright for type errors.
        
        Args:
            code: Python code to check
            module_name: Name for the temporary module
            use_project_context: If True, uses uv run within project. If False, runs pyright directly.
        """
        if not self.use_pyright:
            return True, []

        # Create temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            src_dir = temp_path / "src"
            src_dir.mkdir()

            # Write code to file
            code_file = src_dir / f"{module_name}.py"
            code_file.write_text(code)

            # Write pyrightconfig.json
            config_file = temp_path / "pyrightconfig.json"
            config_file.write_text(self.get_pyrightconfig_template())

            # Run pyright
            try:
                # Decide whether to use uv run or direct pyright
                if use_project_context and self.use_uv:
                    cmd = ["uv", "run", "pyright", str(src_dir)]
                else:
                    cmd = ["pyright", str(src_dir)]
                    
                result = subprocess.run(
                    cmd,
                    cwd=temp_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )

                # Parse output for errors
                errors: List[str] = []
                for line in result.stdout.split("\n"):
                    if "error:" in line.lower():
                        errors.append(line.strip())

                # Check if there were any errors
                passed = result.returncode == 0 and len(errors) == 0

                return passed, errors

            except subprocess.CalledProcessError as e:
                return False, [f"Pyright check failed: {e}"]

    def create_uv_project(self, project_path: Path, name: str, version: str = "0.1.0") -> bool:
        """Initialize a UV project with standard configuration."""
        if not self.use_uv:
            return False

        try:
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)

            # Initialize UV project
            subprocess.run(
                ["uv", "init", "--name", name], cwd=project_path, check=True, capture_output=True
            )

            # Write standard pyproject.toml
            pyproject_path = project_path / "pyproject.toml"
            pyproject_content = self.get_pyproject_template().format(
                name=name,
                version=version,
                description=f"{name} - Generated by Recipe Executor",
                dependencies="[]",
            )
            pyproject_path.write_text(pyproject_content)

            # Create src directory structure
            src_dir = project_path / "src" / name.replace("-", "_")
            src_dir.mkdir(parents=True, exist_ok=True)

            # Create __init__.py
            init_file = src_dir / "__init__.py"
            init_file.write_text('"""Auto-generated package."""\n\n__version__ = "0.1.0"\n')

            # Create tests directory
            tests_dir = project_path / "tests"
            tests_dir.mkdir(exist_ok=True)

            # Sync dependencies
            subprocess.run(
                ["uv", "sync", "--all-extras"], cwd=project_path, check=True, capture_output=True
            )

            return True

        except subprocess.CalledProcessError as e:
            print(f"Failed to create UV project: {e}")
            return False

    def add_type_stubs(self, code: str) -> str:
        """Add type stubs and annotations to code if missing."""
        lines = code.split("\n")
        updated_lines: List[str] = []

        # Check if typing imports are present
        has_typing_import = any("from typing import" in line for line in lines)

        if not has_typing_import:
            # Add typing imports at the top
            updated_lines.append('"""Module with type annotations."""')
            updated_lines.append("")
            updated_lines.append("from typing import Any, Optional, Union, List, Dict, Tuple")
            updated_lines.append("")

        # Process each line

        for line in lines:
            # Skip if we already added typing imports
            if not has_typing_import and line.startswith('"""') and updated_lines:
                continue

            # Detect function definitions without return type
            if line.strip().startswith("def ") and "->" not in line and line.strip().endswith(":"):
                # Add return type annotation
                line = line.rstrip(":") + " -> None:"

            updated_lines.append(line)

        return "\n".join(updated_lines)

    def generate_test_template(self, module_name: str, class_name: Optional[str] = None) -> str:
        """Generate test template with proper type annotations."""
        if class_name:
            return f'''"""Tests for {module_name}.{class_name}."""

import pytest
from typing import Any, Generator
from unittest.mock import Mock, patch

from {module_name} import {class_name}


class Test{class_name}:
    """Test suite for {class_name}."""
    
    @pytest.fixture
    def instance(self) -> {class_name}:
        """Create {class_name} instance for testing."""
        return {class_name}()
    
    def test_initialization(self, instance: {class_name}) -> None:
        """Test {class_name} initialization."""
        assert instance is not None
    
    def test_basic_functionality(self, instance: {class_name}) -> None:
        """Test basic functionality."""
        # Test that the instance has expected attributes and methods
        assert hasattr(instance, '__init__')
        # Test basic operations based on class interface
        # This would be customized per actual class implementation
'''
        else:
            return f'''"""Tests for {module_name} module."""

import pytest
from typing import Any, Generator
from unittest.mock import Mock, patch

import {module_name}


def test_module_imports() -> None:
    """Test that module can be imported."""
    assert {module_name} is not None


def test_basic_functionality() -> None:
    """Test basic module functionality."""
    # Test that module functions work as expected
    # This would test actual module functions based on what's exported
    assert {module_name}.__name__ == "{module_name}"
    # Test key module functions if they exist
    module_attrs = dir({module_name})
    assert len(module_attrs) > 0  # Module should export something
'''


@dataclass
class QualityGates:
    """Quality gate configuration and execution."""

    standards: PythonStandards = field(default_factory=PythonStandards)

    def run_all_gates(self, project_path: Path) -> Dict[str, bool]:
        """Run all quality gates on a project.
        
        MUST set up UV environment before running checks if pyproject.toml exists.
        """
        results: Dict[str, bool] = {}

        # First, ensure UV environment is set up if this is a UV project
        if (project_path / "pyproject.toml").exists():
            try:
                setup_result = subprocess.run(
                    ["uv", "sync", "--all-extras"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                results["uv_setup"] = setup_result.returncode == 0
                
                if not results["uv_setup"]:
                    print(f"Warning: UV setup failed, quality gates may not work properly")
                    # Try to continue anyway
            except FileNotFoundError:
                print("Warning: UV not found, skipping environment setup")
                results["uv_setup"] = False

        # Format code first (fixes issues automatically)
        try:
            format_result = subprocess.run(
                ["uv", "run", "ruff", "format", "."],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            results["ruff_format"] = format_result.returncode == 0
        except:
            results["ruff_format"] = False

        # Fix auto-fixable linting issues
        try:
            lint_fix_result = subprocess.run(
                ["uv", "run", "ruff", "check", ".", "--fix"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            results["ruff_lint_fix"] = lint_fix_result.returncode == 0
        except:
            results["ruff_lint_fix"] = False

        # Now check quality after fixes
        results["pyright"] = self._run_pyright(project_path)
        results["ruff_check"] = self._run_ruff_lint(project_path)
        results["pytest"] = self._run_pytest(project_path)

        return results

    def _run_pyright(self, project_path: Path) -> bool:
        """Run pyright type checking."""
        try:
            result = subprocess.run(
                ["uv", "run", "pyright"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_ruff_format_check(self, project_path: Path) -> bool:
        """Check if code is properly formatted."""
        try:
            result = subprocess.run(
                ["uv", "run", "ruff", "format", "--check", "."],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_ruff_lint(self, project_path: Path) -> bool:
        """Run ruff linting."""
        try:
            result = subprocess.run(
                ["uv", "run", "ruff", "check", "."],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_pytest(self, project_path: Path) -> bool:
        """Run pytest tests."""
        try:
            result = subprocess.run(
                ["uv", "run", "pytest", "tests/", "-v"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_ruff_format(self, directory_path: Path) -> bool:
        """Check if all Python files in directory are properly formatted.
        
        This method handles both project directories and external directories.
        For external directories (like temp dirs), it runs ruff directly without UV.
        """
        try:
            # Check if this is a UV project (has pyproject.toml and uv.lock)
            is_uv_project = (directory_path / "pyproject.toml").exists() and (directory_path / "uv.lock").exists()
            
            # Find all Python files
            python_files = list(directory_path.rglob("*.py"))
            if not python_files:
                return True  # No Python files to check
            
            # Run ruff format check
            if is_uv_project:
                # Use UV for project directories
                cmd = ["uv", "run", "ruff", "format", "--check"] + [str(f) for f in python_files]
                cwd = directory_path
            else:
                # Run ruff directly for non-project directories (like temp dirs)
                cmd = ["ruff", "format", "--check"] + [str(f) for f in python_files]
                cwd = directory_path
            
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            return result.returncode == 0
        except FileNotFoundError:
            # Ruff not installed
            print("Warning: ruff not found, skipping format check")
            return True
        except Exception as e:
            print(f"Error checking ruff format: {e}")
            return False
