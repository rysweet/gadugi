#!/usr/bin/env python3
"""Active monitor for self-hosting test v3 - provides continuous updates."""

import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import sys

class ActiveMonitor:
    def __init__(self):
        self.test_dir = Path(".recipe_build/self_host_test_v3_20250909_173158")
        self.last_file_count = 0
        self.last_update = datetime.now()
        self.current_component = None
        self.components_completed = []
        self.start_time = datetime.now()
        
    def get_file_count(self, directory):
        """Count Python files in directory."""
        if not directory.exists():
            return 0
        count = 0
        for f in directory.rglob("*.py"):
            if "venv" not in str(f) and ".venv" not in str(f):
                count += 1
        return count
    
    def parse_generation_log(self):
        """Parse the generation log for current status."""
        log_file = self.test_dir / "Generation_1.log"
        if not log_file.exists():
            return None
        
        status = {
            "current_component": None,
            "current_iteration": 0,
            "files_created": [],
            "quality_checking": False,
            "errors": []
        }
        
        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in lines[-200:]:  # Check last 200 lines
                if "Executing recipe:" in line and "/recipes/" in line:
                    # Extract component name
                    parts = line.split("/recipes/")
                    if len(parts) > 1:
                        comp = parts[1].strip()
                        status["current_component"] = comp
                        if comp not in self.components_completed:
                            self.current_component = comp
                
                if "Generation iteration" in line:
                    try:
                        iter_num = int(line.split("Generation iteration")[1].split()[0])
                        status["current_iteration"] = iter_num
                    except:
                        pass
                
                if "Creating file:" in line or "Claude creating file:" in line:
                    file_name = line.split(":")[-1].strip()
                    status["files_created"].append(file_name)
                
                if "Running quality gate checks" in line:
                    status["quality_checking"] = True
                
                if "Quality gates failed" in line and "will iterate" in line:
                    status["quality_iterating"] = True
                
                if "ERROR" in line or "CRITICAL" in line:
                    status["errors"].append(line.strip())
                
                if "Code generation successful after" in line:
                    if self.current_component and self.current_component not in self.components_completed:
                        self.components_completed.append(self.current_component)
        
        return status
    
    def format_elapsed_time(self):
        """Format elapsed time nicely."""
        elapsed = datetime.now() - self.start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        seconds = int(elapsed.total_seconds() % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def print_status(self):
        """Print current status with clear formatting."""
        gen2_count = self.get_file_count(self.test_dir / "gen2")
        gen3_count = self.get_file_count(self.test_dir / "gen3")
        status = self.parse_generation_log()
        
        # Clear screen for clean output
        print("\033[H\033[J", end="")  # Clear screen
        
        print("=" * 80)
        print(f"🔬 SELF-HOSTING TEST V3 - ACTIVE MONITORING")
        print(f"⏱️  Elapsed: {self.format_elapsed_time()}")
        print("=" * 80)
        
        print(f"\n📊 FILE GENERATION PROGRESS:")
        print(f"   Gen2 Python files: {gen2_count}")
        if gen2_count > self.last_file_count:
            print(f"   ↗️  {gen2_count - self.last_file_count} new files since last check")
            self.last_file_count = gen2_count
        print(f"   Gen3 Python files: {gen3_count}")
        
        if status:
            print(f"\n🎯 CURRENT ACTIVITY:")
            if status["current_component"]:
                print(f"   Component: {status['current_component']}")
                print(f"   Iteration: {status['current_iteration']}")
            
            if status.get("quality_checking"):
                print(f"   🔍 Running quality gate checks...")
            
            if status.get("quality_iterating"):
                print(f"   ♻️  Quality gates failed - iterating to fix...")
            
            if status["files_created"]:
                recent_files = status["files_created"][-5:]  # Last 5 files
                print(f"\n📝 RECENT FILES CREATED:")
                for f in recent_files:
                    print(f"   • {f}")
            
            if self.components_completed:
                print(f"\n✅ COMPONENTS COMPLETED ({len(self.components_completed)}/10):")
                for comp in self.components_completed[-3:]:  # Show last 3
                    print(f"   ✓ {comp}")
                if len(self.components_completed) > 3:
                    print(f"   ... and {len(self.components_completed) - 3} more")
            
            if status["errors"]:
                print(f"\n⚠️  RECENT ISSUES:")
                for err in status["errors"][-3:]:  # Show last 3 errors
                    print(f"   {err[:100]}")
        
        # Progress bar
        progress = (len(self.components_completed) / 10) * 100
        bar_length = 40
        filled = int(bar_length * progress / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\n📈 OVERALL PROGRESS: [{bar}] {progress:.0f}%")
        
        # Key feature reminder
        print(f"\n💡 KEY FEATURE: Quality gate iteration is ENABLED")
        print(f"   Components will automatically iterate until quality gates pass")
        
        print("\n" + "=" * 80)
        print("Press Ctrl+C to stop monitoring")
    
    def run(self):
        """Run the continuous monitor."""
        print("Starting active monitoring of self-hosting test v3...")
        print("Updates every 10 seconds...")
        
        try:
            while True:
                self.print_status()
                time.sleep(10)  # Update every 10 seconds
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            print(f"Final statistics:")
            print(f"  - Test ran for: {self.format_elapsed_time()}")
            print(f"  - Components completed: {len(self.components_completed)}/10")
            print(f"  - Files generated: {self.last_file_count}")

if __name__ == "__main__":
    monitor = ActiveMonitor()
    monitor.run()