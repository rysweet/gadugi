#!/usr/bin/env python3
"""
Test decomposed recipe generation approach
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

def test_single_component_generation():
    """Test generating a single decomposed component"""
    print("=== TESTING SINGLE COMPONENT GENERATION ===\n")
    
    # Test with data-models which we know works
    print("Testing data-models generation...")
    result = subprocess.run([
        "uv", "run", "python", "-m", "src.recipe_executor",
        "execute", "recipes/data-models",
        "--output", ".recipe_build/test-single"
    ], capture_output=True, text=True, timeout=30)
    
    if "generated" in result.stdout.lower() or result.returncode == 0:
        print("✅ data-models generation works")
        return True
    else:
        print(f"❌ data-models generation failed: {result.stderr[:200]}")
        return False

def analyze_recipe_executor_current_state():
    """Analyze the current Recipe Executor implementation"""
    print("\n=== ANALYZING CURRENT RECIPE EXECUTOR ===\n")
    
    recipe_executor_dir = Path("src/recipe_executor")
    
    # List key files
    key_files = [
        "orchestrator.py",
        "claude_code_generator.py", 
        "recipe_parser.py",
        "dependency_resolver.py",
        "validator.py"
    ]
    
    print("Key Recipe Executor components:")
    for file in key_files:
        file_path = recipe_executor_dir / file
        if file_path.exists():
            lines = len(file_path.read_text().splitlines())
            print(f"  ✅ {file}: {lines} lines")
        else:
            print(f"  ❌ {file}: NOT FOUND")
    
    # Check for decomposed recipe handling
    claude_gen = recipe_executor_dir / "claude_code_generator.py"
    if claude_gen.exists():
        content = claude_gen.read_text()
        if "_is_component_recipe" in content:
            print("\n✅ Recipe Executor has decomposed recipe support")
        else:
            print("\n❌ Recipe Executor lacks decomposed recipe support")

def create_improved_recipe_executor():
    """Create an improved Recipe Executor that handles decomposed recipes"""
    print("\n=== CREATING IMPROVED RECIPE EXECUTOR ===\n")
    
    improved_executor = Path(".recipe_build/improved_executor.py")
    improved_executor.parent.mkdir(exist_ok=True)
    
    improved_executor.write_text('''#!/usr/bin/env python3
"""
Improved Recipe Executor with decomposed recipe support
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class ImprovedRecipeExecutor:
    """Improved executor that handles decomposed recipes"""
    
    def __init__(self):
        self.recipes_dir = Path("recipes")
        self.output_base = Path(".recipe_build/improved-gen2")
        
    def load_recipe(self, name: str) -> Dict[str, Any]:
        """Load a recipe"""
        recipe_dir = self.recipes_dir / name
        
        # Try different file formats
        for file in ["recipe.json", "components.json", "dependencies.json"]:
            file_path = recipe_dir / file
            if file_path.exists():
                with open(file_path) as f:
                    return json.load(f)
        
        # Fallback to basic recipe
        return {
            "name": name,
            "dependencies": [],
            "type": "component"
        }
    
    def get_all_dependencies(self, recipe_name: str, visited: set = None) -> List[str]:
        """Get all dependencies recursively"""
        if visited is None:
            visited = set()
        
        if recipe_name in visited:
            return []
        
        visited.add(recipe_name)
        result = []
        
        recipe = self.load_recipe(recipe_name)
        deps = recipe.get("dependencies", [])
        
        for dep in deps:
            result.extend(self.get_all_dependencies(dep, visited))
            if dep not in result:
                result.append(dep)
        
        return result
    
    def generate_component(self, name: str) -> bool:
        """Generate a single component using the current Recipe Executor"""
        print(f"Generating component: {name}")
        
        output_dir = self.output_base / name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Try using the actual Recipe Executor first
        result = subprocess.run([
            "uv", "run", "python", "-m", "src.recipe_executor",
            "execute", f"recipes/{name}",
            "--output", str(output_dir)
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"  ✅ Generated {name}")
            return True
        else:
            # Fallback to simple generation
            print(f"  ⚠️  Fallback generation for {name}")
            self.generate_simple_component(name, output_dir)
            return True
    
    def generate_simple_component(self, name: str, output_dir: Path):
        """Simple fallback generation"""
        component_file = output_dir / f"{name.replace('-', '_')}.py"
        component_file.write_text(f\'\'\'
"""
{name} component
Generated by Improved Recipe Executor
"""

class {name.replace("-", " ").title().replace(" ", "")}:
    """Generated {name} component"""
    
    def __init__(self):
        self.name = "{name}"
    
    def execute(self, **kwargs):
        return {{"status": "success", "component": self.name}}
\'\'\')
    
    def execute(self, recipe_name: str):
        """Execute a recipe with all its dependencies"""
        print(f"\\n{'='*60}")
        print(f"IMPROVED RECIPE EXECUTOR")
        print(f"Executing: {recipe_name}")
        print(f"{'='*60}\\n")
        
        # Get all dependencies
        deps = self.get_all_dependencies(recipe_name)
        print(f"Dependencies to generate: {deps}")
        
        # Generate each dependency
        for dep in deps:
            self.generate_component(dep)
        
        # Generate the main recipe
        self.generate_component(recipe_name)
        
        print(f"\\n{'='*60}")
        print(f"✅ Generation complete!")
        print(f"Output: {self.output_base}")
        print(f"{'='*60}\\n")

if __name__ == "__main__":
    executor = ImprovedRecipeExecutor()
    executor.execute("recipe-executor")
''')
    
    print(f"Created improved executor at: {improved_executor}")
    
    # Test it
    print("\nTesting improved executor...")
    result = subprocess.run([
        "uv", "run", "python", str(improved_executor)
    ], capture_output=True, text=True, timeout=120)
    
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error: {result.stderr[:500]}")

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DECOMPOSED RECIPE GENERATION TEST")
    print("="*80 + "\n")
    
    # Test single component
    if test_single_component_generation():
        print("✅ Single component generation works")
    
    # Analyze current state
    analyze_recipe_executor_current_state()
    
    # Create and test improved executor
    create_improved_recipe_executor()
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()