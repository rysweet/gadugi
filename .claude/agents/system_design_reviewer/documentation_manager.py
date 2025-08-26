"""
Documentation Manager - Automated architecture documentation maintenance

Handles updating ARCHITECTURE.md and other system design documentation
based on detected architectural changes.
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .ast_parser import ArchitecturalChange, ElementType, ImpactLevel


@dataclass
class DocumentationUpdate:
    """Represents a documentation update"""
    file_path: str
    section: str
    update_type: str  # add, modify, remove
    content: str
    line_number: Optional[int] = None


class DocumentationManager:
    """Manages automated updates to architecture documentation"""

    def __init__(self, architecture_file: str) -> None:
        self.architecture_file = architecture_file
        self.template_sections = {
            "system_overview": self._generate_system_overview,
            "component_architecture": self._generate_component_architecture,
            "agent_ecosystem": self._generate_agent_ecosystem,
            "data_flow": self._generate_data_flow,
            "security_architecture": self._generate_security_architecture,
            "performance_architecture": self._generate_performance_architecture,
            "integration_points": self._generate_integration_points,
            "evolution_history": self._generate_evolution_history
        }

    def update_architecture_doc(self, changes: List[ArchitecturalChange],
                              pr_info: Dict[str, Any]) -> List[str]:
        """Update ARCHITECTURE.md based on detected changes"""
        updates_made = []

        try:
            # Ensure architecture document exists
            if not os.path.exists(self.architecture_file):
                self._create_architecture_doc()
                updates_made.append(f"Created {self.architecture_file}")

            # Read current document
            with open(self.architecture_file, 'r', encoding='utf-8') as f:
                current_content = f.read()

            # Analyze what sections need updates
            sections_to_update = self._identify_sections_to_update(changes)

            # Update each section
            updated_content = current_content
            for section in sections_to_update:
                new_section_content = self._update_section(section, changes, pr_info)
                if new_section_content:
                    updated_content = self._replace_section(
                        updated_content, section, new_section_content
                    )
                    updates_made.append(f"Updated {section} section")

            # Add evolution history entry
            evolution_entry = self._create_evolution_entry(changes, pr_info)
            if evolution_entry:
                updated_content = self._add_evolution_entry(updated_content, evolution_entry)
                updates_made.append("Added evolution history entry")

            # Write updated document if changes were made
            if updated_content != current_content:
                with open(self.architecture_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                updates_made.append(f"Saved updated {self.architecture_file}")

            return updates_made

        except Exception as e:
            print(f"Error updating architecture documentation: {e}")
            return [f"Error updating documentation: {str(e)}"]

    def _create_architecture_doc(self):
        """Create initial ARCHITECTURE.md file"""
        template = """# Gadugi System Architecture

## System Overview

Gadugi is a multi-agent development orchestration system that enables parallel execution
of development workflows with comprehensive security, performance analytics, and
architectural coherence.

### Key Characteristics
- **Enhanced Separation Architecture**: Shared modules for common operations
- **Agent Ecosystem**: Coordinated specialized agents
- **Container Execution**: Secure, isolated execution contexts
- **Parallel Orchestration**: 3-5x performance improvements
- **GitHub Integration**: Automated issue/PR management

## Component Architecture

### Core Components

#### Agent System
- **WorkflowManager**: Individual workflow execution
- **OrchestratorAgent**: Parallel task coordination
- **TeamCoach**: Performance analytics and optimization
- **SystemDesignReviewer**: Architectural review and documentation

#### Shared Infrastructure
- **Enhanced Separation**: Common utilities and patterns
- **Container Runtime**: Secure execution environment
- **State Management**: Persistent workflow state
- **GitHub Operations**: API integration layer

## Agent Ecosystem

### Agent Hierarchy
```
OrchestratorAgent (Top-level coordinator)
├── WorkflowManager (Individual workflows)
├── TaskDecomposer (Dependency analysis)
├── ExecutionMonitor (Progress tracking)
└── WorktreeManager (Isolation management)

Specialized Agents
├── SystemDesignReviewer (Architecture review)
├── CodeReviewer (Code quality review)
├── TeamCoach (Performance analytics)
└── PromptWriter (Structured prompts)
```

## Data Flow Architecture

### Workflow Data Flow
1. **Input Processing**: Prompt files and user requests
2. **Task Decomposition**: Dependency analysis and planning
3. **Parallel Execution**: Coordinated agent invocation
4. **State Management**: Progress tracking and checkpointing
5. **Integration**: GitHub operations and CI/CD

## Security Architecture

### Container Execution Environment
- **Isolation**: Each agent runs in isolated container
- **Resource Limits**: CPU, memory, and network constraints
- **Audit Logging**: Comprehensive operation tracking
- **XPIA Defense**: Cross-agent protection mechanisms

## Performance Architecture

### Parallel Execution
- **3-5x Speedup**: Measured performance improvements
- **Resource Optimization**: Efficient CPU and memory usage
- **Load Balancing**: Dynamic task distribution
- **Caching**: Shared module result caching

## Integration Points

### External Systems
- **GitHub API**: Issue and PR management
- **Git Operations**: Repository management
- **CI/CD Pipelines**: Automated testing and deployment
- **Container Registry**: Image management

## Evolution History

### Recent Changes
*Architecture evolution entries will be added automatically*

---

*This document is automatically maintained by the SystemDesignReviewer agent.*
*Last updated: {timestamp}*
""".format(timestamp=datetime.now().isoformat())

        with open(self.architecture_file, 'w', encoding='utf-8') as f:
            f.write(template)

    def _identify_sections_to_update(self, changes: List[ArchitecturalChange]) -> List[str]:
        """Identify which sections need updates based on changes"""
        sections_to_update = []

        for change in changes:
            element = change.element

            # Component architecture updates for new classes/modules
            if element.element_type in [ElementType.CLASS, ElementType.MODULE]:
                if "component_architecture" not in sections_to_update:
                    sections_to_update.append("component_architecture")

            # Agent ecosystem updates for agent-related changes
            if "agent" in element.name.lower() or "agent" in str(element.location).lower():
                if "agent_ecosystem" not in sections_to_update:
                    sections_to_update.append("agent_ecosystem")

            # Security updates for security-related patterns
            security_patterns = ["auth", "security", "xpia", "defense", "audit"]
            if any(pattern in element.name.lower() for pattern in security_patterns):
                if "security_architecture" not in sections_to_update:
                    sections_to_update.append("security_architecture")

            # Performance updates for performance-critical changes
            if element.is_async or "performance" in element.name.lower():
                if "performance_architecture" not in sections_to_update:
                    sections_to_update.append("performance_architecture")

            # Integration updates for external interface changes
            integration_patterns = ["github", "api", "webhook", "cli"]
            if any(pattern in element.name.lower() for pattern in integration_patterns):
                if "integration_points" not in sections_to_update:
                    sections_to_update.append("integration_points")

        # Always update evolution history
        if "evolution_history" not in sections_to_update:
            sections_to_update.append("evolution_history")

        return sections_to_update

    def _update_section(self, section: str, changes: List[ArchitecturalChange],
                       pr_info: Dict[str, Any]) -> Optional[str]:
        """Update a specific section based on changes"""
        if section in self.template_sections:
            return self.template_sections[section](changes, pr_info)
        return None

    def _replace_section(self, content: str, section: str, new_content: str) -> str:
        """Replace a section in the document"""
        # Find section header
        section_titles = {
            "system_overview": "System Overview",
            "component_architecture": "Component Architecture",
            "agent_ecosystem": "Agent Ecosystem",
            "data_flow": "Data Flow Architecture",
            "security_architecture": "Security Architecture",
            "performance_architecture": "Performance Architecture",
            "integration_points": "Integration Points",
            "evolution_history": "Evolution History"
        }

        section_title = section_titles.get(section, section.replace("_", " ").title())

        # Pattern to match section (## Title until next ## or end)
        pattern = rf"(##\s+{re.escape(section_title)}.*?)(?=##|\Z)"

        if re.search(pattern, content, re.DOTALL):
            return re.sub(pattern, new_content, content, flags=re.DOTALL)
        else:
            # Section doesn't exist, append before evolution history
            evolution_pattern = r"(##\s+Evolution History)"
            if re.search(evolution_pattern, content):
                return re.sub(
                    evolution_pattern,
                    f"{new_content}\n\n\\1",
                    content
                )
            else:
                # Append at end
                return content + "\n\n" + new_content

    def _generate_system_overview(self, changes: List[ArchitecturalChange],
                                pr_info: Dict[str, Any]) -> str:
        """Generate updated system overview section"""
        # For now, return None to keep existing content
        # Could be enhanced to detect major architectural shifts
        return None

    def _generate_component_architecture(self, changes: List[ArchitecturalChange],
                                       pr_info: Dict[str, Any]) -> str:
        """Generate updated component architecture section"""
        new_components = []
        modified_components = []

        for change in changes:
            if change.element.element_type in [ElementType.CLASS, ElementType.MODULE]:
                if change.change_type.value == "added":
                    new_components.append(change.element)
                elif change.change_type.value == "modified":
                    modified_components.append(change.element)

        if not new_components and not modified_components:
            return None

        section = "## Component Architecture\n\n### Core Components\n\n"

        if new_components:
            section += "#### Recently Added Components\n\n"
            for component in new_components:
                section += f"- **{component.name}**: {component.docstring or 'New component'}\n"
                if component is not None and component.patterns:
                    section += f"  - Patterns: {', '.join(component.patterns)}\n"
            section += "\n"

        if modified_components:
            section += "#### Recently Modified Components\n\n"
            for component in modified_components:
                section += f"- **{component.name}**: Updated functionality\n"
            section += "\n"

        # Keep existing content structure
        section += """
#### Agent System
- **WorkflowManager**: Individual workflow execution
- **OrchestratorAgent**: Parallel task coordination
- **TeamCoach**: Performance analytics and optimization
- **SystemDesignReviewer**: Architectural review and documentation

#### Shared Infrastructure
- **Enhanced Separation**: Common utilities and patterns
- **Container Runtime**: Secure execution environment
- **State Management**: Persistent workflow state
- **GitHub Operations**: API integration layer
"""

        return section

    def _generate_agent_ecosystem(self, changes: List[ArchitecturalChange],
                                pr_info: Dict[str, Any]) -> str:
        """Generate updated agent ecosystem section"""
        # For now, return None to keep existing content
        return None

    def _generate_data_flow(self, changes: List[ArchitecturalChange],
                          pr_info: Dict[str, Any]) -> str:
        """Generate updated data flow section"""
        return None

    def _generate_security_architecture(self, changes: List[ArchitecturalChange],
                                      pr_info: Dict[str, Any]) -> str:
        """Generate updated security architecture section"""
        security_changes = [
            change for change in changes
            if any(pattern in change.element.name.lower()
                  for pattern in ["security", "auth", "xpia", "defense"])
        ]

        if not security_changes:
            return None

        section = """## Security Architecture

### Container Execution Environment
- **Isolation**: Each agent runs in isolated container
- **Resource Limits**: CPU, memory, and network constraints
- **Audit Logging**: Comprehensive operation tracking
- **XPIA Defense**: Cross-agent protection mechanisms

### Recent Security Updates
"""

        for change in security_changes:
            section += f"- **{change.get_description()}**: {change.element.location}\n"
            if change is not None and change.design_implications:
                for implication in change.design_implications:
                    section += f"  - {implication}\n"

        return section

    def _generate_performance_architecture(self, changes: List[ArchitecturalChange],
                                         pr_info: Dict[str, Any]) -> str:
        """Generate updated performance architecture section"""
        perf_changes = [
            change for change in changes
            if (change.element.is_async or
                "performance" in change.element.name.lower() or
                "parallel" in change.element.name.lower())
        ]

        if not perf_changes:
            return None

        section = """## Performance Architecture

### Parallel Execution
- **3-5x Speedup**: Measured performance improvements
- **Resource Optimization**: Efficient CPU and memory usage
- **Load Balancing**: Dynamic task distribution
- **Caching**: Shared module result caching

### Recent Performance Updates
"""

        for change in perf_changes:
            section += f"- **{change.get_description()}**: {change.element.location}\n"
            if change.element.is_async:
                section += "  - Async implementation for improved concurrency\n"

        return section

    def _generate_integration_points(self, changes: List[ArchitecturalChange],
                                   pr_info: Dict[str, Any]) -> str:
        """Generate updated integration points section"""
        return None

    def _generate_evolution_history(self, changes: List[ArchitecturalChange],
                                  pr_info: Dict[str, Any]) -> str:
        """Generate updated evolution history section"""
        return None  # Handled by _add_evolution_entry

    def _create_evolution_entry(self, changes: List[ArchitecturalChange],
                              pr_info: Dict[str, Any]) -> Optional[str]:
        """Create an evolution history entry"""
        if not changes:
            return None

        pr_number = pr_info.get('number', 'Unknown')
        pr_title = pr_info.get('title', 'Untitled Change')
        pr_author = pr_info.get('author', {}).get('login', 'Unknown')

        # Categorize changes
        high_impact_changes = [c for c in changes if c.impact_level == ImpactLevel.HIGH]
        critical_changes = [c for c in changes if c.impact_level == ImpactLevel.CRITICAL]

        if not high_impact_changes and not critical_changes:
            return None

        entry = f"""
### {datetime.now().strftime('%Y-%m-%d')} - PR #{pr_number}: {pr_title}
**Author**: {pr_author}
"""

        if critical_changes:
            entry += "\n**Critical Changes**:\n"
            for change in critical_changes:
                entry += f"- {change.get_description()}\n"

        if high_impact_changes:
            entry += "\n**High Impact Changes**:\n"
            for change in high_impact_changes:
                entry += f"- {change.get_description()}\n"

        # Add architectural implications
        all_implications = set()
        for change in high_impact_changes + critical_changes:
            all_implications.update(change.design_implications)

        if all_implications:
            entry += "\n**Architectural Implications**:\n"
            for implication in sorted(all_implications):
                entry += f"- {implication}\n"

        return entry

    def _add_evolution_entry(self, content: str, entry: str) -> str:
        """Add an entry to the evolution history section"""
        # Find evolution history section
        pattern = r"(##\s+Evolution History.*?)(\n### Recent Changes.*?)(?=\n###|\n##|\Z)"

        if re.search(pattern, content, re.DOTALL):
            # Replace "Recent Changes" with the new entry
            return re.sub(
                pattern,
                f"\\1\\n### Recent Changes{entry}",
                content,
                flags=re.DOTALL
            )
        else:
            # Just append to evolution history section
            evolution_pattern = r"(##\s+Evolution History.*?)(?=\n##|\Z)"
            if re.search(evolution_pattern, content, re.DOTALL):
                return re.sub(
                    evolution_pattern,
                    f"\\1{entry}",
                    content,
                    flags=re.DOTALL
                )
            else:
                # Append at end
                return content + f"\n\n## Evolution History{entry}"
