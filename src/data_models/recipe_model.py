"""Core Recipe model with metadata, requirements, design, and components.

This module defines the main Recipe class and its nested structures for representing
a complete recipe specification in the Recipe Executor system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class RequirementPriority(str, Enum):
    """Priority levels for requirements."""

    MUST = "MUST"
    SHOULD = "SHOULD"
    COULD = "COULD"


class ComponentType(str, Enum):
    """Types of components that can be generated."""

    SERVICE = "SERVICE"
    LIBRARY = "LIBRARY"
    CLI = "CLI"
    AGENT = "AGENT"
    MODULE = "MODULE"


class RecipeMetadata(BaseModel):
    """Metadata for a recipe including version and authorship information."""

    name: str = Field(..., description="Name of the recipe")
    version: str = Field(..., description="Semantic version of the recipe")
    description: str = Field(..., description="Brief description of what the recipe creates")
    author: str = Field(..., description="Author of the recipe")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    license: Optional[str] = Field(None, description="License for generated code")

    def __str__(self) -> str:
        """Return a string representation of the metadata."""
        return f"{self.name} v{self.version} by {self.author}"

    def __repr__(self) -> str:
        """Return a detailed representation of the metadata."""
        return (
            f"RecipeMetadata(name='{self.name}', version='{self.version}', author='{self.author}')"
        )


class Requirement(BaseModel):
    """Individual requirement with priority and description."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique requirement ID")
    priority: RequirementPriority = Field(..., description="Requirement priority level")
    description: str = Field(..., description="Full description of the requirement")
    category: str = Field("general", description="Category for grouping requirements")
    acceptance_criteria: List[str] = Field(
        default_factory=list, description="Measurable acceptance criteria"
    )

    def __str__(self) -> str:
        """Return a string representation of the requirement."""
        return f"[{self.priority.value}] {self.description[:50]}..."

    def __repr__(self) -> str:
        """Return a detailed representation of the requirement."""
        return f"Requirement(id='{self.id}', priority={self.priority}, category='{self.category}')"


class Requirements(BaseModel):
    """Collection of functional and non-functional requirements."""

    functional: List[Requirement] = Field(
        default_factory=list, description="Functional requirements"
    )
    non_functional: List[Requirement] = Field(
        default_factory=list, description="Non-functional requirements"
    )

    def get_by_priority(self, priority: RequirementPriority) -> List[Requirement]:
        """Filter requirements by priority level.

        Args:
            priority: The priority level to filter by

        Returns:
            List of requirements with the specified priority
        """
        all_requirements = self.functional + self.non_functional
        return [req for req in all_requirements if req.priority == priority]

    def count(self) -> Dict[str, int]:
        """Count requirements by category.

        Returns:
            Dictionary with counts for functional and non-functional requirements
        """
        return {
            "functional": len(self.functional),
            "non_functional": len(self.non_functional),
            "total": len(self.functional) + len(self.non_functional),
        }

    def get_all(self) -> List[Requirement]:
        """Get all requirements combined.

        Returns:
            List of all functional and non-functional requirements
        """
        return self.functional + self.non_functional

    def __str__(self) -> str:
        """Return a string representation of the requirements."""
        counts = self.count()
        return f"Requirements(functional={counts['functional']}, non_functional={counts['non_functional']})"


class ComponentDesign(BaseModel):
    """Design specification for a single component."""

    name: str = Field(..., description="Component name")
    type: ComponentType = Field(..., description="Type of component")
    path: str = Field(..., description="Path where component will be generated")
    interfaces: List[str] = Field(default_factory=list, description="Public interfaces exposed")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    description: str = Field("", description="Description of component purpose")
    implementation_notes: Optional[str] = Field(None, description="Implementation-specific notes")

    def __str__(self) -> str:
        """Return a string representation of the component design."""
        return f"{self.name} ({self.type.value}) at {self.path}"

    def __repr__(self) -> str:
        """Return a detailed representation of the component design."""
        return f"ComponentDesign(name='{self.name}', type={self.type}, path='{self.path}')"


class Design(BaseModel):
    """Overall design specification for the recipe."""

    overview: str = Field(..., description="High-level design overview")
    technology_choices: Dict[str, str] = Field(
        default_factory=dict, description="Technology stack decisions"
    )
    components: List[ComponentDesign] = Field(
        default_factory=list, description="Component specifications"
    )
    patterns: List[str] = Field(default_factory=list, description="Design patterns to be applied")
    constraints: List[str] = Field(default_factory=list, description="Design constraints")

    def get_component(self, name: str) -> Optional[ComponentDesign]:
        """Find a component by name.

        Args:
            name: Name of the component to find

        Returns:
            ComponentDesign if found, None otherwise
        """
        for component in self.components:
            if component.name == name:
                return component
        return None

    def __str__(self) -> str:
        """Return a string representation of the design."""
        return f"Design with {len(self.components)} components"


class Components(BaseModel):
    """Component registry with dependency information."""

    name: str = Field(..., description="Component name")
    version: str = Field("1.0.0", description="Component version")
    type: ComponentType = Field(..., description="Component type")
    dependencies: List[str] = Field(
        default_factory=list, description="Dependencies on other components"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def __str__(self) -> str:
        """Return a string representation of the component."""
        return f"{self.name} v{self.version} ({self.type.value})"

    def __repr__(self) -> str:
        """Return a detailed representation of the component."""
        return f"Components(name='{self.name}', version='{self.version}', type={self.type})"


class Recipe(BaseModel):
    """Complete recipe specification with all nested structures."""

    id: UUID = Field(default_factory=uuid4, description="Unique recipe identifier")
    metadata: RecipeMetadata = Field(..., description="Recipe metadata")
    requirements: Requirements = Field(..., description="Recipe requirements")
    design: Design = Field(..., description="Recipe design specification")
    components: List[Components] = Field(default_factory=list, description="Component registry")
    dependencies: List[str] = Field(
        default_factory=list, description="External recipe dependencies"
    )
    build_order: List[str] = Field(default_factory=list, description="Component build order")

    def get_dependencies(self) -> List[str]:
        """Return list of recipe dependencies.

        Returns:
            List of external recipe dependencies
        """
        return self.dependencies

    def is_valid(self) -> bool:
        """Check if recipe is complete and valid.

        Returns:
            True if recipe has all required fields and is consistent
        """
        # Check basic required fields
        if not self.metadata.name or not self.metadata.version:
            return False

        # Check requirements exist
        if self.requirements.count()["total"] == 0:
            return False

        # Check design has components
        if len(self.design.components) == 0:
            return False

        # Check build order matches components if specified
        if self.build_order:
            component_names = {comp.name for comp in self.components}
            build_names = set(self.build_order)
            if build_names != component_names:
                return False

        return True

    def to_summary(self) -> str:
        """Generate human-readable summary.

        Returns:
            Formatted summary string of the recipe
        """
        req_counts = self.requirements.count()
        summary_lines = [
            f"Recipe: {self.metadata.name} v{self.metadata.version}",
            f"Author: {self.metadata.author}",
            f"Description: {self.metadata.description}",
            "",
            "Requirements:",
            f"  - Functional: {req_counts['functional']}",
            f"  - Non-functional: {req_counts['non_functional']}",
            "",
            "Design:",
            f"  - Components: {len(self.design.components)}",
            f"  - Patterns: {', '.join(self.design.patterns) if self.design.patterns else 'None'}",
            "",
            "Components:",
        ]

        for comp in self.components:
            summary_lines.append(f"  - {comp.name} ({comp.type.value})")

        if self.dependencies:
            summary_lines.extend(["", "Dependencies:"])
            for dep in self.dependencies:
                summary_lines.append(f"  - {dep}")

        return "\n".join(summary_lines)

    def __str__(self) -> str:
        """Return a string representation of the recipe."""
        return f"Recipe({self.metadata.name} v{self.metadata.version})"

    def __repr__(self) -> str:
        """Return a detailed representation of the recipe."""
        return (
            f"Recipe(id={self.id}, name='{self.metadata.name}', version='{self.metadata.version}')"
        )

    @field_validator("build_order")
    @classmethod
    def validate_build_order(cls, v: List[str], info) -> List[str]:
        """Validate that build order references existing components.

        Args:
            v: Build order list
            info: Validation context

        Returns:
            Validated build order

        Raises:
            ValueError: If build order references non-existent components
        """
        if not v:
            return v

        # Can't validate against components during initial construction
        # This will be checked in is_valid() method
        return v
