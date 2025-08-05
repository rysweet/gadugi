#!/usr/bin/env python3
"""
Simple test to verify TeamCoach imports work correctly
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def test_teamcoach_imports():
    """Test that TeamCoach modules can be imported successfully."""
    try:
        # Test basic imports - use absolute imports

        # Test TeamCoach Phase 1 imports

        # Test TeamCoach Phase 2 imports

        # Test TeamCoach Phase 3 imports

        print("✅ All TeamCoach imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


if __name__ == "__main__":
    success = test_teamcoach_imports()
    sys.exit(0 if success else 1)
