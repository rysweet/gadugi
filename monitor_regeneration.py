#!/usr/bin/env python3

import time
import subprocess
from pathlib import Path
from datetime import datetime

def count_python_files(directory):
    """Count Python files excluding venv directories."""
    cmd = f"find {directory} -name '*.py' -not -path '*/venv/*' -not -path '*/.venv/*' 2>/dev/null | wc -l"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return int(result.stdout.strip())

def get_log_lines(log_file):
    """Count lines in log file."""
    if Path(log_file).exists():
        with open(log_file, 'r') as f:
            return sum(1 for _ in f)
    return 0

def get_last_action(log_file):
    """Get last action from log."""
    if Path(log_file).exists():
        cmd = f"tail -1 {log_file}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            # Extract the action after "INFO: "
            parts = result.stdout.strip().split(': ', 1)
            if len(parts) > 1:
                return parts[1]
    return "Starting..."

def monitor_generation():
    """Monitor the generation process."""
    gen_dir = ".recipe_build/self_host_test_20250909_030021/gen2"
    log_file = ".recipe_build/self_host_test_20250909_030021/Generation_1_to_2.log"
    
    print("Starting generation monitoring...")
    print("=" * 70)
    
    while True:
        py_files = count_python_files(gen_dir)
        log_lines = get_log_lines(log_file)
        last_action = get_last_action(log_file)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"[{timestamp}] Gen1→2 Status:")
        print(f"  Python files: {py_files}")
        print(f"  Log lines: {log_lines}")
        print(f"  Last action: {last_action}")
        print("-" * 70)
        
        time.sleep(30)

if __name__ == "__main__":
    try:
        monitor_generation()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
