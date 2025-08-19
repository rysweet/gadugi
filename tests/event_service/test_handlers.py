from typing import Any, Dict, List, Optional

"""Tests for event handlers and filtering."""

from gadugi.event_service.events import (
    Event,
    create_github_event,
    create_local_event,
    create_agent_event,
)
from gadugi.event_service.handlers import (
    GitHubFilter,
    EventFilter,
    EventHandler,
    EventMatcher,
    CommonFilters,
)
from gadugi.event_service.config import AgentInvocation


class TestGitHubFilter:
    """Test GitHub event filtering."""

    def test_repository_filter(self):
        """Test repository filtering."""
        filter = GitHubFilter(repositories=["owner/repo1", "owner/repo2"])

        event1 = create_github_event("issues", "owner/repo1", "opened")
        event2 = create_github_event("issues", "owner/repo3", "opened")

        github_event1 = event1.get_github_event()
        github_event2 = event2.get_github_event()

        assert filter.matches(github_event1)
        assert not filter.matches(github_event2)

    def test_webhook_event_filter(self):
        """Test webhook event type filtering."""
        filter = GitHubFilter(webhook_events=["issues", "pull_request"])

        event1 = create_github_event("issues", "owner/repo", "opened")
        event2 = create_github_event("push", "owner/repo", "")

        github_event1 = event1.get_github_event()
        github_event2 = event2.get_github_event()

        assert filter.matches(github_event1)
        assert not filter.matches(github_event2)

    def test_action_filter(self):
        """Test action filtering."""
        filter = GitHubFilter(actions=["opened", "closed"])

        event1 = create_github_event("issues", "owner/repo", "opened")
        event2 = create_github_event("issues", "owner/repo", "edited")

        github_event1 = event1.get_github_event()
        github_event2 = event2.get_github_event()

        assert filter.matches(github_event1)
        assert not filter.matches(github_event2)

    def test_labels_filter(self):
        """Test labels filtering."""
        filter = GitHubFilter(labels=["bug", "urgent"])

        event1 = create_github_event(
            "issues", "owner/repo", "opened", labels=["bug", "feature"]
        )
        event2 = create_github_event(
            "issues", "owner/repo", "opened", labels=["feature"]
        )
        event3 = create_github_event(
            "issues", "owner/repo", "opened", labels=["urgent"]
        )

        github_event1 = event1.get_github_event()
        github_event2 = event2.get_github_event()
        github_event3 = event3.get_github_event()

        assert filter.matches(github_event1)  # Has "bug"
        assert not filter.matches(github_event2)  # No matching labels
        assert filter.matches(github_event3)  # Has "urgent"

    def test_ref_filter(self):
        """Test ref filtering with patterns."""
        filter = GitHubFilter(refs=["refs/heads/main", "refs/heads/feature/*"])

        event1 = create_github_event("push", "owner/repo", "", ref="refs/heads/main")
        event2 = create_github_event(
            "push", "owner/repo", "", ref="refs/heads/feature/test"
        )
        event3 = create_github_event("push", "owner/repo", "", ref="refs/heads/develop")

        github_event1 = event1.get_github_event()
        github_event2 = event2.get_github_event()
        github_event3 = event3.get_github_event()

        assert filter.matches(github_event1)  # Exact match
        assert filter.matches(github_event2)  # Pattern match
        assert not filter.matches(github_event3)  # No match

    def test_empty_filter_matches_all(self):
        """Test that empty filter matches all events."""
        filter = GitHubFilter()

        event = create_github_event("issues", "owner/repo", "opened")
        github_event = event.get_github_event()

        assert filter.matches(github_event)

    def test_from_config(self):
        """Test creating filter from configuration."""
        config = {
            "repositories": ["owner/repo"],
            "webhook_events": ["issues"],
            "actions": ["opened"],
            "labels": ["bug"],
        }

        filter = GitHubFilter.from_config(config)

        assert filter.repositories == ["owner/repo"]
        assert filter.webhook_events == ["issues"]
        assert filter.actions == ["opened"]
        assert filter.labels == ["bug"]


class TestEventFilter:
    """Test general event filtering."""

    def test_event_type_filter(self):
        """Test event type filtering."""
        filter = EventFilter(event_types=["github.issues.opened", "local.file_changed"])

        event1 = create_github_event("issues", "owner/repo", "opened")
        event2 = create_local_event("file_changed")
        event3 = create_agent_event("test-agent", status="completed")

        assert filter.matches(event1)
        assert filter.matches(event2)
        assert not filter.matches(event3)

    def test_event_type_patterns(self):
        """Test event type pattern matching."""
        filter = EventFilter(event_types=["github.*", "agent.*.completed"])

        event1 = create_github_event("issues", "owner/repo", "opened")
        event2 = create_local_event("file_changed")
        event3 = create_agent_event("test-agent", status="completed")
        event4 = create_agent_event("test-agent", status="started")

        assert filter.matches(event1)  # github.*
        assert not filter.matches(event2)  # local event
        assert filter.matches(event3)  # agent.*.completed
        assert not filter.matches(event4)  # agent.*.started

    def test_source_filter(self):
        """Test source filtering."""
        filter = EventFilter(sources=["github", "local"])

        event1 = create_github_event("issues", "owner/repo", "opened")
        event2 = create_local_event("file_changed")
        event3 = create_agent_event("test-agent")

        assert filter.matches(event1)
        assert filter.matches(event2)
        assert not filter.matches(event3)

    def test_metadata_filter(self):
        """Test metadata filtering."""
        filter = EventFilter(metadata_match={"priority": "high", "team": "backend"})

        event1 = Event(
            metadata={"priority": "high", "team": "backend", "other": "value"}
        )
        event2 = Event(metadata={"priority": "high", "team": "frontend"})
        event3 = Event(metadata={"priority": "low", "team": "backend"})

        assert filter.matches(event1)  # All matches
        assert not filter.matches(event2)  # team mismatch
        assert not filter.matches(event3)  # priority mismatch

    def test_github_filter_integration(self):
        """Test integration with GitHub filter."""
        github_filter = GitHubFilter(repositories=["owner/repo"], actions=["opened"])
        filter = EventFilter(event_types=["github.*"], github_filter=github_filter)

        event1 = create_github_event("issues", "owner/repo", "opened")
        event2 = create_github_event("issues", "owner/other", "opened")
        event3 = create_github_event("issues", "owner/repo", "closed")
        event4 = create_local_event("file_changed")

        assert filter.matches(event1)  # Passes both filters
        assert not filter.matches(event2)  # Wrong repo
        assert not filter.matches(event3)  # Wrong action
        assert not filter.matches(event4)  # Not GitHub event, GitHub filter ignored

    def test_from_config(self):
        """Test creating filter from configuration."""
        config = {
            "event_types": ["github.*"],
            "sources": ["github"],
            "metadata_match": {"priority": "high"},
            "github_filter": {"repositories": ["owner/repo"], "actions": ["opened"]},
        }

        filter = EventFilter.from_config(config)

        assert filter.event_types == ["github.*"]
        assert filter.sources == ["github"]
        assert filter.metadata_match == {"priority": "high"}
        assert filter.github_filter is not None
        assert filter.github_filter.repositories == ["owner/repo"]


class TestEventHandler:
    """Test event handler."""

    def test_creation(self):
        """Test handler creation."""
        filter = EventFilter(event_types=["github.issues.opened"])
        invocation = AgentInvocation(agent_name="workflow-manager")

        handler = EventHandler(
            name="issue-handler",
            filter=filter,
            invocation=invocation,
            priority=100,
            timeout_seconds=300,
        )

        assert handler.name == "issue-handler"
        assert handler.filter == filter
        assert handler.invocation == invocation
        assert handler.enabled
        assert handler.priority == 100
        assert handler.timeout_seconds == 300

    def test_matches(self):
        """Test event matching."""
        filter = EventFilter(event_types=["github.issues.opened"])
        invocation = AgentInvocation(agent_name="workflow-manager")
        handler = EventHandler(name="test", filter=filter, invocation=invocation)

        event1 = create_github_event("issues", "owner/repo", "opened")
        event2 = create_github_event("issues", "owner/repo", "closed")

        assert handler.matches(event1)
        assert not handler.matches(event2)

    def test_disabled_handler(self):
        """Test disabled handler doesn't match."""
        filter = EventFilter(event_types=["github.issues.opened"])
        invocation = AgentInvocation(agent_name="workflow-manager")
        handler = EventHandler(
            name="test", filter=filter, invocation=invocation, enabled=False
        )

        event = create_github_event("issues", "owner/repo", "opened")
        assert not handler.matches(event)


class TestEventMatcher:
    """Test event matcher."""

    def test_find_matching_handlers(self):
        """Test finding matching handlers."""
        # Create handlers
        handler1 = EventHandler(
            name="issue-handler",
            filter=EventFilter(event_types=["github.issues.*"]),
            invocation=AgentInvocation(agent_name="workflow-manager"),
            priority=100,
        )

        handler2 = EventHandler(
            name="pr-handler",
            filter=EventFilter(event_types=["github.pull_request.*"]),
            invocation=AgentInvocation(agent_name="code-reviewer"),
            priority=90,
        )

        handler3 = EventHandler(
            name="all-github-handler",
            filter=EventFilter(event_types=["github.*"]),
            invocation=AgentInvocation(agent_name="logger"),
            priority=50,
        )

        matcher = EventMatcher([handler1, handler2, handler3])

        # Test issue event
        issue_event = create_github_event("issues", "owner/repo", "opened")
        matching = matcher.find_matching_handlers(issue_event)

        assert len(matching) == 2  # handler1 and handler3
        assert matching[0].name == "issue-handler"  # Higher priority first
        assert matching[1].name == "all-github-handler"

        # Test PR event
        pr_event = create_github_event("pull_request", "owner/repo", "opened")
        matching = matcher.find_matching_handlers(pr_event)

        assert len(matching) == 2  # handler2 and handler3
        assert matching[0].name == "pr-handler"
        assert matching[1].name == "all-github-handler"

        # Test local event
        local_event = create_local_event("file_changed")
        matching = matcher.find_matching_handlers(local_event)

        assert len(matching) == 0  # No handlers match

    def test_handler_management(self):
        """Test handler management methods."""
        handler = EventHandler(
            name="test-handler",
            filter=EventFilter(),
            invocation=AgentInvocation(agent_name="test-agent"),
        )

        matcher = EventMatcher([])

        # Test add handler
        matcher.add_handler(handler)
        assert len(matcher.handlers) == 1
        assert matcher.get_handler_by_name("test-handler") == handler

        # Test enable/disable
        assert matcher.disable_handler("test-handler")
        assert not handler.enabled

        assert matcher.enable_handler("test-handler")
        assert handler.enabled

        # Test remove handler
        assert matcher.remove_handler("test-handler")
        assert len(matcher.handlers) == 0
        assert matcher.get_handler_by_name("test-handler") is None

        # Test operations on non-existent handler
        assert not matcher.remove_handler("non-existent")
        assert not matcher.enable_handler("non-existent")
        assert not matcher.disable_handler("non-existent")


class TestCommonFilters:
    """Test predefined common filters."""

    def test_new_issues_filter(self):
        """Test new issues filter."""
        filter = CommonFilters.new_issues()

        event1 = create_github_event("issues", "owner/repo", "opened")
        event2 = create_github_event("issues", "owner/repo", "closed")
        event3 = create_github_event("pull_request", "owner/repo", "opened")

        assert filter.matches(event1)
        assert not filter.matches(event2)
        assert not filter.matches(event3)

    def test_new_pull_requests_filter(self):
        """Test new pull requests filter."""
        filter = CommonFilters.new_pull_requests()

        event1 = create_github_event("pull_request", "owner/repo", "opened")
        event2 = create_github_event("pull_request", "owner/repo", "closed")
        event3 = create_github_event("issues", "owner/repo", "opened")

        assert filter.matches(event1)
        assert not filter.matches(event2)
        assert not filter.matches(event3)

    def test_main_branch_pushes_filter(self):
        """Test main branch pushes filter."""
        filter = CommonFilters.main_branch_pushes()

        event1 = create_github_event("push", "owner/repo", "", ref="refs/heads/main")
        event2 = create_github_event("push", "owner/repo", "", ref="refs/heads/feature")
        event3 = create_github_event("issues", "owner/repo", "opened")

        assert filter.matches(event1)
        assert not filter.matches(event2)
        assert not filter.matches(event3)

    def test_bug_issues_filter(self):
        """Test bug issues filter."""
        filter = CommonFilters.bug_issues()

        event1 = create_github_event("issues", "owner/repo", "opened", labels=["bug"])
        event2 = create_github_event(
            "issues", "owner/repo", "opened", labels=["feature"]
        )
        event3 = create_github_event("issues", "owner/repo", "closed", labels=["bug"])

        assert filter.matches(event1)
        assert not filter.matches(event2)
        assert filter.matches(event3)  # Any issue action with bug label

    def test_agent_completions_filter(self):
        """Test agent completions filter."""
        filter = CommonFilters.agent_completions()

        event1 = create_agent_event("test-agent", status="completed")
        event2 = create_agent_event("test-agent", status="started")
        event3 = create_github_event("issues", "owner/repo", "opened")

        assert filter.matches(event1)
        assert not filter.matches(event2)
        assert not filter.matches(event3)

    def test_local_file_changes_filter(self):
        """Test local file changes filter."""
        filter = CommonFilters.local_file_changes()

        event1 = create_local_event("file_changed")
        event2 = create_local_event("directory_created")
        event3 = create_github_event("issues", "owner/repo", "opened")

        assert filter.matches(event1)
        assert not filter.matches(event2)
        assert not filter.matches(event3)
