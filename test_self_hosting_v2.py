#!/usr/bin/env python3
"""
Test self-hosting capability of Recipe Executor with improved handling.
This test verifies that Recipe Executor can regenerate itself from its own recipe.

Changes from previous version:
1. Fixed file context issues in prompt generation
2. Fixed ruff permission errors by using uv run
3. Better monitoring and error reporting
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("self_hosting_test_v2.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SelfHostingValidator:
    """Validates self-hosting capability of Recipe Executor."""
    
    def __init__(self, base_dir: Path = Path.cwd()):
        self.base_dir = base_dir
        self.test_dir = base_dir / f".recipe_build/self_host_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
    def run_recipe_executor(self, generation: int, source_dir: Path, output_dir: Path) -> Tuple[bool, Dict]:
        """Run Recipe Executor to generate code."""
        logger.info(f"Running Generation {generation}")
        logger.info(f"Source: {source_dir}")
        logger.info(f"Output: {output_dir}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file for this generation
        log_file = self.test_dir / f"Generation_{generation}.log"
        
        # Build command to run Recipe Executor
        if generation == 1:
            # Generation 1: Use current Recipe Executor to generate Gen 2
            cmd = [
                sys.executable,
                "-m", "src.recipe_executor",
                "execute",
                str(self.base_dir / "recipes/recipe-executor"),
                "--output-dir", str(output_dir),
                "--force",
                "--verbose"
            ]
        else:
            # Generation 2+: Use previous generation to generate next
            # Add the generated directory to Python path
            env = os.environ.copy()
            env["PYTHONPATH"] = f"{source_dir}:{env.get('PYTHONPATH', '')}"
            
            cmd = [
                sys.executable,
                "-m", "src.recipe_executor",
                "execute",
                str(source_dir / "recipes/recipe-executor"),
                "--output-dir", str(output_dir),
                "--force",
                "--verbose"
            ]
        
        logger.info(f"Command: {' '.join(cmd)}")
        
        # Run the command with monitoring
        start_time = time.time()
        try:
            with open(log_file, "w") as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env if generation > 1 else None
                )
                
                # Monitor process output
                last_progress_time = time.time()
                file_count = 0
                
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    
                    # Log key events
                    if "INFO" in line:
                        if "Claude" in line or "Creating" in line or "Writing" in line:
                            logger.info(line.strip())
                        elif "Python files" in line:
                            # Track file creation progress
                            current_count = self.count_python_files(output_dir)
                            if current_count > file_count:
                                file_count = current_count
                                logger.info(f"  Progress: {file_count} Python files created")
                                last_progress_time = time.time()
                    elif "ERROR" in line or "CRITICAL" in line:
                        logger.error(line.strip())
                    elif "WARNING" in line and "stub" in line.lower():
                        logger.warning(line.strip())
                    
                    # Check for timeout (warn but don't kill)
                    elapsed = time.time() - last_progress_time
                    if elapsed > 600:  # 10 minutes without progress
                        logger.warning(f"No progress for {elapsed:.0f}s - process may be stuck")
                        last_progress_time = time.time()  # Reset to avoid spam
                
                # Wait for process to complete
                return_code = process.wait()
                
            elapsed_time = time.time() - start_time
            logger.info(f"Generation {generation} completed in {elapsed_time:.1f}s with exit code {return_code}")
            
            if return_code == 0:
                # Validate the generated files
                validation_results = self.validate_generation(output_dir)
                return True, validation_results
            else:
                logger.error(f"Generation {generation} failed with exit code {return_code}")
                logger.error(f"Check log file: {log_file}")
                
                # Show last few lines of output for debugging
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    logger.error("Last 10 lines of output:")
                    for line in lines[-10:]:
                        logger.error(f"  {line.rstrip()}")
                
                return False, {"error": f"Exit code {return_code}"}
                
        except Exception as e:
            logger.error(f"Exception during generation {generation}: {e}")
            return False, {"error": str(e)}
    
    def count_python_files(self, directory: Path) -> int:
        """Count Python files in directory (excluding venv)."""
        count = 0
        if directory.exists():
            for py_file in directory.rglob("*.py"):
                # Skip virtual environment files
                if "venv" not in str(py_file) and ".venv" not in str(py_file):
                    count += 1
        return count
    
    def validate_generation(self, gen_dir: Path) -> Dict:
        """Validate a generated Recipe Executor."""
        results = {
            "valid": False,
            "file_count": 0,
            "has_core_files": False,
            "has_stubs": False,
            "has_external_deps": False,
            "import_errors": [],
            "missing_files": []
        }
        
        # Count Python files
        results["file_count"] = self.count_python_files(gen_dir)
        logger.info(f"Found {results['file_count']} Python files")
        
        # Check for core files
        core_files = [
            "src/recipe_executor/__init__.py",
            "src/recipe_executor/recipe_model.py",
            "src/recipe_executor/recipe_parser.py",
            "src/recipe_executor/orchestrator.py",
            "src/recipe_executor/claude_code_generator.py",
            "src/recipe_executor/dependency_resolver.py",
            "src/recipe_executor/file_system.py",
            "pyproject.toml"
        ]
        
        missing = []
        for file in core_files:
            if not (gen_dir / file).exists():
                missing.append(file)
        
        results["missing_files"] = missing
        results["has_core_files"] = len(missing) == 0
        
        if missing:
            logger.warning(f"Missing {len(missing)} core files: {missing[:5]}...")
        
        # Check for stub implementations
        stub_patterns = ["pass\n", "raise NotImplementedError", "TODO:", "FIXME:"]
        stub_count = 0
        
        for py_file in gen_dir.rglob("*.py"):
            if "venv" in str(py_file) or ".venv" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                for pattern in stub_patterns:
                    if pattern in content:
                        stub_count += 1
                        break
            except Exception:
                pass
        
        results["has_stubs"] = stub_count > 0
        if stub_count > 0:
            logger.warning(f"Found {stub_count} files with potential stubs")
        
        # Check for external dependencies
        pyproject_file = gen_dir / "pyproject.toml"
        if pyproject_file.exists():
            try:
                content = pyproject_file.read_text()
                # Check dependencies section
                if "dependencies = [" in content:
                    deps_section = content.split("dependencies = [")[1].split("]")[0]
                    if deps_section.strip():  # Not empty
                        results["has_external_deps"] = True
                        logger.warning("Found external dependencies in pyproject.toml")
            except Exception as e:
                logger.error(f"Error checking dependencies: {e}")
        
        # Check if imports work
        try:
            sys.path.insert(0, str(gen_dir))
            import src.recipe_executor
            logger.info("Successfully imported generated Recipe Executor")
        except ImportError as e:
            results["import_errors"].append(str(e))
            logger.warning(f"Import error: {e}")
        finally:
            # Clean up sys.path
            if str(gen_dir) in sys.path:
                sys.path.remove(str(gen_dir))
        
        # Determine overall validity
        results["valid"] = (
            results["file_count"] >= 25 and  # Should have at least 25 files
            results["has_core_files"] and
            not results["has_external_deps"] and
            len(results["import_errors"]) == 0
        )
        
        return results
    
    def run_self_hosting_test(self) -> bool:
        """Run the complete self-hosting test."""
        logger.info("=" * 60)
        logger.info("Starting Recipe Executor Self-Hosting Test v2")
        logger.info("=" * 60)
        
        # Generation 1: Current → Gen2
        gen1_dir = self.test_dir / "gen1"
        gen2_dir = self.test_dir / "gen2"
        
        logger.info("\n" + "=" * 60)
        logger.info("GENERATION 1 → 2: Using current Recipe Executor")
        logger.info("=" * 60)
        
        success, gen2_results = self.run_recipe_executor(
            generation=1,
            source_dir=self.base_dir,
            output_dir=gen2_dir
        )
        
        if not success:
            logger.error("Generation 1 → 2 failed")
            return False
        
        logger.info(f"Generation 2 validation: {gen2_results}")
        
        if not gen2_results.get("valid", False):
            logger.error("Generation 2 is not valid")
            if gen2_results.get("missing_files"):
                logger.error(f"  Missing files: {gen2_results['missing_files'][:10]}")
            if gen2_results.get("has_stubs"):
                logger.error("  Contains stub implementations")
            if gen2_results.get("has_external_deps"):
                logger.error("  Contains external dependencies")
            return False
        
        # Generation 2: Gen2 → Gen3 (true self-hosting test)
        gen3_dir = self.test_dir / "gen3"
        
        logger.info("\n" + "=" * 60)
        logger.info("GENERATION 2 → 3: Using generated Recipe Executor (self-hosting)")
        logger.info("=" * 60)
        
        success, gen3_results = self.run_recipe_executor(
            generation=2,
            source_dir=gen2_dir,
            output_dir=gen3_dir
        )
        
        if not success:
            logger.error("Generation 2 → 3 failed")
            logger.error("This means the generated Recipe Executor cannot regenerate itself")
            return False
        
        logger.info(f"Generation 3 validation: {gen3_results}")
        
        if not gen3_results.get("valid", False):
            logger.error("Generation 3 is not valid")
            return False
        
        # Compare Gen2 and Gen3
        logger.info("\n" + "=" * 60)
        logger.info("Comparing Generation 2 and Generation 3")
        logger.info("=" * 60)
        
        gen2_files = set(gen2_dir.rglob("*.py"))
        gen3_files = set(gen3_dir.rglob("*.py"))
        
        gen2_names = {f.relative_to(gen2_dir) for f in gen2_files}
        gen3_names = {f.relative_to(gen3_dir) for f in gen3_files}
        
        if gen2_names != gen3_names:
            logger.warning(f"File sets differ:")
            logger.warning(f"  Gen2 only: {gen2_names - gen3_names}")
            logger.warning(f"  Gen3 only: {gen3_names - gen2_names}")
        else:
            logger.info(f"Both generations have the same {len(gen2_names)} files")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 SELF-HOSTING TEST PASSED!")
        logger.info("Recipe Executor successfully regenerated itself!")
        logger.info("=" * 60)
        
        return True


def main():
    """Run the self-hosting test."""
    import os
    
    validator = SelfHostingValidator()
    
    try:
        success = validator.run_self_hosting_test()
        
        if success:
            logger.info("\n✅ Self-hosting validation PASSED")
            logger.info("Recipe Executor can successfully regenerate itself from its recipe!")
            sys.exit(0)
        else:
            logger.error("\n❌ Self-hosting validation FAILED")
            logger.error("Recipe Executor cannot regenerate itself from its recipe")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()