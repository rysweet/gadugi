"""
Recipe Executor - Self-hosting build system for transforming recipes into code.

This package implements a complete recipe-driven development system that can
generate, validate, and deploy production-quality code from structured recipes.
"""

__version__ = "1.0.0"
__author__ = "Recipe Executor Team"

from .recipe_model import Recipe, Requirements, Design, Components
from .recipe_parser import RecipeParser
from .orchestrator import RecipeOrchestrator
from .claude_code_generator import ClaudeCodeGenerator

__all__ = [
    "Recipe",
    "Requirements", 
    "Design",
    "Components",
    "RecipeParser",
    "RecipeOrchestrator",
    "ClaudeCodeGenerator"
]