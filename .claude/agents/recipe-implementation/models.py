"""Data models for Recipe Implementation Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class RequirementType(Enum):
    """Types of requirements."""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    INTERFACE = "interface"
    QUALITY = "quality"
    CONSTRAINT = "constraint"
    ASSUMPTION = "assumption"


class ImplementationStatus(Enum):
    """Status of implementation."""

    NOT_STARTED = "not_started"
    PARTIAL = "partial"
    COMPLETE = "complete"
    NEEDS_UPDATE = "needs_update"


class GapSeverity(Enum):
    """Severity of implementation gap."""

    CRITICAL = "critical"  # Must be fixed
    HIGH = "high"         # Should be fixed
    MEDIUM = "medium"     # Nice to have
    LOW = "low"          # Minor issue


@dataclass
class Requirement:
    """A single requirement from recipe."""

    id: str
    type: RequirementType
    category: str
    description: str
    priority: int = 1
    test_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DesignDecision:
    """A design decision from recipe."""

    id: str
    category: str
    decision: str
    rationale: str
    alternatives: List[str] = field(default_factory=list)
    trade_offs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterfaceSpec:
    """Interface specification from recipe."""

    name: str
    type: str  # class, function, api_endpoint, etc.
    description: str
    signature: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    returns: Optional[Dict[str, Any]] = None
    exceptions: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class Dependency:
    """Component dependency."""

    name: str
    version: Optional[str] = None
    type: str = "library"  # library, service, component
    required: bool = True
    alternatives: List[str] = field(default_factory=list)


@dataclass
class RecipeSpec:
    """Complete recipe specification."""

    name: str
    version: str
    description: str
    requirements: List[Requirement] = field(default_factory=list)
    design_decisions: List[DesignDecision] = field(default_factory=list)
    interfaces: List[InterfaceSpec] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    quality_requirements: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_requirements_by_type(self, req_type: RequirementType) -> List[Requirement]:
        """Get requirements by type."""
        return [r for r in self.requirements if r.type == req_type]

    def get_high_priority_requirements(self, threshold: int = 3) -> List[Requirement]:
        """Get high priority requirements."""
        return [r for r in self.requirements if r.priority >= threshold]


@dataclass
class ImplementationGap:
    """Gap between recipe and implementation."""

    requirement_id: str
    description: str
    severity: GapSeverity
    current_state: str
    expected_state: str
    suggested_fix: str
    affected_files: List[str] = field(default_factory=list)
    estimated_effort: str = "unknown"  # hours, days, etc.


@dataclass
class EvaluationReport:
    """Code evaluation report."""

    recipe_name: str
    code_path: Path
    evaluated_at: datetime = field(default_factory=datetime.now)
    total_requirements: int = 0
    implemented_requirements: int = 0
    gaps: List[ImplementationGap] = field(default_factory=list)
    coverage_percentage: float = 0.0
    compliance_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_critical_gaps(self) -> List[ImplementationGap]:
        """Get critical gaps that must be fixed."""
        return [g for g in self.gaps if g.severity == GapSeverity.CRITICAL]

    def is_compliant(self, threshold: float = 0.8) -> bool:
        """Check if implementation is compliant."""
        return self.compliance_score >= threshold


@dataclass
class GeneratedCode:
    """Generated code from recipe."""

    recipe_name: str
    file_path: Path
    content: str
    language: str = "python"
    is_new_file: bool = True
    modifications: List[Dict[str, Any]] = field(default_factory=list)
    imports_added: List[str] = field(default_factory=list)
    functions_added: List[str] = field(default_factory=list)
    classes_added: List[str] = field(default_factory=list)
    tests_generated: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCase:
    """Test case for validating implementation."""

    id: str
    name: str
    description: str
    requirement_id: str
    test_type: str  # unit, integration, functional
    setup: Optional[str] = None
    steps: List[str] = field(default_factory=list)
    expected_result: str = ""
    teardown: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Implementation validation result."""

    recipe_name: str
    code_path: Path
    validated_at: datetime = field(default_factory=datetime.now)
    is_valid: bool = False
    test_results: Dict[str, bool] = field(default_factory=dict)
    quality_checks: Dict[str, bool] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def get_test_pass_rate(self) -> float:
        """Get test pass rate."""
        if not self.test_results:
            return 0.0
        passed = sum(1 for result in self.test_results.values() if result)
        return passed / len(self.test_results)

    def get_quality_score(self) -> float:
        """Get quality score."""
        if not self.quality_checks:
            return 0.0
        passed = sum(1 for check in self.quality_checks.values() if check)
        return passed / len(self.quality_checks)
