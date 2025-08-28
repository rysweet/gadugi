#!/usr/bin/env python3
"""Install Recipe Executor agents to .claude/agents directory."""

import shutil
from pathlib import Path
from typing import List, Tuple, Optional


def install_recipe_agents(target_dir: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """Install Recipe Executor agents to the Claude Code agents directory.

    Args:
        target_dir: Directory to install agents to (default: .claude/agents)

    Returns:
        Tuple of (success, list of messages)
    """
    messages: List[str] = []
    
    # Use default directory if none provided
    if target_dir is None:
        target_dir = Path(".claude/agents")

    # Find agent files
    agents_source_dir = Path(__file__).parent / "agents"
    if not agents_source_dir.exists():
        return False, [f"Agents source directory not found: {agents_source_dir}"]

    agent_files = list(agents_source_dir.glob("*.md"))
    if not agent_files:
        return False, [f"No agent files found in {agents_source_dir}"]

    # Create target directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)
    messages.append(f"Created/verified target directory: {target_dir}")

    # Install each agent
    installed: List[str] = []
    for agent_file in agent_files:
        target_file = target_dir / agent_file.name

        # Check if file exists and has different content
        if target_file.exists():
            existing_content = target_file.read_text()
            new_content = agent_file.read_text()
            if existing_content == new_content:
                messages.append(f"Skipped {agent_file.name} (already up to date)")
                continue
            else:
                messages.append(f"Updating {agent_file.name}")
        else:
            messages.append(f"Installing {agent_file.name}")

        # Copy the file
        shutil.copy2(agent_file, target_file)
        installed.append(agent_file.name)

    if installed:
        messages.append(f"\nSuccessfully installed {len(installed)} agent(s):")
        for name in installed:
            # Remove .md extension for agent name
            agent_name = name[:-3] if name.endswith(".md") else name
            messages.append(f"  - /agent:{agent_name}")
    else:
        messages.append("\nAll agents are already up to date.")

    messages.append("\nUsage examples:")
    messages.append("  /agent:recipe-executor     - Execute recipes to generate code")
    messages.append("  /agent:recipe-writer        - Write recipes from requirements")
    messages.append("  /agent:recipe-extractor     - Extract recipes from existing code")

    return True, messages


def main():
    """Main entry point for CLI usage."""
    import sys

    # Check if custom directory provided
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        # Try to find .claude directory
        current = Path.cwd()
        while current != current.parent:
            claude_dir = current / ".claude" / "agents"
            if (current / ".claude").exists():
                target = claude_dir
                break
            current = current.parent
        else:
            # Default to current directory
            target = Path(".claude/agents")

    success, messages = install_recipe_agents(target)

    for message in messages:
        print(message)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
