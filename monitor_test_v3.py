#!/usr/bin/env python3
"""Monitor the self-hosting test v3 progress with quality iteration tracking."""

import time
import subprocess
from pathlib import Path
from datetime import datetime

def get_latest_test_dir():
    """Find the latest v3 test directory."""
    base = Path(".recipe_build")
    if not base.exists():
        return None
    
    test_dirs = sorted([d for d in base.iterdir() if d.name.startswith("self_host_test_v3_")])
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

def get_component_status(log_file):
    """Extract component recipe status from log."""
    components = {}
    current_component = None
    
    if log_file.exists():
        with open(log_file, "r") as f:
            for line in f:
                if "Component:" in line:
                    parts = line.split("Component:")
                    if len(parts) > 1:
                        component = parts[1].strip()
                        current_component = component
                        if component not in components:
                            components[component] = {"iterations": 0, "status": "running"}
                
                if current_component and "Iteration" in line and "for" in line:
                    try:
                        iter_num = int(line.split("Iteration")[1].split()[0])
                        components[current_component]["iterations"] = iter_num
                    except:
                        pass
                
                if current_component and "✅" in line and current_component in line:
                    components[current_component]["status"] = "complete"
                
                if "Quality gates failed, iterating to fix" in line and current_component:
                    components[current_component]["status"] = "iterating"
    
    return components

def main():
    print("Monitoring self-hosting test v3 with quality iteration...")
    print("=" * 70)
    
    while True:
        test_dir = get_latest_test_dir()
        if test_dir:
            gen2_dir = test_dir / "gen2"
            gen3_dir = test_dir / "gen3"
            
            gen2_files = count_files(gen2_dir)
            gen3_files = count_files(gen3_dir)
            
            # Check log file for component status
            log_file = Path("self_hosting_test_v3.log")
            components = get_component_status(log_file)
            
            # Get overall status
            overall_status = "Starting..."
            if log_file.exists():
                with open(log_file, "r") as f:
                    lines = f.readlines()
                    for line in reversed(lines[-5:]):
                        if "GENERATION" in line:
                            overall_status = line.strip()
                            break
                        elif "PASSED" in line:
                            overall_status = "✅ TEST PASSED WITH QUALITY ITERATION!"
                            break
                        elif "FAILED" in line:
                            overall_status = "❌ Test failed"
                            break
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] Test v3 Status:")
            print(f"  Test dir: {test_dir.name}")
            print(f"  Gen2 files: {gen2_files}")
            print(f"  Gen3 files: {gen3_files}")
            print(f"  Overall: {overall_status[:80]}")
            
            if components:
                print(f"\n  Component Recipes ({len(components)}):")
                for comp, info in sorted(components.items())[:5]:  # Show first 5
                    status_icon = "✅" if info["status"] == "complete" else "♻️" if info["status"] == "iterating" else "🔄"
                    print(f"    {status_icon} {comp}: {info['iterations']} iterations")
                if len(components) > 5:
                    print(f"    ... and {len(components) - 5} more")
            
            print("-" * 70)
        else:
            print("No v3 test directory found yet...")
        
        time.sleep(20)  # Update every 20 seconds

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")