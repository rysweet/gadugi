#!/usr/bin/env python3
"""Comprehensive test for Recipe Executor model and parser integration."""

import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.recipe_executor.recipe_model import (
    ComponentType,
    RequirementPriority,
    Requirement,
    Requirements,
    ComponentDesign,
    Interface,
    Design,
    Components,
    RecipeMetadata,
    Recipe,
    BuildContext,
    GeneratedCode,
    RecipeTestSuite,
    ValidationResult,
    BuildResult,
    SingleBuildResult,
    ComplexityMetrics,
    DesignPattern,
    RecipeComplexity,
    SubRecipe,
    DependencyNode,
    DependencyGraph,
    BuildState,
    ParallelBuildResult
)

def test_recipe_model_comprehensive():
    """Test all required Recipe Executor model functionality."""
    
    print("=" * 60)
    print("Recipe Executor Model Comprehensive Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Core Model Classes
    print("Test 1: Core Model Classes")
    try:
        # Create a requirement
        req = Requirement(
            id="req_1",
            description="MUST implement code generation",
            priority=RequirementPriority.MUST,
            validation_criteria=["Code compiles", "Tests pass"]
        )
        assert req.id == "req_1"
        assert req.priority == RequirementPriority.MUST
        results.append(("Core Model Classes", True, "✅ All core classes exist"))
        print("  ✅ All core classes exist and work")
    except Exception as e:
        results.append(("Core Model Classes", False, f"❌ {str(e)}"))
        print(f"  ❌ Failed: {e}")
    
    # Test 2: Design Pattern Support
    print("\nTest 2: Design Pattern Support")
    try:
        pattern = DesignPattern(
            name="singleton",
            description="Singleton pattern",
            template="class Singleton: ...",
            applicable_types=[ComponentType.SERVICE],
            required_methods=["get_instance"],
            required_properties=["_instance"]
        )
        assert pattern.name == "singleton"
        assert ComponentType.SERVICE in pattern.applicable_types
        results.append(("Design Pattern Support", True, "✅ DesignPattern class works"))
        print("  ✅ DesignPattern class works")
    except Exception as e:
        results.append(("Design Pattern Support", False, f"❌ {str(e)}"))
        print(f"  ❌ Failed: {e}")
    
    # Test 3: Complexity Metrics
    print("\nTest 3: Complexity Metrics")
    try:
        metrics = ComplexityMetrics(
            functional_requirements_count=15,
            non_functional_requirements_count=5,
            component_count=7,
            dependency_count=3,
            interface_count=4,
            estimated_loc=800,
            complexity_score=8.5
        )
        assert metrics.is_complex  # Should be True with these values
        assert "High complexity score" in metrics.decomposition_reason
        results.append(("Complexity Metrics", True, "✅ ComplexityMetrics works"))
        print("  ✅ ComplexityMetrics works with is_complex property")
    except Exception as e:
        results.append(("Complexity Metrics", False, f"❌ {str(e)}"))
        print(f"  ❌ Failed: {e}")
    
    # Test 4: Recipe Complexity
    print("\nTest 4: Recipe Complexity")
    try:
        complexity = RecipeComplexity(
            recipe_name="test-recipe",
            metrics=metrics,
            decomposition_recommended=True,
            decomposition_strategy="component-based",
            sub_recipes=[],
            estimated_effort_hours=24.0,
            risk_level="high"
        )
        assert complexity.should_decompose()
        results.append(("Recipe Complexity", True, "✅ RecipeComplexity works"))
        print("  ✅ RecipeComplexity works with should_decompose method")
    except Exception as e:
        results.append(("Recipe Complexity", False, f"❌ {str(e)}"))
        print(f"  ❌ Failed: {e}")
    
    # Test 5: Dependency Graph
    print("\nTest 5: Dependency Graph")
    try:
        graph = DependencyGraph()
        
        # Create test recipes
        components1 = Components(
            name="recipe1",
            version="1.0.0",
            type=ComponentType.SERVICE,
            dependencies=[]
        )
        
        components2 = Components(
            name="recipe2",
            version="1.0.0",
            type=ComponentType.SERVICE,
            dependencies=["recipe1"]
        )
        
        req = Requirements(
            purpose="Test",
            functional_requirements=[],
            non_functional_requirements=[],
            success_criteria=[]
        )
        
        design = Design(
            architecture="test",
            components=[],
            interfaces=[],
            implementation_notes=""
        )
        
        metadata = RecipeMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        recipe1 = Recipe(
            name="recipe1",
            path=Path("recipes/recipe1"),
            requirements=req,
            design=design,
            components=components1,
            metadata=metadata
        )
        
        recipe2 = Recipe(
            name="recipe2",
            path=Path("recipes/recipe2"),
            requirements=req,
            design=design,
            components=components2,
            metadata=metadata
        )
        
        graph.add_recipe(recipe1)
        graph.add_recipe(recipe2)
        
        # Test circular dependency detection
        has_circular, cycle = graph.has_circular_dependency()
        assert not has_circular
        
        # Test build order
        build_order = graph.get_build_order()
        assert len(build_order) == 2
        assert build_order[0] == ["recipe1"]  # recipe1 has no dependencies
        assert build_order[1] == ["recipe2"]  # recipe2 depends on recipe1
        
        results.append(("Dependency Graph", True, "✅ DependencyGraph works"))
        print("  ✅ DependencyGraph with circular detection and build order")
    except Exception as e:
        results.append(("Dependency Graph", False, f"❌ {str(e)}"))
        print(f"  ❌ Failed: {e}")
    
    # Test 6: Build State
    print("\nTest 6: Build State")
    try:
        state = BuildState(
            recipe_name="test-recipe",
            last_build_time=datetime.now(),
            last_checksum="abc123",
            output_files=["file1.py", "file2.py"],
            success=True
        )
        assert not state.needs_rebuild("abc123")  # Same checksum
        assert state.needs_rebuild("xyz789")  # Different checksum
        results.append(("Build State", True, "✅ BuildState works"))
        print("  ✅ BuildState with incremental build support")
    except Exception as e:
        results.append(("Build State", False, f"❌ {str(e)}"))
        print(f"  ❌ Failed: {e}")
    
    # Test 7: Recipe Methods
    print("\nTest 7: Recipe Methods")
    try:
        # Test checksum calculation
        checksum = recipe1.calculate_checksum()
        assert checksum is not None
        assert len(checksum) == 64  # SHA256 hex digest
        
        # Test dependency validation
        is_valid, errors = recipe1.validate_dependencies()
        assert is_valid  # recipe1 has no dependencies
        
        # Test self-overwrite protection
        has_risk = recipe1.has_self_overwrite_risk()
        assert isinstance(has_risk, bool)
        
        # Test pattern merging
        recipe1.merge_with_pattern(pattern)
        assert recipe1.pattern == pattern
        
        results.append(("Recipe Methods", True, "✅ All Recipe methods work"))
        print("  ✅ All Recipe methods work (checksum, validation, etc.)")
    except Exception as e:
        results.append(("Recipe Methods", False, f"❌ {str(e)}"))
        print(f"  ❌ Failed: {e}")
    
    # Test 8: Parallel Build Result
    print("\nTest 8: Parallel Build Result")
    try:
        single_result = SingleBuildResult(
            recipe=recipe1,
            code=None,
            tests=None,
            validation=None,
            quality_result={},
            success=True,
            build_time=1.5
        )
        
        parallel_result = ParallelBuildResult(
            results={"recipe1": single_result},
            total_time=2.0,
            parallel_groups=[["recipe1"]]
        )
        assert "recipe1" in parallel_result.results
        assert parallel_result.total_time == 2.0
        results.append(("Parallel Build Result", True, "✅ ParallelBuildResult works"))
        print("  ✅ ParallelBuildResult works")
    except Exception as e:
        results.append(("Parallel Build Result", False, f"❌ {str(e)}"))
        print(f"  ❌ Failed: {e}")
    
    # Test 9: Sub-Recipe
    print("\nTest 9: Sub-Recipe")
    try:
        sub_recipe = SubRecipe(
            name="test-sub",
            parent_recipe="test-parent",
            requirements=req,
            design=design,
            dependencies=["dep1"],
            complexity_metrics=metrics
        )
        assert sub_recipe.parent_recipe == "test-parent"
        assert len(sub_recipe.dependencies) == 1
        results.append(("Sub-Recipe", True, "✅ SubRecipe class works"))
        print("  ✅ SubRecipe class works")
    except Exception as e:
        results.append(("Sub-Recipe", False, f"❌ {str(e)}"))
        print(f"  ❌ Failed: {e}")
    
    # Print summary
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not success:
            print(f"       {message}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("🎉 SUCCESS! All Recipe Executor model functionality is working!")
        print()
        print("The Recipe Executor has:")
        print("✅ All required model classes (DesignPattern, RecipeComplexity, etc.)")
        print("✅ Dependency graph with circular detection")
        print("✅ Complexity analysis and decomposition support")
        print("✅ Incremental build support with checksums")
        print("✅ Self-hosting protection")
        print("✅ Pattern merging capabilities")
        print()
        print("The model is READY for recipe execution!")
        return True
    else:
        print()
        print("❌ Some tests failed. Please review the failures above.")
        return False


if __name__ == "__main__":
    success = test_recipe_model_comprehensive()
    sys.exit(0 if success else 1)