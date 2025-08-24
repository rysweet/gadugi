#!/usr/bin/env python3
"""Analyze the regenerated Recipe Executor against requirements and current implementation."""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def analyze_requirements_coverage():
    """Check if all required components from requirements.md are present."""
    
    print("=" * 60)
    print("REQUIREMENTS ANALYSIS")
    print("=" * 60)
    
    # Required components from requirements.md
    required_components = {
        "Recipe Structure Management": [
            "recipe_parser.py",  # Recipe file parsing
            "recipe_validator.py",  # Recipe validation
            "recipe_model.py",  # Data models
        ],
        "Dependency Resolution": [
            "dependency_resolver.py",  # Dependency graph and resolution
        ],
        "Design Patterns": [
            "pattern_manager.py",  # Design pattern support
        ],
        "Recipe Complexity": [
            "recipe_decomposer.py",  # Recipe complexity evaluation
        ],
        "Prompt Management": [
            "prompt_loader.py",  # Prompt template system
        ],
        "Execution Engine": [
            "test_generator.py",  # TDD test generation
            "claude_code_generator.py",  # AI-powered generation
            "quality_gates.py",  # Code quality enforcement
        ],
        "Code Review": [
            # Note: code-reviewer is an agent, not a module
        ],
        "Validation": [
            "validator.py",  # Post-generation validation
        ],
        "Self-Hosting": [
            "orchestrator.py",  # Main orchestration engine
        ],
        "State Management": [
            "state_manager.py",  # Build state tracking
        ],
        "Stub Detection": [
            "stub_detector.py",  # Basic stub detection
            "intelligent_stub_detector.py",  # Claude-based detection (NEW)
        ],
        "Python Standards": [
            "python_standards.py",  # Python-specific quality
        ],
        "CLI Interface": [
            "cli.py or __main__.py",  # Command-line interface
        ],
    }
    
    # Check current implementation
    current_dir = Path("src/recipe_executor")
    current_files = set(f.name for f in current_dir.glob("*.py"))
    
    # Check generated implementation
    generated_dir = Path(".recipe_build/regenerated/generated_recipe-executor/src")
    generated_files = set()
    if generated_dir.exists():
        generated_files = set(f.name for f in generated_dir.glob("*.py"))
    
    print("\n📋 Component Coverage:")
    for category, files in required_components.items():
        print(f"\n{category}:")
        for file in files:
            # Handle "or" cases
            file_options = file.split(" or ")
            
            current_has = any(f in current_files for f in file_options)
            generated_has = any(f in generated_files for f in file_options)
            
            status_current = "✅" if current_has else "❌"
            status_generated = "✅" if generated_has else "❌"
            
            print(f"  {file:30} Current: {status_current}  Generated: {status_generated}")
    
    return current_files, generated_files

def analyze_missing_in_generated(current_files: set, generated_files: set):
    """Find what's in current but missing in generated."""
    
    print("\n" + "=" * 60)
    print("MISSING IN GENERATED VERSION")
    print("=" * 60)
    
    missing = current_files - generated_files
    if missing:
        print("\n❌ Files in current but NOT in generated:")
        for file in sorted(missing):
            print(f"  - {file}")
            
            # Check what each missing file does
            current_path = Path(f"src/recipe_executor/{file}")
            if current_path.exists():
                with open(current_path, 'r') as f:
                    lines = f.readlines()
                    # Get first docstring or comment
                    for line in lines[:10]:
                        if '"""' in line or line.strip().startswith('#'):
                            print(f"    Purpose: {line.strip()}")
                            break
    else:
        print("\n✅ No files missing - generated has all current files")
    
    return missing

def analyze_extra_in_generated(current_files: set, generated_files: set):
    """Find what's in generated but not in current."""
    
    print("\n" + "=" * 60)
    print("EXTRA IN GENERATED VERSION")
    print("=" * 60)
    
    extra = generated_files - current_files
    if extra:
        print("\n📦 Files in generated but NOT in current:")
        for file in sorted(extra):
            print(f"  + {file}")
    else:
        print("\n✅ No extra files - generated matches current structure")
    
    return extra

def analyze_file_sizes():
    """Compare file sizes to detect stub vs real implementations."""
    
    print("\n" + "=" * 60)
    print("FILE SIZE COMPARISON")
    print("=" * 60)
    
    current_dir = Path("src/recipe_executor")
    generated_dir = Path(".recipe_build/regenerated/generated_recipe-executor/src")
    
    if not generated_dir.exists():
        print("\n⚠️  Generated directory not found")
        return
    
    print("\n📊 Size comparison (chars):")
    print(f"{'File':<35} {'Current':>10} {'Generated':>10} {'Diff %':>10}")
    print("-" * 70)
    
    total_current = 0
    total_generated = 0
    
    all_files = set()
    for f in current_dir.glob("*.py"):
        all_files.add(f.name)
    for f in generated_dir.glob("*.py"):
        all_files.add(f.name)
    
    for file in sorted(all_files):
        current_path = current_dir / file
        generated_path = generated_dir / file
        
        current_size = current_path.stat().st_size if current_path.exists() else 0
        generated_size = generated_path.stat().st_size if generated_path.exists() else 0
        
        total_current += current_size
        total_generated += generated_size
        
        if current_size > 0:
            diff_pct = ((generated_size - current_size) / current_size) * 100
        else:
            diff_pct = 100 if generated_size > 0 else 0
        
        # Highlight significant differences
        marker = ""
        if diff_pct < -50:
            marker = " ⚠️ Much smaller"
        elif diff_pct > 50:
            marker = " 📈 Much larger"
        
        print(f"{file:<35} {current_size:>10,} {generated_size:>10,} {diff_pct:>9.1f}%{marker}")
    
    print("-" * 70)
    print(f"{'TOTAL':<35} {total_current:>10,} {total_generated:>10,} {((total_generated - total_current) / total_current * 100):>9.1f}%")

def analyze_key_features():
    """Check for key features and capabilities."""
    
    print("\n" + "=" * 60)
    print("KEY FEATURES ANALYSIS")
    print("=" * 60)
    
    features_to_check = {
        "TDD Support": ["test_generator", "red.*green.*refactor"],
        "Claude Integration": ["claude_code_generator", "invoke.*claude"],
        "UV Support": ["uv sync", "uv run"],
        "Pyright Integration": ["pyright", "type.*check"],
        "Ruff Integration": ["ruff", "format.*code"],
        "Parallel Execution": ["parallel", "concurrent", "asyncio", "multiprocess"],
        "State Management": ["state_manager", "build.*state"],
        "Incremental Builds": ["incremental", "cache", "checksum"],
        "Self-Protection": ["self.*overwrite", "protect"],
        "Design Patterns": ["pattern", "template"],
        "Intelligent Stub Detection": ["intelligent.*stub", "claude.*stub.*detect"],
        "Prompt Templates": ["prompt.*loader", "prompt.*template"],
        "Error Handling": ["try.*except", "error.*handling"],
        "CLI Interface": ["click", "argparse", "__main__"],
    }
    
    current_dir = Path("src/recipe_executor")
    generated_dir = Path(".recipe_build/regenerated/generated_recipe-executor/src")
    
    print("\n🔍 Feature Detection:")
    print(f"{'Feature':<30} {'Current':^10} {'Generated':^10}")
    print("-" * 52)
    
    for feature, patterns in features_to_check.items():
        current_found = False
        generated_found = False
        
        # Check in current
        for py_file in current_dir.glob("*.py"):
            if py_file.exists():
                content = py_file.read_text().lower()
                if any(pattern.lower() in content for pattern in patterns):
                    current_found = True
                    break
        
        # Check in generated
        if generated_dir.exists():
            for py_file in generated_dir.glob("*.py"):
                if py_file.exists():
                    content = py_file.read_text().lower()
                    if any(pattern.lower() in content for pattern in patterns):
                        generated_found = True
                        break
        
        current_status = "✅" if current_found else "❌"
        generated_status = "✅" if generated_found else "❌"
        
        marker = ""
        if not current_found and generated_found:
            marker = " 🆕"  # New in generated
        elif current_found and not generated_found:
            marker = " ⚠️"  # Missing in generated
        
        print(f"{feature:<30} {current_status:^10} {generated_status:^10}{marker}")

def analyze_imports_and_dependencies():
    """Check if all imports and dependencies are consistent."""
    
    print("\n" + "=" * 60)
    print("IMPORT ANALYSIS")
    print("=" * 60)
    
    def get_imports(directory: Path) -> set:
        """Extract all imports from Python files."""
        imports = set()
        if directory.exists():
            for py_file in directory.glob("*.py"):
                with open(py_file, 'r') as f:
                    for line in f:
                        if line.strip().startswith('import ') or line.strip().startswith('from '):
                            # Clean up the import statement
                            import_stmt = line.strip().split('#')[0].strip()
                            imports.add(import_stmt)
        return imports
    
    current_imports = get_imports(Path("src/recipe_executor"))
    generated_imports = get_imports(Path(".recipe_build/regenerated/generated_recipe-executor/src"))
    
    missing_imports = current_imports - generated_imports
    extra_imports = generated_imports - current_imports
    
    if missing_imports:
        print("\n⚠️  Imports in current but missing in generated:")
        for imp in sorted(missing_imports)[:10]:  # Show first 10
            print(f"  - {imp}")
        if len(missing_imports) > 10:
            print(f"  ... and {len(missing_imports) - 10} more")
    
    if extra_imports:
        print("\n📦 Extra imports in generated:")
        for imp in sorted(extra_imports)[:10]:  # Show first 10
            print(f"  + {imp}")
        if len(extra_imports) > 10:
            print(f"  ... and {len(extra_imports) - 10} more")
    
    if not missing_imports and not extra_imports:
        print("\n✅ Imports are consistent between versions")

def main():
    """Run all analyses."""
    
    print("\n" + "🔬 RECIPE EXECUTOR REGENERATION ANALYSIS 🔬".center(60))
    print("=" * 60)
    
    # Check if generated version exists
    generated_dir = Path(".recipe_build/regenerated/generated_recipe-executor")
    if not generated_dir.exists():
        print("\n❌ Generated version not found at:", generated_dir)
        print("   Run ./run_regeneration.sh first")
        return
    
    # Run analyses
    current_files, generated_files = analyze_requirements_coverage()
    missing = analyze_missing_in_generated(current_files, generated_files)
    extra = analyze_extra_in_generated(current_files, generated_files)
    analyze_file_sizes()
    analyze_key_features()
    analyze_imports_and_dependencies()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print(f"\n📊 Statistics:")
    print(f"  Current implementation: {len(current_files)} files")
    print(f"  Generated implementation: {len(generated_files)} files")
    print(f"  Missing in generated: {len(missing)} files")
    print(f"  Extra in generated: {len(extra)} files")
    
    # Critical missing files
    critical_missing = missing & {
        'parallel_builder.py',
        'pattern_manager.py', 
        'prompt_loader.py',
        'language_detector.py',
        'base_generator.py',
        '__main__.py'
    }
    
    if critical_missing:
        print(f"\n⚠️  CRITICAL: Missing important files:")
        for file in critical_missing:
            print(f"    - {file}")
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()