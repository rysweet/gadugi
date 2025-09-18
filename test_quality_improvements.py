#!/usr/bin/env python3
"""Test the Recipe Executor quality improvements for Python 3.9 compatibility."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.recipe_executor.cli import main as execute_recipe_cli
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_small_component():
    """Test generation of a small component with quality requirements."""
    
    logger.info("=" * 60)
    logger.info("Testing Recipe Executor with Quality Improvements")
    logger.info("Target: Python 3.9 compatibility")
    logger.info("=" * 60)
    
    # Use the validator recipe as a small test case
    recipe_path = Path("recipes/validation-service")
    output_dir = Path(".recipe_build/quality_test")
    
    # Clean output directory
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Recipe: {recipe_path}")
    logger.info(f"Output: {output_dir}")
    
    try:
        # Execute the recipe with quality iteration enabled
        result = subprocess.run(
            ["python", "-m", "src.recipe_executor", "execute", 
             str(recipe_path), "--output-dir", str(output_dir),
             "--force", "--verbose"],
            capture_output=True,
            text=True
        )
        
        logger.info("Recipe execution completed")
        
        # Check if generated files exist
        src_dir = output_dir / "src" / "recipe_executor"
        if src_dir.exists():
            py_files = list(src_dir.glob("*.py"))
            logger.info(f"Generated {len(py_files)} Python files")
            
            # Run quality checks
            import subprocess
            
            # Check with pyright for Python 3.9
            logger.info("\nRunning pyright check (Python 3.9)...")
            pyright_result = subprocess.run(
                ["uv", "run", "pyright", str(src_dir), "--pythonversion", "3.9"],
                capture_output=True,
                text=True
            )
            
            if pyright_result.returncode == 0:
                logger.info("✅ Pyright check PASSED for Python 3.9")
            else:
                logger.error(f"❌ Pyright check FAILED")
                # Show first few errors
                lines = pyright_result.stdout.split('\n')
                for line in lines[:10]:
                    if 'error:' in line:
                        logger.error(f"  {line}")
            
            # Check with ruff
            logger.info("\nRunning ruff check...")
            ruff_result = subprocess.run(
                ["uv", "run", "ruff", "check", str(src_dir)],
                capture_output=True,
                text=True
            )
            
            if ruff_result.returncode == 0:
                logger.info("✅ Ruff check PASSED")
            else:
                logger.error(f"❌ Ruff check FAILED")
                logger.error(ruff_result.stdout[:500])
            
            # Check for Python 3.10+ syntax
            logger.info("\nChecking for Python 3.10+ syntax...")
            found_issues = False
            for py_file in py_files:
                content = py_file.read_text()
                if ' | ' in content and 'Optional[' not in content:
                    logger.error(f"❌ Found Python 3.10+ union syntax in {py_file.name}")
                    found_issues = True
                if 'match ' in content:
                    logger.error(f"❌ Found match/case statement in {py_file.name}")
                    found_issues = True
            
            if not found_issues:
                logger.info("✅ No Python 3.10+ syntax found")
                
        else:
            logger.error("No source files generated")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_small_component()
    sys.exit(0 if success else 1)