#!/usr/bin/env python3
"""Analyze capability parity between generations, not file parity."""

import os
import re
from pathlib import Path


def analyze_capabilities(path: Path) -> dict:
    """Analyze what capabilities exist in a generation."""
    capabilities = {
        "can_parse_recipe": False,
        "can_validate_recipe": False,
        "can_resolve_dependencies": False,
        "can_generate_code": False,
        "can_invoke_claude": False,
        "can_run_tests": False,
        "can_check_quality": False,
        "can_manage_state": False,
        "can_detect_stubs": False,
        "has_cli": False,
        "has_tdd_support": False,
        "has_self_protection": False,
    }
    
    if not path.exists():
        return capabilities
    
    # Check for key files and patterns
    files = list(path.rglob("*.py"))
    all_code = ""
    for f in files:
        try:
            all_code += f.read_text()
        except:
            pass
    
    # Check capabilities based on code patterns
    if "class RecipeParser" in all_code:
        capabilities["can_parse_recipe"] = True
    
    if "class RecipeValidator" in all_code or "def validate" in all_code:
        capabilities["can_validate_recipe"] = True
    
    if "class DependencyResolver" in all_code or "topological" in all_code:
        capabilities["can_resolve_dependencies"] = True
    
    if "ClaudeCodeGenerator" in all_code or "def generate" in all_code:
        capabilities["can_generate_code"] = True
    
    if "claude -p" in all_code or "subprocess" in all_code and "claude" in all_code:
        capabilities["can_invoke_claude"] = True
    
    if "pytest" in all_code or "TestGenerator" in all_code:
        capabilities["can_run_tests"] = True
    
    if "QualityGates" in all_code or "pyright" in all_code:
        capabilities["can_check_quality"] = True
    
    if "StateManager" in all_code or "cache" in all_code.lower():
        capabilities["can_manage_state"] = True
    
    if "stub" in all_code.lower() and "detect" in all_code.lower():
        capabilities["can_detect_stubs"] = True
    
    if "cli.py" in [f.name for f in files] or "__main__.py" in [f.name for f in files]:
        capabilities["has_cli"] = True
    
    if "TDD" in all_code or "Red-Green-Refactor" in all_code:
        capabilities["has_tdd_support"] = True
    
    if "allow-self-overwrite" in all_code or "self_protection" in all_code:
        capabilities["has_self_protection"] = True
    
    return capabilities


def main():
    print("=" * 60)
    print("CAPABILITY ANALYSIS (Not File Count)")
    print("=" * 60)
    
    paths = {
        "Gen 1 (Original)": Path("src/recipe_executor"),
        "Gen 2 (Regenerated)": Path(".recipe_build/regenerated_v2/generated_recipe-executor/src"),
        "Gen 3 (Attempted)": Path(".recipe_build/regenerated_v3/recipe-executor/src"),
    }
    
    results = {}
    for name, path in paths.items():
        results[name] = analyze_capabilities(path)
    
    # Print comparison table
    print("\n📊 Capability Comparison:\n")
    print(f"{'Capability':<30} {'Gen 1':>8} {'Gen 2':>8} {'Gen 3':>8}")
    print("-" * 56)
    
    all_capabilities = sorted(set().union(*[r.keys() for r in results.values()]))
    
    for cap in all_capabilities:
        gen1 = "✅" if results.get("Gen 1 (Original)", {}).get(cap, False) else "❌"
        gen2 = "✅" if results.get("Gen 2 (Regenerated)", {}).get(cap, False) else "❌"
        gen3 = "✅" if results.get("Gen 3 (Attempted)", {}).get(cap, False) else "❌"
        
        # Highlight missing capabilities
        if gen1 == "✅" and gen2 == "❌":
            print(f"{cap:<30} {gen1:>8} {gen2:>8} {gen3:>8} ⚠️")
        else:
            print(f"{cap:<30} {gen1:>8} {gen2:>8} {gen3:>8}")
    
    # Calculate capability retention
    print("\n📈 Capability Retention:")
    gen1_caps = sum(1 for v in results["Gen 1 (Original)"].values() if v)
    gen2_caps = sum(1 for v in results["Gen 2 (Regenerated)"].values() if v)
    gen3_caps = sum(1 for v in results["Gen 3 (Attempted)"].values() if v)
    
    print(f"  Gen 1: {gen1_caps}/12 capabilities")
    print(f"  Gen 2: {gen2_caps}/12 capabilities ({gen2_caps/gen1_caps*100:.0f}% retention)")
    print(f"  Gen 3: {gen3_caps}/12 capabilities (incomplete)")
    
    # Key findings
    print("\n🔍 Key Findings:")
    gen1_set = set(k for k, v in results["Gen 1 (Original)"].items() if v)
    gen2_set = set(k for k, v in results["Gen 2 (Regenerated)"].items() if v)
    
    lost = gen1_set - gen2_set
    if lost:
        print(f"  ❌ Lost capabilities: {', '.join(lost)}")
    
    gained = gen2_set - gen1_set
    if gained:
        print(f"  ✅ Gained capabilities: {', '.join(gained)}")
    
    if gen2_caps >= gen1_caps:
        print("  ✅ Gen 2 has full capability parity!")
    else:
        print(f"  ⚠️  Gen 2 missing {gen1_caps - gen2_caps} capabilities")


if __name__ == "__main__":
    main()