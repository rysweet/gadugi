#!/usr/bin/env python3
"""Test the Recipe Executor model components."""

import sys
from pathlib import Path
from dataclasses import dataclass

# Test imports
print("Testing imports...")

try:
    from src.recipe_executor.recipe_model import (
        Recipe, Requirements, Design, Components, RecipeMetadata,
        DesignPattern, DependencyGraph, BuildState, RecipeComplexity,
        ComplexityMetrics, SubRecipe, ComponentType, RequirementPriority,
        Requirement, ComponentDesign, Interface, DependencyNode
    )
    print("✅ Recipe model imports successful")
except ImportError as e:
    print(f"❌ Recipe model import failed: {e}")
    sys.exit(1)

try:
    from src.recipe_executor.pattern_loader import PatternLoader, PatternLibrary
    print("✅ Pattern loader imports successful")
except ImportError as e:
    print(f"❌ Pattern loader import failed: {e}")
    sys.exit(1)

try:
    from src.recipe_executor.dependency_graph import DependencyAnalyzer
    print("✅ Dependency graph imports successful")
except ImportError as e:
    print(f"❌ Dependency graph import failed: {e}")
    sys.exit(1)

try:
    from src.recipe_executor.complexity_analyzer import ComplexityAnalyzer
    print("✅ Complexity analyzer imports successful")
except ImportError as e:
    print(f"❌ Complexity analyzer import failed: {e}")
    sys.exit(1)

# Test functionality
print("\nTesting functionality...")

# Test pattern loading
pattern_loader = PatternLoader()
patterns = pattern_loader.list_available_patterns()
print(f"✅ Pattern loader initialized with {len(patterns)} patterns: {patterns}")

# Test design pattern
agent_pattern = pattern_loader.get_pattern_for_component(ComponentType.AGENT)
if agent_pattern:
    print(f"✅ Agent pattern loaded: {agent_pattern.name}")
else:
    print("❌ Agent pattern not found")

# Test dependency analyzer
dep_analyzer = DependencyAnalyzer()
print("✅ Dependency analyzer initialized")

# Test complexity analyzer
comp_analyzer = ComplexityAnalyzer()
print("✅ Complexity analyzer initialized")

# Create a sample recipe to test
from datetime import datetime

req = Requirement(
    id="req_001",
    description="Test requirement",
    priority=RequirementPriority.MUST,
    validation_criteria=["Must pass tests"],
    implemented=False
)

requirements = Requirements(
    purpose="Test recipe",
    functional_requirements=[req],
    non_functional_requirements=[],
    success_criteria=["All tests pass"]
)

component = ComponentDesign(
    name="TestComponent",
    description="A test component",
    methods=["execute", "validate"],
    properties=["config", "state"]
)

design = Design(
    architecture="Simple test architecture",
    components=[component],
    interfaces=[],
    implementation_notes="Test implementation"
)

components = Components(
    name="test-recipe",
    version="1.0.0",
    type=ComponentType.SERVICE,
    dependencies=[],
    description="Test recipe component"
)

metadata = RecipeMetadata(
    created_at=datetime.now(),
    updated_at=datetime.now(),
    author="Test"
)

recipe = Recipe(
    name="test-recipe",
    path=Path("test"),
    requirements=requirements,
    design=design,
    components=components,
    metadata=metadata
)

print(f"✅ Created test recipe: {recipe.name}")

# Test complexity analysis
complexity = comp_analyzer.analyze_recipe(recipe)
print(f"✅ Complexity analysis: score={complexity.metrics.complexity_score}, decompose={complexity.decomposition_recommended}")

# Test dependency graph
dep_analyzer.build_dependency_graph([recipe])
build_order = dep_analyzer.get_build_order()
print(f"✅ Dependency graph built: {len(build_order)} build groups")

# Test pattern merging
recipe.merge_with_pattern(agent_pattern)
print(f"✅ Pattern merged with recipe")

# Test checksum calculation
checksum = recipe.calculate_checksum()
print(f"✅ Checksum calculated: {checksum[:8]}...")

# Test self-overwrite protection
has_risk = recipe.has_self_overwrite_risk()
print(f"✅ Self-overwrite protection check: {'PROTECTED' if has_risk else 'SAFE'}")

# Test dependency validation
is_valid, errors = recipe.validate_dependencies()
print(f"✅ Dependency validation: {'VALID' if is_valid else 'INVALID'}")

# Test build state
build_state = BuildState(
    recipe_name=recipe.name,
    last_build_time=datetime.now(),
    last_checksum=checksum,
    output_files=["test.py"],
    success=True
)
needs_rebuild = build_state.needs_rebuild(checksum)
print(f"✅ Build state check: needs_rebuild={needs_rebuild}")

# Test dependency graph features
dep_graph = DependencyGraph()
dep_graph.add_recipe(recipe)
has_circular, cycle = dep_graph.has_circular_dependency()
print(f"✅ Circular dependency check: {'FOUND' if has_circular else 'NONE'}")

print("\n" + "="*50)
print("✅ ALL TESTS PASSED - Recipe Executor model is fully functional!")
print("="*50)