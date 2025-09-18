#!/usr/bin/env python3
"""Test third generation creation using fixed second generation."""

import sys
import os
from pathlib import Path

# Add second generation to path
sys.path.insert(0, str(Path(".recipe_build/gen2/src")))

# Import from second generation
from recipe_executor import RecipeExecutor
from recipe_executor.cli import main

if __name__ == "__main__":
    print("=" * 80)
    print("TESTING THIRD GENERATION WITH FIXED SECOND GENERATION")
    print("=" * 80)
    
    # Set output directory for third generation
    output_dir = Path(".recipe_build/gen3")
    
    # Run the fixed second generation to create third generation
    executor = RecipeExecutor(output_dir=output_dir)
    
    try:
        print(f"Output directory: {output_dir}")
        print("Starting recipe execution...")
        
        # Execute the recipe
        report = executor.execute(Path("recipes/recipe-executor"), force=True)
        
        print(f"\nExecution completed!")
        print(f"Success: {report.success}")
        print(f"Total components: {report.total_components}")
        print(f"Successful components: {report.successful_components}")
        print(f"Failed components: {report.failed_components}")
        print(f"Total lines of code: {report.total_lines_of_code}")
        print(f"Total stub count: {report.total_stub_count}")
        
        if report.total_stub_count > 0:
            print(f"\n⚠️ WARNING: Found {report.total_stub_count} stubs in generated code!")
        else:
            print("\n✅ SUCCESS: No stubs found in generated code!")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()