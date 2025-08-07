"""
Version information for Gadugi v0.3.

This module provides version information for all Gadugi components
and agents, ensuring consistent version display across the system.
"""

__version__ = "0.3.0"
VERSION = __version__

# Version display formatting
def get_version_string() -> str:
    """Get formatted version string for display."""
    return f"Gadugi v{VERSION}"

def get_full_version_info() -> dict[str, str]:
    """Get complete version information."""
    return {
        "version": VERSION,
        "major": "0",
        "minor": "3", 
        "patch": "0",
        "display": get_version_string()
    }

# For easy import
__all__ = ["__version__", "VERSION", "get_version_string", "get_full_version_info"]