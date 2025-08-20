"""Recipe Executor - Self-hosting build system for Gadugi."""

from .recipe_model import Recipe, Requirements, Design, Components
from .recipe_parser import RecipeParser
from .dependency_resolver import DependencyResolver
from .code_generator import CodeGenerator
from .test_generator import TestGenerator
from .validator import Validator
from .orchestrator import RecipeOrchestrator
from .state_manager import StateManager

__version__ = "1.0.0"

__all__ = [
    "Recipe",
    "Requirements",
    "Design",
    "Components",
    "RecipeParser",
    "DependencyResolver",
    "CodeGenerator",
    "TestGenerator",
    "Validator",
    "RecipeOrchestrator",
    "StateManager",
]
