"""Validator for checking implementation against requirements."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .recipe_model import Recipe, Requirement

logger = logging.getLogger(__name__)


@dataclass
class CoverageResult:
    """Result of requirements coverage check."""
    complete: bool
    coverage_map: Dict[str, bool]
    missing: List[str]
    coverage_percentage: float = 0.0


@dataclass
class ComplianceResult:
    """Result of design compliance check."""
    compliant: bool
    compliance_map: Dict[str, bool]
    issues: List[str]


@dataclass
class ValidationResult:
    """Complete validation result."""
    recipe_name: str
    passed: bool
    requirements_coverage: Dict[str, bool]
    design_compliance: Dict[str, bool]
    quality_gates: Dict[str, bool]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_summary(self) -> str:
        """Get validation summary."""
        lines = [
            f"Validation for {self.recipe_name}: {'PASSED' if self.passed else 'FAILED'}"
        ]
        
        # Requirements coverage
        covered = sum(1 for v in self.requirements_coverage.values() if v)
        total = len(self.requirements_coverage)
        lines.append(f"  Requirements: {covered}/{total} covered")
        
        # Design compliance
        compliant = sum(1 for v in self.design_compliance.values() if v)
        total_design = len(self.design_compliance)
        if total_design > 0:
            lines.append(f"  Design: {compliant}/{total_design} compliant")
        
        # Quality gates
        passed_gates = sum(1 for v in self.quality_gates.values() if v)
        total_gates = len(self.quality_gates)
        if total_gates > 0:
            lines.append(f"  Quality: {passed_gates}/{total_gates} passed")
        
        # Errors and warnings
        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
        if self.warnings:
            lines.append(f"  Warnings: {len(self.warnings)}")
        
        return '\n'.join(lines)


class Validator:
    """Validates implementations against requirements."""
    
    def validate(self, recipe: Recipe, implementation) -> ValidationResult:
        """Comprehensive validation of generated code.
        
        Args:
            recipe: Recipe with requirements
            implementation: Generated implementation
            
        Returns:
            Validation result
        """
        logger.info(f"Validating implementation for {recipe.name}")
        
        errors = []
        warnings = []
        
        # Check requirements coverage
        req_coverage = self._validate_requirements_coverage(recipe, implementation)
        if not req_coverage.complete:
            errors.extend(req_coverage.missing)
        
        # Check design compliance
        design_compliance = self._validate_design_compliance(recipe, implementation)
        if not design_compliance.compliant:
            warnings.extend(design_compliance.issues)
        
        # Check quality gates (if available in implementation)
        quality_gates = self._validate_quality_gates(implementation)
        if not all(quality_gates.values()):
            failed = [k for k, v in quality_gates.items() if not v]
            errors.extend([f"Quality gate failed: {g}" for g in failed])
        
        # Determine overall pass/fail
        passed = len(errors) == 0
        
        result = ValidationResult(
            recipe_name=recipe.name,
            passed=passed,
            requirements_coverage=req_coverage.coverage_map,
            design_compliance=design_compliance.compliance_map,
            quality_gates=quality_gates,
            errors=errors,
            warnings=warnings
        )
        
        logger.info(result.get_summary())
        return result
    
    def _validate_requirements_coverage(self, recipe: Recipe, impl) -> CoverageResult:
        """Ensure all MUST requirements are implemented.
        
        Args:
            recipe: Recipe with requirements
            impl: Implementation to check
            
        Returns:
            Coverage result
        """
        coverage_map = {}
        missing = []
        
        # Check each MUST requirement
        for req in recipe.requirements.get_must_requirements():
            if self._requirement_implemented(req, impl):
                coverage_map[req.id] = True
            else:
                coverage_map[req.id] = False
                missing.append(f"Requirement {req.id} not implemented: {req.description}")
        
        # Calculate coverage percentage
        covered = sum(1 for v in coverage_map.values() if v)
        total = len(coverage_map)
        coverage_pct = (covered / total * 100) if total > 0 else 0
        
        return CoverageResult(
            complete=len(missing) == 0,
            coverage_map=coverage_map,
            missing=missing,
            coverage_percentage=coverage_pct
        )
    
    def _validate_design_compliance(self, recipe: Recipe, impl) -> ComplianceResult:
        """Check if implementation follows design specification.
        
        Args:
            recipe: Recipe with design
            impl: Implementation to check
            
        Returns:
            Compliance result
        """
        compliance_map = {}
        issues = []
        
        # Check each component in design
        for component in recipe.design.components:
            if self._component_implemented(component, impl):
                compliance_map[component.name] = True
            else:
                compliance_map[component.name] = False
                issues.append(f"Component {component.name} not properly implemented")
        
        return ComplianceResult(
            compliant=len(issues) == 0,
            compliance_map=compliance_map,
            issues=issues
        )
    
    def _validate_quality_gates(self, impl) -> Dict[str, bool]:
        """Validate quality gate results.
        
        Args:
            impl: Implementation with quality results
            
        Returns:
            Quality gate results
        """
        # If implementation has quality results, use them
        if hasattr(impl, 'quality_results'):
            return impl.quality_results
        
        # Otherwise, check basic quality indicators
        quality = {}
        
        # Check for tests
        if impl.tests and impl.tests.get_test_count() > 0:
            quality["has_tests"] = True
        else:
            quality["has_tests"] = False
        
        # Check for documentation
        quality["has_docs"] = self._check_documentation(impl)
        
        # Check for proper structure
        quality["proper_structure"] = self._check_structure(impl)
        
        return quality
    
    def _requirement_implemented(self, req: Requirement, impl) -> bool:
        """Check if a requirement is implemented.
        
        Args:
            req: Requirement to check
            impl: Implementation
            
        Returns:
            True if requirement appears to be implemented
        """
        if not impl or not impl.code:
            return False
        
        # Simple heuristic: check if requirement keywords appear in code
        req_keywords = self._extract_keywords(req.description)
        
        # Check in all code files
        for filepath, content in impl.code.get_all_files().items():
            content_lower = content.lower()
            if any(keyword in content_lower for keyword in req_keywords):
                # Found potential implementation
                return True
        
        # Check in tests
        if impl.tests:
            for test in impl.tests.unit_tests:
                if test.requirement_id == req.id:
                    # Has specific test for this requirement
                    return True
        
        return False
    
    def _component_implemented(self, component, impl) -> bool:
        """Check if a component is implemented.
        
        Args:
            component: Component design
            impl: Implementation
            
        Returns:
            True if component appears to be implemented
        """
        if not impl or not impl.code:
            return False
        
        # Look for class or module with component name
        component_name = component.class_name or component.name
        
        for filepath, content in impl.code.files.items():
            # Check for class definition
            if f"class {component_name}" in content:
                # Found class, check for methods
                if component.methods:
                    methods_found = sum(
                        1 for method in component.methods 
                        if f"def {method}" in content
                    )
                    # Require at least 50% of methods
                    if methods_found >= len(component.methods) * 0.5:
                        return True
                else:
                    # No specific methods required
                    return True
        
        return False
    
    def _check_documentation(self, impl) -> bool:
        """Check if implementation has proper documentation.
        
        Args:
            impl: Implementation
            
        Returns:
            True if documentation present
        """
        if not impl or not impl.code:
            return False
        
        # Check for docstrings in code
        doc_count = 0
        for filepath, content in impl.code.files.items():
            if filepath.endswith('.py'):
                # Count docstrings (simple heuristic)
                doc_count += content.count('"""')
        
        # Require at least some documentation
        return doc_count >= 4  # At least 2 docstrings
    
    def _check_structure(self, impl) -> bool:
        """Check if implementation has proper structure.
        
        Args:
            impl: Implementation
            
        Returns:
            True if structure is good
        """
        if not impl or not impl.code:
            return False
        
        # Check for required files
        has_init = any(f.endswith('__init__.py') for f in impl.code.files)
        has_main = any('main' in f or 'cli' in f for f in impl.code.files)
        has_tests = impl.tests and impl.tests.get_test_count() > 0
        
        # Require basic structure
        return has_init or has_main or has_tests
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from requirement text.
        
        Args:
            text: Requirement description
            
        Returns:
            List of keywords
        """
        # Simple keyword extraction
        import re
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                     'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 
                     'was', 'are', 'were', 'be', 'been', 'being', 'have', 
                     'has', 'had', 'do', 'does', 'did', 'will', 'would', 
                     'should', 'could', 'may', 'might', 'must', 'can', 
                     'shall', 'that', 'this', 'these', 'those'}
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        return keywords[:5]  # Top 5 keywords