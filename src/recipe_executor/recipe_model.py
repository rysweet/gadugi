"""Recipe data models for the Recipe Executor."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any
from enum import Enum
from datetime import datetime


class ComponentType(Enum):
    """Types of components that can be built from recipes."""
    SERVICE = "service"
    AGENT = "agent"
    LIBRARY = "library"
    TOOL = "tool"
    CORE = "core"


class RequirementPriority(Enum):
    """Priority levels for requirements."""
    MUST = "must"
    SHOULD = "should"
    COULD = "could"
    WONT = "wont"


@dataclass
class Requirement:
    """A single functional or non-functional requirement."""
    id: str
    description: str
    priority: RequirementPriority
    validation_criteria: list[str] = field(default_factory=list)
    implemented: bool = False


@dataclass
class Requirements:
    """Parsed requirements from requirements.md."""
    purpose: str
    functional_requirements: list[Requirement]
    non_functional_requirements: list[Requirement]
    success_criteria: list[str]
    
    def get_all_requirements(self) -> list[Requirement]:
        """Get all requirements regardless of type."""
        return self.functional_requirements + self.non_functional_requirements
    
    def get_must_requirements(self) -> list[Requirement]:
        """Get only MUST requirements."""
        return [r for r in self.get_all_requirements() if r.priority == RequirementPriority.MUST]


@dataclass
class ComponentDesign:
    """Design specification for a single component."""
    name: str
    description: str
    class_name: Optional[str] = None
    methods: list[str] = field(default_factory=list)
    properties: list[str] = field(default_factory=list)
    code_snippet: Optional[str] = None


@dataclass
class Interface:
    """Interface specification between components."""
    name: str
    description: str
    methods: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    data_types: list[str] = field(default_factory=list)


@dataclass
class Design:
    """Parsed design from design.md."""
    architecture: str
    components: list[ComponentDesign]
    interfaces: list[Interface]
    implementation_notes: str
    code_blocks: list[str] = field(default_factory=list)
    
    def get_component_by_name(self, name: str) -> Optional[ComponentDesign]:
        """Find a component by name."""
        for component in self.components:
            if component.name == name:
                return component
        return None


@dataclass
class Components:
    """Dependencies from components.json."""
    name: str
    version: str
    type: ComponentType
    dependencies: list[str] = field(default_factory=list)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    external_dependencies: dict[str, list[str]] = field(default_factory=dict)
    outputs: dict[str, list[str]] = field(default_factory=dict)
    
    def is_self_hosting(self) -> bool:
        """Check if this recipe is self-hosting."""
        return self.metadata.get("self_hosting", False)
    
    def requires_bootstrap(self) -> bool:
        """Check if bootstrap is required."""
        return self.metadata.get("bootstrap_required", False)


@dataclass
class RecipeMetadata:
    """Metadata about a recipe."""
    created_at: datetime
    updated_at: datetime
    author: str = "Recipe Executor"
    tags: list[str] = field(default_factory=list)
    build_count: int = 0
    last_build: Optional[datetime] = None
    checksum: Optional[str] = None


@dataclass
class Recipe:
    """Represents a complete recipe with all components."""
    name: str
    path: Path
    requirements: Requirements
    design: Design
    components: Components
    metadata: RecipeMetadata
    
    def __post_init__(self):
        """Validate recipe consistency."""
        if self.name != self.components.name:
            raise ValueError(f"Recipe name mismatch: {self.name} != {self.components.name}")
    
    def get_dependencies(self) -> list[str]:
        """Get list of recipe dependencies."""
        return self.components.dependencies
    
    def get_outputs(self) -> dict[str, list[str]]:
        """Get expected outputs from recipe."""
        return self.components.outputs
    
    def is_valid(self) -> bool:
        """Check if recipe is valid and complete."""
        # Check that we have all required parts
        if not self.requirements or not self.design or not self.components:
            return False
        
        # Check that we have at least one requirement
        if not self.requirements.get_all_requirements():
            return False
        
        # Check that we have at least one component in design
        if not self.design.components:
            return False
        
        return True


@dataclass
class BuildContext:
    """Context for building a recipe."""
    recipe: Recipe
    dependencies: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, str] = field(default_factory=dict)
    dry_run: bool = False
    verbose: bool = False
    force_rebuild: bool = False
    
    def get_dependency(self, name: str) -> Any:
        """Get a built dependency by name."""
        return self.dependencies.get(name)
    
    def has_dependency(self, name: str) -> bool:
        """Check if a dependency is available."""
        return name in self.dependencies


@dataclass
class GeneratedCode:
    """Code generated from a recipe."""
    recipe_name: str
    files: dict[str, str]  # filepath -> content
    language: str = "python"
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_file(self, path: str) -> Optional[str]:
        """Get generated file content by path."""
        return self.files.get(path)
    
    def add_file(self, path: str, content: str):
        """Add a generated file."""
        self.files[path] = content


@dataclass
class TestSuite:
    """Generated test suite for a recipe."""
    recipe_name: str
    unit_tests: list[str]
    integration_tests: list[str]
    test_files: dict[str, str]  # filepath -> content
    
    def get_all_tests(self) -> list[str]:
        """Get all test names."""
        return self.unit_tests + self.integration_tests


@dataclass
class ValidationResult:
    """Result of validating generated code against requirements."""
    recipe_name: str
    passed: bool
    requirements_coverage: dict[str, bool]  # requirement_id -> covered
    design_compliance: dict[str, bool]  # component_name -> compliant
    quality_gates: dict[str, bool]  # gate_name -> passed
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def get_coverage_percentage(self) -> float:
        """Calculate requirement coverage percentage."""
        if not self.requirements_coverage:
            return 0.0
        covered = sum(1 for covered in self.requirements_coverage.values() if covered)
        return (covered / len(self.requirements_coverage)) * 100
    
    def get_failed_requirements(self) -> list[str]:
        """Get list of uncovered requirements."""
        return [req_id for req_id, covered in self.requirements_coverage.items() if not covered]


@dataclass
class BuildResult:
    """Result of building one or more recipes."""
    results: list["SingleBuildResult"]
    success: bool
    total_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_failed_recipes(self) -> list[str]:
        """Get list of recipes that failed to build."""
        return [r.recipe.name for r in self.results if not r.success]
    
    def get_successful_recipes(self) -> list[str]:
        """Get list of successfully built recipes."""
        return [r.recipe.name for r in self.results if r.success]


@dataclass
class SingleBuildResult:
    """Result of building a single recipe."""
    recipe: Recipe
    code: Optional[GeneratedCode]
    tests: Optional[TestSuite]
    validation: Optional[ValidationResult]
    quality_result: dict[str, bool]  # tool_name -> passed
    success: bool
    build_time: float
    errors: list[str] = field(default_factory=list)
    
    def get_quality_failures(self) -> list[str]:
        """Get list of failed quality gates."""
        return [tool for tool, passed in self.quality_result.items() if not passed]