#!/usr/bin/env python3
"""Test intelligent stub detection on the regenerated Recipe Executor."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.recipe_executor.intelligent_stub_detector import IntelligentStubDetector

def test_generated_files():
    """Test intelligent detection on the generated Recipe Executor files."""
    
    generated_dir = Path(".recipe_build/regenerated/generated_recipe-executor")
    if not generated_dir.exists():
        print("❌ Generated directory not found. Run regeneration first.")
        return
    
    # Collect all Python files
    files = {}
    for py_file in generated_dir.rglob("*.py"):
        rel_path = py_file.relative_to(generated_dir)
        files[str(rel_path)] = py_file.read_text()
    
    print(f"📁 Found {len(files)} Python files to check")
    
    # Test with intelligent detector
    detector = IntelligentStubDetector(strict_mode=True)
    
    print("\n🤖 Running intelligent stub detection with Claude...")
    try:
        has_stubs, issues = detector.detect_stubs_with_claude(files)
        
        if has_stubs:
            print("\n❌ Real stubs detected:")
            for issue in issues:
                print(issue)
        else:
            print("\n✅ No real stubs detected! All flagged items were false positives.")
            
    except Exception as e:
        print(f"\n⚠️ Intelligent detection failed: {e}")
        print("This might be because Claude needs to be invoked differently or is unavailable.")

if __name__ == "__main__":
    test_generated_files()