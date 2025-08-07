#!/usr/bin/env python3
"""
Convert existing agents to proper Claude Code sub-agent format.
This creates actual executable agent definitions, not documentation about agents.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

def process_agent(source_file: Path, target_dir: Path) -> None:
    """Process a single agent file and convert to proper format."""
    
    agent_name = source_file.stem
    
    # Convert to CamelCase for directory name
    camel_name = ''.join(word.capitalize() for word in agent_name.split('-'))
    
    # Create agent directory
    agent_dir = target_dir / camel_name
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    # Read the original agent content
    with open(source_file, 'r') as f:
        content = f.read()
    
    # Copy the agent definition directly - it's already in the right format!
    # The original agents ARE the agent definitions, not documentation
    agent_file = agent_dir / f"{camel_name}.md"
    
    # For the main agent file, we want to preserve the original structure
    # but potentially extract embedded Python code to separate files
    
    # Extract Python code blocks
    python_blocks = []
    pattern = r'```python\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    if matches:
        src_dir = agent_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        for i, code in enumerate(matches, 1):
            # Try to extract a meaningful name
            if 'def ' in code:
                func_match = re.search(r'def\s+(\w+)', code)
                if func_match:
                    code_name = func_match.group(1)
                else:
                    code_name = f"function_{i}"
            elif 'class ' in code:
                class_match = re.search(r'class\s+(\w+)', code)
                if class_match:
                    code_name = class_match.group(1).lower()
                else:
                    code_name = f"class_{i}"
            else:
                code_name = f"code_{i}"
            
            # Save the code to a file
            code_file = src_dir / f"{code_name}.py"
            with open(code_file, 'w') as f:
                f.write(code)
            
            python_blocks.append((code_name, code_file.name))
    
    # Now write the agent file
    # Check if we should modify it to reference external code
    if python_blocks and len(content) > 10000:  # Only extract for large agents
        # For very large agents with lots of embedded code, we can reference external files
        # But for most agents, keeping the code inline is better for clarity
        
        # Replace large code blocks with references
        modified_content = content
        for code_name, file_name in python_blocks:
            # Add a note about extracted code at the end
            if "## Code Modules" not in modified_content:
                modified_content += "\n\n## Code Modules\n\n"
                modified_content += "Large code blocks have been extracted to the `src/` directory for maintainability:\n\n"
            modified_content += f"- `src/{file_name}` - {code_name} implementation\n"
        
        with open(agent_file, 'w') as f:
            f.write(modified_content)
    else:
        # For most agents, just copy the original - it's already perfect
        shutil.copy2(source_file, agent_file)
    
    # Create a README for the agent directory (for human reference)
    readme_content = f"""# {camel_name}

This directory contains the {agent_name} agent definition.

## Files

- `{camel_name}.md` - The agent definition (this IS the agent)
{'- `src/` - Extracted Python code modules' if python_blocks else ''}

## Usage

This agent can be invoked using:
```
/agent:{agent_name}
```

## Note

The `{camel_name}.md` file is not documentation ABOUT the agent - it IS the agent itself.
It contains the complete instructions and logic that Claude Code uses when this agent is invoked.
"""
    
    readme_path = agent_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)

def create_agents_index(target_dir: Path) -> None:
    """Create an index of all agents."""
    
    # Find all agent directories
    agent_dirs = [d for d in target_dir.iterdir() if d.is_dir()]
    agent_dirs.sort()
    
    content = """# Gadugi Agent Definitions

This directory contains the actual agent definitions for the Gadugi system.

## Important Note

These `.md` files are NOT documentation about agents - they ARE the agents themselves.
Each markdown file contains the complete instructions and logic that Claude Code executes when the agent is invoked.

## Agent Organization

Each agent has its own directory with:
- `AgentName.md` - The actual agent definition (the executable instructions)
- `README.md` - Human-readable notes about the agent
- `src/` - (optional) Extracted Python code for very large agents

## Available Agents

"""
    
    # Group agents by category based on their purpose
    categories = {
        "Orchestration": [],
        "Development": [],
        "Testing": [],
        "Infrastructure": [],
        "Planning": [],
        "Documentation": [],
        "Support": []
    }
    
    for agent_dir in agent_dirs:
        agent_name = agent_dir.name
        kebab_name = re.sub(r'(?<!^)(?=[A-Z])', '-', agent_name).lower()
        
        # Categorize based on name
        if any(x in agent_name.lower() for x in ['orchestrat', 'workflow', 'execution', 'analyzer']):
            category = "Orchestration"
        elif any(x in agent_name.lower() for x in ['code', 'review', 'pr', 'prompt']):
            category = "Development"
        elif any(x in agent_name.lower() for x in ['test']):
            category = "Testing"
        elif any(x in agent_name.lower() for x in ['worktree', 'memory', 'gadugi', 'update']):
            category = "Infrastructure"
        elif any(x in agent_name.lower() for x in ['task', 'decompos', 'research', 'bounds']):
            category = "Planning"
        elif any(x in agent_name.lower() for x in ['readme', 'design']):
            category = "Documentation"
        else:
            category = "Support"
        
        categories[category].append((agent_name, kebab_name))
    
    # Write categories
    for category, agents in categories.items():
        if agents:
            content += f"\n### {category}\n\n"
            for agent_name, kebab_name in sorted(agents):
                content += f"- **[{agent_name}](./{agent_name}/{agent_name}.md)** (`/agent:{kebab_name}`) - The {kebab_name} agent\n"
    
    content += """

## How to Use These Agents

1. **Direct Invocation**: Use `/agent:agent-name` to invoke an agent
2. **Reading the Definition**: Open the `.md` file to see exactly what the agent does
3. **Modifying Agents**: Edit the `.md` file directly to change agent behavior
4. **Testing Changes**: Invoke the agent after editing to test your changes

## Agent Definition Format

Each agent follows the Claude Code sub-agent format:

```yaml
---
name: agent-name
description: What the agent does
tools: [List, of, required, tools]
imports: Optional imports or dependencies
---

# Agent instructions in markdown
```

## Development Notes

When creating or modifying agents:
1. Keep instructions clear and specific
2. Use the tools list to declare required capabilities
3. Include error handling instructions
4. Follow the "bricks & studs" philosophy from Guidelines.md
5. Test the agent thoroughly after changes

Remember: These files ARE the agents - they're not documentation, they're executable definitions.
"""
    
    # Write the index
    index_path = target_dir / "README.md"
    with open(index_path, 'w') as f:
        f.write(content)

def main():
    """Main conversion function."""
    source_dir = Path("/Users/ryan/gadugi7/gadugi/.claude/agents")
    target_dir = Path("/Users/ryan/gadugi7/gadugi/prompts/Gadugi-v0.3/agents")
    
    # Clear existing directory
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)
    
    print("Converting agents to proper executable format...")
    
    # Process each agent markdown file
    for agent_file in source_dir.glob("*.md"):
        # Skip special files
        if any(skip in agent_file.stem for skip in ['simplified', 'phase9', 'reflection']):
            continue
        
        print(f"  Converting {agent_file.stem}...")
        process_agent(agent_file, target_dir)
    
    # Copy Python support files where appropriate
    for py_file in source_dir.glob("*.py"):
        if py_file.stem not in ['__init__', 'shared_test_instructions']:
            # These are support files that some agents reference
            agent_name = py_file.stem.replace('_', '-')
            camel_name = ''.join(word.capitalize() for word in agent_name.split('-'))
            
            agent_dir = target_dir / camel_name
            if agent_dir.exists():
                src_dir = agent_dir / "src"
                src_dir.mkdir(exist_ok=True)
                shutil.copy2(py_file, src_dir / py_file.name)
                print(f"    Added support file {py_file.name}")
    
    # Copy agent subdirectories with their code
    for subdir in source_dir.iterdir():
        if subdir.is_dir() and subdir.name not in ['__pycache__']:
            agent_name = subdir.name.replace('_', '-')
            camel_name = ''.join(word.capitalize() for word in agent_name.split('-'))
            
            agent_dir = target_dir / camel_name
            if agent_dir.exists():
                src_dir = agent_dir / "src"
                if subdir.exists():
                    shutil.copytree(subdir, src_dir, dirs_exist_ok=True)
                    print(f"    Copied {subdir.name} code directory")
    
    # Create the index
    print("\nCreating agent index...")
    create_agents_index(target_dir)
    
    print(f"\n✅ Conversion complete! Agents are now in proper executable format.")
    print(f"   Location: {target_dir}")
    print(f"   Remember: The .md files ARE the agents, not documentation about them.")

if __name__ == "__main__":
    main()