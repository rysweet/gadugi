#!/usr/bin/env python3
"""
WorktreeManager Component for OrchestratorAgent

Manages git worktrees for isolated parallel execution environments,
including creation, synchronization, and cleanup operations.
"""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class WorktreeInfo:
    """Information about a managed worktree"""
    task_id: str
    task_name: str
    worktree_path: Path
    branch_name: str
    status: str  # 'active', 'completed', 'failed', 'cleaning'
    created_at: str
    pid: Optional[int] = None  # Process ID if task is running


class WorktreeManager:
    """Manages git worktrees for parallel task execution"""

    def __init__(self, project_root: str, worktrees_dir: str) -> None:
        self.project_root = Path(project_root).resolve()
        self.worktrees_dir = self.project_root / worktrees_dir
        self.worktrees: Dict[Any, Any] = field(default_factory=dict)
        self.state_file = self.project_root / ".claude" / "orchestrator" / "worktree_state.json"

        # Ensure directories exist
        self.worktrees_dir.mkdir(exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing state
        self._load_state()

    def create_worktree(self, task_id: str, task_name: str, base_branch: str = "main") -> WorktreeInfo:
        """Create a new git worktree for a task"""
        print(f"🌳 Creating worktree for task: {task_id}")

        # Generate unique branch and directory names
        # Sanitize task_name for valid Git branch name (remove invalid characters)
        sanitized_name = task_name.lower().replace(' ', '-').replace(':', '').replace('#', '').replace('(', '').replace(')', '').replace('%', '').replace('-', '', 1) if task_name.lower().startswith('resume') else task_name.lower().replace(' ', '-').replace(':', '').replace('#', '').replace('(', '').replace(')', '').replace('%', '')
        branch_name = f"feature/parallel-{sanitized_name}-{task_id}"
        worktree_path = self.worktrees_dir / f"task-{task_id}"

        # Clean up if worktree already exists
        if task_id in self.worktrees:
            print(f"⚠️  Cleaning up existing worktree for task: {task_id}")
            self.cleanup_worktree(task_id)

        try:
            # Create the worktree
            cmd = [
                "git", "worktree", "add",
                str(worktree_path),
                "-b", branch_name,
                base_branch
            ]

            subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            # Set up the worktree environment
            self._setup_worktree_environment(worktree_path)

            # Create worktree info
            worktree_info = WorktreeInfo(
                task_id=task_id,
                task_name=task_name,
                worktree_path=worktree_path,
                branch_name=branch_name,
                status="active",
                created_at=self._get_timestamp()
            )

            self.worktrees[task_id] = worktree_info
            self._save_state()

            print(f"✅ Created worktree: {worktree_path}")
            print(f"   Branch: {branch_name}")

            return worktree_info

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to create worktree for {task_id}: {e.stderr}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)

    def _setup_worktree_environment(self, worktree_path: Path):
        """Set up the worktree environment for task execution"""
        # Copy necessary configuration files
        config_files = [
            ".env",
            ".env.local",
            "pyproject.toml",
            "pytest.ini",
            "requirements.txt"
        ]

        for config_file in config_files:
            src = self.project_root / config_file
            dst = worktree_path / config_file

            if src.exists() and not dst.exists():
                try:
                    shutil.copy2(src, dst)
                except Exception as e:
                    print(f"⚠️  Warning: Failed to copy {config_file}: {e}")

        # Create task-specific directories
        task_dirs = [
            ".claude/logs",
            "temp",
            "results"
        ]

        for task_dir in task_dirs:
            (worktree_path / task_dir).mkdir(parents=True, exist_ok=True)

    def list_worktrees(self) -> List[WorktreeInfo]:
        """List all managed worktrees"""
        return list(self.worktrees.values())

    def get_worktree(self, task_id: str) -> Optional[WorktreeInfo]:
        """Get worktree information for a specific task"""
        return self.worktrees.get(task_id)

    def update_worktree_status(self, task_id: str, status: str, pid: Optional[int] = None):
        """Update worktree status"""
        if task_id in self.worktrees:
            self.worktrees[task_id].status = status
            if pid is not None:
                self.worktrees[task_id].pid = pid
            self._save_state()
            print(f"📊 Updated worktree {task_id} status: {status}")

    def sync_worktree_from_main(self, task_id: str, base_branch: str = "main") -> bool:
        """Sync worktree with latest changes from main branch"""
        if task_id not in self.worktrees:
            print(f"❌ Worktree not found: {task_id}")
            return False

        worktree_info = self.worktrees[task_id]
        print(f"🔄 Syncing worktree {task_id} with {base_branch}")

        try:
            # Fetch latest changes
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=worktree_info.worktree_path,
                check=True,
                capture_output=True
            )

            # Merge changes from base branch
            subprocess.run(
                ["git", "merge", f"origin/{base_branch}"],
                cwd=worktree_info.worktree_path,
                check=True,
                capture_output=True
            )

            print(f"✅ Synced worktree {task_id}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to sync worktree {task_id}: {e}")
            return False

    def collect_worktree_results(self, task_id: str) -> Optional[Dict]:
        """Collect results from a completed worktree"""
        if task_id not in self.worktrees:
            return None

        worktree_info = self.worktrees[task_id]
        results_dir = worktree_info.worktree_path / "results"

        results = {
            'task_id': task_id,
            'task_name': worktree_info.task_name,
            'branch_name': worktree_info.branch_name,
            'status': (worktree_info.status if worktree_info is not None else None),
            'files_changed': [],
            'commits': [],
            'logs': None,
            'artifacts': []
        }

        try:
            # Get list of changed files
            cmd = ["git", "diff", "--name-only", "HEAD~1..HEAD"]
            result = subprocess.run(
                cmd,
                cwd=worktree_info.worktree_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                results['files_changed'] = result.stdout.strip().split('\n') if result.stdout.strip() else []

            # Get commit information
            cmd = ["git", "log", "--oneline", "-n", "5"]
            result = subprocess.run(
                cmd,
                cwd=worktree_info.worktree_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                results['commits'] = result.stdout.strip().split('\n') if result.stdout.strip() else []

            # Collect log files
            log_files = list((worktree_info.worktree_path / ".claude" / "logs").glob("*.log"))
            if log_files:
                results['logs'] = str(log_files[0])  # Most recent log

            # Collect result artifacts
            if results_dir.exists():
                artifacts = list(results_dir.glob("*"))
                results['artifacts'] = [str(f) for f in artifacts]

        except Exception as e:
            print(f"⚠️  Warning: Failed to collect some results for {task_id}: {e}")

        return results

    def cleanup_worktree(self, task_id: str, force: bool = False) -> bool:
        """Clean up a worktree and its associated branch"""
        if task_id not in self.worktrees:
            print(f"⚠️  Worktree not found: {task_id}")
            return False

        worktree_info = self.worktrees[task_id]
        print(f"🧹 Cleaning up worktree: {task_id}")

        # Update status
        self.update_worktree_status(task_id, "cleaning")

        success = True

        try:
            # Stop any running processes
            if worktree_info is not None and worktree_info.pid:
                try:
                    os.kill(worktree_info.pid, 15)  # SIGTERM
                    print(f"🛑 Terminated process {worktree_info.pid}")
                except ProcessLookupError:
                    pass  # Process already terminated

            # Remove the worktree
            if worktree_info.worktree_path.exists():
                cmd = ["git", "worktree", "remove", str(worktree_info.worktree_path)]
                if force:
                    cmd.append("--force")

                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print(f"⚠️  Git worktree remove failed: {result.stderr}")
                    # Force remove directory if git command failed
                    shutil.rmtree(worktree_info.worktree_path, ignore_errors=True)

            # Delete the branch (optional, for cleanup)
            if not force:  # Keep branch for review if not forced cleanup
                try:
                    subprocess.run(
                        ["git", "branch", "-D", worktree_info.branch_name],
                        cwd=self.project_root,
                        capture_output=True,
                        check=False  # Don't fail if branch doesn't exist
                    )
                except Exception:
                    pass  # Branch cleanup is optional

            # Remove from tracking
            del self.worktrees[task_id]
            self._save_state()

            print(f"✅ Cleaned up worktree: {task_id}")

        except Exception as e:
            print(f"❌ Failed to cleanup worktree {task_id}: {e}")
            success = False

        return success

    def cleanup_all_worktrees(self, force: bool = False) -> int:
        """Clean up all managed worktrees"""
        print("🧹 Cleaning up all worktrees...")

        task_ids = list(self.worktrees.keys())
        cleaned = 0

        for task_id in task_ids:
            if self.cleanup_worktree(task_id, force):
                cleaned += 1

        print(f"✅ Cleaned up {cleaned}/{len(task_ids)} worktrees")
        return cleaned

    def get_system_worktrees(self) -> List[Dict]:
        """Get all git worktrees (including non-managed ones)"""
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            worktrees = []
            current_worktree = {}

            for line in result.stdout.split('\n'):
                if line.startswith('worktree '):
                    if current_worktree:
                        worktrees.append(current_worktree)
                    current_worktree = {'path': line[9:]}
                elif line.startswith('HEAD '):
                    current_worktree['head'] = line[5:]
                elif line.startswith('branch '):
                    current_worktree['branch'] = line[7:]
                elif line == 'bare':
                    current_worktree['bare'] = True
                elif line == 'detached':
                    current_worktree['detached'] = True

            if current_worktree:
                worktrees.append(current_worktree)

            return worktrees

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to list system worktrees: {e}")
            return []

    def validate_worktrees(self) -> List[str]:
        """Validate all managed worktrees and return list of issues"""
        issues = []
        system_worktrees = {wt['path']: wt for wt in self.get_system_worktrees()}

        for task_id, worktree_info in self.worktrees.items():
            path_str = str(worktree_info.worktree_path)

            # Check if worktree exists in git
            if path_str not in system_worktrees:
                issues.append(f"Managed worktree {task_id} not found in git worktree list")
                continue

            # Check if directory exists
            if not worktree_info.worktree_path.exists():
                issues.append(f"Worktree directory missing: {task_id}")
                continue

            # Check if branch exists
            try:
                result = subprocess.run(
                    ["git", "branch", "--list", worktree_info.branch_name],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True
                )
                if not result.stdout.strip():
                    issues.append(f"Branch missing for worktree {task_id}: {worktree_info.branch_name}")
            except Exception as e:
                issues.append(f"Failed to check branch for {task_id}: {e}")

        return issues

    def _load_state(self):
        """Load worktree state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)

                self.worktrees = {}
                for task_id, wt_data in data.get('worktrees', {}).items():
                    self.worktrees[task_id] = WorktreeInfo(
                        task_id=wt_data['task_id'],
                        task_name=wt_data['task_name'],
                        worktree_path=Path(wt_data['worktree_path']),
                        branch_name=wt_data['branch_name'],
                        status=wt_data['status'],
                        created_at=wt_data['created_at'],
                        pid=wt_data.get('pid')
                    )

            except Exception as e:
                print(f"⚠️  Warning: Failed to load worktree state: {e}")
                self.worktrees = {}

    def _save_state(self):
        """Save worktree state to file"""
        try:
            data = {
                'worktrees': {
                    task_id: {
                        'task_id': (wt.task_id if wt is not None else None),
                        'task_name': wt.task_name,
                        'worktree_path': str(wt.worktree_path),
                        'branch_name': wt.branch_name,
                        'status': (wt.status if wt is not None else None),
                        'created_at': wt.created_at,
                        'pid': wt.pid
                    }
                    for task_id, wt in self.worktrees.items()
                }
            }

            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"⚠️  Warning: Failed to save worktree state: {e}")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_status_summary(self) -> Dict:
        """Get summary of all worktree statuses"""
        summary = {
            'total': len(self.worktrees),
            'active': 0,
            'completed': 0,
            'failed': 0,
            'cleaning': 0
        }

        for worktree in self.worktrees.values():
            summary[(worktree.status if worktree is not None else None)] = summary.get((worktree.status if worktree is not None else None), 0) + 1

        return summary


def main():
    """CLI entry point for WorktreeManager"""
    import argparse

    parser = argparse.ArgumentParser(description="Manage git worktrees for parallel execution")
    parser.add_argument("command", choices=["list", "create", "cleanup", "validate", "status"])
    parser.add_argument("--task-id", help="Task ID for operations")
    parser.add_argument("--task-name", help="Task name for create operation")
    parser.add_argument("--force", action="store_true", help="Force operation")
    parser.add_argument("--all", action="store_true", help="Apply to all worktrees")

    args = parser.parse_args()

    manager = WorktreeManager()

    try:
        if args.command == "list":
            worktrees = manager.list_worktrees()
            print(f"Managed worktrees: {len(worktrees)}")
            for wt in worktrees:
                print(f"  {(wt.task_id if wt is not None else None)}: {wt.task_name} ({(wt.status if wt is not None else None)})")

        elif args.command == "create":
            if not (args.task_id if args is not None else None) or not args.task_name:
                print("❌ --task-id and --task-name required for create")
                return 1

            manager.create_worktree((args.task_id if args is not None else None), args.task_name)

        elif args.command == "cleanup":
            if args is not None and args.all:
                manager.cleanup_all_worktrees(args.force)
            elif args is not None and (args.task_id if args is not None else None):
                manager.cleanup_worktree((args.task_id if args is not None else None), args.force)
            else:
                print("❌ --task-id or --all required for cleanup")
                return 1

        elif args.command == "validate":
            issues = manager.validate_worktrees()
            if issues:
                print("⚠️  Validation issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("✅ All worktrees valid")

        elif args.command == "status":
            summary = manager.get_status_summary()
            print("Worktree Status Summary:")
            for status, count in summary.items():
                print(f"  {status}: {count}")

    except Exception as e:
        print(f"❌ Operation failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
