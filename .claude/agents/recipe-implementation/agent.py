"""Recipe Implementation Agent - Main agent implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .code_evaluator import CodeEvaluator, EvaluationReport
from .code_generator import CodeGenerator, GeneratedCode
from .models import RecipeSpec, ValidationResult
from .recipe_parser import RecipeParser
from .validator import ImplementationValidator


class RecipeImplementationAgent:
    """Agent that implements components from recipe specifications."""

    def __init__(self, verbose: bool = False):
        """Initialize the Recipe Implementation Agent.

        Args:
            verbose: Enable verbose logging
        """
        self.logger = self._setup_logging(verbose)
        self.parser = RecipeParser()
        self.evaluator = CodeEvaluator()
        self.generator = CodeGenerator()
        self.validator = ImplementationValidator()

        # Agent state
        self.current_recipe: Optional[RecipeSpec] = None
        self.current_evaluation: Optional[EvaluationReport] = None
        self.generated_code: List[GeneratedCode] = []
        self.validation_result: Optional[ValidationResult] = None

    def _setup_logging(self, verbose: bool) -> logging.Logger:
        """Set up logging for the agent."""
        logger = logging.getLogger("RecipeImplementationAgent")
        level = logging.DEBUG if verbose else logging.INFO
        logger.setLevel(level)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def implement_from_recipe(
        self,
        recipe_path: Path,
        code_path: Optional[Path] = None,
        output_path: Optional[Path] = None,
        auto_fix: bool = True,
        validate: bool = True,
    ) -> Dict[str, Any]:
        """Implement a component from recipe specification.

        Args:
            recipe_path: Path to recipe directory
            code_path: Path to existing code (for evaluation)
            output_path: Path for generated code output
            auto_fix: Automatically fix gaps
            validate: Validate generated implementation

        Returns:
            Dictionary with implementation results
        """
        self.logger.info(f"Starting implementation from recipe: {recipe_path}")

        # Step 1: Parse recipe
        self.logger.info("Parsing recipe specification...")
        self.current_recipe = self.parser.parse_recipe(recipe_path)
        self.logger.info(
            f"Parsed recipe: {self.current_recipe.name} with "
            f"{len(self.current_recipe.requirements)} requirements"
        )

        # Step 2: Evaluate existing code (if provided)
        if code_path and code_path.exists():
            self.logger.info("Evaluating existing code...")
            self.current_evaluation = self.evaluator.evaluate_existing_code(
                code_path,
                self.current_recipe
            )
            self.logger.info(
                f"Evaluation complete: {self.current_evaluation.coverage_percentage:.1f}% coverage, "
                f"{len(self.current_evaluation.gaps)} gaps found"
            )
        else:
            # Create empty evaluation for new implementation
            self.current_evaluation = EvaluationReport(
                recipe_name=self.current_recipe.name,
                code_path=code_path or Path("."),
                total_requirements=len(self.current_recipe.requirements),
            )
            # All requirements are gaps for new implementation
            from .models import ImplementationGap, GapSeverity
            for req in self.current_recipe.requirements:
                self.current_evaluation.gaps.append(ImplementationGap(
                    requirement_id=req.id,
                    description=f"Not implemented: {req.description}",
                    severity=GapSeverity.HIGH if req.priority >= 3 else GapSeverity.MEDIUM,
                    current_state="Not implemented",
                    expected_state=req.description,
                    suggested_fix=f"Implement {req.description}",
                ))

        # Step 3: Generate implementation
        if auto_fix and self.current_evaluation.gaps:
            self.logger.info("Generating implementation...")
            self.generated_code = self.generator.generate_implementation(
                self.current_recipe,
                self.current_evaluation,
                output_path
            )
            self.logger.info(f"Generated {len(self.generated_code)} code files")

        # Step 4: Validate implementation
        if validate and self.generated_code:
            self.logger.info("Validating implementation...")
            self.validation_result = self.validator.validate_implementation(
                self.generated_code,
                self.current_recipe,
                run_tests=True
            )
            self.logger.info(
                f"Validation complete: {'PASSED' if self.validation_result.is_valid else 'FAILED'}"
            )

        # Step 5: Generate report
        report = self._generate_report()

        self.logger.info("Implementation process complete")

        return report

    def parse_recipe(self, recipe_path: Path) -> RecipeSpec:
        """Parse a recipe specification.

        Args:
            recipe_path: Path to recipe directory

        Returns:
            Parsed recipe specification
        """
        return self.parser.parse_recipe(recipe_path)

    def evaluate_code(self, code_path: Path, recipe: RecipeSpec) -> EvaluationReport:
        """Evaluate existing code against recipe.

        Args:
            code_path: Path to code
            recipe: Recipe specification

        Returns:
            Evaluation report
        """
        return self.evaluator.evaluate_existing_code(code_path, recipe)

    def generate_code(
        self,
        recipe: RecipeSpec,
        evaluation: EvaluationReport,
        output_path: Optional[Path] = None,
    ) -> List[GeneratedCode]:
        """Generate code from recipe and evaluation.

        Args:
            recipe: Recipe specification
            evaluation: Evaluation report
            output_path: Output directory

        Returns:
            List of generated code files
        """
        return self.generator.generate_implementation(recipe, evaluation, output_path)

    def validate_code(
        self,
        code: GeneratedCode | List[GeneratedCode],
        recipe: RecipeSpec,
    ) -> ValidationResult:
        """Validate generated code.

        Args:
            code: Generated code
            recipe: Recipe specification

        Returns:
            Validation result
        """
        return self.validator.validate_implementation(code, recipe)

    def create_tests(self, recipe: RecipeSpec) -> GeneratedCode:
        """Create tests for recipe implementation.

        Args:
            recipe: Recipe specification

        Returns:
            Generated test file
        """
        # Use generator to create tests
        self.generator.recipe_spec = recipe
        test_code = self.generator._generate_tests()
        if test_code is None:
            # Return empty GeneratedCode if generation fails
            from pathlib import Path
            return GeneratedCode(
                recipe_name=recipe.name if recipe else "unknown",
                file_path=Path("test_empty.py"),
                content="# Test generation failed\n",
                metadata={}
            )
        return test_code

    def _generate_report(self) -> Dict[str, Any]:
        """Generate implementation report."""
        report = {
            "recipe": {
                "name": self.current_recipe.name if self.current_recipe else None,
                "version": self.current_recipe.version if self.current_recipe else None,
                "requirements_count": len(self.current_recipe.requirements) if self.current_recipe else 0,
                "interfaces_count": len(self.current_recipe.interfaces) if self.current_recipe else 0,
            },
            "evaluation": None,
            "generation": None,
            "validation": None,
            "summary": {
                "success": False,
                "issues": [],
                "recommendations": [],
            },
        }

        if self.current_evaluation:
            report["evaluation"] = {
                "coverage_percentage": self.current_evaluation.coverage_percentage,
                "compliance_score": self.current_evaluation.compliance_score,
                "gaps_found": len(self.current_evaluation.gaps),
                "critical_gaps": len(self.current_evaluation.get_critical_gaps()),
                "recommendations": self.current_evaluation.recommendations,
            }

        if self.generated_code:
            report["generation"] = {
                "files_generated": len(self.generated_code),
                "classes_added": sum(len(code.classes_added) for code in self.generated_code),
                "functions_added": sum(len(code.functions_added) for code in self.generated_code),
                "tests_generated": sum(len(code.tests_generated) for code in self.generated_code),
            }

        if self.validation_result:
            report["validation"] = {
                "is_valid": self.validation_result.is_valid,
                "test_pass_rate": self.validation_result.get_test_pass_rate(),
                "quality_score": self.validation_result.get_quality_score(),
                "errors": self.validation_result.errors,
                "warnings": self.validation_result.warnings,
                "suggestions": self.validation_result.suggestions,
            }

            report["summary"]["success"] = self.validation_result.is_valid
            report["summary"]["issues"] = (
                self.validation_result.errors +
                self.validation_result.warnings[:3]
            )
            report["summary"]["recommendations"] = self.validation_result.suggestions[:5]

        return report

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "recipe_loaded": self.current_recipe is not None,
            "evaluation_complete": self.current_evaluation is not None,
            "code_generated": len(self.generated_code) > 0,
            "validation_complete": self.validation_result is not None,
            "current_recipe": self.current_recipe.name if self.current_recipe else None,
            "gaps_remaining": len(self.current_evaluation.gaps) if self.current_evaluation else None,
        }

    def reset(self) -> None:
        """Reset agent state."""
        self.current_recipe = None
        self.current_evaluation = None
        self.generated_code = []
        self.validation_result = None
        self.logger.info("Agent state reset")


def main():
    """Example usage of the Recipe Implementation Agent."""
    # Create agent
    agent = RecipeImplementationAgent(verbose=True)

    # Example: Implement from recipe
    recipe_path = Path(".claude/recipes/event-system")
    output_path = Path(".claude/generated/event-system")

    if recipe_path.exists():
        result = agent.implement_from_recipe(
            recipe_path=recipe_path,
            code_path=None,  # No existing code
            output_path=output_path,
            auto_fix=True,
            validate=True,
        )

        print("\n=== Implementation Report ===")
        print(f"Recipe: {result['recipe']['name']}")
        print(f"Requirements: {result['recipe']['requirements_count']}")

        if result['generation']:
            print(f"Files Generated: {result['generation']['files_generated']}")
            print(f"Classes Added: {result['generation']['classes_added']}")
            print(f"Functions Added: {result['generation']['functions_added']}")

        if result['validation']:
            print(f"Validation: {'PASSED' if result['validation']['is_valid'] else 'FAILED'}")
            print(f"Test Pass Rate: {result['validation']['test_pass_rate']:.1%}")
            print(f"Quality Score: {result['validation']['quality_score']:.1%}")

        print("\nRecommendations:")
        for rec in result['summary']['recommendations']:
            print(f"  - {rec}")
    else:
        print(f"Recipe path not found: {recipe_path}")


if __name__ == "__main__":
    main()
