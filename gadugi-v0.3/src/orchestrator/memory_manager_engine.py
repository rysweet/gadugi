#!/usr/bin/env python3
"""Memory Manager Engine for Gadugi v0.3.

Manages AI assistant memory, context persistence, and GitHub Issues synchronization.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class MemoryItem:
    """Represents a single memory item."""

    type: str  # goal, accomplishment, context, todo
    content: str
    priority: str  # high, medium, low
    created: datetime
    updated: datetime
    metadata: dict[str, Any]


@dataclass
class MemorySection:
    """Represents a section in Memory.md."""

    name: str
    content: list[str]
    items: list[MemoryItem]


@dataclass
class GitHubIssue:
    """Represents a GitHub issue."""

    number: int
    title: str
    body: str
    state: str
    labels: list[str]
    url: str


@dataclass
class MemoryManagerRequest:
    """Request format for memory management operations."""

    action: str  # update, prune, sync, archive, status
    memory_content: str | None = None
    updates: list[dict[str, Any]] = None
    sync_options: dict[str, bool] = None
    prune_options: dict[str, Any] = None


@dataclass
class MemoryManagerResponse:
    """Response format for memory management operations."""

    success: bool
    updated_memory: str | None
    actions_taken: list[dict[str, Any]]
    statistics: dict[str, int]
    errors: list[str]


class MemoryManager:
    """Core memory management engine."""

    def __init__(self) -> None:
        self.memory_sections = [
            "Active Goals",
            "Current Context",
            "Recent Accomplishments",
            "Important Context",
            "Reflections",
        ]
        self.optional_sections = [
            "Next Actions",
            "Performance Metrics",
            "Technical Notes",
            "User Feedback",
        ]

    def parse_memory_content(self, content: str) -> dict[str, MemorySection]:
        """Parse Memory.md content into structured sections."""
        sections = {}
        current_section = None
        current_content = []

        lines = content.split("\n")

        for line in lines:
            # Check for section headers
            if line.startswith("## "):
                # Save previous section
                if current_section:
                    sections[current_section] = MemorySection(
                        name=current_section,
                        content=current_content,
                        items=self._parse_section_items(current_content),
                    )

                # Start new section
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Save final section
        if current_section:
            sections[current_section] = MemorySection(
                name=current_section,
                content=current_content,
                items=self._parse_section_items(current_content),
            )

        return sections

    def _parse_section_items(self, content: list[str]) -> list[MemoryItem]:
        """Parse section content into memory items."""
        items = []
        current_item = None
        current_text = []

        for line in content:
            # Check for list items
            if line.strip().startswith(("- ", "* ", "1. ", "✅", "🔄", "⏳")):
                # Save previous item
                if current_item is not None and current_text:
                    current_item.content = "\n".join(current_text).strip()
                    items.append(current_item)

                # Start new item
                item_type = self._determine_item_type(line)
                priority = self._determine_priority(line)

                current_item = MemoryItem(
                    type=item_type,
                    content=line.strip(),
                    priority=priority,
                    created=datetime.now(),
                    updated=datetime.now(),
                    metadata={},
                )
                current_text = [line.strip()]
            elif current_item is not None:
                current_text.append(line)

        # Save final item
        if current_item is not None and current_text:
            current_item.content = "\n".join(current_text).strip()
            items.append(current_item)

        return items

    def _determine_item_type(self, line: str) -> str:
        """Determine the type of a memory item."""
        line_lower = line.lower()

        if any(marker in line for marker in ["✅", "complete", "implemented", "fixed"]):
            return "accomplishment"
        if any(marker in line for marker in ["🔄", "todo", "implement", "need to"]):
            return "todo"
        if any(marker in line_lower for marker in ["goal:", "objective:", "target:"]):
            return "goal"
        return "context"

    def _determine_priority(self, line: str) -> str:
        """Determine the priority of a memory item."""
        line_lower = line.lower()

        if any(marker in line_lower for marker in ["critical", "urgent", "high priority", "major"]):
            return "high"
        if any(marker in line_lower for marker in ["low priority", "minor", "nice to have"]):
            return "low"
        return "medium"

    def update_memory(
        self,
        sections: dict[str, MemorySection],
        updates: list[dict[str, Any]],
    ) -> dict[str, MemorySection]:
        """Update memory sections with new content."""
        updated_sections = sections.copy()

        for update in updates:
            item_type = update.get("type", "context")
            content = update.get("content", "")
            priority = update.get("priority", "medium")
            metadata = update.get("metadata", {})

            # Determine target section
            target_section = self._get_target_section(item_type)

            # Create new memory item
            new_item = MemoryItem(
                type=item_type,
                content=content,
                priority=priority,
                created=datetime.now(),
                updated=datetime.now(),
                metadata=metadata,
            )

            # Add to appropriate section
            if target_section in updated_sections:
                updated_sections[target_section].items.append(new_item)
            else:
                # Create new section if needed
                updated_sections[target_section] = MemorySection(
                    name=target_section,
                    content=[],
                    items=[new_item],
                )

        return updated_sections

    def _get_target_section(self, item_type: str) -> str:
        """Determine which section an item should go in."""
        type_mapping = {
            "goal": "Active Goals",
            "accomplishment": "Recent Accomplishments",
            "context": "Important Context",
            "todo": "Active Goals",
            "reflection": "Reflections",
        }
        return type_mapping.get(item_type, "Important Context")

    def prune_memory(
        self,
        sections: dict[str, MemorySection],
        days_threshold: int = 7,
        preserve_critical: bool = True,
    ) -> dict[str, MemorySection]:
        """Remove outdated memory items."""
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        pruned_sections = {}

        for section_name, section in sections.items():
            pruned_items = []

            for item in section.items:
                should_keep = True

                # Check age
                if item.updated < cutoff_date:
                    # Check if critical
                    if preserve_critical and item.priority == "high":
                        should_keep = True
                    elif item.type == "accomplishment":
                        # Archive old accomplishments
                        should_keep = False
                    elif "completed" in item.content.lower() or "✅" in item.content:
                        # Remove completed items
                        should_keep = False
                    else:
                        should_keep = True

                if should_keep:
                    pruned_items.append(item)

            # Rebuild section with pruned items
            pruned_sections[section_name] = MemorySection(
                name=section_name,
                content=self._items_to_content(pruned_items),
                items=pruned_items,
            )

        return pruned_sections

    def _items_to_content(self, items: list[MemoryItem]) -> list[str]:
        """Convert memory items back to content lines."""
        content = []
        for item in items:
            content.extend(item.content.split("\n"))
        return content

    def render_memory(self, sections: dict[str, MemorySection]) -> str:
        """Render sections back to Memory.md format."""
        output = ["# AI Assistant Memory", ""]

        # Add required sections first
        for section_name in self.memory_sections:
            if section_name in sections:
                section = sections[section_name]
                output.append(f"## {section_name}")

                if section.items:
                    # Sort items by priority and date
                    sorted_items = sorted(
                        section.items,
                        key=lambda x: (
                            {"high": 0, "medium": 1, "low": 2}[x.priority],
                            x.updated,
                        ),
                        reverse=True,
                    )

                    for item in sorted_items:
                        output.append(item.content)
                else:
                    output.append("- No items")

                output.append("")

        # Add optional sections
        for section_name in sections:
            if section_name not in self.memory_sections:
                section = sections[section_name]
                output.append(f"## {section_name}")

                for item in section.items:
                    output.append(item.content)

                output.append("")

        # Add footer
        output.extend(["---", f"*Last updated: {datetime.now().isoformat()}*"])

        return "\n".join(output)


class GitHubSync:
    """Handles GitHub Issues synchronization."""

    def __init__(self) -> None:
        self.gh_available = self._check_gh_cli()

    def _check_gh_cli(self) -> bool:
        """Check if GitHub CLI is available."""
        try:
            result = subprocess.run(["gh", "--version"], check=False, capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def get_memory_issues(self) -> list[GitHubIssue]:
        """Get existing GitHub issues created from memory sync."""
        if not self.gh_available:
            return []

        try:
            # Get issues with memory-sync label
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "list",
                    "--label",
                    "memory-sync",
                    "--json",
                    "number,title,body,state,labels,url",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                issues_data = json.loads(result.stdout)
                return [
                    GitHubIssue(
                        number=issue["number"],
                        title=issue["title"],
                        body=issue["body"],
                        state=issue["state"],
                        labels=[label["name"] for label in issue["labels"]],
                        url=issue["url"],
                    )
                    for issue in issues_data
                ]

        except Exception:
            pass

        return []

    def create_issue_for_item(self, item: MemoryItem) -> GitHubIssue | None:
        """Create a GitHub issue for a memory item."""
        if not self.gh_available or item.type not in ["todo", "goal"]:
            return None

        try:
            title = self._extract_title(item.content)
            body = self._format_issue_body(item)
            labels = self._get_labels_for_item(item)

            # Create the issue
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "create",
                    "--title",
                    title,
                    "--body",
                    body,
                    "--label",
                    ",".join(labels),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Parse the issue URL from output
                issue_url = result.stdout.strip()
                issue_number = int(issue_url.split("/")[-1])

                return GitHubIssue(
                    number=issue_number,
                    title=title,
                    body=body,
                    state="open",
                    labels=labels,
                    url=issue_url,
                )

        except Exception:
            pass

        return None

    def _extract_title(self, content: str) -> str:
        """Extract a title from memory item content."""
        lines = content.strip().split("\n")
        first_line = lines[0]

        # Remove markdown formatting
        title = re.sub(r"[*_`#\-•]", "", first_line).strip()
        title = re.sub(r"✅|🔄|⏳", "", title).strip()

        # Limit length
        if len(title) > 80:
            title = title[:77] + "..."

        return title

    def _format_issue_body(self, item: MemoryItem) -> str:
        """Format the issue body from memory item."""
        body_lines = [
            "**Memory Item Details**",
            f"- Type: {item.type}",
            f"- Priority: {item.priority}",
            f"- Created: {item.created.strftime('%Y-%m-%d %H:%M')}",
            "",
            "**Content:**",
            item.content,
            "",
        ]

        if item.metadata:
            body_lines.extend(
                [
                    "**Metadata:**",
                    "```json",
                    json.dumps(item.metadata, indent=2),
                    "```",
                    "",
                ],
            )

        body_lines.extend(
            [
                "---",
                "*This issue was automatically created from Memory.md by the Memory Manager Agent.*",
            ],
        )

        return "\n".join(body_lines)

    def _get_labels_for_item(self, item: MemoryItem) -> list[str]:
        """Get appropriate labels for a memory item."""
        labels = ["memory-sync", "ai-assistant"]

        # Add priority label
        if item.priority != "medium":
            labels.append(f"{item.priority}-priority")

        # Add type-based labels
        if item.type == "goal":
            labels.append("enhancement")
        elif item.type == "todo":
            labels.append("task")

        # Add metadata-based labels
        if "bug" in item.content.lower():
            labels.append("bug")
        if "documentation" in item.content.lower() or "docs" in item.content.lower():
            labels.append("documentation")
        if "test" in item.content.lower():
            labels.append("testing")

        return labels

    def update_issue_status(self, issue: GitHubIssue, new_state: str) -> bool:
        """Update the status of a GitHub issue."""
        if not self.gh_available:
            return False

        try:
            if new_state in {"completed", "closed"}:
                result = subprocess.run(
                    ["gh", "issue", "close", str(issue.number)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            elif new_state == "open" and issue.state == "closed":
                result = subprocess.run(
                    ["gh", "issue", "reopen", str(issue.number)],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            else:
                return True  # No change needed

            return result.returncode == 0

        except Exception:
            return False


class MemoryManagerEngine:
    """Main engine that orchestrates memory management operations."""

    def __init__(self) -> None:
        self.memory_manager = MemoryManager()
        self.github_sync = GitHubSync()

    def process_request(self, request: MemoryManagerRequest) -> MemoryManagerResponse:
        """Process a memory management request."""
        try:
            if request.action == "update":
                return self._handle_update(request)
            if request.action == "prune":
                return self._handle_prune(request)
            if request.action == "sync":
                return self._handle_sync(request)
            if request.action == "archive":
                return self._handle_archive(request)
            if request.action == "status":
                return self._handle_status(request)
            return MemoryManagerResponse(
                success=False,
                updated_memory=None,
                actions_taken=[],
                statistics={},
                errors=[f"Unknown action: {request.action}"],
            )

        except Exception as e:
            return MemoryManagerResponse(
                success=False,
                updated_memory=None,
                actions_taken=[],
                statistics={},
                errors=[f"Error processing request: {e!s}"],
            )

    def _handle_update(self, request: MemoryManagerRequest) -> MemoryManagerResponse:
        """Handle memory update requests."""
        actions_taken = []
        errors = []

        # Parse current memory
        if request.memory_content:
            sections = self.memory_manager.parse_memory_content(request.memory_content)
        else:
            sections = {}

        # Apply updates
        if request.updates:
            sections = self.memory_manager.update_memory(sections, request.updates)
            actions_taken.append(
                {"action": "updated_memory", "items_count": len(request.updates)},
            )

        # Render updated memory
        updated_memory = self.memory_manager.render_memory(sections)

        return MemoryManagerResponse(
            success=True,
            updated_memory=updated_memory,
            actions_taken=actions_taken,
            statistics={"items_added": len(request.updates or [])},
            errors=errors,
        )

    def _handle_prune(self, request: MemoryManagerRequest) -> MemoryManagerResponse:
        """Handle memory pruning requests."""
        actions_taken = []
        errors = []

        if not request.memory_content:
            errors.append("No memory content provided for pruning")
            return MemoryManagerResponse(
                success=False,
                updated_memory=None,
                actions_taken=actions_taken,
                statistics={},
                errors=errors,
            )

        # Parse current memory
        sections = self.memory_manager.parse_memory_content(request.memory_content)
        original_items = sum(len(section.items) for section in sections.values())

        # Apply pruning
        prune_options = request.prune_options or {}
        days_threshold = prune_options.get("days_threshold", 7)
        preserve_critical = prune_options.get("preserve_critical", True)

        pruned_sections = self.memory_manager.prune_memory(
            sections,
            days_threshold,
            preserve_critical,
        )

        pruned_items = sum(len(section.items) for section in pruned_sections.values())
        items_removed = original_items - pruned_items

        actions_taken.append(
            {"action": "pruned_memory", "items_removed": items_removed},
        )

        # Render pruned memory
        updated_memory = self.memory_manager.render_memory(pruned_sections)

        return MemoryManagerResponse(
            success=True,
            updated_memory=updated_memory,
            actions_taken=actions_taken,
            statistics={"items_removed": items_removed},
            errors=errors,
        )

    def _handle_sync(self, request: MemoryManagerRequest) -> MemoryManagerResponse:
        """Handle GitHub synchronization requests."""
        actions_taken = []
        errors = []
        statistics = {"issues_created": 0, "issues_updated": 0, "issues_closed": 0}

        if not request.memory_content:
            errors.append("No memory content provided for sync")
            return MemoryManagerResponse(
                success=False,
                updated_memory=None,
                actions_taken=actions_taken,
                statistics=statistics,
                errors=errors,
            )

        sync_options = request.sync_options or {}

        # Parse memory content
        sections = self.memory_manager.parse_memory_content(request.memory_content)

        # Get existing issues
        existing_issues = self.github_sync.get_memory_issues()

        # Create issues for new items
        if sync_options.get("create_issues", True):
            for section in sections.values():
                for item in section.items:
                    if item.type in ["todo", "goal"]:
                        # Check if issue already exists
                        title = self.github_sync._extract_title(item.content)
                        if not any(title in issue.title for issue in existing_issues):
                            new_issue = self.github_sync.create_issue_for_item(item)
                            if new_issue:
                                actions_taken.append(
                                    {
                                        "action": "created_issue",
                                        "issue_number": new_issue.number,
                                        "title": new_issue.title,
                                        "url": new_issue.url,
                                    },
                                )
                                statistics["issues_created"] += 1

        # Close completed issues
        if sync_options.get("close_completed", True):
            for issue in existing_issues:
                if issue.state == "open":
                    # Check if corresponding memory item is completed
                    issue_content = issue.title.lower()
                    for section in sections.values():
                        for item in section.items:
                            if issue_content in item.content.lower() and (
                                item.type == "accomplishment" or "✅" in item.content
                            ):
                                if self.github_sync.update_issue_status(
                                    issue,
                                    "closed",
                                ):
                                    actions_taken.append(
                                        {
                                            "action": "closed_issue",
                                            "issue_number": issue.number,
                                            "title": issue.title,
                                        },
                                    )
                                    statistics["issues_closed"] += 1

        return MemoryManagerResponse(
            success=len(errors) == 0,
            updated_memory=request.memory_content,  # No memory changes for sync
            actions_taken=actions_taken,
            statistics=statistics,
            errors=errors,
        )

    def _handle_archive(self, request: MemoryManagerRequest) -> MemoryManagerResponse:
        """Handle memory archiving requests."""
        # TODO: Implement archiving to separate files
        return MemoryManagerResponse(
            success=True,
            updated_memory=request.memory_content,
            actions_taken=[{"action": "archive_placeholder"}],
            statistics={},
            errors=["Archiving not yet implemented"],
        )

    def _handle_status(self, request: MemoryManagerRequest) -> MemoryManagerResponse:
        """Handle status requests."""
        actions_taken = []
        statistics = {}

        if request.memory_content:
            sections = self.memory_manager.parse_memory_content(request.memory_content)
            total_items = sum(len(section.items) for section in sections.values())

            statistics = {
                "total_sections": len(sections),
                "total_items": total_items,
                "github_cli_available": self.github_sync.gh_available,
            }

            # Count by type
            type_counts = {}
            priority_counts = {}

            for section in sections.values():
                for item in section.items:
                    type_counts[item.type] = type_counts.get(item.type, 0) + 1
                    priority_counts[item.priority] = priority_counts.get(item.priority, 0) + 1

            statistics.update(
                {"items_by_type": type_counts, "items_by_priority": priority_counts},
            )

        return MemoryManagerResponse(
            success=True,
            updated_memory=None,
            actions_taken=actions_taken,
            statistics=statistics,
            errors=[],
        )


def run_memory_manager(request_data: dict[str, Any]) -> dict[str, Any]:
    """Entry point for memory manager operations."""
    try:
        # Parse request
        request = MemoryManagerRequest(**request_data)

        # Process request
        engine = MemoryManagerEngine()
        response = engine.process_request(request)

        # Return response
        return {
            "success": response.success,
            "updated_memory": response.updated_memory,
            "actions_taken": response.actions_taken,
            "statistics": response.statistics,
            "errors": response.errors,
        }

    except Exception as e:
        return {
            "success": False,
            "updated_memory": None,
            "actions_taken": [],
            "statistics": {},
            "errors": [f"Memory manager error: {e!s}"],
        }


if __name__ == "__main__":
    # Example usage
    sample_memory = """# AI Assistant Memory

## Active Goals
- ✅ Complete memory manager implementation
- 🔄 Implement remaining agents for v0.3

## Current Context
- Branch: feature/v0.3-memory-manager
- Working on memory management capabilities

## Recent Accomplishments
- ✅ Created memory manager agent structure
- ✅ Implemented core memory parsing logic
"""

    # Test update operation
    request = {
        "action": "update",
        "memory_content": sample_memory,
        "updates": [
            {
                "type": "accomplishment",
                "content": "✅ Successfully implemented memory manager engine",
                "priority": "high",
                "metadata": {"component": "memory-manager"},
            },
        ],
    }

    result = run_memory_manager(request)
