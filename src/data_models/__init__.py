"""Data models package for Recipe Executor.

This package provides comprehensive data models using Pydantic v2 for the Recipe Executor system,
including models for recipes, requirements, design, execution state, and validation.
"""

# Recipe Model exports
from .recipe_model import (
    ComponentType,
    Components,
    Design,
    Recipe,
    RecipeMetadata,
    Requirement,
    RequirementPriority,
    Requirements,
    ComponentDesign,
)

# Requirements Model exports
from .requirements_model import (
    ExtendedRequirement,
    RequirementCategory,
    RequirementLink,
    RequirementStatus,
    RequirementsMatrix,
    ValidationRule as RequirementValidationRule,
)

# Design Model exports
from .design_model import (
    ComponentArchitecture,
    Dependency,
    DesignPattern,
    Interface,
    InterfaceType,
    MethodSignature,
    SystemArchitecture,
)

# Execution Model exports
from .execution_model import (
    ComponentStatus,
    ErrorSeverity,
    ExecutionError,
    ExecutionPhase,
    ExecutionReport,
    ExecutionState,
    GenerationResult,
    TestResult,
)

# Validation Model exports
from .validation_model import (
    ValidationCategory,
    ValidationContext,
    ValidationError,
    ValidationInfo,
    ValidationIssue,
    ValidationReport,
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
    ValidationWarning,
)

__all__ = [
    # Recipe Model
    "ComponentType",
    "Components",
    "Design",
    "Recipe",
    "RecipeMetadata",
    "Requirement",
    "RequirementPriority",
    "Requirements",
    "ComponentDesign",
    # Requirements Model
    "ExtendedRequirement",
    "RequirementCategory",
    "RequirementLink",
    "RequirementStatus",
    "RequirementsMatrix",
    "RequirementValidationRule",
    # Design Model
    "ComponentArchitecture",
    "Dependency",
    "DesignPattern",
    "Interface",
    "InterfaceType",
    "MethodSignature",
    "SystemArchitecture",
    # Execution Model
    "ComponentStatus",
    "ErrorSeverity",
    "ExecutionError",
    "ExecutionPhase",
    "ExecutionReport",
    "ExecutionState",
    "GenerationResult",
    "TestResult",
    # Validation Model
    "ValidationCategory",
    "ValidationContext",
    "ValidationError",
    "ValidationInfo",
    "ValidationIssue",
    "ValidationReport",
    "ValidationResult",
    "ValidationRule",
    "ValidationSeverity",
    "ValidationWarning",
]

__version__ = "1.0.0"
