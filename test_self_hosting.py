#!/usr/bin/env python3
"""Test Recipe Executor's self-hosting capability with all fixes applied.

This script runs a complete self-hosting test:
1. Generation 1 (current) creates Generation 2
2. Generation 2 creates Generation 3
3. Validates that Generation 3 is functional
"""

import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('self_hosting_test.log')
    ]
)
logger = logging.getLogger(__name__)


def run_generation(recipe_executor_path: Path, recipe_path: Path, output_dir: Path, generation_name: str) -> bool:
    """Run Recipe Executor to generate itself.
    
    Args:
        recipe_executor_path: Path to Recipe Executor module (e.g., src/recipe_executor)
        recipe_path: Path to recipe directory (e.g., recipes/recipe-executor)
        output_dir: Where to generate output
        generation_name: Name for logging (e.g., "Generation 2")
    
    Returns:
        True if generation succeeded
    """
    logger.info(f"Starting {generation_name}...")
    logger.info(f"  Recipe Executor: {recipe_executor_path}")
    logger.info(f"  Recipe: {recipe_path}")
    logger.info(f"  Output: {output_dir}")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run Recipe Executor on its own recipe
    cmd = [
        sys.executable, "-m", "src.recipe_executor",
        "execute", str(recipe_path),
        "--output-dir", str(output_dir),
        "--force",
        "--verbose"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Set PYTHONPATH to include the project root
    env = subprocess.os.environ.copy()
    # For gen1, we need the project root
    if "src" in str(recipe_executor_path):
        env["PYTHONPATH"] = str(recipe_executor_path.parent.parent)  # Go up to project root
    else:
        env["PYTHONPATH"] = str(recipe_executor_path.parent)
    
    # Also set CLAUDE_MODEL if not already set
    if "CLAUDE_MODEL" not in env:
        env["CLAUDE_MODEL"] = "opus"
    
    # Run with a log file for this generation
    log_file = output_dir.parent / f"{generation_name.lower().replace(' ', '_')}.log"
    
    try:
        with open(log_file, 'w') as log:
            # Set working directory to project root for proper imports
            if "src" in str(recipe_executor_path):
                cwd = recipe_executor_path.parent.parent  # Project root
            else:
                cwd = recipe_executor_path.parent
                
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=7200  # 2 hour timeout for generation
            )
        
        if result.returncode != 0:
            logger.error(f"{generation_name} failed with exit code {result.returncode}")
            logger.error(f"Check log file: {log_file}")
            return False
        
        logger.info(f"{generation_name} completed successfully")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"{generation_name} timed out after 2 hours")
        return False
    except Exception as e:
        logger.error(f"{generation_name} failed with exception: {e}")
        return False


def validate_generation(generation_path: Path, generation_name: str) -> bool:
    """Validate that a generation is functional.
    
    Args:
        generation_path: Path to generated code
        generation_name: Name for logging
    
    Returns:
        True if generation is valid
    """
    logger.info(f"Validating {generation_name}...")
    
    # Check critical files exist
    required_files = [
        generation_path / "src" / "recipe_executor" / "__init__.py",
        generation_path / "src" / "recipe_executor" / "cli.py",
        generation_path / "src" / "recipe_executor" / "recipe_parser.py",
        generation_path / "src" / "recipe_executor" / "claude_code_generator.py",
    ]
    
    for file in required_files:
        if not file.exists():
            logger.error(f"Missing required file: {file}")
            return False
    
    # Check RecipeParser has directory checking
    parser_file = generation_path / "src" / "recipe_executor" / "recipe_parser.py"
    content = parser_file.read_text()
    
    if "is_dir()" not in content:
        logger.error(f"{generation_name} RecipeParser doesn't check for directories")
        return False
    
    if "Recipe path must be a directory" not in content:
        logger.error(f"{generation_name} RecipeParser doesn't have proper error message")
        return False
    
    # Check ClaudeCodeGenerator uses subprocess
    generator_file = generation_path / "src" / "recipe_executor" / "claude_code_generator.py"
    content = generator_file.read_text()
    
    if "subprocess.run" not in content and "subprocess.Popen" not in content:
        logger.error(f"{generation_name} ClaudeCodeGenerator doesn't use subprocess")
        return False
    
    if "_invoke_claude" not in content:
        logger.error(f"{generation_name} ClaudeCodeGenerator missing _invoke_claude method")
        return False
    
    # Check for stubs (basic check)
    stub_count = 0
    for py_file in (generation_path / "src").rglob("*.py"):
        content = py_file.read_text()
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if "raise NotImplementedError" in line:
                # Skip if it's in an abstract method
                if i > 1 and "@abstractmethod" not in lines[i-2]:
                    stub_count += 1
                    logger.warning(f"Stub found in {py_file.relative_to(generation_path)}:{i}")
            
            if line.strip() == "pass":
                # Check if it's a legitimate use
                if i > 1:
                    prev_line = lines[i-2].strip()
                    if not (prev_line.startswith("class") and "Exception" in prev_line):
                        if "@abstractmethod" not in prev_line:
                            stub_count += 1
                            logger.warning(f"Pass stub in {py_file.relative_to(generation_path)}:{i}")
    
    if stub_count > 10:  # Allow a few stubs but not many
        logger.error(f"{generation_name} has too many stubs: {stub_count}")
        return False
    
    logger.info(f"{generation_name} validation passed (stubs found: {stub_count})")
    return True


def main():
    """Run complete self-hosting test."""
    logger.info("=" * 80)
    logger.info("Recipe Executor Self-Hosting Test")
    logger.info("=" * 80)
    
    # Paths
    recipe_executor_gen1 = Path("src/recipe_executor")
    recipe_path = Path("recipes/recipe-executor")
    
    if not recipe_executor_gen1.exists():
        logger.error(f"Recipe Executor not found at {recipe_executor_gen1}")
        return 1
    
    if not recipe_path.exists():
        logger.error(f"Recipe not found at {recipe_path}")
        return 1
    
    # Create temporary directory for test
    test_dir = Path(".recipe_build") / f"self_host_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Test directory: {test_dir}")
    
    # Generation 1 → Generation 2
    gen2_dir = test_dir / "gen2"
    if not run_generation(recipe_executor_gen1, recipe_path, gen2_dir, "Generation 1 → 2"):
        logger.error("Generation 1 → 2 failed")
        return 1
    
    if not validate_generation(gen2_dir, "Generation 2"):
        logger.error("Generation 2 validation failed")
        return 1
    
    # Generation 2 → Generation 3
    gen3_dir = test_dir / "gen3"
    gen2_executor = gen2_dir / "src" / "recipe_executor"
    
    if not run_generation(gen2_executor, recipe_path, gen3_dir, "Generation 2 → 3"):
        logger.error("Generation 2 → 3 failed")
        return 1
    
    if not validate_generation(gen3_dir, "Generation 3"):
        logger.error("Generation 3 validation failed")
        return 1
    
    # Success!
    logger.info("=" * 80)
    logger.info("✅ SELF-HOSTING TEST PASSED!")
    logger.info("✅ Generation 1 → Generation 2 → Generation 3 successful")
    logger.info(f"✅ Test artifacts saved in: {test_dir}")
    logger.info("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())