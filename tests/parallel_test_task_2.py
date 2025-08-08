#!/usr/bin/env python3
"""
Parallel Test Task 2 - Timestamp Execution
This script writes timestamps to demonstrate parallel execution capabilities.
"""

from datetime import datetime
from pathlib import Path
import time


def main():
    # Write start timestamp
    timestamp = datetime.now().isoformat()
    Path("/tmp/parallel-task-2.txt").write_text(f"Task 2 executed at: {timestamp}\n")
    print(f"Task 2 executed at: {timestamp}")

    # Wait 3 seconds
    time.sleep(3)

    # Write completion timestamp
    completion = datetime.now().isoformat()
    Path("/tmp/parallel-task-2-done.txt").write_text(
        f"Task 2 completed at: {completion}\n"
    )
    print(f"Task 2 completed at: {completion}")


if __name__ == "__main__":
    main()
