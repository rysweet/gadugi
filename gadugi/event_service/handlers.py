"""
Event handler and filtering system for Gadugi Event Service

Provides event filtering logic and handler execution coordination.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union

from .events import Event, GitHubEvent, LocalEvent, AgentEvent
from .config import (
    EventHandlerConfig,
    EventFilter as EventFilterConfig,
    GitHubFilter as GitHubFilterConfig,
    AgentInvocation,
)

logger = logging.getLogger(__name__)


class GitHubFilter:
    """GitHub-specific event filtering."""

    def __init__(
        self,
        repositories: Optional[List[str]] = None,
        webhook_events: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        actors: Optional[List[str]] = None,
        refs: Optional[List[str]] = None,
        milestones: Optional[List[str]] = None,
    ):
        self.repositories = repositories or []
        self.webhook_events = webhook_events or []
        self.actions = actions or []
        self.labels = labels or []
        self.actors = actors or []
        self.refs = refs or []
        self.milestones = milestones or []

    def matches(self, github_event: GitHubEvent) -> bool:
        """Check if GitHub event matches this filter."""
        # Check repository
        if self.repositories and github_event.repository not in self.repositories:
            return False

        # Check webhook event type
        if (
            self.webhook_events
            and github_event.webhook_event not in self.webhook_events
        ):
            return False

        # Check action
        if self.actions and github_event.action not in self.actions:
            return False

        # Check labels (any label matches)
        if self.labels:
            if not any(label in github_event.labels for label in self.labels):
                return False

        # Check actor
        if self.actors and github_event.actor not in self.actors:
            return False

        # Check ref (supports patterns like refs/heads/main)
        if self.refs:
            if not any(
                self._matches_ref(pattern, github_event.ref) for pattern in self.refs
            ):
                return False

        # Check milestone
        if self.milestones and github_event.milestone not in self.milestones:
            return False

        return True

    def _matches_ref(self, pattern: str, ref: str) -> bool:
        """Check if ref matches pattern (supports wildcards)."""
        if not pattern or not ref:
            return False

        # Convert glob pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex_pattern}$", ref))

    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]]) -> "GitHubFilter":
        """Create GitHubFilter from configuration dictionary."""
        if not config:
            return cls()

        return cls(
            repositories=config.get("repositories", []),
            webhook_events=config.get("webhook_events", []),
            actions=config.get("actions", []),
            labels=config.get("labels", []),
            actors=config.get("actors", []),
            refs=config.get("refs", []),
            milestones=config.get("milestones", []),
        )


class EventFilter:
    """General event filtering logic."""

    def __init__(
        self,
        event_types: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        metadata_match: Optional[Dict[str, str]] = None,
        github_filter: Optional[GitHubFilter] = None,
    ):
        self.event_types = event_types or []
        self.sources = sources or []
        self.metadata_match = metadata_match or {}
        self.github_filter = github_filter

    def matches(self, event: Event) -> bool:
        """Check if event matches this filter."""
        # Check event type (supports patterns)
        if self.event_types:
            if not any(
                self._matches_pattern(pattern, event.event_type)
                for pattern in self.event_types
            ):
                return False

        # Check source
        if self.sources and event.source not in self.sources:
            return False

        # Check metadata
        for key, expected_value in self.metadata_match.items():
            if key not in event.metadata or event.metadata[key] != expected_value:
                return False

        # Check GitHub-specific filters
        if self.github_filter and event.is_github_event():
            github_event = event.get_github_event()
            if github_event and not self.github_filter.matches(github_event):
                return False

        return True

    def _matches_pattern(self, pattern: str, value: str) -> bool:
        """Check if value matches pattern (supports wildcards)."""
        if not pattern:
            return True

        # Convert glob pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex_pattern}$", value))

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "EventFilter":
        """Create EventFilter from configuration dictionary."""
        github_filter = None
        if "github_filter" in config:
            github_filter = GitHubFilter.from_config(config["github_filter"])

        return cls(
            event_types=config.get("event_types", []),
            sources=config.get("sources", []),
            metadata_match=config.get("metadata_match", {}),
            github_filter=github_filter,
        )


@dataclass
class EventHandler:
    """Event handler configuration and execution."""

    name: str
    filter: EventFilter
    invocation: AgentInvocation
    enabled: bool = True
    priority: int = 100
    timeout_seconds: int = 300
    async_execution: bool = False

    def matches(self, event: Event) -> bool:
        """Check if this handler should process the event."""
        return self.enabled and self.filter.matches(event)

    @classmethod
    def from_config(cls, config: EventHandlerConfig) -> "EventHandler":
        """Create EventHandler from configuration."""
        # Parse filter
        event_filter = EventFilter.from_config(config.filter)

        # Parse invocation
        invocation = AgentInvocation(**config.invocation)

        return cls(
            name=config.name,
            filter=event_filter,
            invocation=invocation,
            enabled=config.enabled,
            priority=config.priority,
            timeout_seconds=config.timeout_seconds,
            async_execution=config.async_execution,
        )


class EventMatcher:
    """Utility class for event matching and routing."""

    def __init__(self, handlers: List[EventHandler]):
        """Initialize with list of event handlers."""
        self.handlers = handlers
        # Sort by priority (higher first)
        self.handlers.sort(key=lambda h: h.priority, reverse=True)

    def find_matching_handlers(self, event: Event) -> List[EventHandler]:
        """Find all handlers that match the given event."""
        matching = []

        for handler in self.handlers:
            if handler.matches(event):
                matching.append(handler)
                logger.debug(
                    f"Event {event.event_type} matched handler: {handler.name}"
                )

        if not matching:
            logger.debug(f"No handlers found for event: {event.event_type}")

        return matching

    def get_handler_by_name(self, name: str) -> Optional[EventHandler]:
        """Get handler by name."""
        for handler in self.handlers:
            if handler.name == name:
                return handler
        return None

    def add_handler(self, handler: EventHandler) -> None:
        """Add a new handler and re-sort by priority."""
        self.handlers.append(handler)
        self.handlers.sort(key=lambda h: h.priority, reverse=True)

    def remove_handler(self, name: str) -> bool:
        """Remove handler by name."""
        for i, handler in enumerate(self.handlers):
            if handler.name == name:
                del self.handlers[i]
                return True
        return False

    def enable_handler(self, name: str) -> bool:
        """Enable handler by name."""
        handler = self.get_handler_by_name(name)
        if handler:
            handler.enabled = True
            return True
        return False

    def disable_handler(self, name: str) -> bool:
        """Disable handler by name."""
        handler = self.get_handler_by_name(name)
        if handler:
            handler.enabled = False
            return True
        return False


# Predefined common filters
class CommonFilters:
    """Common event filter patterns."""

    @staticmethod
    def new_issues() -> EventFilter:
        """Filter for new GitHub issues."""
        return EventFilter(
            event_types=["github.issues.opened"],
            github_filter=GitHubFilter(webhook_events=["issues"], actions=["opened"]),
        )

    @staticmethod
    def new_pull_requests() -> EventFilter:
        """Filter for new GitHub pull requests."""
        return EventFilter(
            event_types=["github.pull_request.opened"],
            github_filter=GitHubFilter(
                webhook_events=["pull_request"], actions=["opened"]
            ),
        )

    @staticmethod
    def main_branch_pushes() -> EventFilter:
        """Filter for pushes to main branch."""
        return EventFilter(
            event_types=["github.push"],
            github_filter=GitHubFilter(
                webhook_events=["push"], refs=["refs/heads/main"]
            ),
        )

    @staticmethod
    def pr_updates() -> EventFilter:
        """Filter for PR updates (opened, synchronize)."""
        return EventFilter(
            event_types=["github.pull_request.*"],
            github_filter=GitHubFilter(
                webhook_events=["pull_request"], actions=["opened", "synchronize"]
            ),
        )

    @staticmethod
    def bug_issues() -> EventFilter:
        """Filter for issues labeled as bugs."""
        return EventFilter(
            event_types=["github.issues.*"],
            github_filter=GitHubFilter(webhook_events=["issues"], labels=["bug"]),
        )

    @staticmethod
    def agent_completions() -> EventFilter:
        """Filter for agent completion events."""
        return EventFilter(event_types=["agent.*.completed"], sources=["agent"])

    @staticmethod
    def local_file_changes() -> EventFilter:
        """Filter for local file change events."""
        return EventFilter(event_types=["local.file_changed"], sources=["local"])
