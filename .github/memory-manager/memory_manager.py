#!/usr/bin/env python3
"""
Memory Manager CLI - Main interface for Memory.md to GitHub Issues integration

This module provides the command-line interface for managing Memory.md synchronization
with GitHub Issues, including pruning, syncing, and conflict resolution.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import ConfigManager, create_default_config
from github_integration import GitHubIntegration

# Import our components
from memory_parser import MemoryParser, TaskStatus
from sync_engine import SyncDirection, SyncEngine
from memory_compactor import MemoryCompactor


class MemoryManager:
    """Main Memory Manager class"""

    def __init__(self, repo_path: str = None, config_path: str = None):
        """Initialize Memory Manager"""
        self.repo_path = Path(repo_path or os.getcwd())
        self.config_manager = ConfigManager(str(self.repo_path), config_path)
        self.config = self.config_manager.load_config()

        # Initialize components
        memory_path = self.repo_path / self.config.memory_file_path
        self.parser = MemoryParser()
        self.github = GitHubIntegration(str(self.repo_path))
        self.sync_engine = SyncEngine(str(memory_path), str(self.repo_path), self.config.sync)
        # Initialize memory compactor with config-based thresholds
        details_path = self.repo_path / ".github" / self.config.compaction.details_file_name
        self.compactor = MemoryCompactor(
            str(memory_path),
            str(details_path),
            size_thresholds={
                "max_lines": self.config.compaction.max_lines,
                "max_chars": self.config.compaction.max_chars,
                "target_lines": self.config.compaction.target_lines,
                "min_compaction_benefit": self.config.compaction.min_benefit,
            },
        )

    def status(self) -> Dict[str, Any]:
        """Get current status of Memory.md and GitHub integration"""
        try:
            # Parse Memory.md
            memory_path = self.repo_path / self.config.memory_file_path
            memory_doc = self.parser.parse_file(str(memory_path))

            # Get GitHub issues
            github_issues = self.github.get_all_memory_issues()

            # Get sync status
            sync_status = self.sync_engine.get_sync_status()

            return {
                "memory_file": {
                    "path": str(memory_path),
                    "exists": memory_path.exists(),
                    "last_updated": (
                        memory_doc.last_updated.isoformat() if memory_doc.last_updated else None
                    ),
                    "total_tasks": len(memory_doc.tasks),
                    "completed_tasks": len(memory_doc.get_tasks_by_status(TaskStatus.COMPLETED)),
                    "pending_tasks": len(memory_doc.get_tasks_by_status(TaskStatus.PENDING)),
                    "sections": len(memory_doc.sections),
                },
                "github_issues": {
                    "total_memory_issues": len(github_issues),
                    "open_issues": len([i for i in github_issues if i.state == "open"]),
                    "closed_issues": len([i for i in github_issues if i.state == "closed"]),
                },
                "sync_status": sync_status,
                "config": {
                    "sync_direction": (
                        self.config.sync.direction.value
                        if hasattr(self.config.sync.direction, "value")
                        else str(self.config.sync.direction)
                    ),
                    "auto_create_issues": self.config.sync.auto_create_issues,
                    "conflict_resolution": (
                        self.config.sync.conflict_resolution.value
                        if hasattr(self.config.sync.conflict_resolution, "value")
                        else str(self.config.sync.conflict_resolution)
                    ),
                },
            }

        except Exception as e:
            return {"error": str(e)}

    def sync(self, direction: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Perform synchronization between Memory.md and GitHub Issues"""
        try:
            # Set sync options
            sync_direction = None
            if direction:
                sync_direction = SyncDirection(direction)

            if dry_run:
                self.config.sync.dry_run = True

            # Perform sync
            result = self.sync_engine.sync(sync_direction)

            return {
                "success": result.success,
                "duration_seconds": result.duration.total_seconds(),
                "created_issues": result.created_issues,
                "updated_issues": result.updated_issues,
                "closed_issues": result.closed_issues,
                "updated_tasks": result.updated_tasks,
                "conflicts": len(result.conflicts),
                "errors": result.errors,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def prune(self, dry_run: bool = False) -> Dict[str, Any]:
        """Prune old entries from Memory.md using automatic compaction"""
        try:
            # Use the memory compactor for intelligent pruning
            return self.compact_memory(dry_run=dry_run)

        except Exception as e:
            return {"success": False, "error": str(e)}

    def compact_memory(self, dry_run: bool = False) -> Dict[str, Any]:
        """Perform automatic memory compaction with LongTermMemoryDetails.md archiving"""
        try:
            # Check if compaction is needed
            needs_compaction, analysis = self.compactor.needs_compaction()

            if not needs_compaction:
                return {
                    "success": True,
                    "compaction_needed": False,
                    "analysis": analysis,
                    "message": "Memory.md is within size limits - no compaction needed",
                }

            # Perform compaction
            result = self.compactor.compact_memory(dry_run=dry_run)

            if result["success"] and not dry_run and result.get("compaction_executed"):
                # Update the status to reflect successful compaction
                result["message"] = (
                    f"Memory compaction completed successfully. "
                    f"Size reduced by {result['result']['reduction_percentage']:.1f}%. "
                    f"{result['result']['archived_items']} items archived to LongTermMemoryDetails.md"
                )

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def auto_compact_if_needed(self) -> Dict[str, Any]:
        """Automatically compact memory if it exceeds thresholds"""
        try:
            needs_compaction, analysis = self.compactor.needs_compaction()

            if not needs_compaction:
                return {
                    "success": True,
                    "auto_compaction_triggered": False,
                    "analysis": analysis,
                }

            # Perform automatic compaction
            result = self.compact_memory(dry_run=False)
            result["auto_compaction_triggered"] = True

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_conflicts(self) -> List[Dict[str, Any]]:
        """List all pending synchronization conflicts"""
        return self.sync_engine.list_conflicts()

    def resolve_conflict(self, conflict_id: str, resolution: str) -> Dict[str, Any]:
        """Resolve a specific synchronization conflict"""
        try:
            success = self.sync_engine.resolve_conflict(conflict_id, resolution)
            return {
                "success": success,
                "conflict_id": conflict_id,
                "resolution": resolution,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_issues(self, section: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Create GitHub issues for Memory.md tasks"""
        try:
            memory_path = self.repo_path / self.config.memory_file_path
            memory_doc = self.parser.parse_file(str(memory_path))

            # Filter tasks
            tasks_to_process = memory_doc.tasks
            if section:
                tasks_to_process = memory_doc.get_tasks_by_section(section)

            created_count = 0
            errors = []

            for task in tasks_to_process:
                if task.issue_number:
                    continue  # Skip tasks that already have issues

                if dry_run:
                    print(f"[DRY RUN] Would create issue for: {task.content[:50]}...")
                    created_count += 1
                else:
                    try:
                        self.github.create_issue_from_task(task)
                        created_count += 1
                    except Exception as e:
                        errors.append(f"Failed to create issue for task {task.id}: {str(e)}")

            return {
                "success": len(errors) == 0,
                "created_issues": created_count,
                "total_tasks": len(tasks_to_process),
                "errors": errors,
                "dry_run": dry_run,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration"""
        errors = self.config_manager.validate_config()
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "config_path": self.config_manager._find_config_file(),
        }


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Memory Manager - Sync Memory.md with GitHub Issues"
    )

    parser.add_argument("--repo-path", help="Path to repository (default: current directory)")
    parser.add_argument("--config", help="Path to configuration file")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show current status")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize Memory.md with GitHub Issues")
    sync_parser.add_argument(
        "--direction",
        choices=["memory_to_github", "github_to_memory", "bidirectional"],
        help="Sync direction",
    )
    sync_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )

    # Prune command (legacy alias for compact)
    prune_parser = subparsers.add_parser(
        "prune", help="Prune old entries from Memory.md (alias for compact)"
    )
    prune_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )

    # Compact command
    compact_parser = subparsers.add_parser(
        "compact",
        help="Automatically compact Memory.md with archiving to LongTermMemoryDetails.md",
    )
    compact_parser.add_argument(
        "--dry-run", action="store_true", help="Preview compaction without applying"
    )
    compact_parser.add_argument(
        "--force", action="store_true", help="Force compaction even if not needed"
    )

    # Auto-compact command
    subparsers.add_parser(
        "auto-compact",
        help="Check and automatically compact if thresholds are exceeded",
    )

    # Create issues command
    create_parser = subparsers.add_parser(
        "create-issues", help="Create GitHub issues for Memory.md tasks"
    )
    create_parser.add_argument("--section", help="Only process tasks from specific section")
    create_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without applying"
    )

    # Conflicts command
    subparsers.add_parser("conflicts", help="List synchronization conflicts")

    # Resolve conflict command
    resolve_parser = subparsers.add_parser("resolve", help="Resolve synchronization conflict")
    resolve_parser.add_argument("conflict_id", help="Conflict ID to resolve")
    resolve_parser.add_argument("resolution", help="Resolution strategy")

    # Validate command
    subparsers.add_parser("validate", help="Validate configuration")

    # Init command
    subparsers.add_parser("init", help="Initialize Memory Manager configuration")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "init":
            # Create default configuration
            repo_path = Path(args.repo_path or os.getcwd())
            config_path = repo_path / ".github/MemoryManager/config.yaml"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            config = create_default_config()
            config.save_to_file(str(config_path))

            print(f"✅ Initialized Memory Manager configuration at {config_path}")
            print("Edit the configuration file to customize behavior")
            return

        # Initialize Memory Manager
        manager = MemoryManager(args.repo_path, args.config)

        # Execute commands
        if args.command == "status":
            status = manager.status()
            print(json.dumps(status, indent=2))

        elif args.command == "sync":
            result = manager.sync(args.direction, args.dry_run)
            print(json.dumps(result, indent=2))

            if result.get("success"):
                print("✅ Synchronization completed successfully")
            else:
                print("❌ Synchronization failed")
                sys.exit(1)

        elif args.command == "prune":
            result = manager.prune(args.dry_run)
            print(json.dumps(result, indent=2))

            if result.get("success") and result.get("compaction_executed"):
                print("✅ Memory compaction completed successfully")
            elif result.get("success") and not result.get("compaction_needed"):
                print("ℹ️  No compaction needed - Memory.md is within size limits")

        elif args.command == "compact":
            # Force compaction if requested, otherwise use normal logic
            if args.force:
                result = manager.compactor.compact_memory(dry_run=args.dry_run)
            else:
                result = manager.compact_memory(dry_run=args.dry_run)

            print(json.dumps(result, indent=2))

            if result.get("success"):
                if result.get("compaction_executed"):
                    print("✅ Memory compaction completed successfully")
                    if not args.dry_run:
                        reduction = result.get("result", {}).get("reduction_percentage", 0)
                        archived = result.get("result", {}).get("archived_items", 0)
                        print(f"📊 Size reduced by {reduction:.1f}%, {archived} items archived")
                elif result.get("compaction_needed") is False:
                    print("ℹ️  No compaction needed - Memory.md is within size limits")
            else:
                print("❌ Memory compaction failed")
                sys.exit(1)

        elif args.command == "auto-compact":
            result = manager.auto_compact_if_needed()
            print(json.dumps(result, indent=2))

            if result.get("success"):
                if result.get("auto_compaction_triggered"):
                    print("✅ Automatic compaction completed successfully")
                else:
                    print("ℹ️  No automatic compaction needed")
            else:
                print("❌ Automatic compaction failed")
                sys.exit(1)

        elif args.command == "create-issues":
            result = manager.create_issues(args.section, args.dry_run)
            print(json.dumps(result, indent=2))

        elif args.command == "conflicts":
            conflicts = manager.list_conflicts()
            if conflicts:
                print("Pending conflicts:")
                for conflict in conflicts:
                    print(f"  {conflict}")
            else:
                print("No pending conflicts")

        elif args.command == "resolve":
            result = manager.resolve_conflict(args.conflict_id, args.resolution)
            print(json.dumps(result, indent=2))

        elif args.command == "validate":
            result = manager.validate_config()
            print(json.dumps(result, indent=2))

            if result["valid"]:
                print("✅ Configuration is valid")
            else:
                print("❌ Configuration has errors:")
                for error in result["errors"]:
                    print(f"  - {error}")
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
