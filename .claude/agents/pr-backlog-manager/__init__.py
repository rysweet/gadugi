"""
PR Backlog Manager for Gadugi Multi-Agent System.

This module provides automated PR backlog management capabilities including:
- PR readiness assessment
- Merge conflict detection
- CI/CD status monitoring
- Code review coordination
- Automated labeling and delegation
"""

from .core import PRBacklogManager
from .readiness_assessor import ReadinessAssessor
from .delegation_coordinator import DelegationCoordinator
from .github_actions_integration import GitHubActionsIntegration

__version__ = "1.0.0"
__author__ = "Gadugi AI System"

__all__ = [
    "PRBacklogManager",
    "ReadinessAssessor", 
    "DelegationCoordinator",
    "GitHubActionsIntegration"
]