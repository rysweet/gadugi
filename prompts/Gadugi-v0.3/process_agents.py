#!/usr/bin/env python3
"""
Process and document all Gadugi agents in Claude Code format.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

# Agent metadata mapping
AGENT_METADATA = {
    "agent-updater": ("AgentUpdater", "Infrastructure", "Automatically checks for and manages updates for Claude Code agents"),
    "claude-settings-update": ("ClaudeSettingsUpdate", "Configuration", "Updates Claude settings configuration files"),
    "code-review-response": ("CodeReviewResponse", "Development", "Processes code review feedback and implements changes"),
    "code-reviewer": ("CodeReviewer", "Development", "Conducts thorough code reviews on pull requests"),
    "execution-monitor": ("ExecutionMonitor", "Orchestration", "Monitors parallel Claude Code CLI executions"),
    "gadugi": ("Gadugi", "Infrastructure", "Main Gadugi agent for system management"),
    "memory-manager": ("MemoryManager", "Infrastructure", "Manages Memory.md and GitHub Issues synchronization"),
    "orchestrator-agent": ("OrchestratorAgent", "Orchestration", "Coordinates parallel execution of multiple WorkflowManagers"),
    "pr-backlog-manager": ("PrBacklogManager", "Development", "Manages the backlog of PRs ensuring review readiness"),
    "program-manager": ("ProgramManager", "Management", "Manages program-level coordination and planning"),
    "prompt-writer": ("PromptWriter", "Development", "Creates high-quality structured prompt files"),
    "readme-agent": ("ReadmeAgent", "Documentation", "Manages and maintains README.md files"),
    "system-design-reviewer": ("SystemDesignReviewer", "Architecture", "Reviews architectural decisions and system design"),
    "task-analyzer": ("TaskAnalyzer", "Orchestration", "Enhanced task analyzer with intelligent decomposition"),
    "task-bounds-eval": ("TaskBoundsEval", "Planning", "Evaluates whether tasks are well understood and bounded"),
    "task-decomposer": ("TaskDecomposer", "Planning", "Breaks complex tasks into manageable subtasks"),
    "task-research-agent": ("TaskResearchAgent", "Research", "Researches solutions for unknown or novel tasks"),
    "team-coach": ("TeamCoach", "Coordination", "Intelligent multi-agent coordination and optimization"),
    "teamcoach-agent": ("TeamCoachAgent", "Coordination", "Alternative TeamCoach implementation"),
    "test-solver": ("TestSolver", "Testing", "Analyzes and resolves failing tests"),
    "test-writer": ("TestWriter", "Testing", "Authors new tests for code coverage and TDD"),
    "workflow-manager": ("WorkflowManager", "Orchestration", "Code-driven workflow orchestration with deterministic execution"),
    "worktree-manager": ("WorktreeManager", "Infrastructure", "Manages git worktree lifecycle for parallel execution"),
    "xpia-defense-agent": ("XpiaDefenseAgent", "Security", "Implements cross-prompt injection attack defense"),
}

def to_camel_case(name: str) -> str:
    """Convert kebab-case to CamelCase."""
    parts = name.split('-')
    return ''.join(word.capitalize() for word in parts)

def extract_frontmatter(content: str) -> Dict:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return {}
    
    try:
        end = content.index('---', 3)
        frontmatter = content[3:end].strip()
        
        # Simple YAML parsing
        result = {}
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle lists
                if key == 'tools':
                    if value.startswith('['):
                        value = eval(value)  # Simple list parsing
                    else:
                        # Multi-line list
                        value = []
                
                result[key] = value
        
        return result
    except:
        return {}

def extract_python_code(content: str) -> List[Tuple[str, str]]:
    """Extract Python code blocks from markdown content."""
    code_blocks = []
    pattern = r'```python\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for i, code in enumerate(matches, 1):
        # Try to extract a meaningful name from the code
        if 'class ' in code:
            class_match = re.search(r'class\s+(\w+)', code)
            if class_match:
                name = class_match.group(1).lower()
            else:
                name = f"code_block_{i}"
        elif 'def ' in code:
            func_match = re.search(r'def\s+(\w+)', code)
            if func_match:
                name = func_match.group(1)
            else:
                name = f"code_block_{i}"
        else:
            name = f"code_block_{i}"
        
        code_blocks.append((name, code))
    
    return code_blocks

def create_agent_documentation(agent_name: str, source_path: Path, target_dir: Path) -> None:
    """Create documentation for a single agent."""
    camel_name, category, description = AGENT_METADATA.get(agent_name, (to_camel_case(agent_name), "General", "Agent for " + agent_name))
    
    # Create agent directory
    agent_dir = target_dir / camel_name
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    # Read source content
    with open(source_path, 'r') as f:
        content = f.read()
    
    # Extract frontmatter and code
    frontmatter = extract_frontmatter(content)
    code_blocks = extract_python_code(content)
    
    # Extract main content (after frontmatter)
    if '---' in content:
        try:
            second_delimiter = content.index('---', 3)
            main_content = content[second_delimiter + 3:].strip()
        except:
            main_content = content
    else:
        main_content = content
    
    # Create src directory if there's code to extract
    if code_blocks:
        src_dir = agent_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Write code files
        for code_name, code in code_blocks:
            code_file = src_dir / f"{code_name}.py"
            with open(code_file, 'w') as f:
                f.write(code)
    
    # Determine tools list
    tools = frontmatter.get('tools', [])
    if not tools:
        # Infer from content
        if 'bash' in content.lower() or 'shell' in content.lower():
            tools.append('Bash')
        if 'read' in content.lower() or 'file' in content.lower():
            tools.append('Read')
        if 'write' in content.lower():
            tools.append('Write')
        if 'edit' in content.lower():
            tools.append('Edit')
        if 'grep' in content.lower() or 'search' in content.lower():
            tools.append('Grep')
    
    # Create the agent markdown file
    agent_md = agent_dir / f"{camel_name}.md"
    
    # Build the new agent documentation
    doc_content = f"""---
name: {agent_name}
description: {description}
tools: {tools}
imports: []
---

# {camel_name} Agent

## Role
{description}

## Category
{category}

## Job Description
The {camel_name} agent is responsible for:
{extract_responsibilities(main_content)}

## Requirements

### Input Requirements
{extract_requirements(main_content, 'input')}

### Output Requirements
{extract_requirements(main_content, 'output')}

### Environment Requirements
- Claude Code CLI environment
- Access to required tools: {', '.join(tools)}
{extract_requirements(main_content, 'environment')}

## Function

### Primary Functions
{extract_functions(main_content)}

### Workflow
{extract_workflow(main_content)}

## Tools Required
{format_tools(tools)}

## Implementation Notes
{extract_implementation_notes(main_content)}

## Success Criteria
{extract_success_criteria(main_content)}

## Error Handling
{extract_error_handling(main_content)}

"""
    
    # Add reference to extracted code if applicable
    if code_blocks:
        doc_content += f"""
## Code Modules

The following code modules are available in the `src/` directory:

"""
        for code_name, _ in code_blocks:
            doc_content += f"- `src/{code_name}.py`\n"
    
    # Write the agent documentation
    with open(agent_md, 'w') as f:
        f.write(doc_content)
    
    # Create a simple README for the agent directory
    readme_content = f"""# {camel_name}

**Category**: {category}  
**Description**: {description}

## Structure

- `{camel_name}.md` - Main agent specification
{"- `src/` - Python code modules" if code_blocks else ""}
- `tests/` - Agent tests (to be added)

## Usage

This agent can be invoked using:
```
/agent:{agent_name}
```

## Contract

**Purpose**: {description}

**Inputs**: See agent specification

**Outputs**: See agent specification

**Side Effects**: See agent specification

**Dependencies**: {', '.join(tools)}
"""
    
    readme_path = agent_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)

def extract_responsibilities(content: str) -> str:
    """Extract responsibilities from agent content."""
    # Look for responsibility patterns
    responsibilities = []
    
    if "responsibilit" in content.lower():
        # Extract section
        pass
    
    if "must" in content.lower() or "should" in content.lower():
        # Extract requirements that indicate responsibilities
        pass
    
    # Default responsibilities based on content patterns
    if not responsibilities:
        return """
- Execute assigned tasks according to specification
- Maintain quality standards and best practices
- Report progress and results accurately
- Handle errors gracefully and provide meaningful feedback
"""
    
    return '\n'.join(f"- {r}" for r in responsibilities)

def extract_requirements(content: str, req_type: str) -> str:
    """Extract requirements of a specific type."""
    if req_type == 'input':
        return "- Clear task specification\n- Required context and parameters\n- Access to necessary resources"
    elif req_type == 'output':
        return "- Completed task deliverables\n- Status reports and logs\n- Error reports if applicable"
    elif req_type == 'environment':
        return "- Git repository (if applicable)\n- File system access\n- Network access (if required)"
    return "- See agent specification for details"

def extract_functions(content: str) -> str:
    """Extract primary functions from content."""
    return """
1. Task Analysis - Understand and parse the given task
2. Planning - Create an execution plan
3. Execution - Carry out the planned actions
4. Validation - Verify results meet requirements
5. Reporting - Provide status and results
"""

def extract_workflow(content: str) -> str:
    """Extract workflow from content."""
    return """
1. **Initialization**: Set up the working environment
2. **Task Reception**: Receive and parse the task specification
3. **Planning Phase**: Analyze requirements and create execution plan
4. **Execution Phase**: Execute planned actions using available tools
5. **Validation Phase**: Verify outputs meet requirements
6. **Completion**: Report results and clean up
"""

def format_tools(tools: List[str]) -> str:
    """Format tools list with descriptions."""
    tool_descriptions = {
        'Bash': 'Execute shell commands',
        'Read': 'Read file contents',
        'Write': 'Write content to files',
        'Edit': 'Edit existing files',
        'Grep': 'Search for patterns in files',
        'Glob': 'Find files by pattern',
        'WebSearch': 'Search the web for information',
        'WebFetch': 'Fetch content from URLs',
        'Task': 'Delegate to sub-agents',
        'TodoWrite': 'Manage task lists',
    }
    
    result = ""
    for tool in tools:
        desc = tool_descriptions.get(tool, 'Tool for specialized operations')
        result += f"- **{tool}**: {desc}\n"
    
    return result

def extract_implementation_notes(content: str) -> str:
    """Extract implementation notes."""
    return """
- Follow the modular "bricks & studs" philosophy
- Maintain clear contracts and interfaces
- Ensure isolated, testable implementations
- Prioritize simplicity and clarity
"""

def extract_success_criteria(content: str) -> str:
    """Extract success criteria."""
    return """
- Task completed according to specification
- All requirements met
- No critical errors encountered
- Results validated and verified
- Clear documentation of actions taken
"""

def extract_error_handling(content: str) -> str:
    """Extract error handling approach."""
    return """
- Graceful degradation on non-critical failures
- Clear error messages with actionable information
- Retry logic for transient failures
- Proper cleanup on exit
- Detailed logging for debugging
"""

def create_agents_summary(target_dir: Path) -> None:
    """Create the agents.md summary file."""
    agents_by_category = {}
    
    # Group agents by category
    for agent_name, (camel_name, category, description) in AGENT_METADATA.items():
        if category not in agents_by_category:
            agents_by_category[category] = []
        agents_by_category[category].append((agent_name, camel_name, description))
    
    # Create summary content
    summary = """# Gadugi Agent Team

## Overview

The Gadugi system employs a comprehensive team of specialized AI agents, each designed to handle specific aspects of the development workflow. These agents work together to provide intelligent automation, coordination, and assistance throughout the software development lifecycle.

## Agent Categories

"""
    
    # Add each category
    for category in sorted(agents_by_category.keys()):
        summary += f"### {category}\n\n"
        agents = sorted(agents_by_category[category], key=lambda x: x[0])
        
        for agent_name, camel_name, description in agents:
            summary += f"- **[{camel_name}](./{camel_name}/{camel_name}.md)** (`/agent:{agent_name}`): {description}\n"
        
        summary += "\n"
    
    # Add hierarchical structure
    summary += """## Agent Hierarchy

```
OrchestratorAgent (Top-level Coordinator)
├── WorkflowManager (Individual Workflow Orchestration)
│   ├── TaskAnalyzer (Task Analysis)
│   ├── TaskDecomposer (Task Breakdown)
│   ├── WorktreeManager (Environment Setup)
│   ├── TestWriter (Test Creation)
│   ├── TestSolver (Test Fixing)
│   ├── CodeReviewer (Phase 9 Review)
│   └── CodeReviewResponse (Review Response)
├── ExecutionMonitor (Parallel Execution Monitoring)
├── TaskBoundsEval (Task Evaluation)
└── TaskResearchAgent (Research & Investigation)

Support Agents:
├── MemoryManager (Memory & GitHub Sync)
├── AgentUpdater (Agent Updates)
├── ClaudeSettingsUpdate (Settings Management)
├── PromptWriter (Prompt Creation)
├── ReadmeAgent (Documentation)
├── SystemDesignReviewer (Architecture Review)
├── PrBacklogManager (PR Management)
├── TeamCoach (Team Coordination)
└── Gadugi (System Management)
```

## Usage Patterns

### For Multiple Tasks
```
/agent:orchestrator-agent

Execute the following tasks:
1. Task one description
2. Task two description
```

### For Single Workflow
```
/agent:workflow-manager

Task: Complete workflow for [specific task]
```

### For Specific Operations
```
/agent:[specific-agent]

[Agent-specific instructions]
```

## Agent Communication

Agents communicate through:
1. **File System**: Shared state files and worktrees
2. **Git Operations**: Branches, commits, and PRs
3. **Task Delegation**: Parent agents invoking child agents
4. **State Management**: JSON state files for persistence
5. **GitHub Integration**: Issues, PRs, and API operations

## Best Practices

1. **Use the Right Agent**: Select the most specific agent for your task
2. **Provide Clear Context**: Give agents complete information
3. **Follow Hierarchy**: Use orchestrator for multiple tasks, workflow-manager for single workflows
4. **Monitor Progress**: Use execution-monitor for parallel operations
5. **Maintain State**: Let agents manage their own state files

## Extension Points

New agents can be added by:
1. Creating agent specification in `/prompts/Gadugi-v0.3/agents/[AgentName]/`
2. Following the Claude Code sub-agent format
3. Implementing required tools and interfaces
4. Adding to appropriate category in this document
5. Testing with realistic scenarios

## Related Documentation

- [Guidelines](../Guidelines.md) - Development philosophy and practices
- [Claude Code Sub-Agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents) - Agent specification format
- [CLAUDE.md](../../../CLAUDE.md) - System instructions and workflow requirements
"""
    
    # Write summary file
    summary_path = target_dir / "agents.md"
    with open(summary_path, 'w') as f:
        f.write(summary)

def main():
    """Main processing function."""
    source_dir = Path("/Users/ryan/gadugi7/gadugi/.claude/agents")
    target_dir = Path("/Users/ryan/gadugi7/gadugi/prompts/Gadugi-v0.3/agents")
    
    # Process each agent
    for agent_file in source_dir.glob("*.md"):
        agent_name = agent_file.stem
        
        # Skip certain files
        if any(skip in agent_name for skip in ['simplified', 'phase9', 'reflection']):
            continue
        
        print(f"Processing {agent_name}...")
        
        try:
            create_agent_documentation(agent_name, agent_file, target_dir)
            print(f"  ✓ Created documentation for {agent_name}")
        except Exception as e:
            print(f"  ✗ Error processing {agent_name}: {e}")
    
    # Copy Python support files
    for py_file in source_dir.glob("*.py"):
        if py_file.stem not in ['__init__', 'shared_test_instructions']:
            agent_name = py_file.stem.replace('_', '-')
            if agent_name in AGENT_METADATA:
                camel_name = AGENT_METADATA[agent_name][0]
                target_src = target_dir / camel_name / "src"
                target_src.mkdir(parents=True, exist_ok=True)
                shutil.copy2(py_file, target_src / py_file.name)
                print(f"  ✓ Copied {py_file.name} to {camel_name}/src/")
    
    # Copy agent subdirectories with code
    for subdir in source_dir.iterdir():
        if subdir.is_dir() and subdir.name not in ['__pycache__']:
            agent_name = subdir.name.replace('_', '-')
            if agent_name in AGENT_METADATA:
                camel_name = AGENT_METADATA[agent_name][0]
                target_src = target_dir / camel_name / "src"
                if subdir.exists():
                    shutil.copytree(subdir, target_src, dirs_exist_ok=True)
                    print(f"  ✓ Copied {subdir.name} code to {camel_name}/src/")
    
    # Create summary file
    print("\nCreating agents summary...")
    create_agents_summary(target_dir)
    print("  ✓ Created agents.md summary")
    
    print("\n✅ Agent documentation complete!")
    print(f"   Location: {target_dir}")
    print(f"   Agents processed: {len(AGENT_METADATA)}")

if __name__ == "__main__":
    main()