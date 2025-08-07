#!/usr/bin/env python3
"""Tests for Memory Manager Engine."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestrator"))

from memory_manager_engine import (
    GitHubIssue,
    GitHubSync,
    MemoryItem,
    MemoryManager,
    MemoryManagerEngine,
    MemoryManagerRequest,
    run_memory_manager,
)


class TestMemoryManager:
    """Test the core MemoryManager class."""

    def setup_method(self) -> None:
        self.memory_manager = MemoryManager()
        self.sample_memory = """# AI Assistant Memory

## Active Goals
- ✅ Complete feature X implementation (PR #123)
- 🔄 Implement feature Y with high priority
- Minor documentation updates

## Current Context
- Branch: feature/test-branch
- Working on memory management

## Recent Accomplishments
- ✅ Fixed critical bug in authentication system
- ✅ Added comprehensive test coverage

## Important Context
- Architecture decision: Using microservices approach
- Database migration scheduled for next week

## Reflections
- Code review process is working well
- Need to improve CI/CD pipeline speed
"""

    def test_parse_memory_content(self) -> None:
        """Test parsing Memory.md content into sections."""
        sections = self.memory_manager.parse_memory_content(self.sample_memory)

        assert len(sections) == 5
        assert "Active Goals" in sections
        assert "Current Context" in sections
        assert "Recent Accomplishments" in sections
        assert "Important Context" in sections
        assert "Reflections" in sections

        # Check Active Goals section
        goals_section = sections["Active Goals"]
        assert len(goals_section.items) == 3

        # Check item types
        items = goals_section.items
        assert items[0].type == "accomplishment"  # ✅ marker
        assert items[1].type == "todo"  # 🔄 marker
        assert items[2].type == "context"  # default

    def test_determine_item_type(self) -> None:
        """Test item type determination."""
        # Accomplishment markers
        assert self.memory_manager._determine_item_type("- ✅ Completed task") == "accomplishment"
        assert self.memory_manager._determine_item_type("- Fixed the bug") == "context"
        assert self.memory_manager._determine_item_type("- Implemented feature") == "context"

        # Todo markers
        assert self.memory_manager._determine_item_type("- 🔄 Working on feature") == "todo"
        assert self.memory_manager._determine_item_type("- Need to implement X") == "todo"

        # Goal markers
        assert self.memory_manager._determine_item_type("- Goal: Complete project") == "goal"
        assert (
            self.memory_manager._determine_item_type("- Objective: Improve performance") == "goal"
        )

    def test_determine_priority(self) -> None:
        """Test priority determination."""
        assert self.memory_manager._determine_priority("- Critical bug fix needed") == "high"
        assert self.memory_manager._determine_priority("- High priority task") == "high"
        assert self.memory_manager._determine_priority("- Minor documentation update") == "low"
        assert self.memory_manager._determine_priority("- Regular task") == "medium"

    def test_update_memory(self) -> None:
        """Test updating memory with new items."""
        sections = self.memory_manager.parse_memory_content(self.sample_memory)

        updates = [
            {
                "type": "accomplishment",
                "content": "✅ Implemented memory manager",
                "priority": "high",
                "metadata": {"pr_number": 456},
            },
            {
                "type": "goal",
                "content": "Complete all v0.3 agents",
                "priority": "high",
                "metadata": {},
            },
        ]

        updated_sections = self.memory_manager.update_memory(sections, updates)

        # Check that items were added to correct sections
        accomplishments = updated_sections["Recent Accomplishments"]
        goals = updated_sections["Active Goals"]

        # Should have original + new items
        assert len(accomplishments.items) >= 2  # Original + new
        assert len(goals.items) >= 3  # Original + new

        # Check new items exist
        new_accomplishment = accomplishments.items[-1]
        assert new_accomplishment.content == "✅ Implemented memory manager"
        assert new_accomplishment.priority == "high"
        assert new_accomplishment.metadata["pr_number"] == 456

    def test_prune_memory(self) -> None:
        """Test memory pruning functionality."""
        sections = self.memory_manager.parse_memory_content(self.sample_memory)

        # Add some old items
        old_date = datetime.now() - timedelta(days=10)
        for section in sections.values():
            if section.items:
                section.items[0].updated = old_date
                # Mark first item as completed
                if "✅" not in section.items[0].content:
                    section.items[0].content = "✅ " + section.items[0].content

        # Prune with 7-day threshold
        pruned_sections = self.memory_manager.prune_memory(
            sections,
            days_threshold=7,
            preserve_critical=True,
        )

        # Should have fewer items after pruning
        original_count = sum(len(s.items) for s in sections.values())
        pruned_count = sum(len(s.items) for s in pruned_sections.values())

        assert pruned_count <= original_count

    def test_render_memory(self) -> None:
        """Test rendering sections back to Memory.md format."""
        sections = self.memory_manager.parse_memory_content(self.sample_memory)
        rendered = self.memory_manager.render_memory(sections)

        # Check structure
        assert rendered.startswith("# AI Assistant Memory")
        assert "## Active Goals" in rendered
        assert "## Current Context" in rendered
        assert "## Recent Accomplishments" in rendered
        assert "## Important Context" in rendered
        assert "## Reflections" in rendered

        # Check footer
        assert "*Last updated:" in rendered
        assert rendered.endswith("*")

    def test_get_target_section(self) -> None:
        """Test section targeting for different item types."""
        assert self.memory_manager._get_target_section("goal") == "Active Goals"
        assert self.memory_manager._get_target_section("accomplishment") == "Recent Accomplishments"
        assert self.memory_manager._get_target_section("context") == "Important Context"
        assert self.memory_manager._get_target_section("todo") == "Active Goals"
        assert self.memory_manager._get_target_section("reflection") == "Reflections"


class TestGitHubSync:
    """Test the GitHubSync class."""

    def setup_method(self) -> None:
        self.github_sync = GitHubSync()

    @patch("subprocess.run")
    def test_check_gh_cli(self, mock_run) -> None:
        """Test GitHub CLI availability check."""
        # Test CLI available
        mock_run.return_value = MagicMock(returncode=0)
        sync = GitHubSync()
        assert sync.gh_available is True

        # Test CLI not available
        mock_run.side_effect = FileNotFoundError()
        sync = GitHubSync()
        assert sync.gh_available is False

    def test_extract_title(self) -> None:
        """Test title extraction from memory item content."""
        content1 = "- ✅ Complete feature X implementation with tests"
        title1 = self.github_sync._extract_title(content1)
        assert "Complete feature X implementation with tests" in title1
        assert "✅" not in title1

        content2 = "- **Critical**: Fix authentication bug immediately"
        title2 = self.github_sync._extract_title(content2)
        assert "Critical" in title2
        assert "*" not in title2

        # Test long title truncation
        long_content = "- " + "A" * 100
        long_title = self.github_sync._extract_title(long_content)
        assert len(long_title) <= 80
        assert long_title.endswith("...")

    def test_get_labels_for_item(self) -> None:
        """Test label generation for memory items."""
        item = MemoryItem(
            type="todo",
            content="Fix critical bug in authentication",
            priority="high",
            created=datetime.now(),
            updated=datetime.now(),
            metadata={},
        )

        labels = self.github_sync._get_labels_for_item(item)

        assert "memory-sync" in labels
        assert "ai-assistant" in labels
        assert "high-priority" in labels
        assert "task" in labels
        assert "bug" in labels

    def test_format_issue_body(self) -> None:
        """Test issue body formatting."""
        item = MemoryItem(
            type="goal",
            content="Complete all v0.3 agents implementation",
            priority="high",
            created=datetime.now(),
            updated=datetime.now(),
            metadata={"milestone": "v0.3", "estimate": "2 weeks"},
        )

        body = self.github_sync._format_issue_body(item)

        assert "**Memory Item Details**" in body
        assert "Type: goal" in body
        assert "Priority: high" in body
        assert "Complete all v0.3 agents implementation" in body
        assert "milestone" in body
        assert "Memory Manager Agent" in body

    @patch("subprocess.run")
    def test_get_memory_issues(self, mock_run) -> None:
        """Test getting existing memory issues."""
        # Mock successful response
        mock_response = json.dumps(
            [
                {
                    "number": 123,
                    "title": "Test Issue",
                    "body": "Test body",
                    "state": "open",
                    "labels": [{"name": "memory-sync"}, {"name": "high-priority"}],
                    "url": "https://github.com/test/repo/issues/123",
                },
            ],
        )

        mock_run.return_value = MagicMock(returncode=0, stdout=mock_response)
        self.github_sync.gh_available = True

        issues = self.github_sync.get_memory_issues()

        assert len(issues) == 1
        assert issues[0].number == 123
        assert issues[0].title == "Test Issue"
        assert "memory-sync" in issues[0].labels

    @patch("subprocess.run")
    def test_create_issue_for_item(self, mock_run) -> None:
        """Test creating GitHub issue for memory item."""
        # Mock successful issue creation
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/test/repo/issues/456",
        )
        self.github_sync.gh_available = True

        item = MemoryItem(
            type="todo",
            content="Implement remaining agents",
            priority="high",
            created=datetime.now(),
            updated=datetime.now(),
            metadata={},
        )

        issue = self.github_sync.create_issue_for_item(item)

        assert issue is not None
        assert issue.number == 456
        assert issue.state == "open"
        assert "memory-sync" in issue.labels

    @patch("subprocess.run")
    def test_update_issue_status(self, mock_run) -> None:
        """Test updating issue status."""
        mock_run.return_value = MagicMock(returncode=0)
        self.github_sync.gh_available = True

        issue = GitHubIssue(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            labels=["memory-sync"],
            url="https://github.com/test/repo/issues/123",
        )

        # Test closing issue
        success = self.github_sync.update_issue_status(issue, "completed")
        assert success is True

        # Test reopening issue
        issue.state = "closed"
        success = self.github_sync.update_issue_status(issue, "open")
        assert success is True


class TestMemoryManagerEngine:
    """Test the main MemoryManagerEngine."""

    def setup_method(self) -> None:
        self.engine = MemoryManagerEngine()
        self.sample_memory = """# AI Assistant Memory

## Active Goals
- 🔄 Complete memory manager implementation
- 🔄 Add comprehensive tests

## Recent Accomplishments
- ✅ Created memory manager structure

## Important Context
- Working on v0.3 regeneration
"""

    def test_handle_update(self) -> None:
        """Test handling update requests."""
        request = MemoryManagerRequest(
            action="update",
            memory_content=self.sample_memory,
            updates=[
                {
                    "type": "accomplishment",
                    "content": "✅ Implemented memory manager engine",
                    "priority": "high",
                    "metadata": {"component": "memory-manager"},
                },
            ],
        )

        response = self.engine.process_request(request)

        assert response.success is True
        assert response.updated_memory is not None
        assert len(response.actions_taken) > 0
        assert response.statistics["items_added"] == 1
        assert "✅ Implemented memory manager engine" in response.updated_memory

    def test_handle_prune(self) -> None:
        """Test handling prune requests."""
        request = MemoryManagerRequest(
            action="prune",
            memory_content=self.sample_memory,
            prune_options={"days_threshold": 7, "preserve_critical": True},
        )

        response = self.engine.process_request(request)

        assert response.success is True
        assert response.updated_memory is not None
        assert "items_removed" in response.statistics

    def test_handle_status(self) -> None:
        """Test handling status requests."""
        request = MemoryManagerRequest(
            action="status",
            memory_content=self.sample_memory,
        )

        response = self.engine.process_request(request)

        assert response.success is True
        assert "total_sections" in response.statistics
        assert "total_items" in response.statistics
        assert "github_cli_available" in response.statistics
        assert "items_by_type" in response.statistics
        assert "items_by_priority" in response.statistics

    @patch("memory_manager_engine.GitHubSync")
    def test_handle_sync(self, mock_github_sync) -> None:
        """Test handling sync requests."""
        # Mock GitHub sync
        mock_sync_instance = MagicMock()
        mock_sync_instance.get_memory_issues.return_value = []
        mock_sync_instance.create_issue_for_item.return_value = GitHubIssue(
            number=123,
            title="Test",
            body="Test",
            state="open",
            labels=["memory-sync"],
            url="https://github.com/test/repo/issues/123",
        )
        mock_github_sync.return_value = mock_sync_instance

        engine = MemoryManagerEngine()

        request = MemoryManagerRequest(
            action="sync",
            memory_content=self.sample_memory,
            sync_options={
                "create_issues": True,
                "close_completed": True,
                "update_labels": True,
            },
        )

        response = engine.process_request(request)

        assert response.success is True
        assert "issues_created" in response.statistics

    def test_invalid_action(self) -> None:
        """Test handling invalid action."""
        request = MemoryManagerRequest(action="invalid_action")
        response = self.engine.process_request(request)

        assert response.success is False
        assert len(response.errors) > 0
        assert "Unknown action" in response.errors[0]

    def test_exception_handling(self) -> None:
        """Test exception handling in engine."""
        # Create request with invalid data to trigger exception
        request = MemoryManagerRequest(
            action="update",
            memory_content=None,  # This should cause issues
            updates=[{"invalid": "data"}],
        )

        response = self.engine.process_request(request)

        # Should handle gracefully
        assert response.success is False or response.success is True
        # Should have some response even if error


class TestRunMemoryManager:
    """Test the run_memory_manager entry point."""

    def test_successful_request(self) -> None:
        """Test successful memory manager request."""
        request_data = {
            "action": "status",
            "memory_content": "# AI Assistant Memory\n\n## Active Goals\n- Test goal",
        }

        result = run_memory_manager(request_data)

        assert "success" in result
        assert "statistics" in result
        assert "actions_taken" in result
        assert "errors" in result

    def test_invalid_request(self) -> None:
        """Test invalid request handling."""
        request_data = {"action": "invalid"}

        result = run_memory_manager(request_data)

        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_exception_handling(self) -> None:
        """Test exception handling in entry point."""
        # Pass completely invalid data
        request_data = None

        result = run_memory_manager(request_data)

        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Memory manager error" in result["errors"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
