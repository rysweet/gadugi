#!/usr/bin/env python3
"""Simple test script to verify data models work correctly."""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_models import (
    Recipe,
    RecipeMetadata,
    Requirements,
    Requirement,
    RequirementPriority,
    Design,
    ComponentDesign,
    ComponentArchitecture,
    ExecutionState,
    ExecutionPhase,
    ValidationResult,
    ValidationSeverity,
    ValidationCategory
)

def test_recipe_model():
    """Test basic Recipe model creation."""
    print("Testing Recipe model...")
    
    # Create a simple requirement
    req = Requirement(
        id="REQ001",
        description="System must process requests",
        priority=RequirementPriority.MUST,
        validation_criteria=["Performance test passes"],
        implemented=False,
        test_coverage=0.0
    )
    
    # Create requirements
    requirements = Requirements(
        purpose="Test system",
        functional_requirements=[req],
        non_functional_requirements=[],
        success_criteria=["All tests pass"]
    )
    
    # Create design
    comp_design = ComponentDesign(
        name="TestComponent",
        description="A test component",
        class_name="TestClass",
        methods=["test_method"],
        properties=["test_property"]
    )
    
    design = Design(
        architecture="Microservices",
        components=[comp_design],
        interfaces=[],
        implementation_notes="Test implementation"
    )
    
    # Create metadata
    metadata = RecipeMetadata(
        created_at=datetime.now(),
        updated_at=datetime.now(),
        author="Test Author",
        tags=["test"],
        build_count=0
    )
    
    # Create recipe
    recipe = Recipe(
        name="test-recipe",
        version="1.0.0",
        description="Test recipe",
        author="Test Author",
        metadata=metadata,
        requirements=requirements,
        design=design,
        components=[]
    )
    
    print(f"✓ Created recipe: {recipe.name}")
    print(f"  - Version: {recipe.version}")
    print(f"  - Author: {recipe.author}")
    print(f"  - Requirements: {len(recipe.requirements.get_all_requirements())}")
    print(f"  - Components: {len(recipe.design.components)}")
    
    # Test serialization
    recipe_dict = recipe.model_dump()
    print(f"✓ Serialized to dict with {len(recipe_dict)} fields")
    
    # Test JSON serialization
    recipe_json = recipe.model_dump_json()
    print(f"✓ Serialized to JSON ({len(recipe_json)} chars)")
    
    return True

def test_execution_model():
    """Test ExecutionState model."""
    print("\nTesting ExecutionState model...")
    
    state = ExecutionState(
        recipe_name="test-recipe",
        phase=ExecutionPhase.INITIALIZING,
        start_time=datetime.now()
    )
    
    # Update phase
    state.update_phase(ExecutionPhase.PARSING)
    print(f"✓ Created execution state in phase: {state.phase.value}")
    
    # Add an error
    state.add_error(ExecutionPhase.PARSING, "Test error", {"detail": "test"})
    print(f"✓ Added error, total errors: {len(state.errors)}")
    
    # Check progress
    progress = state.get_progress()
    print(f"✓ Progress: {progress}%")
    
    return True

def test_validation_model():
    """Test ValidationResult model."""
    print("\nTesting ValidationResult model...")
    
    result = ValidationResult()
    
    # Add different types of issues
    result.add_error("Critical error", ValidationCategory.SYNTAX, location="line 10")
    result.add_warning("Potential issue", ValidationCategory.SEMANTIC, location="line 20")
    result.add_info("Style suggestion", ValidationCategory.STYLE, location="line 30")
    
    print(f"✓ Added validation issues:")
    print(f"  - Errors: {len(result.errors)}")
    print(f"  - Warnings: {len(result.warnings)}")
    print(f"  - Info: {len(result.info)}")
    
    # Check if has critical errors
    has_critical = result.has_critical_errors()
    print(f"✓ Has critical errors: {has_critical}")
    
    # Get summary
    summary = result.to_summary()
    print(f"✓ Generated summary with {len(summary)} fields")
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("DATA MODELS VERIFICATION TEST")
    print("=" * 60)
    
    try:
        # Test each model
        test_recipe_model()
        test_execution_model()
        test_validation_model()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED - Data models are working correctly!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())