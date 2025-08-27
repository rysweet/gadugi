"""
Test suite for Documentation Manager

Tests automated ARCHITECTURE.md updates, section management,
and evolution history tracking.
"""

import pytest
import tempfile
import os

# from pathlib import Path
# from datetime import datetime
from agents.system_design_reviewer.documentation_manager import (
    DocumentationManager,
    DocumentationUpdate,
)
from agents.system_design_reviewer.ast_parser import (
    ArchitecturalChange,
    ArchitecturalElement,
    ElementType,
    ChangeType,
    ImpactLevel,
)


@pytest.fixture
def sample_architecture_doc():
    """Sample ARCHITECTURE.md content for testing"""
    return """# Gadugi System Architecture

## System Overview

Gadugi is a multi-agent development orchestration system.

## Component Architecture

### Core Components

#### Agent System
- **WorkflowManager**: Individual workflow execution
- **OrchestratorAgent**: Parallel task coordination

## Agent Ecosystem

### Agent Hierarchy
- OrchestratorAgent (Top-level)

## Security Architecture

### Container Execution Environment
- **Isolation**: Each agent runs in isolated container

## Performance Architecture

### Parallel Execution
- **3-5x Speedup**: Measured performance improvements

## Evolution History

### Recent Changes
*Architecture evolution entries will be added automatically*

---
*Last updated: 2024-01-01T00:00:00*
"""


@pytest.fixture
def sample_changes():
    """Sample architectural changes for testing"""
    return [
        ArchitecturalChange(
            change_type=ChangeType.ADDED,
            element=ArchitecturalElement(
                element_type=ElementType.CLASS,
                name="SystemDesignReviewer",
                location="agents/system_design_reviewer.py:10",
                patterns=["reviewer", "architecture"],
                docstring="Automated architectural review agent",
            ),
            impact_level=ImpactLevel.HIGH,
            design_implications=["Introduces automated architecture review"],
            requires_adr=True,
        ),
        ArchitecturalChange(
            change_type=ChangeType.MODIFIED,
            element=ArchitecturalElement(
                element_type=ElementType.FUNCTION,
                name="github_integration",
                location="shared/github_operations.py:50",
                is_async=True,
            ),
            impact_level=ImpactLevel.MEDIUM,
            design_implications=["Enhanced GitHub API integration"],
        ),
        ArchitecturalChange(
            change_type=ChangeType.ADDED,
            element=ArchitecturalElement(
                element_type=ElementType.CLASS,
                name="SecurityEnforcer",
                location="security/enforcer.py:5",
                patterns=["security", "xpia"],
            ),
            impact_level=ImpactLevel.HIGH,
            design_implications=["Enhanced security architecture"],
        ),
    ]


@pytest.fixture
def sample_pr_info():
    """Sample PR information for testing"""
    return {
        "number": "123",
        "title": "Add System Design Review Agent",
        "author": {"login": "developer"},
        "body": "This PR adds automated architectural review capabilities",
    }


class TestDocumentationManager:
    """Test the DocumentationManager class"""

    def test_initialization(self):
        """Test documentation manager initialization"""
        manager = DocumentationManager("architecture.md")

        assert manager.architecture_file == "ARCHITECTURE.md"
        assert len(manager.template_sections) > 0
        assert "component_architecture" in manager.template_sections

    def test_initialization_custom_file(self):
        """Test initialization with custom architecture file"""
        manager = DocumentationManager("custom_arch.md")

        assert manager.architecture_file == "custom_arch.md"

    def test_create_architecture_doc(self):
        """Test creating initial ARCHITECTURE.md file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            arch_file = os.path.join(temp_dir, "ARCHITECTURE.md")
            manager = DocumentationManager(arch_file)

            # Should not exist initially
            assert not os.path.exists(arch_file)

            # Create the document
            manager._create_architecture_doc()

            # Should exist now
            assert os.path.exists(arch_file)

            # Check content
            with open(arch_file, "r") as f:
                content = f.read()

            assert "# Gadugi System Architecture" in content
            assert "## System Overview" in content
            assert "## Component Architecture" in content
            assert "## Evolution History" in content

    def test_identify_sections_to_update_component_changes(self, sample_changes):
        """Test identifying sections to update for component changes"""
        manager = DocumentationManager("architecture.md")

        # Filter to only class/module changes
        component_changes = [
            c for c in sample_changes if c.element.element_type == ElementType.CLASS
        ]

        sections = manager._identify_sections_to_update(component_changes)

        assert "component_architecture" in sections
        assert "evolution_history" in sections

    def test_identify_sections_to_update_security_changes(self, sample_changes):
        """Test identifying sections to update for security changes"""
        manager = DocumentationManager("architecture.md")

        # Filter to security-related changes
        security_changes = [
            c for c in sample_changes if "security" in c.element.name.lower()
        ]

        sections = manager._identify_sections_to_update(security_changes)

        assert "security_architecture" in sections
        assert "evolution_history" in sections

    def test_identify_sections_to_update_performance_changes(self, sample_changes):
        """Test identifying sections to update for performance changes"""
        manager = DocumentationManager("architecture.md")

        # Create performance-related change
        perf_change = ArchitecturalChange(
            change_type=ChangeType.MODIFIED,
            element=ArchitecturalElement(
                element_type=ElementType.FUNCTION,
                name="async_processor",
                location="perf/processor.py:10",
                is_async=True,
            ),
            impact_level=ImpactLevel.MEDIUM,
        )

        sections = manager._identify_sections_to_update([perf_change])

        assert "performance_architecture" in sections
        assert "evolution_history" in sections

    def test_replace_section_existing(self, sample_architecture_doc):
        """Test replacing existing section in document"""
        manager = DocumentationManager("architecture.md")

        new_section_content = """## Component Architecture

### Core Components

#### Updated Agent System
- **SystemDesignReviewer**: Automated architectural review
- **WorkflowManager**: Individual workflow execution
- **OrchestratorAgent**: Parallel task coordination

#### Recently Added Components

- **SystemDesignReviewer**: Automated architectural review agent
  - Patterns: reviewer, architecture
"""

        updated_content = manager._replace_section(
            sample_architecture_doc, "component_architecture", new_section_content
        )

        assert "SystemDesignReviewer" in updated_content
        assert "Recently Added Components" in updated_content
        assert "## Component Architecture" in updated_content

    def test_replace_section_new(self, sample_architecture_doc):
        """Test adding new section to document"""
        manager = DocumentationManager("architecture.md")

        new_section_content = """## Integration Points

### External Systems
- **GitHub API**: Issue and PR management
- **Container Registry**: Image management
"""

        updated_content = manager._replace_section(
            sample_architecture_doc, "integration_points", new_section_content
        )

        assert "## Integration Points" in updated_content
        assert "GitHub API" in updated_content

    def test_generate_component_architecture_new_components(self, sample_changes):
        """Test generating component architecture section with new components"""
        manager = DocumentationManager("architecture.md")

        # Filter to added class changes
        new_components = [
            c
            for c in sample_changes
            if c.change_type == ChangeType.ADDED
            and c.element.element_type == ElementType.CLASS
        ]

        section_content = manager._generate_component_architecture(new_components, {})

        assert section_content is not None
        assert "SystemDesignReviewer" in section_content
        assert "Recently Added Components" in section_content
        assert "Automated architectural review agent" in section_content

    def test_generate_security_architecture_updates(self, sample_changes):
        """Test generating security architecture section updates"""
        manager = DocumentationManager("architecture.md")

        # Filter to security changes
        security_changes = [
            c for c in sample_changes if "security" in c.element.name.lower()
        ]

        section_content = manager._generate_security_architecture(security_changes, {})

        assert section_content is not None
        assert "Recent Security Updates" in section_content
        assert "SecurityEnforcer" in section_content

    def test_generate_performance_architecture_updates(self):
        """Test generating performance architecture section updates"""
        manager = DocumentationManager("architecture.md")

        # Create async performance change
        perf_changes = [
            ArchitecturalChange(
                change_type=ChangeType.MODIFIED,
                element=ArchitecturalElement(
                    element_type=ElementType.FUNCTION,
                    name="async_handler",
                    location="handlers/async.py:20",
                    is_async=True,
                ),
                impact_level=ImpactLevel.MEDIUM,
            )
        ]

        section_content = manager._generate_performance_architecture(perf_changes, {})

        assert section_content is not None
        assert "Recent Performance Updates" in section_content
        assert "async_handler" in section_content
        assert "Async implementation" in section_content

    def test_create_evolution_entry_high_impact(self, sample_changes, sample_pr_info):
        """Test creating evolution entry for high impact changes"""
        manager = DocumentationManager("architecture.md")

        # Filter to high impact changes
        high_impact_changes = [
            c for c in sample_changes if c.impact_level == ImpactLevel.HIGH
        ]

        entry = manager._create_evolution_entry(high_impact_changes, sample_pr_info)

        assert entry is not None
        assert "PR #123" in entry
        assert "Add System Design Review Agent" in entry
        assert "**High Impact Changes**:" in entry
        assert "SystemDesignReviewer" in entry
        assert "**Architectural Implications**:" in entry

    def test_create_evolution_entry_low_impact_only(self, sample_pr_info):
        """Test evolution entry with only low impact changes (should return None)"""
        manager = DocumentationManager("architecture.md")

        low_impact_changes = [
            ArchitecturalChange(
                change_type=ChangeType.MODIFIED,
                element=ArchitecturalElement(
                    element_type=ElementType.FUNCTION,
                    name="helper_func",
                    location="utils.py:10",
                ),
                impact_level=ImpactLevel.LOW,
            )
        ]

        entry = manager._create_evolution_entry(low_impact_changes, sample_pr_info)

        assert entry is None

    def test_add_evolution_entry_existing_section(self, sample_architecture_doc):
        """Test adding evolution entry to existing section"""
        manager = DocumentationManager("architecture.md")

        entry = """
### 2024-01-15 - PR #123: Add System Design Review Agent
**Author**: developer

**High Impact Changes**:
- Added class 'SystemDesignReviewer'

**Architectural Implications**:
- Introduces automated architecture review
"""

        updated_content = manager._add_evolution_entry(sample_architecture_doc, entry)

        assert "### 2024-01-15 - PR #123" in updated_content
        assert "Add System Design Review Agent" in updated_content
        assert "High Impact Changes" in updated_content

    def test_add_evolution_entry_no_existing_section(self):
        """Test adding evolution entry when no evolution section exists"""
        manager = DocumentationManager("architecture.md")

        simple_doc = """# Simple Architecture

## Overview
Basic overview."""

        entry = """
### 2024-01-15 - PR #123: New Feature
**Author**: developer

**High Impact Changes**:
- Added new feature
"""

        updated_content = manager._add_evolution_entry(simple_doc, entry)

        assert "## Evolution History" in updated_content
        assert "### 2024-01-15 - PR #123" in updated_content

    def test_update_architecture_doc_full_workflow(
        self, sample_changes, sample_pr_info
    ):
        """Test complete architecture document update workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            arch_file = os.path.join(temp_dir, "ARCHITECTURE.md")
            manager = DocumentationManager(arch_file)

            # Should create new file and update it
            updates = manager.update_architecture_doc(sample_changes, sample_pr_info)

            assert len(updates) > 0
            assert any("Created" in update for update in updates)
            assert any("Updated" in update for update in updates)
            assert os.path.exists(arch_file)

            # Check file content
            with open(arch_file, "r") as f:
                content = f.read()

            assert "SystemDesignReviewer" in content
            assert "PR #123" in content

    def test_update_architecture_doc_existing_file(
        self, sample_architecture_doc, sample_changes, sample_pr_info
    ):
        """Test updating existing architecture document"""
        with tempfile.TemporaryDirectory() as temp_dir:
            arch_file = os.path.join(temp_dir, "ARCHITECTURE.md")

            # Write existing content
            with open(arch_file, "w") as f:
                f.write(sample_architecture_doc)

            manager = DocumentationManager(arch_file)
            updates = manager.update_architecture_doc(sample_changes, sample_pr_info)

            assert len(updates) > 0
            assert not any(
                "Created" in update for update in updates
            )  # Should not create new
            assert any("Updated" in update for update in updates)

            # Check updated content
            with open(arch_file, "r") as f:
                updated_content = f.read()

            assert updated_content != sample_architecture_doc  # Should be different
            assert "SystemDesignReviewer" in updated_content

    def test_update_architecture_doc_no_relevant_changes(self, sample_pr_info):
        """Test update with no architecturally relevant changes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            arch_file = os.path.join(temp_dir, "ARCHITECTURE.md")
            manager = DocumentationManager(arch_file)

            # Create low-impact changes only
            low_impact_changes = [
                ArchitecturalChange(
                    change_type=ChangeType.MODIFIED,
                    element=ArchitecturalElement(
                        element_type=ElementType.FUNCTION,
                        name="helper_function",
                        location="utils.py:10",
                    ),
                    impact_level=ImpactLevel.LOW,
                )
            ]

            updates = manager.update_architecture_doc(
                low_impact_changes, sample_pr_info
            )

            # Should still create file but minimal updates
            assert len(updates) >= 1  # At least file creation
            assert os.path.exists(arch_file)

    def test_error_handling_file_permissions(self, sample_changes, sample_pr_info):
        """Test error handling when file cannot be written"""
        # Try to write to invalid path
        manager = DocumentationManager("/invalid/path/ARCHITECTURE.md")

        updates = manager.update_architecture_doc(sample_changes, sample_pr_info)

        # Should handle error gracefully
        assert len(updates) >= 1
        assert any("Error" in update for update in updates)


class TestDocumentationUpdate:
    """Test the DocumentationUpdate data structure"""

    def test_documentation_update_creation(self):
        """Test creating documentation update object"""
        update = DocumentationUpdate(
            file_path="ARCHITECTURE.md",
            section="component_architecture",
            update_type="modify",
            content="Updated content",
            line_number=42,
        )

        assert update.file_path == "ARCHITECTURE.md"
        assert update.section == "component_architecture"
        assert update.update_type == "modify"
        assert update.content == "Updated content"
        assert update.line_number == 42


if __name__ == "__main__":
    pytest.main([__file__])
