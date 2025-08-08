#!/usr/bin/env python3
"""
Parallel Test Task 3 - Timestamp Writer

This script is part of the parallel execution testing suite.
It writes timestamps to temporary files to verify concurrent execution.
"""

from datetime import datetime
from pathlib import Path
import time
import sys


def main():
    """Execute parallel test task 3."""
    try:
        # Write start timestamp
        start_timestamp = datetime.now().isoformat()
        start_file = Path("/tmp/parallel-task-3.txt")
        start_file.write_text(f"Task 3 executed at: {start_timestamp}\n")
        print(f"Task 3 executed at: {start_timestamp}")

        # Wait 3 seconds to simulate work
        print("Waiting 3 seconds...")
        time.sleep(3)

        # Write completion timestamp
        completion_timestamp = datetime.now().isoformat()
        completion_file = Path("/tmp/parallel-task-3-done.txt")
        completion_file.write_text(f"Task 3 completed at: {completion_timestamp}\n")
        print(f"Task 3 completed at: {completion_timestamp}")

        print("✓ Parallel test task 3 completed successfully")
        return 0

    except Exception as e:
        print(f"Error in parallel test task 3: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
