#!/usr/bin/env python3
"""Monitor the self-hosting test v2 progress."""

import time
import subprocess
from pathlib import Path
from datetime import datetime

def get_latest_test_dir():
    """Find the latest test directory."""
    base = Path(".recipe_build")
    if not base.exists():
        return None
    
    test_dirs = sorted([d for d in base.iterdir() if d.name.startswith("self_host_test_")])
    return test_dirs[-1] if test_dirs else None

def count_files(directory):
    """Count Python files in directory."""
    if not directory or not directory.exists():
        return 0
    count = 0
    for f in directory.rglob("*.py"):
        if "venv" not in str(f) and ".venv" not in str(f):
            count += 1
    return count

def main():
    print("Monitoring self-hosting test v2...")
    print("=" * 70)
    
    while True:
        test_dir = get_latest_test_dir()
        if test_dir:
            gen2_dir = test_dir / "gen2"
            gen3_dir = test_dir / "gen3"
            
            gen2_files = count_files(gen2_dir)
            gen3_files = count_files(gen3_dir)
            
            # Check log file
            log_file = Path("self_hosting_test_v2.log")
            if log_file.exists():
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    last_line = lines[-1].strip() if lines else "Starting..."
                    
                    # Look for key status messages
                    for line in reversed(lines[-20:]):
                        if "GENERATION" in line or "ERROR" in line or "PASSED" in line or "FAILED" in line:
                            last_line = line.strip()
                            break
            else:
                last_line = "Waiting for log..."
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Test Status:")
            print(f"  Test dir: {test_dir.name}")
            print(f"  Gen2 files: {gen2_files}")
            print(f"  Gen3 files: {gen3_files}")
            print(f"  Status: {last_line[:80]}...")
            print("-" * 70)
        else:
            print("No test directory found yet...")
        
        time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")