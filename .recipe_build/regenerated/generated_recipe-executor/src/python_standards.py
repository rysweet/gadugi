"""Python coding standards enforcement."""

import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple


class PythonStandards:
    """Enforces Python coding standards for generated code."""
    
    def __init__(self):
        """Initialize standards configuration."""
        self.use_uv = True
        self.use_ruff = True
        self.use_pyright = True
        self.pyright_strict = True
        
    def format_code_with_ruff(self, code: str) -> str:
        """Format Python code using ruff.
        
        Args:
            code: Python code to format
            
        Returns:
            Formatted code
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Run ruff format
            cmd = ["ruff", "format", temp_path]
            if self.use_uv:
                cmd = ["uv", "run"] + cmd
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Read formatted code
            with open(temp_path, 'r') as f:
                formatted_code = f.read()
            
            return formatted_code
            
        except Exception:
            # Return original if formatting fails
            return code
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def check_code_with_pyright(self, code: str, module_name: str = "temp") -> Tuple[bool, List[str]]:
        """Check Python code with pyright for type errors.
        
        Args:
            code: Python code to check
            module_name: Module name for the code
            
        Returns:
            Tuple of (success, list of errors)
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write code
            code_file = Path(temp_dir) / f"{module_name}.py"
            code_file.write_text(code)
            
            # Write pyrightconfig.json
            config_file = Path(temp_dir) / "pyrightconfig.json"
            config_file.write_text(self.get_pyrightconfig_template())
            
            # Run pyright
            cmd = ["pyright", str(code_file)]
            if self.use_uv:
                cmd = ["uv", "run"] + cmd
            
            result = subprocess.run(
                cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse errors
            errors = []
            if result.returncode != 0:
                for line in result.stdout.split('\n'):
                    if 'error:' in line:
                        errors.append(line.strip())
            
            return result.returncode == 0, errors
    
    def get_pyrightconfig_template(self) -> str:
        """Get pyright configuration template.
        
        Returns:
            JSON configuration for pyright
        """
        config = {
            "include": ["**/*.py"],
            "exclude": ["**/node_modules", "**/__pycache__"],
            "typeCheckingMode": "strict" if self.pyright_strict else "standard",
            "pythonVersion": "3.8",
            "reportMissingImports": True,
            "reportMissingTypeStubs": False,
            "reportUnusedImport": True,
            "reportUnusedClass": True,
            "reportUnusedFunction": True,
            "reportUnusedVariable": True,
            "reportDuplicateImport": True,
            "reportIncompatibleMethodOverride": True,
            "reportIncompatibleVariableOverride": True,
            "reportInconsistentConstructor": True,
            "reportMissingParameterType": True,
            "reportMissingReturnType": True,
            "reportUnnecessaryIsInstance": True,
            "reportUnnecessaryCast": True,
            "reportUnnecessaryComparison": True,
            "reportUnnecessaryContains": True,
            "reportUnnecessaryTypeIgnoreComment": True
        }
        
        import json
        return json.dumps(config, indent=2)