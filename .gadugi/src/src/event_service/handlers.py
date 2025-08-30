"""Event handlers and filtering for the event service."""

import fnmatch
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .events import Event, GitHubEvent, TaskStatus
from .config import AgentInvocation


@dataclass
class GitHubFilter:
    """Filter for GitHub events."""
    repositories: List[str] = field(default_factory=list)
    webhook_events: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    refs: List[str] = field(default_factory=list)
    
    def matches(self, github_event: GitHubEvent) -> bool:
        """Check if GitHub event matches filter criteria."""
        # Empty filter matches everything
        if not any([self.repositories, self.webhook_events, self.actions, self.labels, self.refs]):
            return True
        
        # Check repositories
        if self.repositories and github_event.repository not in self.repositories:
            return False
        
        # Check webhook events
        if self.webhook_events and github_event.webhook_event not in self.webhook_events:
            return False
        
        # Check actions
        if self.actions and github_event.action not in self.actions:
            return False
        
        # Check labels (any matching label is sufficient)
        if self.labels:
            if not github_event.labels:
                return False
            if not any(label in self.labels for label in github_event.labels):
                return False
        
        # Check refs with pattern matching
        if self.refs:
            if not github_event.ref:
                return False
            ref_matches = False
            for ref_pattern in self.refs:
                if ref_pattern.endswith('*'):
                    # Pattern matching
                    if github_event.ref.startswith(ref_pattern[:-1]):
                        ref_matches = True
                        break
                else:
                    # Exact match
                    if github_event.ref == ref_pattern:
                        ref_matches = True
                        break
            if not ref_matches:
                return False
        
        return True
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'GitHubFilter':
        """Create filter from configuration dictionary."""
        return cls(
            repositories=config.get('repositories', []),
            webhook_events=config.get('webhook_events', []),
            actions=config.get('actions', []),
            labels=config.get('labels', []),
            refs=config.get('refs', [])
        )


@dataclass
class EventFilter:
    """General event filter."""
    event_types: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    metadata_match: Dict[str, Any] = field(default_factory=dict)
    github_filter: Optional[GitHubFilter] = None
    
    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria."""
        # Check event types with pattern matching
        if self.event_types:
            type_matches = False
            for pattern in self.event_types:
                if fnmatch.fnmatch(event.event_type, pattern):
                    type_matches = True
                    break
            if not type_matches:
                return False
        
        # Check sources
        if self.sources and event.source not in self.sources:
            return False
        
        # Check metadata
        if self.metadata_match:
            for key, value in self.metadata_match.items():
                if event.metadata.get(key) != value:
                    return False
        
        # Check GitHub-specific filter if applicable
        if self.github_filter and event.is_github_event():
            github_event = event.get_github_event()
            if github_event and not self.github_filter.matches(github_event):
                return False
        
        return True
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'EventFilter':
        """Create filter from configuration dictionary."""
        github_filter = None
        if 'github_filter' in config:
            github_filter = GitHubFilter.from_config(config['github_filter'])
        
        return cls(
            event_types=config.get('event_types', []),
            sources=config.get('sources', []),
            metadata_match=config.get('metadata_match', {}),
            github_filter=github_filter
        )


@dataclass
class EventHandler:
    """Event handler configuration."""
    name: str
    filter: EventFilter
    invocation: AgentInvocation
    enabled: bool = True
    priority: int = 0
    timeout_seconds: int = 60
    
    def matches(self, event: Event) -> bool:
        """Check if handler should process this event."""
        if not self.enabled:
            return False
        return self.filter.matches(event)


class EventMatcher:
    """Matches events to handlers."""
    
    def __init__(self, handlers: Optional[List[EventHandler]] = None):
        """Initialize with list of handlers."""
        self.handlers = handlers or []
    
    def find_matching_handlers(self, event: Event) -> List[EventHandler]:
        """Find all handlers that match the given event."""
        matching = []
        for handler in self.handlers:
            if handler.matches(event):
                matching.append(handler)
        
        # Sort by priority (higher priority first)
        matching.sort(key=lambda h: h.priority, reverse=True)
        return matching
    
    def add_handler(self, handler: EventHandler) -> None:
        """Add a handler."""
        self.handlers.append(handler)
    
    def remove_handler(self, name: str) -> bool:
        """Remove a handler by name."""
        for i, handler in enumerate(self.handlers):
            if handler.name == name:
                del self.handlers[i]
                return True
        return False
    
    def get_handler_by_name(self, name: str) -> Optional[EventHandler]:
        """Get handler by name."""
        for handler in self.handlers:
            if handler.name == name:
                return handler
        return None
    
    def enable_handler(self, name: str) -> bool:
        """Enable a handler by name."""
        handler = self.get_handler_by_name(name)
        if handler:
            handler.enabled = True
            return True
        return False
    
    def disable_handler(self, name: str) -> bool:
        """Disable a handler by name."""
        handler = self.get_handler_by_name(name)
        if handler:
            handler.enabled = False
            return True
        return False


class CommonFilters:
    """Common pre-configured filters."""
    
    @staticmethod
    def new_issues() -> EventFilter:
        """Filter for new GitHub issues."""
        return EventFilter(
            event_types=["github.issues.opened"],
            sources=["github"]
        )
    
    @staticmethod
    def new_pull_requests() -> EventFilter:
        """Filter for new GitHub pull requests."""
        return EventFilter(
            event_types=["github.pull_request.opened"],
            sources=["github"]
        )
    
    @staticmethod
    def main_branch_pushes() -> EventFilter:
        """Filter for pushes to main branch."""
        return EventFilter(
            event_types=["github.push"],
            sources=["github"],
            github_filter=GitHubFilter(refs=["refs/heads/main"])
        )
    
    @staticmethod
    def bug_issues() -> EventFilter:
        """Filter for issues labeled as bugs."""
        return EventFilter(
            event_types=["github.issues.*"],
            sources=["github"],
            github_filter=GitHubFilter(labels=["bug"])
        )
    
    @staticmethod
    def agent_completions() -> EventFilter:
        """Filter for agent completion events."""
        return EventFilter(
            event_types=["agent.*.completed"],
            sources=["agent"]
        )
    
    @staticmethod
    def local_file_changes() -> EventFilter:
        """Filter for local file change events."""
        return EventFilter(
            event_types=["local.file_changed"],
            sources=["local"]
        )