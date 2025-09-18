#!/usr/bin/env python3
"""
Recipe Executor Self-Hosting Test - With All Fixes Applied

This script tests whether Recipe Executor can regenerate itself from its recipe.
Generation 1 (current) → Generation 2 → Generation 3
Each generation must be able to create the next.
"""

import sys
import os
import subprocess
import shutil
import logging
import time
from pathlib import Path
from datetime import datetime
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("self_hosting_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SelfHostingTest:
    """Test Recipe Executor's ability to regenerate itself."""
    
    def __init__(self):
        """Initialize test environment."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.test_dir = Path(f".recipe_build/self_host_test_{timestamp}")
        self.venv_python = Path(".venv/bin/python").absolute()
        self.recipe_path = Path("recipes/recipe-executor").absolute()
        
    def setup(self):
        """Set up test directories."""
        logger.info("=" * 80)
        logger.info("Recipe Executor Self-Hosting Test - WITH FIXES")
        logger.info("=" * 80)
        logger.info(f"Test directory: {self.test_dir}")
        
        # Create test directory
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create generation directories
        (self.test_dir / "gen2").mkdir(exist_ok=True)
        (self.test_dir / "gen3").mkdir(exist_ok=True)
        
    def monitor_generation(self, process, gen_name, output_dir, timeout=None):
        """Monitor a generation process with real-time updates."""
        start_time = time.time()
        last_file_count = 0
        
        logger.info(f"Monitoring {gen_name} generation...")
        
        while True:
            # Count Python files created
            py_files = list(Path(output_dir).rglob("*.py")) if Path(output_dir).exists() else []
            current_count = len(py_files)
            
            if current_count != last_file_count:
                logger.info(f"  Progress: {current_count} Python files created")
                last_file_count = current_count
            
            # Check if process is still running
            poll = process.poll()
            if poll is not None:
                # Process finished
                elapsed = time.time() - start_time
                logger.info(f"{gen_name} completed in {elapsed:.1f}s with exit code {poll}")
                return poll
            
            # Check timeout (but don't enforce it - just warn)
            if timeout and (time.time() - start_time) > timeout:
                logger.warning(f"{gen_name} exceeded {timeout}s but continuing (no timeout enforcement)...")
                timeout = None  # Don't warn again
            
            time.sleep(5)  # Check every 5 seconds
    
    def validate_generation(self, gen_dir: Path, gen_name: str) -> dict:
        """Validate a generated Recipe Executor."""
        logger.info(f"Validating {gen_name}...")
        results = {
            "name": gen_name,
            "valid": True,
            "py_files": 0,
            "stub_count": 0,
            "import_errors": 0,
            "external_deps": [],
            "issues": []
        }
        
        # Count Python files
        src_dir = gen_dir / "src" / "recipe_executor"
        if not src_dir.exists():
            results["valid"] = False
            results["issues"].append(f"Missing src/recipe_executor directory")
            return results
        
        py_files = list(src_dir.glob("*.py"))
        results["py_files"] = len(py_files)
        logger.info(f"  Found {len(py_files)} Python files")
        
        # Required files (31 total)
        required_files = [
            "__init__.py", "__main__.py", "cli.py",
            "recipe_model.py", "recipe_parser.py", "recipe_validator.py",
            "dependency_resolver.py", "orchestrator.py", "state_manager.py",
            "claude_code_generator.py", "base_generator.py", "test_generator.py",
            "stub_detector.py", "intelligent_stub_detector.py",
            "validator.py", "quality_gates.py", "parallel_builder.py",
            "prompt_loader.py", "pattern_manager.py", "python_standards.py",
            "language_detector.py", "uv_environment.py"
        ]
        
        missing = [f for f in required_files if not (src_dir / f).exists()]
        if missing:
            results["valid"] = False
            results["issues"].append(f"Missing files: {missing}")
            logger.warning(f"  Missing {len(missing)} required files: {missing[:5]}...")
        
        # Check for stubs
        stub_patterns = ["pass$", "raise NotImplementedError", "TODO", "FIXME", "XXX"]
        for py_file in py_files:
            content = py_file.read_text()
            for pattern in stub_patterns:
                if pattern in content:
                    results["stub_count"] += 1
                    break
        
        if results["stub_count"] > 0:
            results["valid"] = False
            results["issues"].append(f"Found {results['stub_count']} files with stubs")
            logger.warning(f"  Found stubs in {results['stub_count']} files")
        
        # Check for external dependencies
        forbidden_imports = ["networkx", "numpy", "pandas", "requests", "sklearn"]
        for py_file in py_files:
            content = py_file.read_text()
            for lib in forbidden_imports:
                if f"import {lib}" in content or f"from {lib}" in content:
                    results["external_deps"].append(lib)
        
        if results["external_deps"]:
            results["valid"] = False
            results["issues"].append(f"External dependencies: {results['external_deps']}")
            logger.warning(f"  Found external dependencies: {results['external_deps']}")
        
        # Check for absolute imports
        for py_file in py_files:
            if py_file.name == "__init__.py":
                continue
            content = py_file.read_text()
            if "from recipe_executor." in content or "import recipe_executor." in content:
                results["import_errors"] += 1
        
        if results["import_errors"] > 0:
            results["valid"] = False
            results["issues"].append(f"Found {results['import_errors']} files with absolute imports")
            logger.warning(f"  Found absolute imports in {results['import_errors']} files")
        
        # Summary
        if results["valid"]:
            logger.info(f"  ✅ {gen_name} is VALID")
        else:
            logger.error(f"  ❌ {gen_name} is INVALID: {'; '.join(results['issues'])}")
        
        return results
    
    def run_generation(self, gen_name: str, source_dir: Path, output_dir: Path) -> bool:
        """Run a generation from source to output."""
        logger.info(f"Starting {gen_name}...")
        logger.info(f"  Recipe Executor: {source_dir}")
        logger.info(f"  Recipe: {self.recipe_path}")
        logger.info(f"  Output: {output_dir}")
        
        # Determine how to run based on source
        if source_dir.name == "recipe_executor" and source_dir.parent.name == "src":
            # Running from main source
            cmd = [
                str(self.venv_python),
                "-m", "src.recipe_executor",
                "execute",
                str(self.recipe_path),
                "--output-dir", str(output_dir),
                "--force",
                "--verbose"
            ]
        else:
            # Running from generated directory
            cmd = [
                str(self.venv_python),
                "-m", "src.recipe_executor",
                "execute",
                str(self.recipe_path),
                "--output-dir", str(output_dir),
                "--force",
                "--verbose"
            ]
            # Change to the source directory for execution
            os.chdir(source_dir)
        
        # Log to file
        log_file = self.test_dir / f"{gen_name.replace(' ', '_').replace('→', 'to')}.log"
        logger.info(f"Running command: {' '.join(cmd)}")
        
        with open(log_file, "w") as log:
            process = subprocess.Popen(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Monitor with NO timeout enforcement
            exit_code = self.monitor_generation(
                process, 
                gen_name, 
                output_dir,
                timeout=7200  # Warn after 2 hours but don't kill
            )
        
        if exit_code != 0:
            logger.error(f"{gen_name} failed with exit code {exit_code}")
            logger.error(f"Check log file: {log_file}")
            
            # Show last few lines of log
            if log_file.exists():
                with open(log_file) as f:
                    lines = f.readlines()
                    logger.error("Last 10 lines of output:")
                    for line in lines[-10:]:
                        logger.error(f"  {line.rstrip()}")
            
            return False
        
        logger.info(f"{gen_name} completed successfully")
        return True
    
    def run_test(self):
        """Run the complete self-hosting test."""
        self.setup()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_dir": str(self.test_dir),
            "generations": []
        }
        
        # Generation 1 → 2
        gen2_dir = self.test_dir / "gen2"
        success = self.run_generation(
            "Generation 1 → 2",
            Path("src/recipe_executor"),
            gen2_dir
        )
        
        if not success:
            logger.error("Generation 1 → 2 failed")
            results["generations"].append({
                "name": "Generation 1 → 2",
                "status": "FAILED",
                "reason": "Execution failed"
            })
            return results
        
        # Validate Generation 2
        gen2_results = self.validate_generation(gen2_dir, "Generation 2")
        results["generations"].append(gen2_results)
        
        if not gen2_results["valid"]:
            logger.error("Generation 2 validation failed")
            return results
        
        # Generation 2 → 3
        gen3_dir = self.test_dir / "gen3"
        success = self.run_generation(
            "Generation 2 → 3",
            gen2_dir,
            gen3_dir
        )
        
        if not success:
            logger.error("Generation 2 → 3 failed")
            results["generations"].append({
                "name": "Generation 2 → 3",
                "status": "FAILED",
                "reason": "Execution failed"
            })
            return results
        
        # Validate Generation 3
        gen3_results = self.validate_generation(gen3_dir, "Generation 3")
        results["generations"].append(gen3_results)
        
        # Final verdict
        if gen3_results["valid"]:
            logger.info("=" * 80)
            logger.info("✅ SELF-HOSTING TEST PASSED!")
            logger.info("Recipe Executor successfully regenerated itself!")
            logger.info("=" * 80)
            results["status"] = "PASSED"
        else:
            logger.error("=" * 80)
            logger.error("❌ SELF-HOSTING TEST FAILED")
            logger.error("Generation 3 is not valid")
            logger.error("=" * 80)
            results["status"] = "FAILED"
        
        # Save results
        results_file = self.test_dir / "results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {results_file}")
        
        return results


def main():
    """Run the self-hosting test."""
    test = SelfHostingTest()
    try:
        results = test.run_test()
        if results["status"] == "PASSED":
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()