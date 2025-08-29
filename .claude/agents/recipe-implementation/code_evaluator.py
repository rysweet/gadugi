"""Code evaluator for comparing existing code against recipe requirements."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .models import (
    EvaluationReport,
    GapSeverity,
    ImplementationGap,
    InterfaceSpec,
    RecipeSpec,
    Requirement,
    RequirementType,
)


class CodeEvaluator:
    """Evaluates existing code against recipe specifications."""

    def __init__(self):
        """Initialize code evaluator."""
        self.recipe_spec: Optional[RecipeSpec] = None
        self.code_path: Optional[Path] = None
        self.found_functions: Set[str] = set()
        self.found_classes: Set[str] = set()
        self.found_imports: Set[str] = set()
        self.code_structure: Dict[str, Any] = {}

    def evaluate_existing_code(
        self,
        code_path: Path,
        recipe: RecipeSpec,
    ) -> EvaluationReport:
        """Evaluate existing code against recipe requirements.

        Args:
            code_path: Path to code directory or file
            recipe: Recipe specification

        Returns:
            Evaluation report with gaps
        """
        self.recipe_spec = recipe
        self.code_path = code_path

        # Analyze code structure
        self._analyze_code_structure()

        # Create evaluation report
        report = EvaluationReport(
            recipe_name=recipe.name,
            code_path=code_path,
            total_requirements=len(recipe.requirements),
        )

        # Evaluate each requirement
        for requirement in recipe.requirements:
            gap = self._evaluate_requirement(requirement)
            if gap:
                report.gaps.append(gap)
            else:
                report.implemented_requirements += 1

        # Evaluate interfaces
        for interface in recipe.interfaces:
            gap = self._evaluate_interface(interface)
            if gap:
                report.gaps.append(gap)

        # Calculate metrics
        report.coverage_percentage = (
            report.implemented_requirements / report.total_requirements * 100
            if report.total_requirements > 0
            else 0
        )

        # Calculate compliance score
        report.compliance_score = self._calculate_compliance_score(report)

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        return report

    def _analyze_code_structure(self) -> None:
        """Analyze the structure of existing code."""
        if not self.code_path or not self.code_path.exists():
            return

        if self.code_path.is_file():
            self._analyze_python_file(self.code_path)
        else:
            # Analyze all Python files in directory
            for py_file in self.code_path.rglob("*.py"):
                self._analyze_python_file(py_file)

    def _analyze_python_file(self, file_path: Path) -> None:
        """Analyze a Python file."""
        try:
            content = file_path.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    self.found_functions.add(node.name)

                    # Store function details
                    if file_path.name not in self.code_structure:
                        self.code_structure[file_path.name] = {"functions": [], "classes": []}

                    self.code_structure[file_path.name]["functions"].append({
                        "name": node.name,
                        "async": isinstance(node, ast.AsyncFunctionDef),
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                    })

                elif isinstance(node, ast.ClassDef):
                    self.found_classes.add(node.name)

                    # Store class details
                    if file_path.name not in self.code_structure:
                        self.code_structure[file_path.name] = {"functions": [], "classes": []}

                    methods = []
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods.append(item.name)

                    self.code_structure[file_path.name]["classes"].append({
                        "name": node.name,
                        "methods": methods,
                        "bases": [self._get_base_name(base) for base in node.bases],
                    })

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        self.found_imports.add(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.found_imports.add(node.module)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def _evaluate_requirement(self, requirement: Requirement) -> Optional[ImplementationGap]:
        """Evaluate a single requirement."""
        # Check based on requirement type
        if requirement.type == RequirementType.FUNCTIONAL:
            return self._evaluate_functional_requirement(requirement)
        elif requirement.type == RequirementType.INTERFACE:
            return self._evaluate_interface_requirement(requirement)
        elif requirement.type == RequirementType.QUALITY:
            return self._evaluate_quality_requirement(requirement)
        else:
            # For other types, do basic text matching
            return self._evaluate_generic_requirement(requirement)

    def _evaluate_functional_requirement(
        self,
        requirement: Requirement,
    ) -> Optional[ImplementationGap]:
        """Evaluate a functional requirement."""
        # Extract key terms from requirement description
        key_terms = self._extract_key_terms(requirement.description)

        # Check if any functions/classes match the key terms
        found_matches = []
        for term in key_terms:
            for func in self.found_functions:
                if term.lower() in func.lower():
                    found_matches.append(func)
            for cls in self.found_classes:
                if term.lower() in cls.lower():
                    found_matches.append(cls)

        if not found_matches:
            return ImplementationGap(
                requirement_id=requirement.id,
                description=f"No implementation found for: {requirement.description}",
                severity=self._determine_gap_severity(requirement.priority),
                current_state="Not implemented",
                expected_state=requirement.description,
                suggested_fix=f"Implement functionality for: {requirement.description}",
            )

        # If partial matches found, might still have gaps
        if len(found_matches) < len(key_terms) / 2:
            return ImplementationGap(
                requirement_id=requirement.id,
                description=f"Partial implementation for: {requirement.description}",
                severity=GapSeverity.MEDIUM,
                current_state=f"Found: {', '.join(found_matches)}",
                expected_state=requirement.description,
                suggested_fix="Complete the implementation",
            )

        return None

    def _evaluate_interface_requirement(
        self,
        requirement: Requirement,
    ) -> Optional[ImplementationGap]:
        """Evaluate an interface requirement."""
        # Interface requirements should have corresponding interfaces in spec
        # This is handled separately in _evaluate_interface
        return None

    def _evaluate_interface(self, interface: InterfaceSpec) -> Optional[ImplementationGap]:
        """Evaluate an interface specification."""
        if interface.type == "class":
            if interface.name not in self.found_classes:
                return ImplementationGap(
                    requirement_id=f"INTERFACE-{interface.name}",
                    description=f"Missing class: {interface.name}",
                    severity=GapSeverity.CRITICAL,
                    current_state="Class not found",
                    expected_state=f"Class {interface.name} with proper interface",
                    suggested_fix=f"Implement class {interface.name}",
                )

        elif interface.type == "function":
            if interface.name not in self.found_functions:
                return ImplementationGap(
                    requirement_id=f"INTERFACE-{interface.name}",
                    description=f"Missing function: {interface.name}",
                    severity=GapSeverity.HIGH,
                    current_state="Function not found",
                    expected_state=f"Function {interface.name} with signature: {interface.signature}",
                    suggested_fix=f"Implement function {interface.name}",
                )

        return None

    def _evaluate_quality_requirement(
        self,
        requirement: Requirement,
    ) -> Optional[ImplementationGap]:
        """Evaluate a quality requirement."""
        # Check for common quality indicators
        quality_checks = {
            "test": self._check_for_tests(),
            "documentation": self._check_for_documentation(),
            "type": self._check_for_type_hints(),
            "error": self._check_for_error_handling(),
        }

        # Check if requirement mentions any quality aspect
        for aspect, is_present in quality_checks.items():
            if aspect in requirement.description.lower() and not is_present:
                return ImplementationGap(
                    requirement_id=requirement.id,
                    description=f"Quality requirement not met: {requirement.description}",
                    severity=GapSeverity.MEDIUM,
                    current_state=f"Missing {aspect}",
                    expected_state=requirement.description,
                    suggested_fix=f"Add {aspect} to meet quality requirement",
                )

        return None

    def _evaluate_generic_requirement(
        self,
        requirement: Requirement,
    ) -> Optional[ImplementationGap]:
        """Evaluate a generic requirement."""
        # For constraints and assumptions, just check if they're documented
        if requirement.type in [RequirementType.CONSTRAINT, RequirementType.ASSUMPTION]:
            # Check for README or documentation
            if not self._check_for_documentation():
                return ImplementationGap(
                    requirement_id=requirement.id,
                    description=f"Undocumented {requirement.type.value}: {requirement.description}",
                    severity=GapSeverity.LOW,
                    current_state="Not documented",
                    expected_state="Documented in code or README",
                    suggested_fix=f"Document {requirement.type.value} in README or code comments",
                )

        return None

    def _check_for_tests(self) -> bool:
        """Check if tests exist."""
        if self.code_path and self.code_path.is_dir():
            test_files = list(self.code_path.glob("**/test_*.py"))
            test_files.extend(self.code_path.glob("**/*_test.py"))
            return len(test_files) > 0
        return False

    def _check_for_documentation(self) -> bool:
        """Check if documentation exists."""
        if self.code_path and self.code_path.is_dir():
            doc_files = list(self.code_path.glob("**/*.md"))
            doc_files.extend(self.code_path.glob("**/*.rst"))
            return len(doc_files) > 0
        return False

    def _check_for_type_hints(self) -> bool:
        """Check if type hints are used."""
        # Simple check: look for -> in function definitions
        for file_info in self.code_structure.values():
            for func in file_info.get("functions", []):
                # Would need to check actual AST for proper type hints
                # This is a simplified check
                if len(func.get("args", [])) > 1:  # Assuming non-trivial functions
                    return True
        return False

    def _check_for_error_handling(self) -> bool:
        """Check if error handling exists."""
        # Look for try/except blocks in code
        if self.code_path and self.code_path.is_file():
            content = self.code_path.read_text()
            return "try:" in content and "except" in content
        elif self.code_path and self.code_path.is_dir():
            for py_file in self.code_path.glob("**/*.py"):
                content = py_file.read_text()
                if "try:" in content and "except" in content:
                    return True
        return False

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from requirement text."""
        # Remove common words and extract meaningful terms
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "can", "shall",
        }

        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter out stop words and short words
        key_terms = [
            word for word in words
            if word not in stop_words and len(word) > 3
        ]

        # Also extract CamelCase terms
        camel_terms = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)*', text)
        key_terms.extend([term.lower() for term in camel_terms])

        return list(set(key_terms))

    def _determine_gap_severity(self, priority: int) -> GapSeverity:
        """Determine gap severity from requirement priority."""
        if priority >= 4:
            return GapSeverity.CRITICAL
        elif priority == 3:
            return GapSeverity.HIGH
        elif priority == 2:
            return GapSeverity.MEDIUM
        else:
            return GapSeverity.LOW

    def _calculate_compliance_score(self, report: EvaluationReport) -> float:
        """Calculate overall compliance score."""
        if report.total_requirements == 0:
            return 0.0

        # Base score from implemented requirements
        base_score = report.implemented_requirements / report.total_requirements

        # Penalty for critical gaps
        critical_gaps = len(report.get_critical_gaps())
        penalty = critical_gaps * 0.1

        # Bonus for no high/critical gaps
        if not any(g.severity in [GapSeverity.CRITICAL, GapSeverity.HIGH] for g in report.gaps):
            bonus = 0.1
        else:
            bonus = 0

        score = max(0, min(1, base_score - penalty + bonus))
        return score

    def _generate_recommendations(self, report: EvaluationReport) -> List[str]:
        """Generate recommendations based on evaluation."""
        recommendations = []

        # Check critical gaps
        critical_gaps = report.get_critical_gaps()
        if critical_gaps:
            recommendations.append(
                f"URGENT: Address {len(critical_gaps)} critical gaps immediately"
            )
            for gap in critical_gaps[:3]:  # Show top 3
                recommendations.append(f"  - {gap.suggested_fix}")

        # Check compliance
        if report.compliance_score < 0.5:
            recommendations.append(
                "Low compliance score - significant implementation needed"
            )
        elif report.compliance_score < 0.8:
            recommendations.append(
                "Moderate compliance - focus on high-priority gaps"
            )
        else:
            recommendations.append(
                "Good compliance - minor improvements needed"
            )

        # Check for missing tests
        if not self._check_for_tests():
            recommendations.append("Add unit tests for implemented functionality")

        # Check for missing documentation
        if not self._check_for_documentation():
            recommendations.append("Add documentation for the implementation")

        return recommendations

    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return "unknown"

    def _get_base_name(self, base) -> str:
        """Get base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.value.id if isinstance(base.value, ast.Name) else 'unknown'}.{base.attr}"
        return "unknown"
