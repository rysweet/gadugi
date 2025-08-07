#!/usr/bin/env python3
"""Simple test of orchestrator components"""

import sys
import os
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / ".claude/orchestrator"))

# Try to import components
try:
    from components.task_analyzer import TaskAnalyzer
    print("✅ Successfully imported TaskAnalyzer")
    
    # Test analyze_prompts with a simple file
    analyzer = TaskAnalyzer(prompts_dir=".", project_root=".")
    
    # Create a test prompt file
    test_prompt = Path("test-simple.md")
    if test_prompt.exists():
        print(f"✅ Test prompt file exists: {test_prompt}")
        
        # Try to analyze it
        print("Analyzing prompt file...")
        tasks = analyzer.analyze_prompts([str(test_prompt)])
        print(f"Analysis result: {len(tasks)} tasks")
        for task in tasks:
            print(f"  - Task: {task.name}")
    else:
        print(f"❌ Test prompt file not found: {test_prompt}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()