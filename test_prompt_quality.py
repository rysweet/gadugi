#!/usr/bin/env python3
"""Test that prompts include Python 3.9 quality requirements."""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.recipe_executor.prompt_loader import PromptLoader
from src.recipe_executor.claude_code_generator import ClaudeCodeGenerator
from src.recipe_executor.recipe_parser import RecipeParser


def test_prompt_includes_quality_requirements():
    """Check that the prompt includes Python 3.9 requirements."""
    
    print("=" * 60)
    print("Testing Prompt Quality Requirements")
    print("=" * 60)
    
    # Load a sample recipe
    parser = RecipeParser()
    recipe = parser.parse("recipes/validation-service")
    
    # Create generator
    generator = ClaudeCodeGenerator()
    
    # Generate prompt
    output_path = Path(".recipe_build/test")
    prompt = generator._create_generation_prompt_with_path(recipe, output_path)
    
    # Check for quality requirements
    checks = [
        ("Python 3.9 mentioned", "PYTHON 3.9 COMPATIBLE" in prompt),
        ("typing imports mentioned", "from typing import Optional" in prompt),
        ("No Python 3.10 syntax", "NOT Python 3.10+ union syntax" in prompt),
        ("No match/case", "NOT match/case" in prompt),
        ("field(default_factory)", "field(default_factory" in prompt),
        ("No stubs allowed", "NO pass, NO ellipsis, NO NotImplementedError" in prompt),
    ]
    
    print("\nQuality Requirements Check:")
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    # Also check that context files are loaded
    print("\nContext Files Check:")
    loader = PromptLoader()
    context_files = loader.load_context_files()
    
    important_files = [
        "CRITICAL_QUALITY_REQUIREMENTS.md",
        "CRITICAL_GUIDELINES.md",
        "CRITICAL_ANTI_STUB_RULES.md"
    ]
    
    for filename in important_files:
        if filename in context_files:
            print(f"  ✅ {filename} loaded")
            # Check content briefly
            if "QUALITY_REQUIREMENTS" in filename:
                content = context_files[filename]
                if "Python 3.9" in content:
                    print("    → Contains Python 3.9 requirements")
        else:
            print(f"  ❌ {filename} NOT loaded")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All quality requirements are included in prompts!")
    else:
        print("❌ Some quality requirements are missing from prompts")
    
    # Show a snippet of the prompt
    print("\nPrompt snippet (first 1000 chars with quality requirements):")
    print("-" * 60)
    
    # Find and show the quality section
    if "CRITICAL: PYTHON VERSION" in prompt:
        start = prompt.index("CRITICAL: PYTHON VERSION")
        end = min(start + 1000, len(prompt))
        print(prompt[start:end])
    
    return all_passed


if __name__ == "__main__":
    success = test_prompt_includes_quality_requirements()
    sys.exit(0 if success else 1)