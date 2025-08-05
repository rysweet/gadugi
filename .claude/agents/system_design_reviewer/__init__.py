"""
System Design Review Agent - Automated architectural review and documentation maintenance

This module provides automated analysis of code changes for architectural impact,
maintains system design documentation, and generates Architecture Decision Records (ADRs).
"""

from .core import SystemDesignReviewer
from .ast_parser import ASTParserFactory, ArchitecturalElement, ArchitecturalChange
from .documentation_manager import DocumentationManager
from .adr_generator import ADRGenerator

__version__ = "1.0.0"
__all__ = [
    "SystemDesignReviewer",
    "ASTParserFactory", 
    "ArchitecturalElement",
    "ArchitecturalChange",
    "DocumentationManager",
    "ADRGenerator"
]