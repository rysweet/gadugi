#!/usr/bin/env python3
"""Test if we can import the shared modules."""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('.claude'))

try:
    from shared.utils.error_handling import ErrorSeverity
    print("✓ Successfully imported from shared.utils.error_handling")
except ImportError as e:
    print(f"✗ Failed to import from shared.utils.error_handling: {e}")

try:
    from shared.task_tracking import TaskStatus
    print("✓ Successfully imported from shared.task_tracking")
except ImportError as e:
    print(f"✗ Failed to import from shared.task_tracking: {e}")

try:
    from shared.state_management import TaskState
    print("✓ Successfully imported from shared.state_management")
except ImportError as e:
    print(f"✗ Failed to import from shared.state_management: {e}")

try:
    from shared.interfaces import AgentInterface
    print("✓ Successfully imported from shared.interfaces")
except ImportError as e:
    print(f"✗ Failed to import from shared.interfaces: {e}")

try:
    from shared.github_operations import GitHubOperations
    print("✓ Successfully imported from shared.github_operations")
except ImportError as e:
    print(f"✗ Failed to import from shared.github_operations: {e}")