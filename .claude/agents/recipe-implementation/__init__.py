"""Recipe Implementation Agent for Gadugi v0.3.

Automates implementation of components from recipe specifications.
"""

from .agent import RecipeImplementationAgent
from .code_evaluator import CodeEvaluator, EvaluationReport
from .code_generator import CodeGenerator, GeneratedCode
from .models import (
    RecipeSpec,
    RequirementType,
    ImplementationGap,
    ValidationResult,
    TestCase,
)
from .recipe_parser import RecipeParser
from .validator import ImplementationValidator

__all__ = [
    "RecipeImplementationAgent",
    "RecipeParser",
    "CodeEvaluator",
    "CodeGenerator",
    "ImplementationValidator",
    "RecipeSpec",
    "RequirementType",
    "ImplementationGap",
    "EvaluationReport",
    "GeneratedCode",
    "ValidationResult",
    "TestCase",
]

__version__ = "0.3.0"