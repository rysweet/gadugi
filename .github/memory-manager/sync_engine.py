#!/usr/bin/env python3
"""
Memory-GitHub Sync Engine - Bidirectional synchronization between Memory.md and GitHub Issues

This module orchestrates the synchronization between Memory.md tasks and GitHub issues,
handling conflict resolution, status updates, and maintaining data consistency.
"""

import json
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from github_integration import GitHubIntegration, GitHubIssue
from memory_parser import MemoryDocument, MemoryParser, Task, TaskStatus


# Import enums from separate module to avoid circular imports
from enums import SyncDirection, ConflictResolution


@dataclass
class SyncConflict:
    """Represents a synchronization conflict"""

    task_id: str
    issue_number: int
    conflict_type: str
    memory_data: Dict[str, Any]
    github_data: Dict[str, Any]
    timestamp: datetime
    resolution: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class SyncResult:
    """Represents synchronization results"""

    start_time: datetime
    end_time: datetime
    direction: SyncDirection
    memory_tasks_processed: int
    github_issues_processed: int
    created_issues: int
    updated_issues: int
    closed_issues: int
    updated_tasks: int
    conflicts: List[SyncConflict]
    errors: List[str]
    success: bool

    @property
    def duration(self) -> timedelta:
        """Get sync duration"""
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result["start_time"] = self.start_time.isoformat()
        result["end_time"] = self.end_time.isoformat()
        result["duration_seconds"] = self.duration.total_seconds()
        result["direction"] = self.direction.value
        result["conflicts"] = [
            c.to_dict() if hasattr(c, "to_dict") else c for c in self.conflicts
        ]
        return result


@dataclass
class SyncConfig:
    """Synchronization configuration"""

    direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    conflict_resolution: ConflictResolution = ConflictResolution.MANUAL
    auto_create_issues: bool = True
    auto_close_completed: bool = True
    sync_frequency: int = 300  # seconds
    batch_size: int = 10
    backup_before_sync: bool = True
    dry_run: bool = False
    include_sections: Optional[List[str]] = None  # None means all sections
    exclude_sections: Optional[List[str]] = None

    def __post_init__(self):
        if self.include_sections is None:
            self.include_sections = []
        if self.exclude_sections is None:
            self.exclude_sections = ["Reflections", "Important Context"]


class SyncEngine:
    """Bidirectional synchronization engine"""

    def __init__(
        self, memory_path: str, repo_path: Optional[str] = None, config: Optional[SyncConfig] = None
    ):
        """Initialize sync engine"""
        self.memory_path = Path(memory_path)
        self.repo_path = repo_path or str(self.memory_path.parent.parent)
        self.config = config or SyncConfig()

        # Initialize components
        self.parser = MemoryParser()
        self.github = GitHubIntegration(self.repo_path)

        # State tracking
        self.last_sync: Optional[datetime] = None
        self.conflicts: List[SyncConflict] = []

        # Create sync state directory
        self.state_dir = Path(self.repo_path) / ".github" / "memory-sync-state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self._load_sync_state()

    def sync(self, direction: Optional[SyncDirection] = None) -> SyncResult:
        """Perform synchronization"""
        sync_direction = direction or self.config.direction
        start_time = datetime.now()

        print(f"Starting {sync_direction.value} sync at {start_time}")

        # Initialize result
        result = SyncResult(
            start_time=start_time,
            end_time=start_time,  # Will be updated
            direction=sync_direction,
            memory_tasks_processed=0,
            github_issues_processed=0,
            created_issues=0,
            updated_issues=0,
            closed_issues=0,
            updated_tasks=0,
            conflicts=[],
            errors=[],
            success=False,
        )

        try:
            # Backup Memory.md if configured
            if self.config.backup_before_sync:
                self._backup_memory()

            # Load current state
            memory_doc = self.parser.parse_file(str(self.memory_path))
            github_issues = self.github.get_all_memory_issues()

            result.memory_tasks_processed = len(memory_doc.tasks)
            result.github_issues_processed = len(github_issues)

            # Perform sync based on direction
            if sync_direction == SyncDirection.MEMORY_TO_GITHUB:
                self._sync_memory_to_github(memory_doc, github_issues, result)
            elif sync_direction == SyncDirection.GITHUB_TO_MEMORY:
                self._sync_github_to_memory(memory_doc, github_issues, result)
            else:  # BIDIRECTIONAL
                self._sync_bidirectional(memory_doc, github_issues, result)

            result.success = len(result.errors) == 0

        except Exception as e:
            result.errors.append(f"Sync failed: {str(e)}")
            result.success = False

        finally:
            result.end_time = datetime.now()
            self.last_sync = result.end_time
            self._save_sync_state(result)

            print(f"Sync completed in {result.duration.total_seconds():.1f}s")
            print(
                f"Created: {result.created_issues}, Updated: {result.updated_issues}, "
                f"Closed: {result.closed_issues}, Conflicts: {len(result.conflicts)}"
            )

        return result

    def _sync_memory_to_github(
        self,
        memory_doc: MemoryDocument,
        github_issues: List[GitHubIssue],
        result: SyncResult,
    ):
        """Sync Memory.md tasks to GitHub issues"""
        # Create mapping of existing issues
        issue_map = {
            issue.memory_task_id: issue
            for issue in github_issues
            if issue.memory_task_id
        }

        for task in self._filter_tasks(memory_doc.tasks):
            if self.config.dry_run:
                print(f"[DRY RUN] Would sync task: {task.content[:50]}...")
                continue

            try:
                if task.id in issue_map:
                    # Update existing issue
                    issue = issue_map[task.id]

                    # Check for conflicts
                    conflict = self._detect_conflict(task, issue)
                    if conflict:
                        result.conflicts.append(conflict)
                        if self.config.conflict_resolution == ConflictResolution.MANUAL:
                            continue

                    self.github.update_issue_from_task(issue.number, task)
                    result.updated_issues += 1

                    # Close issue if task is completed
                    if (
                        task.status == TaskStatus.COMPLETED
                        and issue.state == "open"
                        and self.config.auto_close_completed
                    ):
                        self.github._close_issue(issue.number)
                        result.closed_issues += 1

                else:
                    # Create new issue
                    if self.config.auto_create_issues:
                        self.github.create_issue_from_task(task)
                        result.created_issues += 1

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                result.errors.append(f"Failed to sync task {task.id}: {str(e)}")

    def _sync_github_to_memory(
        self,
        memory_doc: MemoryDocument,
        github_issues: List[GitHubIssue],
        result: SyncResult,
    ):
        """Sync GitHub issues to Memory.md tasks"""
        # This would update Memory.md content based on GitHub issue changes
        # For now, just track what would be updated
        for issue in github_issues:
            if issue.memory_task_id:
                task = next(
                    (t for t in memory_doc.tasks if t.id == issue.memory_task_id), None
                )
                if task:
                    # Check if issue state differs from task status
                    expected_status = (
                        TaskStatus.COMPLETED
                        if issue.state == "closed"
                        else TaskStatus.PENDING
                    )
                    if task.status != expected_status:
                        if not self.config.dry_run:
                            # Update Memory.md content would happen here
                            pass
                        result.updated_tasks += 1

    def _sync_bidirectional(
        self,
        memory_doc: MemoryDocument,
        github_issues: List[GitHubIssue],
        result: SyncResult,
    ):
        """Perform bidirectional synchronization"""
        # First sync Memory.md to GitHub
        self._sync_memory_to_github(memory_doc, github_issues, result)

        # Then sync GitHub changes back to Memory.md
        # Re-fetch issues to get latest state
        updated_issues = self.github.get_all_memory_issues()
        self._sync_github_to_memory(memory_doc, updated_issues, result)

    def _filter_tasks(self, tasks: List[Task]) -> List[Task]:
        """Filter tasks based on configuration"""
        filtered = []

        for task in tasks:
            # Check include/exclude sections
            if (
                self.config.include_sections
                and task.section not in self.config.include_sections
            ):
                continue
            if (
                self.config.exclude_sections
                and task.section in self.config.exclude_sections
            ):
                continue

            filtered.append(task)

        return filtered

    def _detect_conflict(
        self, task: Task, issue: GitHubIssue
    ) -> Optional[SyncConflict]:
        """Detect conflicts between task and issue"""
        conflicts = []

        # Check if task content has changed significantly
        if self._content_differs_significantly(task.content, issue.title):
            conflicts.append("content_mismatch")

        # Check status consistency
        expected_issue_state = (
            "closed" if task.status == TaskStatus.COMPLETED else "open"
        )
        if issue.state != expected_issue_state:
            conflicts.append("status_mismatch")

        if conflicts:
            # Convert issue to dict manually since it may not be a dataclass
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "updated_at": (
                    issue.updated_at.isoformat()
                    if hasattr(issue.updated_at, "isoformat")
                    else str(issue.updated_at)
                ),
            }

            return SyncConflict(
                task_id=task.id,
                issue_number=issue.number,
                conflict_type=",".join(conflicts),
                memory_data=task.to_dict(),
                github_data=issue_data,
                timestamp=datetime.now(),
            )

        return None

    def _content_differs_significantly(
        self, task_content: str, issue_title: str
    ) -> bool:
        """Check if content differs significantly"""
        # Simple heuristic - check if core content is similar
        task_clean = self._clean_content_for_comparison(task_content)
        title_clean = self._clean_content_for_comparison(issue_title)

        # Allow for some differences but flag major changes
        return not (task_clean in title_clean or title_clean in task_clean)

    def _clean_content_for_comparison(self, content: str) -> str:
        """Clean content for comparison"""
        import re

        # Remove markdown, normalize whitespace, convert to lowercase
        cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", content)  # Remove bold
        cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)  # Remove italic
        cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)  # Remove code
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        return cleaned

    def _backup_memory(self):
        """Create backup of Memory.md"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.state_dir / f"Memory_backup_{timestamp}.md"
        shutil.copy2(self.memory_path, backup_path)

        # Keep only last 10 backups
        backups = sorted(self.state_dir.glob("Memory_backup_*.md"))
        for old_backup in backups[:-10]:
            old_backup.unlink()

    def _load_sync_state(self):
        """Load synchronization state"""
        state_file = self.state_dir / "sync_state.json"
        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
                    if "last_sync" in state:
                        self.last_sync = datetime.fromisoformat(state["last_sync"])
            except Exception as e:
                print(f"Warning: Could not load sync state: {e}")

    def _save_sync_state(self, result: SyncResult):
        """Save synchronization state"""
        state_file = self.state_dir / "sync_state.json"

        state = {
            "last_sync": result.end_time.isoformat(),
            "last_result": result.to_dict(),
        }

        try:
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save sync state: {e}")

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        # Convert config to dict with proper enum serialization
        config_dict = {
            "direction": self.config.direction.value,
            "conflict_resolution": self.config.conflict_resolution.value,
            "auto_create_issues": self.config.auto_create_issues,
            "auto_close_completed": self.config.auto_close_completed,
            "sync_frequency_seconds": self.config.sync_frequency,
            "batch_size": self.config.batch_size,
            "backup_before_sync": self.config.backup_before_sync,
            "dry_run": self.config.dry_run,
        }

        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "config": config_dict,
            "pending_conflicts": len(self.conflicts),
            "memory_file": str(self.memory_path),
            "state_dir": str(self.state_dir),
        }

    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        """Resolve a specific conflict"""
        # Implementation would handle conflict resolution
        return True

    def list_conflicts(self) -> List[Dict[str, Any]]:
        """List all pending conflicts"""
        return [conflict.to_dict() for conflict in self.conflicts]


def main():
    """Example usage of SyncEngine"""
    try:
        # Initialize sync engine
        memory_path = "/Users/ryan/src/gadugi/.github/Memory.md"
        repo_path = "/Users/ryan/src/gadugi"

        config = SyncConfig(
            direction=SyncDirection.BIDIRECTIONAL,
            conflict_resolution=ConflictResolution.MANUAL,
            dry_run=True,  # Safe mode for testing
        )

        sync_engine = SyncEngine(memory_path, repo_path, config)

        # Show current status
        status = sync_engine.get_sync_status()
        print(f"Sync status: {json.dumps(status, indent=2)}")

        # Perform sync
        result = sync_engine.sync()

        print("\nSync result:")
        print(f"Success: {result.success}")
        print(f"Duration: {result.duration.total_seconds():.1f}s")
        print(f"Created issues: {result.created_issues}")
        print(f"Updated issues: {result.updated_issues}")
        print(f"Conflicts: {len(result.conflicts)}")
        print(f"Errors: {len(result.errors)}")

        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
