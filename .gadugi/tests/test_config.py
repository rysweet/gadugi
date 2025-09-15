"""Central configuration for test imports."""

import os
import sys

# Get the absolute path to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the src/src directory containing all the modules
SRC_PATH = os.path.join(PROJECT_ROOT, "src", "src")


def setup_test_paths():
    """Setup Python paths for tests to find modules."""
    if SRC_PATH not in sys.path:
        sys.path.insert(0, SRC_PATH)


# Automatically setup paths when this module is imported
setup_test_paths()
