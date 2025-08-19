"""
Gadugi - Multi-Agent System for AI-Assisted Coding

A comprehensive multi-agent system built on Claude Code that provides
intelligent orchestration, workflow management, and AI-assisted development
capabilities.
"""

__version__ = "0.1.0"
__author__ = "Gadugi Contributors"
__description__ = "Multi-Agent System for AI-Assisted Coding"
__license__ = "MIT"

# Core version info
VERSION_INFO = {"major": 0, "minor": 1, "patch": 0, "release": "stable"}

def get_version():
    """Get the current version string."""
    return __version__

def get_version_info():
    """Get detailed version information."""
    return VERSION_INFO.copy()
