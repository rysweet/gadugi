#!/usr/bin/env python
"""Test script to verify recipe executor generates real code, not stubs."""

from pathlib import Path
from src.recipe_executor.claude_code_generator import ClaudeCodeGenerator
from src.recipe_executor.recipe_parser import RecipeParser
from src.recipe_executor.recipe_model import BuildContext
import sys


def test_recipe_generation(recipe_name: str):
    """Test that a recipe generates real code without stubs."""
    print(f"\n{'='*80}")
    print(f"Testing Recipe: {recipe_name}")
    print(f"{'='*80}")
    
    # Parse recipe
    parser = RecipeParser()
    recipe_path = Path(f"recipes/{recipe_name}")
    
    if not recipe_path.exists():
        print(f"❌ Recipe not found: {recipe_path}")
        return False
    
    try:
        recipe = parser.parse_recipe(recipe_path)
        print(f"✅ Recipe parsed: {recipe.name}")
    except Exception as e:
        print(f"❌ Failed to parse recipe: {e}")
        return False
    
    # Create generator with strict no-stubs enforcement
    generator = ClaudeCodeGenerator(enforce_no_stubs=True)
    
    # Test prompt generation
    output_path = Path(f".recipe_build/test_{recipe_name}")
    prompt = generator._create_simple_component_prompt(recipe, output_path)
    
    # Check prompt contains anti-stub instructions
    anti_stub_checks = [
        "NO STUBS",
        "NO pass STATEMENTS",
        "NO TODO COMMENTS",
        "MINIMUM 3-5 LINES OF LOGIC",
        "COMPLETE IMPLEMENTATION"
    ]
    
    missing_checks = []
    for check in anti_stub_checks:
        if check not in prompt:
            missing_checks.append(check)
    
    if missing_checks:
        print(f"⚠️  Prompt missing anti-stub instructions: {missing_checks}")
    else:
        print(f"✅ Prompt contains all anti-stub instructions")
    
    # Display prompt stats
    print(f"📊 Prompt size: {len(prompt)} characters")
    print(f"📊 Lines: {len(prompt.splitlines())}")
    
    # Count examples in prompt
    examples = prompt.count("# ✅")
    forbidden = prompt.count("# ❌")
    print(f"📊 Implementation examples: {examples}")
    print(f"📊 Forbidden patterns shown: {forbidden}")
    
    return len(missing_checks) == 0


def main():
    """Test multiple recipes for stub-free generation."""
    test_recipes = [
        "data-models",
        "parser",
        "validation-service"
    ]
    
    print("\n" + "="*80)
    print("RECIPE EXECUTOR NO-STUBS VALIDATION")
    print("="*80)
    
    results = []
    for recipe_name in test_recipes:
        success = test_recipe_generation(recipe_name)
        results.append((recipe_name, success))
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for recipe_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {recipe_name}")
    
    print(f"\nTotal: {passed}/{total} recipes ready for stub-free generation")
    
    if passed == total:
        print("\n🎉 SUCCESS: All recipes configured for complete implementations!")
        return 0
    else:
        print(f"\n⚠️  WARNING: {total - passed} recipes need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())