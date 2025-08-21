"""Validation module for Recipe Executor."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from .recipe_model import Recipe, GeneratedCode, ValidationResult, RecipeTestSuite


@dataclass
class Implementation:
    """Represents an implementation to validate."""

    code: GeneratedCode
    tests: Optional[RecipeTestSuite] = None

    def get_all_code(self) -> str:
        """Get all code as a single string."""
        return "\n".join(self.code.files.values())


class Validator:
    """Validates implementations against requirements."""

    def validate(self, recipe: Recipe, implementation: Implementation) -> ValidationResult:
        """Comprehensive validation of generated code."""
        requirements_coverage = self._validate_requirements_coverage(recipe, implementation)
        design_compliance = self._validate_design_compliance(recipe, implementation)
        quality_gates = self._validate_quality_gates(implementation)

        # Determine if validation passed
        passed = (
            all(requirements_coverage.values())
            and all(design_compliance.values())
            and all(quality_gates.values())
        )

        # Collect errors and warnings
        errors: List[str] = []
        warnings: List[str] = []

        # Check requirements coverage
        uncovered = [req_id for req_id, covered in requirements_coverage.items() if not covered]
        if uncovered:
            errors.append(f"Uncovered requirements: {uncovered}")

        # Check design compliance
        non_compliant = [comp for comp, compliant in design_compliance.items() if not compliant]
        if non_compliant:
            errors.append(f"Non-compliant components: {non_compliant}")

        # Check quality gates
        failed_gates = [gate for gate, passed in quality_gates.items() if not passed]
        if failed_gates:
            errors.append(f"Failed quality gates: {failed_gates}")

        return ValidationResult(
            recipe_name=recipe.name,
            passed=passed,
            requirements_coverage=requirements_coverage,
            design_compliance=design_compliance,
            quality_gates=quality_gates,
            errors=errors,
            warnings=warnings,
        )

    def _validate_requirements_coverage(
        self, recipe: Recipe, implementation: Implementation
    ) -> Dict[str, bool]:
        """Ensure all requirements are implemented."""
        coverage: Dict[str, bool] = {}

        all_code = implementation.get_all_code().lower()

        for req in recipe.requirements.get_all_requirements():
            # Simple heuristic: check if key words from requirement appear in code
            # In practice, would need more sophisticated analysis
            req_keywords = req.description.lower().split()[:3]
            covered = any(keyword in all_code for keyword in req_keywords)
            coverage[req.id] = covered

        return coverage

    def _validate_design_compliance(
        self, recipe: Recipe, implementation: Implementation
    ) -> Dict[str, bool]:
        """Validate that implementation follows design."""
        compliance: Dict[str, bool] = {}

        for component in recipe.design.components:
            # Check if component exists in generated code
            component_name = component.name.lower().replace(" ", "_").replace("-", "_")
            component_file = f"src/{recipe.name.replace('-', '_')}/{component_name}.py"

            # Check if file was generated
            if component_file in implementation.code.files:
                file_content = implementation.code.files[component_file]

                # Check if class exists if specified
                if component.class_name:
                    compliance[component.name] = f"class {component.class_name}" in file_content
                else:
                    compliance[component.name] = True
            else:
                compliance[component.name] = False

        return compliance

    def _validate_quality_gates(self, implementation: Implementation) -> Dict[str, bool]:
        """Run quality gate checks."""
        gates: Dict[str, bool] = {}

        # Check that code exists
        gates["has_code"] = len(implementation.code.files) > 0

        # Check that tests exist if provided
        if implementation.tests:
            gates["has_tests"] = len(implementation.tests.test_files) > 0
        else:
            gates["has_tests"] = False

        # Check for proper typing (simplified check)
        all_code = implementation.get_all_code()
        gates["has_type_hints"] = "-> " in all_code  # Simple check for return types
        gates["has_imports"] = "from typing import" in all_code

        return gates

    def validate_recipe_structure(self, recipe: Recipe) -> List[str]:
        """Validate the recipe structure itself."""
        issues: List[str] = []

        # Check recipe validity
        if not recipe.is_valid():
            issues.append("Recipe structure is invalid")

        # Check for MUST requirements
        must_reqs = recipe.requirements.get_must_requirements()
        if not must_reqs:
            issues.append("No MUST requirements defined")

        # Check for components in design
        if not recipe.design.components:
            issues.append("No components defined in design")

        # Check for circular dependencies
        if recipe.name in recipe.get_dependencies():
            issues.append("Recipe has circular self-dependency")

        return issues
