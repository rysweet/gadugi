"""
OrchestratorAgent Source Package

This package contains the extracted implementation code for the OrchestratorAgent,
following the "bricks & studs" modular architecture philosophy.
"""

from .core import OrchestratorCore, OrchestrationRecoveryManager
from .utils import (
    TaskAnalysisUtils,
    ResourceMonitor,
    PromptFileParser,
    TaskIdGenerator,
    FileSystemUtils,
    ConfigurationManager
)

# Expose main classes for external usage
__all__ = [
    'OrchestratorCore',
    'OrchestrationRecoveryManager',
    'TaskAnalysisUtils',
    'ResourceMonitor',
    'PromptFileParser',
    'TaskIdGenerator',
    'FileSystemUtils',
    'ConfigurationManager'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Gadugi Agent System'
__description__ = 'Parallel workflow orchestration for multi-agent development'