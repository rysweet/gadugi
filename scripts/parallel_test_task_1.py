#!/usr/bin/env python3
"""
Parallel Test Task 1 - Timestamp Writer

This script writes timestamps to files to test parallel execution capabilities.
It's part of the OrchestratorAgent testing suite.
"""

from datetime import datetime
from pathlib import Path
import time


def main():
    """Execute the parallel test task 1."""
    # Write initial timestamp
    timestamp = datetime.now().isoformat()
    initial_file = Path("/tmp/parallel-task-1.txt")
    initial_file.write_text(f"Task 1 executed at: {timestamp}\n")
    print(f"Task 1 executed at: {timestamp}")
    print(f"Written to: {initial_file}")

    # Wait 3 seconds
    print("Waiting 3 seconds...")
    time.sleep(3)

    # Write completion timestamp
    completion = datetime.now().isoformat()
    completion_file = Path("/tmp/parallel-task-1-done.txt")
    completion_file.write_text(f"Task 1 completed at: {completion}\n")
    print(f"Task 1 completed at: {completion}")
    print(f"Written to: {completion_file}")

    print("\nTask 1 successfully completed!")
    return 0


if __name__ == "__main__":
    exit(main())
