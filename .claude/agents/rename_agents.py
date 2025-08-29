#!/usr/bin/env python3
"""
Script to rename all agent files from kebab-case to CamelCase
and update all references throughout the codebase.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Define the mapping of old names to new names
AGENT_RENAME_MAP = {
    "AgentUpdater.md": "AgentUpdater.md",
    "ClaudeSettingsUpdate.md": "ClaudeSettingsUpdate.md",
    "CodeExecutor.md": "CodeExecutor.md",
    "CodeReviewResponse.md": "CodeReviewResponse.md",
    "CodeReviewer.md": "CodeReviewer.md",
    "EventRouterManager.md": "EventRouterManager.md",
    "EventRouterServiceManager.md": "EventRouterServiceManager.md",
    "ExecutionMonitor.md": "ExecutionMonitor.md",
    "GadugiCoordinator.md": "GadugiCoordinator.md",
    "GitHubExecutor.md": "GitHubExecutor.md",
    "LlmProxyAgent.md": "LlmProxyAgent.md",
    "MemoryManager.md": "MemoryManager.md",
    "MemoryServiceManager.md": "MemoryServiceManager.md",
    "Neo4jServiceManager.md": "Neo4jServiceManager.md",
    "OrchestratorAgent.md": "OrchestratorAgent.md",
    "PrBacklogManager.md": "PrBacklogManager.md",
    "ProgramManager.md": "ProgramManager.md",
    "PromptWriter.md": "PromptWriter.md",
    "ReadmeAgent.md": "ReadmeAgent.md",
    "RecipeExecutor.md": "RecipeExecutor.md",
    "SystemDesignReviewer.md": "SystemDesignReviewer.md",
    "TaskAnalyzer.md": "TaskAnalyzer.md",
    "TaskBoundsEval.md": "TaskBoundsEval.md",
    "TaskDecomposer.md": "TaskDecomposer.md",
    "TaskResearchAgent.md": "TaskResearchAgent.md",
    "TeamCoach.md": "TeamCoach.md",
    "TeamcoachAgent.md": "TeamcoachAgent.md",
    "TestExecutor.md": "TestExecutor.md",
    "TestSolver.md": "TestSolver.md",
    "TestWriter.md": "TestWriter.md",
    "TypeFixAgent.md": "TypeFixAgent.md",
    "WorkflowManagerPhase9Enforcement.md": "WorkflowManagerPhase9Enforcement.md",
    "WorkflowManagerSimplified.md": "WorkflowManagerSimplified.md",
    "WorkflowManager.md": "WorkflowManager.md",
    "WorkflowPhaseReflection.md": "WorkflowPhaseReflection.md",
    "WorktreeExecutor.md": "WorktreeExecutor.md",
    "WorktreeManager.md": "WorktreeManager.md",
    "XpiaDefenseAgent.md": "XpiaDefenseAgent.md",
}

# Common reference patterns to search for
REFERENCE_PATTERNS = [
    # Agent invocations
    (r'/agent:([a-z-]+)', r'/agent:\1'),
    # Agent file references in strings
    (r'["\'`]([a-z-]+)\.md["\'`]', r'"\1.md"'),
    # Agent file paths
    (r'\.claude/agents/([a-z-]+)\.md', r'.claude/agents/\1.md'),
    # Import statements (if any)
    (r'from \.claude\.agents import ([a-z_]+)', r'from .claude.agents import \1'),
]

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path("/Users/ryan/src/gadugi5/gadugi")

def create_rename_mapping() -> Dict[str, str]:
    """Create a complete mapping including variations."""
    mapping = {}
    
    # Add basic mappings
    for old, new in AGENT_RENAME_MAP.items():
        mapping[old] = new
        # Without .md extension
        old_base = old.replace('.md', '')
        new_base = new.replace('.md', '')
        mapping[old_base] = new_base
        
        # With agent: prefix for invocations
        mapping[f"agent:{old_base}"] = f"agent:{new_base}"
        mapping[f"/agent:{old_base}"] = f"/agent:{new_base}"
    
    return mapping

def find_files_to_update() -> List[Path]:
    """Find all files that might contain references to agents."""
    root = get_project_root()
    files_to_check = []
    
    # File patterns to check
    patterns = [
        "**/*.py",
        "**/*.md",
        "**/*.sh",
        "**/*.json",
        "**/*.yaml",
        "**/*.yml",
        "**/CLAUDE.md",
        "**/Memory.md",
        ".claude/**/*",
        "prompts/**/*",
    ]
    
    for pattern in patterns:
        files_to_check.extend(root.glob(pattern))
    
    # Filter out directories and binary files
    return [f for f in files_to_check if f.is_file() and not f.name.endswith(('.pyc', '.pyo', '.so', '.dylib'))]

def update_file_references(file_path: Path, mapping: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Update references in a single file."""
    try:
        content = file_path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, PermissionError):
        return False, []
    
    original_content = content
    changes = []
    
    # Apply mappings
    for old, new in mapping.items():
        if old in content:
            # Count occurrences
            count = content.count(old)
            if count > 0:
                content = content.replace(old, new)
                changes.append(f"  - Replaced {count} occurrences of '{old}' with '{new}'")
    
    # Save if changed
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return True, changes
    
    return False, []

def rename_agent_files() -> List[str]:
    """Rename the actual agent files."""
    agents_dir = get_project_root() / ".claude" / "agents"
    renamed = []
    
    for old_name, new_name in AGENT_RENAME_MAP.items():
        old_path = agents_dir / old_name
        new_path = agents_dir / new_name
        
        if old_path.exists():
            # Check if target already exists
            if new_path.exists():
                print(f"Warning: {new_name} already exists, skipping {old_name}")
                continue
            
            # Rename the file
            old_path.rename(new_path)
            renamed.append(f"{old_name} -> {new_name}")
            print(f"Renamed: {old_name} -> {new_name}")
    
    return renamed

def create_compatibility_symlinks() -> List[str]:
    """Create symlinks for backward compatibility."""
    agents_dir = get_project_root() / ".claude" / "agents"
    symlinks = []
    
    for old_name, new_name in AGENT_RENAME_MAP.items():
        old_path = agents_dir / old_name
        new_path = agents_dir / new_name
        
        if new_path.exists() and not old_path.exists():
            # Create symlink from old name to new name
            try:
                old_path.symlink_to(new_name)
                symlinks.append(f"{old_name} -> {new_name}")
                print(f"Created symlink: {old_name} -> {new_name}")
            except OSError as e:
                print(f"Could not create symlink for {old_name}: {e}")
    
    return symlinks

def update_agent_registry():
    """Update the agent_registry.py file if it exists."""
    registry_path = get_project_root() / ".claude" / "agents" / "agent_registry.py"
    
    if not registry_path.exists():
        print("Agent registry not found, skipping")
        return
    
    content = registry_path.read_text()
    original = content
    
    # Update any agent name references
    for old, new in AGENT_RENAME_MAP.items():
        old_base = old.replace('.md', '')
        new_base = new.replace('.md', '')
        
        # Update in various contexts
        content = content.replace(f'"{old}"', f'"{new}"')
        content = content.replace(f"'{old}'", f"'{new}'")
        content = content.replace(f'"{old_base}"', f'"{new_base}"')
        content = content.replace(f"'{old_base}'", f"'{new_base}'")
    
    if content != original:
        registry_path.write_text(content)
        print("Updated agent_registry.py")

def main():
    """Main execution function."""
    print("=" * 60)
    print("Agent Renaming: kebab-case to CamelCase")
    print("=" * 60)
    
    # Step 1: Rename agent files
    print("\n1. Renaming agent files...")
    renamed_files = rename_agent_files()
    print(f"Renamed {len(renamed_files)} files")
    
    # Step 2: Update references throughout codebase
    print("\n2. Updating references throughout codebase...")
    mapping = create_rename_mapping()
    files_to_update = find_files_to_update()
    
    updated_count = 0
    all_changes = []
    
    for file_path in files_to_update:
        was_updated, changes = update_file_references(file_path, mapping)
        if was_updated:
            updated_count += 1
            relative_path = file_path.relative_to(get_project_root())
            print(f"Updated: {relative_path}")
            for change in changes:
                print(f"  {change}")
            all_changes.append((str(relative_path), changes))
    
    print(f"\nUpdated {updated_count} files with references")
    
    # Step 3: Update agent registry
    print("\n3. Updating agent registry...")
    update_agent_registry()
    
    # Step 4: Create compatibility symlinks
    print("\n4. Creating backward compatibility symlinks...")
    symlinks = create_compatibility_symlinks()
    print(f"Created {len(symlinks)} symlinks")
    
    # Step 5: Generate summary report
    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    print(f"Files renamed: {len(renamed_files)}")
    print(f"Files updated: {updated_count}")
    print(f"Symlinks created: {len(symlinks)}")
    
    # Save detailed report
    report_path = get_project_root() / ".claude" / "agents" / "rename_report.json"
    report = {
        "renamed_files": renamed_files,
        "updated_files": dict(all_changes),
        "symlinks": symlinks,
        "mapping": AGENT_RENAME_MAP
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")
    print("\nRenaming complete!")

if __name__ == "__main__":
    main()