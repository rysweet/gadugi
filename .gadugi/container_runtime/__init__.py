"""
Container Runtime for Gadugi Multi-Agent System

This module provides secure containerized execution for the Gadugi system,
replacing direct shell execution with isolated container boundaries.
"""

from .container_manager import ContainerManager
from .security_policy import SecurityPolicyEngine
from .resource_manager import ResourceManager
from .audit_logger import AuditLogger
from .image_manager import ImageManager
from .execution_engine import ContainerExecutionEngine

__version__ = "1.0.0"
__all__ = [
    "ContainerManager",
    "SecurityPolicyEngine",
    "ResourceManager",
    "AuditLogger",
    "ImageManager",
    "ContainerExecutionEngine",
]
