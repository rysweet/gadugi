"""Extended requirement tracking with status, validation rules, and coverage analysis.

This module provides comprehensive requirement management capabilities including
status tracking, validation rules, and requirements traceability matrix.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator


class RequirementStatus(str, Enum):
    """Status of a requirement in the development lifecycle."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED = "VERIFIED"
    DEFERRED = "DEFERRED"


class RequirementCategory(str, Enum):
    """Categories for organizing requirements."""

    FUNCTIONAL = "FUNCTIONAL"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    USABILITY = "USABILITY"
    RELIABILITY = "RELIABILITY"
    SCALABILITY = "SCALABILITY"
    MAINTAINABILITY = "MAINTAINABILITY"
    COMPATIBILITY = "COMPATIBILITY"
    DOCUMENTATION = "DOCUMENTATION"


class RequirementPriority(str, Enum):
    """Priority levels for requirements (re-exported for convenience)."""

    MUST = "MUST"
    SHOULD = "SHOULD"
    COULD = "COULD"


class ValidationRule(BaseModel):
    """Validation rule specification for a requirement."""

    name: str = Field(..., description="Name of the validation rule")
    check_type: str = Field(
        ..., description="Type of check (e.g., 'exists', 'performance', 'format')"
    )
    target: str = Field(..., description="Target element to validate")
    expected_value: Any = Field(None, description="Expected value or condition")
    description: str = Field("", description="Description of what the rule validates")

    def __str__(self) -> str:
        """Return a string representation of the validation rule."""
        return f"{self.name}: {self.check_type} on {self.target}"

    def __repr__(self) -> str:
        """Return a detailed representation of the validation rule."""
        return f"ValidationRule(name='{self.name}', check_type='{self.check_type}', target='{self.target}')"


class RequirementLink(BaseModel):
    """Link between requirements for traceability."""

    source_id: str = Field(..., description="Source requirement ID")
    target_id: str = Field(..., description="Target requirement ID")
    link_type: str = Field(
        ..., description="Type of link (e.g., 'depends_on', 'conflicts_with', 'refines')"
    )
    description: str = Field("", description="Description of the relationship")

    def __str__(self) -> str:
        """Return a string representation of the requirement link."""
        return f"{self.source_id} --{self.link_type}--> {self.target_id}"

    def __repr__(self) -> str:
        """Return a detailed representation of the requirement link."""
        return f"RequirementLink(source='{self.source_id}', target='{self.target_id}', type='{self.link_type}')"


class ExtendedRequirement(BaseModel):
    """Full requirement tracking with status, validation, and implementation details."""

    id: str = Field(..., description="Unique requirement identifier")
    title: str = Field(..., description="Brief requirement title")
    description: str = Field(..., description="Full requirement description")
    priority: RequirementPriority = Field(..., description="Requirement priority")
    category: RequirementCategory = Field(..., description="Requirement category")
    status: RequirementStatus = Field(RequirementStatus.PENDING, description="Current status")
    acceptance_criteria: List[str] = Field(
        default_factory=list, description="Measurable acceptance criteria"
    )
    validation_rules: List[ValidationRule] = Field(
        default_factory=list, description="Validation rules for the requirement"
    )
    implementation_components: List[str] = Field(
        default_factory=list, description="Components that implement this requirement"
    )
    test_cases: List[str] = Field(
        default_factory=list, description="Test case IDs that verify this requirement"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    notes: str = Field("", description="Additional notes or comments")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    def is_complete(self) -> bool:
        """Check if requirement is implemented and verified.

        Returns:
            True if status is VERIFIED, False otherwise
        """
        return self.status == RequirementStatus.VERIFIED

    def add_implementation(self, component_name: str) -> None:
        """Link component to requirement.

        Args:
            component_name: Name of the implementing component
        """
        if component_name not in self.implementation_components:
            self.implementation_components.append(component_name)
            self.updated_at = datetime.now()
            if self.status == RequirementStatus.PENDING:
                self.status = RequirementStatus.IN_PROGRESS

    def add_test_case(self, test_case_id: str) -> None:
        """Add a test case that verifies this requirement.

        Args:
            test_case_id: Identifier of the test case
        """
        if test_case_id not in self.test_cases:
            self.test_cases.append(test_case_id)
            self.updated_at = datetime.now()

    def mark_implemented(self) -> None:
        """Mark the requirement as implemented."""
        if self.status in [RequirementStatus.PENDING, RequirementStatus.IN_PROGRESS]:
            self.status = RequirementStatus.IMPLEMENTED
            self.updated_at = datetime.now()

    def mark_verified(self) -> None:
        """Mark the requirement as verified."""
        self.status = RequirementStatus.VERIFIED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()

    def __str__(self) -> str:
        """Return a string representation of the requirement."""
        return f"[{self.priority.value}] {self.title} ({self.status.value})"

    def __repr__(self) -> str:
        """Return a detailed representation of the requirement."""
        return f"ExtendedRequirement(id='{self.id}', title='{self.title}', status={self.status})"

    @field_validator("status")
    @classmethod
    def validate_status_transition(cls, v: RequirementStatus, info) -> RequirementStatus:
        """Validate status transitions follow logical progression.

        Args:
            v: New status value
            info: Validation context

        Returns:
            Validated status

        Note: This is a simple validator. In production, you might want to
        check the previous status to ensure valid transitions.
        """
        return v


class RequirementsMatrix(BaseModel):
    """Track requirements relationships and coverage across the system."""

    requirements: List[ExtendedRequirement] = Field(
        default_factory=list, description="All requirements in the matrix"
    )
    links: List[RequirementLink] = Field(
        default_factory=list, description="Links between requirements"
    )
    coverage_targets: Dict[str, float] = Field(
        default_factory=dict, description="Coverage targets by category"
    )

    def add_requirement(self, requirement: ExtendedRequirement) -> None:
        """Add a requirement to the matrix.

        Args:
            requirement: The requirement to add
        """
        # Check for duplicate IDs
        existing_ids = {req.id for req in self.requirements}
        if requirement.id not in existing_ids:
            self.requirements.append(requirement)

    def add_link(
        self, source_id: str, target_id: str, link_type: str, description: str = ""
    ) -> None:
        """Add a link between requirements.

        Args:
            source_id: Source requirement ID
            target_id: Target requirement ID
            link_type: Type of relationship
            description: Optional description
        """
        link = RequirementLink(
            source_id=source_id, target_id=target_id, link_type=link_type, description=description
        )
        self.links.append(link)

    def get_uncovered_requirements(self) -> List[ExtendedRequirement]:
        """Find unimplemented requirements.

        Returns:
            List of requirements without implementation components
        """
        return [
            req
            for req in self.requirements
            if not req.implementation_components and req.status != RequirementStatus.DEFERRED
        ]

    def get_unverified_requirements(self) -> List[ExtendedRequirement]:
        """Find requirements that are implemented but not verified.

        Returns:
            List of requirements with IMPLEMENTED status
        """
        return [req for req in self.requirements if req.status == RequirementStatus.IMPLEMENTED]

    def get_requirements_by_status(self, status: RequirementStatus) -> List[ExtendedRequirement]:
        """Get requirements filtered by status.

        Args:
            status: Status to filter by

        Returns:
            List of requirements with the specified status
        """
        return [req for req in self.requirements if req.status == status]

    def get_requirements_by_category(
        self, category: RequirementCategory
    ) -> List[ExtendedRequirement]:
        """Get requirements filtered by category.

        Args:
            category: Category to filter by

        Returns:
            List of requirements in the specified category
        """
        return [req for req in self.requirements if req.category == category]

    def get_requirements_by_priority(
        self, priority: RequirementPriority
    ) -> List[ExtendedRequirement]:
        """Get requirements filtered by priority.

        Args:
            priority: Priority to filter by

        Returns:
            List of requirements with the specified priority
        """
        return [req for req in self.requirements if req.priority == priority]

    def get_coverage_stats(self) -> Dict[str, Any]:
        """Calculate implementation and verification percentages.

        Returns:
            Dictionary with coverage statistics
        """
        total = len(self.requirements)
        if total == 0:
            return {
                "total_requirements": 0,
                "implemented": 0,
                "verified": 0,
                "implementation_percentage": 0.0,
                "verification_percentage": 0.0,
                "by_category": {},
                "by_priority": {},
            }

        implemented = sum(
            1
            for req in self.requirements
            if req.status in [RequirementStatus.IMPLEMENTED, RequirementStatus.VERIFIED]
        )
        verified = sum(1 for req in self.requirements if req.status == RequirementStatus.VERIFIED)

        # Calculate by category
        by_category: Dict[str, Dict[str, Any]] = {}
        for category in RequirementCategory:
            cat_reqs = self.get_requirements_by_category(category)
            if cat_reqs:
                cat_implemented = sum(
                    1
                    for req in cat_reqs
                    if req.status in [RequirementStatus.IMPLEMENTED, RequirementStatus.VERIFIED]
                )
                cat_verified = sum(
                    1 for req in cat_reqs if req.status == RequirementStatus.VERIFIED
                )
                by_category[category.value] = {
                    "total": len(cat_reqs),
                    "implemented": cat_implemented,
                    "verified": cat_verified,
                    "implementation_percentage": (cat_implemented / len(cat_reqs)) * 100,
                    "verification_percentage": (cat_verified / len(cat_reqs)) * 100,
                }

        # Calculate by priority
        by_priority: Dict[str, Dict[str, Any]] = {}
        for priority in RequirementPriority:
            pri_reqs = self.get_requirements_by_priority(priority)
            if pri_reqs:
                pri_implemented = sum(
                    1
                    for req in pri_reqs
                    if req.status in [RequirementStatus.IMPLEMENTED, RequirementStatus.VERIFIED]
                )
                pri_verified = sum(
                    1 for req in pri_reqs if req.status == RequirementStatus.VERIFIED
                )
                by_priority[priority.value] = {
                    "total": len(pri_reqs),
                    "implemented": pri_implemented,
                    "verified": pri_verified,
                    "implementation_percentage": (pri_implemented / len(pri_reqs)) * 100,
                    "verification_percentage": (pri_verified / len(pri_reqs)) * 100,
                }

        return {
            "total_requirements": total,
            "implemented": implemented,
            "verified": verified,
            "implementation_percentage": (implemented / total) * 100,
            "verification_percentage": (verified / total) * 100,
            "by_category": by_category,
            "by_priority": by_priority,
        }

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build a dependency graph from requirement links.

        Returns:
            Dictionary mapping requirement IDs to their dependencies
        """
        graph: Dict[str, Set[str]] = {}
        for link in self.links:
            if link.link_type == "depends_on":
                if link.source_id not in graph:
                    graph[link.source_id] = set()
                graph[link.source_id].add(link.target_id)
        return graph

    def __str__(self) -> str:
        """Return a string representation of the requirements matrix."""
        stats = self.get_coverage_stats()
        return (
            f"RequirementsMatrix({stats['total_requirements']} requirements, "
            f"{stats['implementation_percentage']:.1f}% implemented, "
            f"{stats['verification_percentage']:.1f}% verified)"
        )

    def __repr__(self) -> str:
        """Return a detailed representation of the requirements matrix."""
        return f"RequirementsMatrix(requirements={len(self.requirements)}, links={len(self.links)})"
