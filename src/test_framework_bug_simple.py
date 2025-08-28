#!/usr/bin/env python3
"""Simple test to demonstrate the GeneratedCode framework attribute bug."""

import sys
import traceback
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from recipe_executor.recipe_model import GeneratedCode
from recipe_executor.tdd_pipeline import TDDPipeline


def test_bug_exists():
    """Demonstrate that GeneratedCode lacks the framework attribute."""
    print("Testing for framework attribute bug...")
    
    # Create a GeneratedCode instance
    code = GeneratedCode(
        recipe_name="test-recipe",
        files={"test.py": "print('hello')"},
        language="python"
    )
    
    # Check if it has framework attribute
    has_framework = hasattr(code, 'framework')
    print(f"  GeneratedCode has 'framework' attribute: {has_framework}")
    
    if not has_framework:
        print("  ❌ BUG CONFIRMED: GeneratedCode lacks 'framework' attribute")
    else:
        print("  ✅ No bug: GeneratedCode has 'framework' attribute")
    
    return has_framework


def test_tdd_pipeline_crash():
    """Demonstrate that TDD pipeline crashes when accessing framework."""
    print("\nTesting TDD pipeline refactor phase...")
    
    from tempfile import TemporaryDirectory
    
    code = GeneratedCode(
        recipe_name="test-recipe", 
        files={"main.py": "def hello(): pass"},
        language="python"
    )
    
    pipeline = TDDPipeline()
    
    try:
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Write files
            for filepath, content in code.files.items():
                full_path = output_dir / filepath
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
            
            # Try to apply refactoring - this should crash
            # _apply_refactoring takes (code_artifact, quality_results, output_dir)
            quality_results = {"pyright": True, "ruff_format": True}
            result = pipeline._apply_refactoring(code, quality_results, output_dir)
            print("  ✅ No error: TDD pipeline handled GeneratedCode")
            return True
            
    except AttributeError as e:
        if "framework" in str(e):
            print(f"  ❌ BUG CONFIRMED: {e}")
            return False
        else:
            print(f"  ❓ Different error: {e}")
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"  ❓ Unexpected error: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing for GeneratedCode.framework bug")
    print("=" * 60)
    
    # Run tests
    has_attr = test_bug_exists()
    no_crash = test_tdd_pipeline_crash()
    
    print("\n" + "=" * 60)
    if not has_attr or not no_crash:
        print("RESULT: Bug confirmed - GeneratedCode needs framework attribute")
        sys.exit(1)
    else:
        print("RESULT: No bug found")
        sys.exit(0)