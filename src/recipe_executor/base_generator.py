"""Abstract base class for code generators."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Any

from .recipe_model import Recipe, BuildContext, GeneratedCode


class BaseCodeGenerator(ABC):
    """Abstract base class for all code generators.
    
    This defines the interface that all code generators must implement,
    ensuring consistency across different generation strategies (Claude Code,
    templates, LLMs, etc.)
    """
    
    @abstractmethod
    def generate(self, recipe: Recipe, context: Optional[BuildContext] = None) -> GeneratedCode:
        """Generate code from a recipe.
        
        Args:
            recipe: The recipe to generate code from
            context: Optional build context with dependencies and options
            
        Returns:
            GeneratedCode object containing all generated files
            
        Raises:
            CodeGenerationError: If generation fails
        """
        pass


class CodeGenerationError(Exception):
    """Raised when code generation fails.
    
    This exception should include details about what failed and why,
    to help with debugging and error recovery.
    """
    
    def __init__(self, message: str, recipe_name: Optional[str] = None, 
                 component: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize with detailed error information.
        
        Args:
            message: Human-readable error message
            recipe_name: Name of the recipe being processed
            component: Specific component that failed
            details: Additional context about the failure
        """
        super().__init__(message)
        self.recipe_name = recipe_name
        self.component = component
        self.details = details or {}
        
        # Build comprehensive error message
        parts = [message]
        if recipe_name:
            parts.append(f"Recipe: {recipe_name}")
        if component:
            parts.append(f"Component: {component}")
        if details:
            parts.append(f"Details: {details}")
        
        self.message = "\n".join(parts)


class StubGenerationError(CodeGenerationError):
    """Raised when generated code contains stubs or placeholders."""
    
    def __init__(self, message: str, stub_locations: Optional[Dict[str, List[str]]] = None):
        """Initialize with stub location details.
        
        Args:
            message: Error message
            stub_locations: Dictionary of filename -> list of stub descriptions
        """
        super().__init__(message)
        self.stub_locations = stub_locations or {}