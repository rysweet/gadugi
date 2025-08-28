"""Self-hosting capability for Recipe Executor - enables regenerating itself from its own recipe."""

import logging
import shutil
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import subprocess
import json

from .enhanced_orchestrator import EnhancedRecipeOrchestrator
from .component_registry import ComponentRegistry

logger = logging.getLogger(__name__)


@dataclass
class SelfHostingResult:
    """Result of a self-hosting attempt."""
    
    success: bool
    generated_files: Dict[str, str]  # filepath -> content
    missing_components: List[str]
    validation_errors: List[str]
    bootstrap_test_passed: bool
    comparison_report: Dict[str, Any]
    
    @property
    def summary(self) -> str:
        """Generate a summary of the self-hosting result."""
        summary = "Self-Hosting Result:\n"
        summary += f"  Success: {'✅' if self.success else '❌'}\n"
        summary += f"  Files Generated: {len(self.generated_files)}\n"
        summary += f"  Missing Components: {len(self.missing_components)}\n"
        summary += f"  Validation Errors: {len(self.validation_errors)}\n"
        summary += f"  Bootstrap Test: {'✅ PASSED' if self.bootstrap_test_passed else '❌ FAILED'}\n"
        
        if self.missing_components:
            summary += f"\n  Missing:\n"
            for comp in self.missing_components[:5]:
                summary += f"    - {comp}\n"
            if len(self.missing_components) > 5:
                summary += f"    ... and {len(self.missing_components) - 5} more\n"
        
        return summary


class SelfHostingManager:
    """
    Manages the self-hosting capability of Recipe Executor.
    
    This enables Recipe Executor to:
    1. Read its own recipe definition
    2. Generate itself from that recipe
    3. Validate the generated code matches the running code
    4. Bootstrap test the generated version
    """
    
    CRITICAL_COMPONENTS = [
        "orchestrator.py",
        "recipe_parser.py",
        "recipe_model.py",
        "claude_code_generator.py",
        "test_generator.py",
        "dependency_resolver.py",
        "__main__.py"
    ]
    
    def __init__(self):
        """Initialize the self-hosting manager."""
        self.orchestrator = EnhancedRecipeOrchestrator()
        self.component_registry = ComponentRegistry()
        
        # Try to find the recipe path relative to the working directory or parent directories
        self.recipe_executor_recipe_path = Path("recipes/recipe-executor")
        if not self.recipe_executor_recipe_path.exists():
            # Try parent directory (when running from src/)
            alt_path = Path("../recipes/recipe-executor")
            if alt_path.exists():
                self.recipe_executor_recipe_path = alt_path
        
    def regenerate_self(
        self,
        output_dir: Optional[Path] = None,
        validate_only: bool = False,
        allow_overwrite: bool = False
    ) -> SelfHostingResult:
        """
        Regenerate Recipe Executor from its own recipe.
        
        Args:
            output_dir: Directory for generated code (default: temp directory)
            validate_only: Only validate, don't actually generate
            allow_overwrite: Allow overwriting existing Recipe Executor code
            
        Returns:
            SelfHostingResult with generation details
        """
        logger.info("Starting Recipe Executor self-hosting regeneration")
        
        # Check recipe exists
        if not self.recipe_executor_recipe_path.exists():
            logger.error(f"Recipe not found at {self.recipe_executor_recipe_path}")
            return SelfHostingResult(
                success=False,
                generated_files={},
                missing_components=["recipe"],
                validation_errors=[f"Recipe not found at {self.recipe_executor_recipe_path}"],
                bootstrap_test_passed=False,
                comparison_report={}
            )
        
        # Create output directory
        if output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix="recipe_executor_self_host_"))
            logger.info(f"Using temporary output directory: {output_dir}")
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        if validate_only:
            logger.info("Running in validation-only mode")
            return self._validate_self_hosting_capability()
        
        # Execute recipe through enhanced pipeline
        logger.info("Executing Recipe Executor recipe through enhanced pipeline")
        result = self.orchestrator.execute_recipe(
            recipe_path=self.recipe_executor_recipe_path,
            output_dir=output_dir,
            dry_run=False,
            verbose=True,
            force_rebuild=True,
            self_hosting=True
        )
        
        if not result.success:
            logger.error("Pipeline execution failed")
            return SelfHostingResult(
                success=False,
                generated_files={},
                missing_components=[],
                validation_errors=["Pipeline execution failed"],
                bootstrap_test_passed=False,
                comparison_report={"pipeline_result": result.summary}
            )
        
        # Extract generated files
        generated_files: Dict[str, str] = {}
        if result.final_artifact and hasattr(result.final_artifact, 'files'):
            files_attr = getattr(result.final_artifact, 'files', {})
            if isinstance(files_attr, dict):
                # Type assertion to ensure proper typing
                for k, v in files_attr.items():  # type: ignore[assignment]
                    if k is not None and v is not None:
                        generated_files[str(k)] = str(v)  # type: ignore[arg-type]
        
        # Validate completeness
        is_complete, missing = self.component_registry.validate_completeness(generated_files)
        
        # Validate critical components
        validation_errors: List[str] = []
        for component in self.CRITICAL_COMPONENTS:
            component_found = any(component in filepath for filepath in generated_files)
            if not component_found:
                validation_errors.append(f"Critical component missing: {component}")
        
        # Compare with existing code
        comparison_report = self._compare_with_existing(generated_files)
        
        # Bootstrap test if complete
        bootstrap_test_passed = False
        if is_complete and len(validation_errors) == 0:
            bootstrap_test_passed = self._bootstrap_test(output_dir)
        
        # Handle overwrite if requested and successful
        if allow_overwrite and is_complete and bootstrap_test_passed:
            self._overwrite_existing(generated_files)
        
        return SelfHostingResult(
            success=is_complete and bootstrap_test_passed,
            generated_files=generated_files,
            missing_components=missing,
            validation_errors=validation_errors,
            bootstrap_test_passed=bootstrap_test_passed,
            comparison_report=comparison_report
        )
    
    def _validate_self_hosting_capability(self) -> SelfHostingResult:
        """Validate that self-hosting is possible without generating code."""
        logger.info("Validating self-hosting capability")
        
        validation_errors: List[str] = []
        
        # Check recipe exists and is valid
        if not self.recipe_executor_recipe_path.exists():
            validation_errors.append("Recipe not found")
        else:
            try:
                recipe = self.orchestrator.parser.parse_recipe(self.recipe_executor_recipe_path)
                
                # Validate recipe has required sections
                if not recipe.requirements:
                    validation_errors.append("Recipe missing requirements")
                if not recipe.design:
                    validation_errors.append("Recipe missing design")
                
                # Check for circular dependencies
                deps = recipe.get_dependencies() if hasattr(recipe, 'get_dependencies') else []
                if deps and "recipe-executor" in deps:
                    validation_errors.append("Circular dependency detected")
                    
            except Exception as e:
                validation_errors.append(f"Recipe parse error: {e}")
        
        # Check current implementation completeness
        # Try multiple paths to find the recipe_executor directory
        current_src = Path("recipe_executor")
        if not current_src.exists():
            current_src = Path("src/recipe_executor")
            if not current_src.exists():
                current_src = Path(__file__).parent
        
        if not current_src.exists():
            validation_errors.append("Current source directory not found")
        else:
            # Check critical files exist
            for component in self.CRITICAL_COMPONENTS:
                if not (current_src / component).exists():
                    validation_errors.append(f"Current implementation missing: {component}")
        
        # Log validation errors for debugging
        if validation_errors:
            for error in validation_errors:
                logger.error(f"Validation error: {error}")
        
        return SelfHostingResult(
            success=len(validation_errors) == 0,
            generated_files={},
            missing_components=[],
            validation_errors=validation_errors,
            bootstrap_test_passed=False,
            comparison_report={"validation_only": True}
        )
    
    def _compare_with_existing(self, generated_files: Dict[str, str]) -> Dict[str, Any]:
        """Compare generated code with existing implementation."""
        logger.info("Comparing generated code with existing implementation")
        
        files_matched: List[str] = []
        files_different: List[str] = []
        files_new: List[str] = []
        files_missing: List[str] = []
        
        report: Dict[str, Any] = {
            "files_matched": files_matched,
            "files_different": files_different,
            "files_new": files_new,
            "files_missing": files_missing,
            "similarity_score": 0.0
        }
        
        current_src = Path("src/recipe_executor")
        
        # Check each generated file
        for filepath, content in generated_files.items():
            if "recipe_executor" in filepath:
                # Extract relative path
                rel_path = Path(filepath).name
                existing_file = current_src / rel_path
                
                if existing_file.exists():
                    existing_content = existing_file.read_text()
                    if content.strip() == existing_content.strip():
                        files_matched.append(rel_path)
                    else:
                        files_different.append(rel_path)
                        # Could add more sophisticated diff here
                else:
                    files_new.append(rel_path)
        
        # Check for missing files
        for existing_file in current_src.glob("*.py"):
            rel_path = existing_file.name
            if not any(rel_path in fp for fp in generated_files):
                files_missing.append(rel_path)
        
        # Calculate similarity score
        total_files = len(files_matched) + len(files_different) + len(files_new) + len(files_missing)
        if total_files > 0:
            report["similarity_score"] = len(files_matched) / total_files
        
        return report
    
    def _bootstrap_test(self, output_dir: Path) -> bool:
        """
        Bootstrap test the generated Recipe Executor.
        
        Attempts to run the generated version to process a simple test recipe.
        """
        logger.info("Running bootstrap test on generated Recipe Executor")
        
        try:
            # Create a simple test recipe
            test_recipe_dir = output_dir / "test_recipe"
            test_recipe_dir.mkdir(exist_ok=True)
            
            # Write test requirements
            (test_recipe_dir / "requirements.md").write_text("""# Test Recipe Requirements
## Functional Requirements
- The system shall print 'Hello, World!'
""")
            
            # Write test design
            (test_recipe_dir / "design.md").write_text("""# Test Recipe Design
## Architecture
Simple single-file Python script
## Components
- Main: Entry point that prints message
""")
            
            # Write test components.json
            (test_recipe_dir / "components.json").write_text(json.dumps({
                "name": "test-recipe",
                "version": "1.0.0",
                "dependencies": []
            }, indent=2))
            
            # Try to run the generated Recipe Executor on the test recipe
            cmd = [
                "python", "-m", "recipe_executor",
                str(test_recipe_dir),
                "--dry-run"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(output_dir),
                timeout=30
            )
            
            # Check if it ran successfully
            success = result.returncode == 0
            
            if success:
                logger.info("✅ Bootstrap test PASSED")
            else:
                logger.error(f"❌ Bootstrap test FAILED: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error("Bootstrap test timed out")
            return False
        except Exception as e:
            logger.error(f"Bootstrap test failed with exception: {e}")
            return False
    
    def _overwrite_existing(self, generated_files: Dict[str, str]) -> None:
        """
        Overwrite existing Recipe Executor with generated code.
        
        DANGEROUS: This replaces the running code!
        """
        logger.warning("OVERWRITING existing Recipe Executor implementation!")
        
        # Create backup first
        backup_dir = Path("src/recipe_executor.backup")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree("src/recipe_executor", backup_dir)
        logger.info(f"Created backup at {backup_dir}")
        
        # Overwrite files
        for filepath, content in generated_files.items():
            if "recipe_executor" in filepath:
                target_path = Path("src") / Path(filepath).relative_to(Path(filepath).parts[0])
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(content)
                logger.info(f"Overwrote: {target_path}")
    
    def verify_self_hosting(self) -> bool:
        """
        Verify that Recipe Executor can successfully self-host.
        
        Returns:
            True if self-hosting verification passes
        """
        logger.info("Verifying self-hosting capability")
        
        # Run validation
        validation_result = self._validate_self_hosting_capability()
        
        if not validation_result.success:
            logger.error(f"Validation failed: {validation_result.validation_errors}")
            return False
        
        # Attempt generation in temp directory
        result = self.regenerate_self(validate_only=False, allow_overwrite=False)
        
        if result.success:
            logger.info("✅ Self-hosting verification PASSED")
            logger.info(result.summary)
        else:
            logger.error("❌ Self-hosting verification FAILED")
            logger.error(result.summary)
        
        return result.success


def self_host_recipe_executor(args: Dict[str, Any]) -> int:
    """
    CLI entry point for self-hosting Recipe Executor.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success)
    """
    manager = SelfHostingManager()
    
    if args.get("validate"):
        # Just validate
        result = manager.regenerate_self(validate_only=True)
    elif args.get("verify"):
        # Full verification
        success = manager.verify_self_hosting()
        return 0 if success else 1
    else:
        # Full regeneration
        output_dir = Path(args.get("output", ".recipe_build/self_host"))
        result = manager.regenerate_self(
            output_dir=output_dir,
            allow_overwrite=args.get("overwrite", False)
        )
    
    print(result.summary)
    return 0 if result.success else 1