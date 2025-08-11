"""YAML frontmatter parser for agent definitions."""

import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from .base_agent import AgentMetadata


def parse_agent_definition(filepath: Path) -> AgentMetadata:
    """Parse agent definition from markdown file with YAML frontmatter.

    Args:
        filepath: Path to agent definition file

    Returns:
        Parsed agent metadata

    Raises:
        ValueError: If file format is invalid
    """
    if not filepath.exists():
        raise ValueError(f"Agent definition file not found: {filepath}")

    content = filepath.read_text()
    frontmatter, body = extract_frontmatter(content)

    if not frontmatter:
        raise ValueError(f"No frontmatter found in {filepath}")

    # Parse YAML frontmatter
    try:
        metadata_dict = yaml.safe_load(frontmatter)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter in {filepath}: {e}")

    # Validate required fields
    if "name" not in metadata_dict:
        raise ValueError(f"Agent definition missing required field 'name' in {filepath}")

    # Create metadata object
    metadata = AgentMetadata.from_dict(metadata_dict)

    # Store the body content for reference
    metadata.settings["definition_body"] = body

    return metadata


def extract_frontmatter(content: str) -> Tuple[Optional[str], str]:
    """Extract YAML frontmatter and body from markdown content.

    Args:
        content: Markdown content with optional frontmatter

    Returns:
        Tuple of (frontmatter, body)
    """
    # Pattern to match YAML frontmatter between --- markers
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if match:
        frontmatter = match.group(1)
        body = match.group(2)
        return frontmatter, body

    # No frontmatter found
    return None, content


def validate_agent_specification(metadata: AgentMetadata) -> bool:
    """Validate agent specification for completeness.

    Args:
        metadata: Agent metadata to validate

    Returns:
        True if valid, raises ValueError otherwise
    """
    # Check required fields
    if not metadata.name:
        raise ValueError("Agent name is required")

    if not metadata.version:
        raise ValueError("Agent version is required")

    # Validate version format (semantic versioning)
    version_pattern = r'^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$'
    if not re.match(version_pattern, metadata.version):
        raise ValueError(f"Invalid version format: {metadata.version}")

    # Validate tools
    for tool in metadata.tools:
        if "name" not in tool:
            raise ValueError("Tool definition missing 'name' field")

    # Validate events
    if metadata.events:
        if not isinstance(metadata.events, dict):
            raise ValueError("Events must be a dictionary")

        for key in ["subscribes", "publishes"]:
            if key in metadata.events:
                if not isinstance(metadata.events[key], list):
                    raise ValueError(f"Event {key} must be a list")

    # Validate settings
    if metadata.settings:
        if not isinstance(metadata.settings, dict):
            raise ValueError("Settings must be a dictionary")

    return True


def generate_agent_template(
    name: str,
    version: str = "1.0.0",
    description: str = "",
) -> str:
    """Generate a template agent definition file.

    Args:
        name: Agent name
        version: Agent version
        description: Agent description

    Returns:
        Template content as string
    """
    template = f"""---
name: {name}
version: {version}
description: {description}
tools:
  - name: file_reader
    required: true
  - name: code_analyzer
    required: false
events:
  subscribes:
    - task.assigned
    - code.changed
  publishes:
    - task.completed
    - error.occurred
settings:
  max_retries: 3
  timeout: 30
  log_level: INFO
---

# {name}

## Purpose
{description}

## Workflow

1. **Initialization**
   - Load configuration
   - Connect to services
   - Register with orchestrator

2. **Event Processing**
   - Listen for subscribed events
   - Process tasks based on event type
   - Invoke necessary tools

3. **Task Execution**
   - Analyze input data
   - Perform required operations
   - Generate results

4. **Response**
   - Format output
   - Publish completion events
   - Update state

## Tools

### file_reader
Reads and parses files from the filesystem.

### code_analyzer
Analyzes code structure and patterns.

## Events

### Subscribes to:
- `task.assigned`: New task assignment
- `code.changed`: Code modification notification

### Publishes:
- `task.completed`: Task completion notification
- `error.occurred`: Error notification

## Configuration

```yaml
settings:
  max_retries: 3
  timeout: 30
  log_level: INFO
```

## Error Handling

1. Retry failed operations up to max_retries
2. Log errors with context
3. Publish error events
4. Graceful degradation when possible

## Best Practices

- Always validate input data
- Use structured logging
- Handle errors gracefully
- Maintain state consistency
- Clean up resources properly
"""
    return template


def update_agent_metadata(
    filepath: Path,
    updates: Dict[str, Any],
) -> None:
    """Update agent metadata in definition file.

    Args:
        filepath: Path to agent definition file
        updates: Dictionary of fields to update
    """
    content = filepath.read_text()
    frontmatter, body = extract_frontmatter(content)

    if not frontmatter:
        raise ValueError(f"No frontmatter found in {filepath}")

    # Parse existing metadata
    metadata_dict = yaml.safe_load(frontmatter)

    # Apply updates
    metadata_dict.update(updates)

    # Generate new frontmatter
    new_frontmatter = yaml.safe_dump(metadata_dict, default_flow_style=False)

    # Reconstruct file content
    new_content = f"---\n{new_frontmatter}---\n{body}"

    # Write back to file
    filepath.write_text(new_content)
