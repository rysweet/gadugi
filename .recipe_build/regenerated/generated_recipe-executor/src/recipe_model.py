"""Recipe model data structures for Recipe Executor."""

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class RequirementPriority(Enum):
    """Priority levels for requirements."""
    MUST = "MUST"
    SHOULD = "SHOULD"
    COULD = "COULD"
    WONT = "WONT"


class ComponentType(Enum):
    """Types of components that can be built."""
    SERVICE = "SERVICE"
    AGENT = "AGENT"
    LIBRARY = "LIBRARY"
    TOOL = "TOOL"
    CORE = "CORE"
    APPLICATION = "APPLICATION"


@dataclass
class Requirement:
    """Single requirement with validation criteria."""
    id: str  # e.g., "req_1"
    description: str
    priority: RequirementPriority
    validation_criteria: List[str]
    implemented: bool = False
    
    def is_must(self) -> bool:
        """Check if this is a MUST requirement."""
        return self.priority == RequirementPriority.MUST
    
    def is_testable(self) -> bool:
        """Check if requirement has testable criteria."""
        return len(self.validation_criteria) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority.value,
            "validation_criteria": self.validation_criteria,
            "implemented": self.implemented
        }


@dataclass
class Requirements:
    """Parsed requirements from requirements.md."""
    purpose: str
    functional_requirements: List[Requirement]
    non_functional_requirements: List[Requirement]
    success_criteria: List[str]
    
    def get_must_requirements(self) -> List[Requirement]:
        """Get only MUST priority requirements."""
        must_reqs = []
        for req in self.functional_requirements:
            if req.is_must():
                must_reqs.append(req)
        for req in self.non_functional_requirements:
            if req.is_must():
                must_reqs.append(req)
        return must_reqs
    
    def get_all(self) -> List[Requirement]:
        """Get all requirements."""
        return self.functional_requirements + self.non_functional_requirements
    
    def get_testable_requirements(self) -> List[Requirement]:
        """Get requirements with testable criteria."""
        return [req for req in self.get_all() if req.is_testable()]
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for change detection."""
        content = json.dumps({
            "purpose": self.purpose,
            "functional": [r.to_dict() for r in self.functional_requirements],
            "non_functional": [r.to_dict() for r in self.non_functional_requirements],
            "success_criteria": self.success_criteria
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class Interface:
    """Interface specification for a component."""
    name: str
    description: str
    methods: List[str]
    properties: List[str]
    return_types: Dict[str, str] = field(default_factory=dict)


@dataclass
class ComponentDesign:
    """Design specification for a single component."""
    name: str
    description: str
    class_name: Optional[str]
    methods: List[str]
    properties: List[str]
    code_snippet: Optional[str]
    dependencies: List[str] = field(default_factory=list)
    
    def has_implementation_detail(self) -> bool:
        """Check if design has implementation details."""
        return self.code_snippet is not None and len(self.code_snippet.strip()) > 0
    
    def get_public_methods(self) -> List[str]:
        """Get public methods (not starting with underscore)."""
        return [m for m in self.methods if not m.startswith('_')]


@dataclass
class Design:
    """Parsed design from design.md."""
    architecture: str
    components: List[ComponentDesign]
    interfaces: List[Interface]
    implementation_notes: str
    code_blocks: List[str]  # Example code snippets
    language: str = "python"
    
    def get_component_by_name(self, name: str) -> Optional[ComponentDesign]:
        """Find component by name."""
        for component in self.components:
            if component.name == name:
                return component
        return None
    
    def get_all_dependencies(self) -> List[str]:
        """Get all unique dependencies from components."""
        deps = set()
        for component in self.components:
            deps.update(component.dependencies)
        return list(deps)
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for change detection."""
        content = json.dumps({
            "architecture": self.architecture,
            "components": [{"name": c.name, "class": c.class_name} for c in self.components],
            "implementation_notes": self.implementation_notes,
            "language": self.language
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class Components:
    """Recipe metadata from components.json."""
    name: str  # Recipe name
    version: str  # Recipe version (e.g., "1.0.0")
    type: ComponentType
    dependencies: List[str]  # Names of other recipes this depends on
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_self_hosting(self) -> bool:
        """Check if this is a self-hosting component."""
        return self.metadata.get("self_hosting", False)
    
    def has_external_dependencies(self) -> bool:
        """Check if component has external dependencies."""
        return len(self.dependencies) > 0
    
    def calculate_checksum(self) -> str:
        """Calculate checksum for change detection."""
        content = json.dumps({
            "name": self.name,
            "version": self.version,
            "type": self.type.value,
            "dependencies": sorted(self.dependencies),
            "metadata": self.metadata
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class RecipeMetadata:
    """Metadata about a recipe for tracking and caching."""
    created_at: datetime
    last_modified: datetime
    checksum: str
    author: str = "recipe-executor"
    tags: List[str] = field(default_factory=list)
    
    def update_checksum(self, new_checksum: str):
        """Update checksum and modification time."""
        self.checksum = new_checksum
        self.last_modified = datetime.now()
    
    def is_newer_than(self, timestamp: datetime) -> bool:
        """Check if recipe was modified after given timestamp."""
        return self.last_modified > timestamp


@dataclass
class Recipe:
    """Represents a complete recipe with all components."""
    name: str
    path: Path
    requirements: Requirements
    design: Design
    components: Components
    metadata: RecipeMetadata
    
    def get_dependencies(self) -> List[str]:
        """Get list of recipe dependencies."""
        return self.components.dependencies
    
    def get_checksum(self) -> str:
        """Calculate combined checksum of recipe files for change detection."""
        # Combine checksums of all recipe components
        combined = (
            self.requirements.calculate_checksum() +
            self.design.calculate_checksum() +
            self.components.calculate_checksum()
        )
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Basic validation of recipe structure."""
        # Must have at least one requirement
        if not self.requirements.get_all():
            return False
        
        # Must have at least one component design
        if not self.design.components:
            return False
        
        # Name must match in components
        if self.name != self.components.name:
            return False
        
        return True
    
    def get_complexity_score(self) -> int:
        """Calculate complexity score for decomposition decisions."""
        score = 0
        
        # Score based on number of requirements
        req_count = len(self.requirements.get_all())
        if req_count > 20:
            score += 3
        elif req_count > 10:
            score += 2
        elif req_count > 5:
            score += 1
        
        # Score based on number of components
        comp_count = len(self.design.components)
        if comp_count > 10:
            score += 3
        elif comp_count > 5:
            score += 2
        elif comp_count > 3:
            score += 1
        
        # Score based on dependencies
        dep_count = len(self.get_dependencies())
        if dep_count > 5:
            score += 2
        elif dep_count > 2:
            score += 1
        
        # Score based on code complexity (code blocks)
        if len(self.design.code_blocks) > 10:
            score += 2
        elif len(self.design.code_blocks) > 5:
            score += 1
        
        return score
    
    def needs_decomposition(self) -> bool:
        """Check if recipe needs decomposition based on complexity."""
        return self.get_complexity_score() >= 5
    
    def to_summary(self) -> str:
        """Generate a summary of the recipe."""
        return (
            f"Recipe: {self.name}\n"
            f"Type: {self.components.type.value}\n"
            f"Version: {self.components.version}\n"
            f"Requirements: {len(self.requirements.get_all())} "
            f"({len(self.requirements.get_must_requirements())} MUST)\n"
            f"Components: {len(self.design.components)}\n"
            f"Dependencies: {', '.join(self.get_dependencies()) or 'None'}\n"
            f"Complexity Score: {self.get_complexity_score()}/10\n"
            f"Self-Hosting: {self.components.is_self_hosting()}"
        )