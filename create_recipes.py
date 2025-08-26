#!/usr/bin/env python3
"""Quick recipe creator for remaining components."""

import json
from pathlib import Path

recipes = {
    "quality-tools": {
        "purpose": "Code quality checking and enforcement tools",
        "components": ["linter.py", "formatter.py", "type_checker.py"],
        "exports": ["Linter", "Formatter", "TypeChecker"]
    },
    "validation-service": {
        "purpose": "Validate recipes and generated code against requirements",
        "components": ["recipe_validator.py", "code_validator.py"],
        "exports": ["RecipeValidator", "CodeValidator"]
    },
    "dependency-resolution": {
        "purpose": "Resolve and order recipe dependencies using topological sort",
        "components": ["dependency_resolver.py", "graph_builder.py"],
        "exports": ["DependencyResolver", "GraphBuilder"]
    },
    "code-generation": {
        "purpose": "Generate code from recipes using Claude or templates",
        "components": ["code_generator.py", "template_engine.py"],
        "exports": ["CodeGenerator", "TemplateEngine"]
    },
    "state-management": {
        "purpose": "Track build state and incremental compilation",
        "components": ["state_manager.py", "cache_manager.py"],
        "exports": ["StateManager", "CacheManager"]
    },
    "main-orchestrator": {
        "purpose": "Main orchestration engine that coordinates all components",
        "components": ["orchestrator.py", "workflow_engine.py"],
        "exports": ["Orchestrator", "WorkflowEngine"]
    }
}

for name, info in recipes.items():
    recipe_dir = Path(f"recipes/{name}")
    recipe_dir.mkdir(exist_ok=True)
    
    # Create requirements.md
    with open(recipe_dir / "requirements.md", "w") as f:
        f.write(f"# {name.replace('-', ' ').title()} Requirements\n\n")
        f.write(f"## Purpose\n{info['purpose']}\n\n")
        f.write("## Functional Requirements\n")
        for i in range(1, 6):
            f.write(f"- **{name}-fr-{i}** (MUST): Requirement {i}\n")
        f.write("\n## Non-Functional Requirements\n")
        for i in range(1, 4):
            f.write(f"- **{name}-nfr-{i}** (MUST): Non-functional {i}\n")
    
    # Create design.md
    with open(recipe_dir / "design.md", "w") as f:
        f.write(f"# {name.replace('-', ' ').title()} Design\n\n")
        f.write(f"## Architecture\n{info['purpose']}\n\n")
        f.write("## Components\n")
        for comp in info['components']:
            f.write(f"### {comp}\n")
            f.write(f"Main implementation file\n\n")
    
    # Create components.json
    components_data = {
        "name": name,
        "version": "1.0.0",
        "type": "library",
        "components": [
            {
                "name": comp.replace('.py', ''),
                "path": comp,
                "exports": info['exports']
            } for comp in info['components']
        ]
    }
    
    with open(recipe_dir / "components.json", "w") as f:
        json.dump(components_data, f, indent=2)

print(f"Created {len(recipes)} recipes")
