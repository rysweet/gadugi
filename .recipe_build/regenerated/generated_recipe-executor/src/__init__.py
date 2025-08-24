"""Recipe Executor - Self-hosting build system for AI-powered code generation."""

__version__ = "0.1.0"
__author__ = "Gadugi System"

from .orchestrator import RecipeOrchestrator
from .recipe_model import Recipe, Requirements, Design, Components
from .recipe_parser import RecipeParser
from .recipe_validator import RecipeValidator
from .dependency_resolver import DependencyResolver
from .claude_code_generator import ClaudeCodeGenerator
from .state_manager import StateManager
from .quality_gates import QualityGates

__all__ = [
    "RecipeOrchestrator",
    "Recipe",
    "Requirements",
    "Design",
    "Components",
    "RecipeParser",
    "RecipeValidator",
    "DependencyResolver",
    "ClaudeCodeGenerator",
    "StateManager",
    "QualityGates",
]