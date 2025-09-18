#!/usr/bin/env python3
"""
Test self-hosting capability of Recipe Executor with quality gate iteration.
This test verifies that Recipe Executor can regenerate itself from its own recipe.

Changes from v2:
1. Quality gate iteration is now part of the generation loop
2. Better reporting of component recipe status
3. Tracks iterations per component recipe
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
        logging.FileHandler("self_hosting_test_v3.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SelfHostingValidatorV3:
    """Validates self-hosting capability of Recipe Executor with quality iteration."""
    
    def __init__(self, base_dir: Path = Path.cwd()):
        self.base_dir = base_dir
        self.test_dir = base_dir / f".recipe_build/self_host_test_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.component_stats = {}  # Track stats per component recipe
        
    def run_recipe_executor(self, generation: int, source_dir: Path, output_dir: Path) -> Tuple[bool, Dict]:
        """Run Recipe Executor to generate code with quality iteration enabled."""
        logger.info(f"Running Generation {generation} with quality iteration")
        logger.info(f"Source: {source_dir}")
        logger.info(f"Output: {output_dir}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file for this generation
        log_file = self.test_dir / f"Generation_{generation}.log"
        
        # Build command to run Recipe Executor with quality iteration
        if generation == 1:
            # Generation 1: Use current Recipe Executor to generate Gen 2
            cmd = [
                sys.executable,
                "-m", "src.recipe_executor",
                "execute",
                str(self.base_dir / "recipes/recipe-executor"),
                "--output-dir", str(output_dir),
                "--force",
                "--verbose",
                # iterate_quality is True by default now
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
                "--verbose",
                # iterate_quality is True by default now
            ]
        
        logger.info(f"Command: {' '.join(cmd)}")
        logger.info("Quality gate iteration is ENABLED by default")
        
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
                current_component = None
                component_iterations = {}
                
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    
                    # Track component recipes
                    if "Executing recipe:" in line:
                        component = line.split("Executing recipe:")[-1].strip()
                        if "/" in component:
                            component = component.split("/")[-1]
                        current_component = component
                        component_iterations[component] = 0
                        logger.info(f"  📦 Component: {component}")
                    
                    # Track iterations per component
                    if current_component and "Generation iteration" in line:
                        try:
                            iteration_num = int(line.split("Generation iteration")[1].split()[0])
                            component_iterations[current_component] = iteration_num
                            logger.info(f"    Iteration {iteration_num} for {current_component}")
                        except:
                            pass
                    
                    # Track quality gate iterations
                    if "Running quality gate checks (iteration enabled)" in line:
                        logger.info(f"    🔍 Quality gates checking for {current_component}")
                    
                    if "Quality gates failed:" in line and "will iterate to fix" in line:
                        logger.info(f"    ♻️ Quality gates failed, iterating to fix for {current_component}")
                    
                    # Track file creation progress
                    if "Creating:" in line or "Writing:" in line:
                        current_count = self.count_python_files(output_dir)
                        if current_count > file_count:
                            file_count = current_count
                            logger.info(f"  Progress: {file_count} Python files created")
                            last_progress_time = time.time()
                    
                    # Log key events
                    if "ERROR" in line or "CRITICAL" in line:
                        logger.error(line.strip())
                    elif "WARNING" in line and "stub" in line.lower():
                        logger.warning(line.strip())
                    elif "Code generation successful after" in line:
                        logger.info(f"  ✅ {line.strip()}")
                    
                    # Check for timeout (warn but don't kill - we expect longer times with iteration)
                    elapsed = time.time() - last_progress_time
                    if elapsed > 900:  # 15 minutes without progress
                        logger.warning(f"No progress for {elapsed:.0f}s - process may be stuck or iterating")
                        last_progress_time = time.time()  # Reset to avoid spam
                
                # Wait for process to complete
                return_code = process.wait()
                
            elapsed_time = time.time() - start_time
            logger.info(f"Generation {generation} completed in {elapsed_time:.1f}s with exit code {return_code}")
            
            # Report component statistics
            if component_iterations:
                logger.info("Component Recipe Statistics:")
                for comp, iters in sorted(component_iterations.items()):
                    logger.info(f"  - {comp}: {iters} iterations")
                self.component_stats = component_iterations
            
            if return_code == 0:
                # Validate the generated files
                validation_results = self.validate_generation(output_dir)
                validation_results["component_iterations"] = component_iterations
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
                
                return False, {"error": f"Exit code {return_code}", "component_iterations": component_iterations}
                
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
            "missing_files": [],
            "quality_gates_passed": False
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
        
        # Run quality gates on the generated code
        try:
            logger.info("Running quality gates on generated code...")
            from src.recipe_executor.python_standards import QualityGates
            gates = QualityGates()
            gate_results = gates.run_all_gates(gen_dir)
            
            failed_gates = [name for name, passed in gate_results.items() if not passed]
            if failed_gates:
                logger.warning(f"Quality gates failed: {failed_gates}")
                results["quality_gates_passed"] = False
            else:
                logger.info("All quality gates passed!")
                results["quality_gates_passed"] = True
        except Exception as e:
            logger.error(f"Could not run quality gates: {e}")
            results["quality_gates_passed"] = False
        
        # Determine overall validity
        results["valid"] = (
            results["file_count"] >= 25 and  # Should have at least 25 files
            results["has_core_files"] and
            not results["has_external_deps"] and
            len(results["import_errors"]) == 0 and
            results["quality_gates_passed"]  # Now require quality gates to pass
        )
        
        return results
    
    def run_self_hosting_test(self) -> bool:
        """Run the complete self-hosting test with quality iteration."""
        logger.info("=" * 60)
        logger.info("Starting Recipe Executor Self-Hosting Test v3")
        logger.info("Quality Gate Iteration: ENABLED")
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
        
        # Report component iteration statistics
        if "component_iterations" in gen2_results:
            logger.info("\n" + "=" * 60)
            logger.info("Component Recipe Iteration Report:")
            logger.info("=" * 60)
            total_iterations = 0
            for comp, iters in sorted(gen2_results["component_iterations"].items()):
                logger.info(f"  {comp}: {iters} iterations to achieve quality")
                total_iterations += iters
            avg_iterations = total_iterations / len(gen2_results["component_iterations"]) if gen2_results["component_iterations"] else 0
            logger.info(f"  Average iterations per component: {avg_iterations:.1f}")
        
        if not gen2_results.get("valid", False):
            logger.error("Generation 2 is not valid")
            if gen2_results.get("missing_files"):
                logger.error(f"  Missing files: {gen2_results['missing_files'][:10]}")
            if gen2_results.get("has_stubs"):
                logger.error("  Contains stub implementations")
            if gen2_results.get("has_external_deps"):
                logger.error("  Contains external dependencies")
            if not gen2_results.get("quality_gates_passed"):
                logger.error("  Quality gates did not pass")
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
        
        # Report component iteration statistics for Gen3
        if "component_iterations" in gen3_results:
            logger.info("\n" + "=" * 60)
            logger.info("Generation 3 Component Recipe Iteration Report:")
            logger.info("=" * 60)
            total_iterations = 0
            for comp, iters in sorted(gen3_results["component_iterations"].items()):
                logger.info(f"  {comp}: {iters} iterations to achieve quality")
                total_iterations += iters
            avg_iterations = total_iterations / len(gen3_results["component_iterations"]) if gen3_results["component_iterations"] else 0
            logger.info(f"  Average iterations per component: {avg_iterations:.1f}")
        
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
        logger.info("🎉 SELF-HOSTING TEST PASSED WITH QUALITY ITERATION!")
        logger.info("Recipe Executor successfully regenerated itself!")
        logger.info("Quality gates passed through iteration, not manual fixes!")
        logger.info("=" * 60)
        
        return True


def main():
    """Run the self-hosting test v3."""
    
    validator = SelfHostingValidatorV3()
    
    try:
        success = validator.run_self_hosting_test()
        
        if success:
            logger.info("\n✅ Self-hosting validation v3 PASSED")
            logger.info("Recipe Executor can successfully regenerate itself with quality iteration!")
            logger.info("Quality gates are achieved through automatic iteration, not manual fixes!")
            sys.exit(0)
        else:
            logger.error("\n❌ Self-hosting validation v3 FAILED")
            logger.error("Recipe Executor cannot regenerate itself even with quality iteration")
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