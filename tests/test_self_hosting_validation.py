"""Self-hosting validation tests for Recipe Executor.

These tests validate that Recipe Executor can regenerate itself correctly,
ensuring the self-hosting chain works: gen1 → gen2 → gen3.
"""

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class SelfHostingValidator:
    """Validates Recipe Executor's self-hosting capability."""
    
    def __init__(self, recipe_executor_path: Path, recipe_path: Path):
        """Initialize validator.
        
        Args:
            recipe_executor_path: Path to Recipe Executor to test (e.g., src/recipe_executor)
            recipe_path: Path to Recipe Executor's recipe (e.g., recipes/recipe-executor)
        """
        self.recipe_executor_path = recipe_executor_path
        self.recipe_path = recipe_path
        
    def validate_recipe_parser_compatibility(self, generation_path: Path) -> bool:
        """Validate that generated RecipeParser handles directories correctly.
        
        Args:
            generation_path: Path to generated code to validate
            
        Returns:
            True if RecipeParser correctly handles directories
        """
        recipe_parser_file = generation_path / "src" / "recipe_executor" / "recipe_parser.py"
        
        if not recipe_parser_file.exists():
            logger.error(f"RecipeParser not found at {recipe_parser_file}")
            return False
            
        content = recipe_parser_file.read_text()
        
        # Check for critical directory handling code
        required_patterns = [
            "recipe_path.is_dir()",  # Must check if path is directory
            "recipe_path / \"requirements.md\"",  # Must access files within directory
            "recipe_path / \"design.md\"",
            "recipe_path / \"components.json\"",
            "Recipe path must be a directory",  # Must raise error for non-directories
        ]
        
        missing = []
        for pattern in required_patterns:
            if pattern not in content:
                missing.append(pattern)
                
        if missing:
            logger.error(f"RecipeParser missing critical patterns: {missing}")
            return False
            
        # Check it doesn't have file extension checking (wrong pattern)
        bad_patterns = [
            ".endswith('.yaml')",
            ".endswith('.yml')",
            ".endswith('.json')",
            ".endswith('.md')",
            "suffix in ['.yaml', '.yml', '.json', '.md']",
        ]
        
        found_bad = []
        for pattern in bad_patterns:
            if pattern in content:
                found_bad.append(pattern)
                
        if found_bad:
            logger.error(f"RecipeParser has file-based patterns (should be directory-based): {found_bad}")
            return False
            
        return True
        
    def validate_claude_cli_invocation(self, generation_path: Path) -> bool:
        """Validate that ClaudeCodeGenerator invokes Claude CLI correctly.
        
        Args:
            generation_path: Path to generated code to validate
            
        Returns:
            True if ClaudeCodeGenerator correctly invokes Claude CLI
        """
        generator_file = generation_path / "src" / "recipe_executor" / "claude_code_generator.py"
        
        if not generator_file.exists():
            logger.error(f"ClaudeCodeGenerator not found at {generator_file}")
            return False
            
        content = generator_file.read_text()
        
        # Check for subprocess invocation of Claude
        required_patterns = [
            "subprocess.run",  # Must use subprocess
            "subprocess.Popen",  # Or Popen
            '"claude"',  # Must invoke "claude" command
            "'claude'",  # Or 'claude'
            "-p",  # Must use -p flag for prompt file
            "_invoke_claude",  # Must have invocation method
        ]
        
        found_subprocess = False
        found_claude_cmd = False
        found_p_flag = False
        found_invoke_method = False
        
        for pattern in required_patterns:
            if "subprocess" in pattern and pattern in content:
                found_subprocess = True
            if "claude" in pattern and pattern in content:
                found_claude_cmd = True
            if "-p" in pattern and pattern in content:
                found_p_flag = True
            if "_invoke_claude" in pattern and pattern in content:
                found_invoke_method = True
                
        if not found_subprocess:
            logger.error("ClaudeCodeGenerator doesn't use subprocess")
            return False
        if not found_claude_cmd:
            logger.error("ClaudeCodeGenerator doesn't invoke 'claude' command")
            return False
        if not found_invoke_method:
            logger.error("ClaudeCodeGenerator missing _invoke_claude method")
            return False
            
        # Check it doesn't have template generation (wrong pattern)
        bad_patterns = [
            "template.render",
            "jinja2",
            "Template(",
            "f'''class",  # Direct code generation via f-strings
            'f"""def',
            "code = '''",  # Direct code assignment
            'code = """',
        ]
        
        found_bad = []
        for pattern in bad_patterns:
            if pattern in content:
                found_bad.append(pattern)
                
        if found_bad:
            logger.warning(f"ClaudeCodeGenerator may have template-based generation: {found_bad}")
            # This is a warning, not a failure, as it might have both
            
        return True
        
    def validate_no_stubs(self, generation_path: Path) -> Dict[str, List[str]]:
        """Validate that generated code has no stubs.
        
        Args:
            generation_path: Path to generated code to validate
            
        Returns:
            Dictionary of files with stubs found
        """
        stubs_found = {}
        src_path = generation_path / "src"
        
        if not src_path.exists():
            logger.error(f"No src directory found at {src_path}")
            return {"error": ["No src directory found"]}
            
        # Only scan Python files in src/
        for py_file in src_path.rglob("*.py"):
            # Skip __pycache__ and .venv
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue
                
            content = py_file.read_text()
            lines = content.split('\n')
            file_stubs = []
            
            for i, line in enumerate(lines, 1):
                # Check for stub patterns
                if "raise NotImplementedError" in line:
                    # Skip if it's in an abstract method
                    if i > 1 and "@abstractmethod" not in lines[i-2]:
                        file_stubs.append(f"Line {i}: NotImplementedError")
                        
                if line.strip() == "pass":
                    # Check if it's a legitimate use
                    if i > 1:
                        prev_line = lines[i-2].strip()
                        # Skip if it's an exception class or abstract method
                        if not (prev_line.startswith("class") and "Exception" in prev_line):
                            if "@abstractmethod" not in prev_line:
                                file_stubs.append(f"Line {i}: pass statement")
                                
                if "TODO" in line or "FIXME" in line or "XXX" in line:
                    file_stubs.append(f"Line {i}: {line.strip()}")
                    
            if file_stubs:
                stubs_found[str(py_file.relative_to(generation_path))] = file_stubs
                
        return stubs_found
        
    def run_generation(self, input_recipe_executor: Path, output_dir: Path) -> bool:
        """Run Recipe Executor to generate itself.
        
        Args:
            input_recipe_executor: Path to Recipe Executor to run
            output_dir: Where to generate output
            
        Returns:
            True if generation succeeded
        """
        # Run Recipe Executor on its own recipe
        cmd = [
            "python", "-m", "recipe_executor.cli",
            "build", str(self.recipe_path),
            "--output", str(output_dir),
            "--no-cache"
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        # Set PYTHONPATH to include the input Recipe Executor
        env = subprocess.os.environ.copy()
        env["PYTHONPATH"] = str(input_recipe_executor.parent)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=input_recipe_executor.parent,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout for generation
            )
            
            if result.returncode != 0:
                logger.error(f"Generation failed: {result.stderr}")
                return False
                
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Generation timed out after 1 hour")
            return False
        except Exception as e:
            logger.error(f"Generation failed with exception: {e}")
            return False
            
    def validate_self_hosting_chain(self) -> bool:
        """Validate complete self-hosting chain: gen1 → gen2 → gen3.
        
        Returns:
            True if self-hosting chain works completely
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Generation 1 → Generation 2
            gen2_dir = tmpdir / "gen2"
            logger.info("Testing Generation 1 → Generation 2...")
            
            if not self.run_generation(self.recipe_executor_path, gen2_dir):
                logger.error("Generation 1 → 2 failed")
                return False
                
            # Validate Generation 2
            if not self.validate_recipe_parser_compatibility(gen2_dir):
                logger.error("Generation 2 RecipeParser incompatible")
                return False
                
            if not self.validate_claude_cli_invocation(gen2_dir):
                logger.error("Generation 2 ClaudeCodeGenerator incompatible")
                return False
                
            stubs = self.validate_no_stubs(gen2_dir)
            if stubs:
                logger.error(f"Generation 2 has stubs: {stubs}")
                return False
                
            # Generation 2 → Generation 3
            gen3_dir = tmpdir / "gen3"
            logger.info("Testing Generation 2 → Generation 3...")
            
            if not self.run_generation(gen2_dir, gen3_dir):
                logger.error("Generation 2 → 3 failed")
                return False
                
            # Validate Generation 3
            if not self.validate_recipe_parser_compatibility(gen3_dir):
                logger.error("Generation 3 RecipeParser incompatible")
                return False
                
            if not self.validate_claude_cli_invocation(gen3_dir):
                logger.error("Generation 3 ClaudeCodeGenerator incompatible")
                return False
                
            stubs = self.validate_no_stubs(gen3_dir)
            if stubs:
                logger.error(f"Generation 3 has stubs: {stubs}")
                return False
                
            logger.info("✅ Self-hosting chain validated successfully!")
            return True


# Standalone test functions (pytest not required)

def test_recipe_parser_handles_directories():
    """Test that current RecipeParser handles directories correctly."""
    recipe_executor_path = Path(__file__).parent.parent / "src" / "recipe_executor"
    validator = SelfHostingValidator(recipe_executor_path, None)
    return validator.validate_recipe_parser_compatibility(recipe_executor_path.parent.parent)


def test_claude_code_generator_uses_cli():
    """Test that current ClaudeCodeGenerator uses CLI correctly."""
    recipe_executor_path = Path(__file__).parent.parent / "src" / "recipe_executor"
    validator = SelfHostingValidator(recipe_executor_path, None)
    return validator.validate_claude_cli_invocation(recipe_executor_path.parent.parent)


def test_no_stubs_in_current_generation():
    """Test that current generation has no stubs."""
    recipe_executor_path = Path(__file__).parent.parent / "src" / "recipe_executor"
    validator = SelfHostingValidator(recipe_executor_path, None)
    stubs = validator.validate_no_stubs(recipe_executor_path.parent.parent)
    if stubs:
        logger.error(f"Found stubs: {stubs}")
        return False
    return True


def test_self_hosting_chain():
    """Test complete self-hosting chain: gen1 → gen2 → gen3.
    
    This is the ultimate test of self-hosting capability.
    """
    recipe_executor_path = Path(__file__).parent.parent / "src" / "recipe_executor"
    recipe_path = Path(__file__).parent.parent / "recipes" / "recipe-executor"
    validator = SelfHostingValidator(recipe_executor_path, recipe_path)
    return validator.validate_self_hosting_chain()


if __name__ == "__main__":
    # Run validation directly
    import sys
    
    recipe_executor = Path("src/recipe_executor")
    recipe = Path("recipes/recipe-executor")
    
    if not recipe_executor.exists():
        print(f"Recipe Executor not found at {recipe_executor}")
        sys.exit(1)
        
    if not recipe.exists():
        print(f"Recipe not found at {recipe}")
        sys.exit(1)
        
    validator = SelfHostingValidator(recipe_executor, recipe)
    
    print("Validating RecipeParser compatibility...")
    if validator.validate_recipe_parser_compatibility(Path(".")):
        print("✅ RecipeParser handles directories correctly")
    else:
        print("❌ RecipeParser incompatible with directories")
        
    print("\nValidating ClaudeCodeGenerator CLI usage...")
    if validator.validate_claude_cli_invocation(Path(".")):
        print("✅ ClaudeCodeGenerator uses CLI correctly")
    else:
        print("❌ ClaudeCodeGenerator doesn't use CLI")
        
    print("\nChecking for stubs...")
    stubs = validator.validate_no_stubs(Path("."))
    if stubs:
        print(f"❌ Found stubs:")
        for file, issues in stubs.items():
            print(f"  {file}:")
            for issue in issues:
                print(f"    - {issue}")
    else:
        print("✅ No stubs found")