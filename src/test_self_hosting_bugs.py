#!/usr/bin/env python3
"""Simple tests to demonstrate self-hosting bugs without pytest."""

import tempfile
import subprocess
import traceback
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from recipe_executor.python_standards import QualityGates
from recipe_executor.component_registry import ComponentRegistry


def test_ruff_uv_temp_file_bug():
    """Test 1: Ruff with uv run fails on temp files outside project."""
    print("\n" + "="*60)
    print("TEST 1: Ruff + UV on temp files bug")
    print("="*60)
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello( ):\n    return   'world'")
            temp_file = f.name
        
        print(f"Created temp file: {temp_file}")
        
        # Try to run ruff format with uv run
        result = subprocess.run(
            ['uv', 'run', 'ruff', 'format', temp_file],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        if result.returncode != 0:
            print(f"❌ BUG CONFIRMED: uv run ruff format failed")
            print(f"   Return code: {result.returncode}")
            print(f"   Stderr: {result.stderr[:200]}")
            return False
        else:
            print(f"✅ No bug: ruff format succeeded")
            return True
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        traceback.print_exc()
        return False
    finally:
        if 'temp_file' in locals():
            Path(temp_file).unlink(missing_ok=True)


def test_component_registry_path_bug():
    """Test 2: Component registry looks for files at wrong paths."""
    print("\n" + "="*60)
    print("TEST 2: Component registry path mismatch bug")
    print("="*60)
    
    try:
        registry = ComponentRegistry()
        
        # Get expected components
        expected = registry.REQUIRED_COMPONENTS
        
        print(f"Checking {len(expected)} expected component paths...")
        
        wrong_paths = []
        for component, path in expected.items():
            # Check if paths match what Claude generates
            # Claude generates: src/recipe_executor/file.py
            # Registry expects: src/file.py (BUG!)
            if component in ['recipe_model', 'orchestrator', 'recipe_parser']:
                if 'recipe_executor' not in path and not path.startswith('tests/'):
                    wrong_paths.append((component, path))
        
        if wrong_paths:
            print(f"❌ BUG CONFIRMED: {len(wrong_paths)} components have wrong expected paths:")
            for comp, path in wrong_paths[:5]:
                print(f"   {comp}: expects '{path}' but should be 'src/recipe_executor/...'")
            return False
        else:
            print("✅ No bug: All component paths are correct")
            return True
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        traceback.print_exc()
        return False


def test_quality_gates_temp_dir_bug():
    """Test 3: Quality gates don't work with directories outside project."""
    print("\n" + "="*60)
    print("TEST 3: Quality gates temp directory bug")
    print("="*60)
    
    try:
        gates = QualityGates()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            print(f"Created temp dir: {tmpdir_path}")
            
            # Create a Python file (with proper formatting)
            test_file = tmpdir_path / "test.py"
            test_file.write_text('def hello():\n    return "world"\n')
            
            # Try to check format
            try:
                result = gates.check_ruff_format(tmpdir_path)
                if result:
                    print("✅ No bug: Quality gates handled temp dir")
                    return True
                else:
                    print("❌ BUG CONFIRMED: Quality gates failed on temp dir")
                    # Try to debug why
                    import subprocess
                    r = subprocess.run(['ruff', 'format', '--check', str(test_file)], capture_output=True, text=True)
                    print(f"   Direct ruff test exit code: {r.returncode}")
                    return False
            except Exception as e:
                print(f"❌ BUG CONFIRMED: Quality gates crashed on temp dir: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ Error during test: {e}")
        traceback.print_exc()
        return False


def test_missing_components_check():
    """Test 4: Check what the component registry expects vs what's generated."""
    print("\n" + "="*60)
    print("TEST 4: Missing components check")
    print("="*60)
    
    try:
        # Simulate what Claude actually generates (complete set of files)
        generated_files = {
            "src/recipe_executor/recipe_model.py": "# content",
            "src/recipe_executor/recipe_parser.py": "# content",
            "src/recipe_executor/recipe_validator.py": "# content",
            "src/recipe_executor/recipe_decomposer.py": "# content",
            "src/recipe_executor/dependency_resolver.py": "# content",
            "src/recipe_executor/claude_code_generator.py": "# content",
            "src/recipe_executor/test_generator.py": "# content",
            "src/recipe_executor/test_solver.py": "# content",
            "src/recipe_executor/base_generator.py": "# content",
            "src/recipe_executor/code_reviewer.py": "# content",
            "src/recipe_executor/code_review_response.py": "# content",
            "src/recipe_executor/requirements_validator.py": "# content",
            "src/recipe_executor/validator.py": "# content",
            "src/recipe_executor/quality_gates.py": "# content",
            "src/recipe_executor/stub_detector.py": "# content",
            "src/recipe_executor/intelligent_stub_detector.py": "# content",
            "src/recipe_executor/orchestrator.py": "# content",
            "src/recipe_executor/state_manager.py": "# content",
            "src/recipe_executor/parallel_builder.py": "# content",
            "src/recipe_executor/python_standards.py": "# content",
            "src/recipe_executor/pattern_manager.py": "# content",
            "src/recipe_executor/prompt_loader.py": "# content",
            "src/recipe_executor/language_detector.py": "# content",
            "src/recipe_executor/uv_environment.py": "# content",
            "src/recipe_executor/__init__.py": "# content",
            "src/recipe_executor/__main__.py": "# content",
            "src/recipe_executor/cli.py": "# content",
            "pyproject.toml": "# content",
            "README.md": "# content",
            "tests/__init__.py": "# content",
            "tests/test_recipe_executor.py": "# content",
        }
        
        registry = ComponentRegistry()
        is_complete, missing = registry.validate_completeness(generated_files)
        
        if not is_complete:
            print(f"❌ BUG CONFIRMED: Registry reports {len(missing)} missing components")
            print(f"   First 5 missing: {missing[:5]}")
            return False
        else:
            print("✅ No bug: Registry correctly validates components")
            return True
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("Testing Self-Hosting Bugs")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Ruff+UV temp file", test_ruff_uv_temp_file_bug()))
    results.append(("Component registry paths", test_component_registry_path_bug()))
    results.append(("Quality gates temp dir", test_quality_gates_temp_dir_bug()))
    results.append(("Missing components", test_missing_components_check()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    failed = sum(1 for _, p in results if not p)
    print(f"\nTotal: {len(results)} tests, {failed} failures")
    
    sys.exit(0 if failed == 0 else 1)