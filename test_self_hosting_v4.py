#!/usr/bin/env python3
"""Self-hosting test v4 with Python 3.9 quality improvements."""

import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'.recipe_build/self_host_test_v4_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


def run_self_hosting_test():
    """Run Recipe Executor self-hosting test with quality improvements."""
    
    logger.info("=" * 60)
    logger.info("RECIPE EXECUTOR SELF-HOSTING TEST V4")
    logger.info("With Python 3.9 Quality Improvements")
    logger.info("=" * 60)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_dir = Path(f".recipe_build/self_host_test_v4_{timestamp}")
    
    # Generation 1: Use current Recipe Executor to generate Generation 2
    gen2_dir = test_dir / "gen2"
    gen2_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("\n" + "=" * 60)
    logger.info("GENERATION 1 → 2: Using current Recipe Executor")
    logger.info("=" * 60)
    logger.info(f"Source: {Path.cwd()}")
    logger.info(f"Output: {gen2_dir}")
    
    # Run with quality iteration enabled
    cmd = [
        sys.executable, "-m", "src.recipe_executor",
        "execute", "recipes/recipe-executor",
        "--output-dir", str(gen2_dir),
        "--force",
        "--verbose"
    ]
    
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info("Quality gate iteration is ENABLED by default")
    
    start_time = time.time()
    result = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Monitor output
    component_stats = {}
    current_component = None
    iteration_count = 0
    files_created = 0
    
    logger.info("\nMonitoring Generation 1 execution...")
    
    for line in result.stdout:
        line = line.strip()
        
        # Track component processing
        if "Recipe " in line and ": " in line:
            parts = line.split("Recipe ")
            if len(parts) > 1:
                comp_parts = parts[1].split(":")
                if comp_parts:
                    current_component = comp_parts[0].strip()
                    logger.info(f"  📦 Component: {current_component}")
        
        # Track iterations
        if "Iteration" in line and "for" in line:
            iteration_count += 1
            logger.info(f"    Iteration {iteration_count} for {current_component}")
        
        # Track file creation
        if "Created:" in line or "creating file:" in line:
            files_created += 1
        
        # Track quality gate results
        if "quality gates" in line.lower():
            logger.info(f"    🔍 Quality gates checking for {current_component}")
        
        if "INFO: Code generation successful" in line:
            logger.info(f"  ✅ {line}")
        
        if "WARNING:" in line and "stubs" in line:
            logger.warning(f"  ⚠️  {line}")
        
        if "ERROR:" in line:
            logger.error(f"  ❌ {line}")
        
        # Log progress periodically
        if files_created > 0 and files_created % 10 == 0:
            logger.info(f"  Progress: {files_created} Python files created")
    
    result.wait()
    elapsed_time = time.time() - start_time
    
    if result.returncode == 0:
        logger.info(f"\n✅ Generation 1 completed successfully in {elapsed_time:.1f}s")
        logger.info(f"  Total files created: {files_created}")
        logger.info(f"  Total iterations: {iteration_count}")
    else:
        logger.error(f"\n❌ Generation 1 failed with exit code {result.returncode}")
        return False
    
    # Analyze generated code quality
    logger.info("\n" + "=" * 60)
    logger.info("QUALITY ANALYSIS OF GENERATED CODE")
    logger.info("=" * 60)
    
    # Count actual source files (excluding .venv)
    src_files = list((gen2_dir / "src").rglob("*.py")) if (gen2_dir / "src").exists() else []
    src_files = [f for f in src_files if ".venv" not in str(f)]
    logger.info(f"Generated {len(src_files)} source files (excluding .venv)")
    
    # Run pyright check with Python 3.9
    logger.info("\nRunning pyright with Python 3.9...")
    pyright_result = subprocess.run(
        ["uv", "run", "pyright", str(gen2_dir / "src"), "--pythonversion", "3.9"],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd())
    )
    
    # Parse pyright output
    pyright_lines = pyright_result.stdout.split('\n')
    error_count = 0
    warning_count = 0
    
    for line in pyright_lines:
        if " error:" in line:
            error_count += 1
            if error_count <= 5:  # Show first 5 errors
                logger.error(f"  Pyright error: {line.strip()}")
        elif " warning:" in line:
            warning_count += 1
    
    if error_count == 0:
        logger.info(f"✅ Pyright: PASSED (0 errors, {warning_count} warnings)")
    else:
        logger.error(f"❌ Pyright: {error_count} errors, {warning_count} warnings")
    
    # Check for Python 3.10+ syntax
    logger.info("\nChecking for Python 3.10+ syntax...")
    py310_issues = 0
    for src_file in src_files[:10]:  # Check first 10 files
        content = src_file.read_text()
        if ' | None' in content or '| None' in content:
            logger.error(f"  ❌ Python 3.10+ union syntax in {src_file.name}")
            py310_issues += 1
        if 'match ' in content:
            logger.error(f"  ❌ match/case statement in {src_file.name}")
            py310_issues += 1
    
    if py310_issues == 0:
        logger.info("✅ No Python 3.10+ syntax found")
    else:
        logger.error(f"❌ Found {py310_issues} Python 3.10+ syntax issues")
    
    # Run ruff check
    logger.info("\nRunning ruff check...")
    ruff_result = subprocess.run(
        ["uv", "run", "ruff", "check", str(gen2_dir / "src")],
        capture_output=True,
        text=True,
        cwd=str(Path.cwd())
    )
    
    ruff_issues = len([l for l in ruff_result.stdout.split('\n') if l.strip()])
    if ruff_issues == 0:
        logger.info("✅ Ruff: PASSED (0 issues)")
    else:
        logger.warning(f"⚠️  Ruff: {ruff_issues} issues found")
        # Show first few issues
        for line in ruff_result.stdout.split('\n')[:5]:
            if line.strip():
                logger.info(f"  {line.strip()}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    success = (error_count == 0 and py310_issues == 0)
    
    if success:
        logger.info("✅ TEST PASSED: Code is Python 3.9 compatible with quality standards")
    else:
        logger.error("❌ TEST FAILED: Quality issues remain")
    
    logger.info(f"\nResults:")
    logger.info(f"  Files generated: {len(src_files)}")
    logger.info(f"  Pyright errors: {error_count}")
    logger.info(f"  Python 3.10+ syntax: {py310_issues}")
    logger.info(f"  Ruff issues: {ruff_issues}")
    logger.info(f"  Total time: {elapsed_time:.1f}s")
    
    return success


if __name__ == "__main__":
    success = run_self_hosting_test()
    sys.exit(0 if success else 1)