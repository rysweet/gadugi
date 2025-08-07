"""WorktreeManager Engine - Git worktree isolation for parallel development.

This engine manages git worktree lifecycle, environment setup, monitoring,
and cleanup to enable safe concurrent development on multiple tasks.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any


class WorktreeStatus(Enum):
    """Worktree status enumeration."""

    CREATING = "creating"
    READY = "ready"
    ACTIVE = "active"
    IDLE = "idle"
    ERROR = "error"
    CLEANING = "cleaning"
    REMOVED = "removed"


@dataclass
class WorktreeRequirements:
    """Worktree environment requirements."""

    uv_project: bool = False
    container_ready: bool = False
    development_tools: list[str] = None
    python_version: str | None = None
    container_policy: str = "standard"

    def __post_init__(self):
        if self.development_tools is None:
            self.development_tools = ["pytest", "ruff"]


@dataclass
class WorktreeMetadata:
    """Worktree metadata and tracking information."""

    task_id: str
    worktree_path: str
    branch_name: str
    base_branch: str
    base_commit: str
    created_at: datetime
    last_accessed: datetime
    status: WorktreeStatus
    disk_usage_mb: int = 0
    requirements: WorktreeRequirements = None
    error_message: str | None = None

    def __post_init__(self):
        if self.requirements is None:
            self.requirements = WorktreeRequirements()


@dataclass
class WorktreeResult:
    """Result of worktree operations."""

    task_id: str
    worktree_path: str
    branch_name: str
    status: str
    environment: dict[str, Any]
    metadata: dict[str, Any]
    error_message: str | None = None


@dataclass
class CleanupResult:
    """Result of cleanup operations."""

    removed_count: int
    preserved_count: int
    disk_freed_mb: int
    errors: list[str]
    summary: dict[str, Any]


class WorktreeEnvironmentSetup:
    """Handles development environment setup in worktrees."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)

    def _default_config(self) -> dict[str, Any]:
        """Default environment configuration."""
        return {
            "default_uv_extras": ["dev", "test"],
            "development_tools": ["pytest", "ruff", "mypy"],
            "python_version": "3.11",
            "container_policy": "standard",
        }

    async def setup_environment(
        self, worktree_path: str, requirements: WorktreeRequirements,
    ) -> dict[str, Any]:
        """Set up complete development environment in worktree."""
        self.logger.info(f"Setting up environment in {worktree_path}")

        result = {
            "git_status": "unknown",
            "uv_env_ready": False,
            "container_policy": requirements.container_policy,
            "development_tools_installed": False,
        }

        try:
            # Change to worktree directory
            original_cwd = os.getcwd()
            os.chdir(worktree_path)

            # Check git status
            result["git_status"] = await self._check_git_status()

            # Set up UV environment if required
            if requirements.uv_project:
                result["uv_env_ready"] = await self._setup_uv_environment(requirements)

            # Install development tools
            result[
                "development_tools_installed"
            ] = await self._install_development_tools(requirements.development_tools)

            # Set up git configuration
            await self._setup_git_config()

        except Exception as e:
            self.logger.exception(f"Environment setup failed: {e!s}")
            result["error"] = str(e)
        finally:
            os.chdir(original_cwd)

        return result

    async def _check_git_status(self) -> str:
        """Check git repository status."""
        try:
            result = await self._run_command_async(["git", "status", "--porcelain"])
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args)
            return "clean" if not result.stdout.strip() else "dirty"
        except subprocess.CalledProcessError:
            return "error"

    async def _setup_uv_environment(self, requirements: WorktreeRequirements) -> bool:
        """Set up UV virtual environment."""
        try:
            # Check if UV project
            if not Path("pyproject.toml").exists():
                self.logger.warning("pyproject.toml not found, not a UV project")
                return False

            # Install UV if not available
            uv_available = await self._ensure_uv_available()
            if not uv_available:
                return False

            # Create/sync virtual environment
            extras = self.config.get("default_uv_extras", ["dev", "test"])
            extra_args = []
            for extra in extras:
                extra_args.extend(["--extra", extra])

            result = await self._run_command_async(["uv", "sync", *extra_args])
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, result.args)

            self.logger.info("UV environment set up successfully")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.exception(f"UV setup failed: {e.stderr}")
            return False

    async def _ensure_uv_available(self) -> bool:
        """Ensure UV is available."""
        try:
            subprocess.run(["uv", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.logger.exception(
                "UV not available - install from https://docs.astral.sh/uv/",
            )
            return False

    async def _install_development_tools(self, tools: list[str]) -> bool:
        """Install development tools in environment."""
        if not tools:
            return True

        try:
            # Try UV installation first
            if Path(".venv").exists():
                for tool in tools:
                    result = subprocess.run(
                        ["uv", "add", "--group", "dev", tool],
                        check=False, capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        self.logger.warning(
                            f"Failed to install {tool} via UV: {result.stderr}",
                        )

            # Verify tools are available
            available_tools = []
            for tool in tools:
                try:
                    subprocess.run([tool, "--version"], capture_output=True, check=True)
                    available_tools.append(tool)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    self.logger.warning(f"Tool {tool} not available")

            self.logger.info(f"Development tools available: {available_tools}")
            return len(available_tools) >= len(tools) / 2  # At least half should work

        except Exception as e:
            self.logger.exception(f"Development tools setup failed: {e!s}")
            return False

    async def _setup_git_config(self) -> None:
        """Set up git configuration for worktree."""
        try:
            # Set up basic git config if not already set
            result = subprocess.run(
                ["git", "config", "user.name"], check=False, capture_output=True, text=True,
            )

            if result.returncode != 0:
                subprocess.run(
                    ["git", "config", "user.name", "Gadugi Agent"], check=True,
                )

                subprocess.run(
                    ["git", "config", "user.email", "gadugi@example.com"], check=True,
                )

            # Set up commit template if available
            template_path = Path(".github/git-templates/commit-template.txt")
            if template_path.exists():
                subprocess.run(
                    ["git", "config", "commit.template", str(template_path)], check=True,
                )

        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Git config setup failed: {e!s}")


class WorktreeHealthMonitor:
    """Monitors worktree health and resource usage."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)

    def _default_config(self) -> dict[str, Any]:
        """Default monitoring configuration."""
        return {
            "health_check_interval": 300,
            "disk_check_threshold": 0.9,
            "inactive_threshold": 86400,  # 24 hours
            "max_disk_usage_gb": 10,
        }

    async def check_worktree_health(self, metadata: WorktreeMetadata) -> dict[str, Any]:
        """Check health of a specific worktree."""
        health = {
            "status": "healthy",
            "issues": [],
            "metrics": {},
            "recommendations": [],
        }

        try:
            # Check if path exists
            if not Path(metadata.worktree_path).exists():
                health["status"] = "missing"
                health["issues"].append("Worktree path does not exist")
                return health

            # Check git status
            git_health = await self._check_git_health(metadata.worktree_path)
            health["metrics"]["git"] = git_health

            if not git_health["healthy"]:
                health["status"] = "unhealthy"
                health["issues"].extend(git_health["issues"])

            # Check disk usage
            disk_usage = await self._check_disk_usage(metadata.worktree_path)
            health["metrics"]["disk"] = disk_usage
            metadata.disk_usage_mb = disk_usage["usage_mb"]

            # Check if inactive
            inactive_hours = (
                datetime.now() - metadata.last_accessed
            ).total_seconds() / 3600
            health["metrics"]["inactive_hours"] = inactive_hours

            if inactive_hours > self.config["inactive_threshold"] / 3600:
                health["recommendations"].append("Consider cleanup - worktree inactive")

            # Check environment health
            if metadata.requirements.uv_project:
                uv_health = await self._check_uv_health(metadata.worktree_path)
                health["metrics"]["uv"] = uv_health

                if not uv_health["healthy"]:
                    health["issues"].extend(uv_health["issues"])
                    health["recommendations"].append("Repair UV environment")

        except Exception as e:
            health["status"] = "error"
            health["issues"].append(f"Health check failed: {e!s}")
            self.logger.exception(f"Health check failed for {metadata.task_id}: {e!s}")

        return health

    async def _check_git_health(self, worktree_path: str) -> dict[str, Any]:
        """Check git repository health."""
        health = {"healthy": True, "issues": []}

        try:
            original_cwd = os.getcwd()
            os.chdir(worktree_path)

            # Check if git repository
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], check=False, capture_output=True, text=True,
            )

            if result.returncode != 0:
                health["healthy"] = False
                health["issues"].append("Not a git repository")
                return health

            # Check for conflicts
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                check=False, capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                health["healthy"] = False
                health["issues"].append("Git conflicts detected")

            # Check branch status
            result = subprocess.run(
                ["git", "status", "--porcelain"], check=False, capture_output=True, text=True,
            )

            health["uncommitted_changes"] = bool(result.stdout.strip())

        except Exception as e:
            health["healthy"] = False
            health["issues"].append(f"Git check failed: {e!s}")
        finally:
            os.chdir(original_cwd)

        return health

    async def _check_disk_usage(self, path: str) -> dict[str, Any]:
        """Check disk usage for worktree."""
        try:
            # Get directory size
            total_size = 0
            for dirpath, _dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, FileNotFoundError):
                        pass  # Skip files we can't access

            usage_mb = total_size / (1024 * 1024)

            return {
                "usage_mb": round(usage_mb, 2),
                "usage_bytes": total_size,
                "within_limits": usage_mb < (self.config["max_disk_usage_gb"] * 1024),
            }

        except Exception as e:
            self.logger.exception(f"Disk usage check failed: {e!s}")
            return {"usage_mb": 0, "usage_bytes": 0, "within_limits": True}

    async def _check_uv_health(self, worktree_path: str) -> dict[str, Any]:
        """Check UV environment health."""
        health = {"healthy": True, "issues": []}

        try:
            original_cwd = os.getcwd()
            os.chdir(worktree_path)

            # Check if UV project
            if not Path("pyproject.toml").exists():
                health["healthy"] = False
                health["issues"].append("Not a UV project (no pyproject.toml)")
                return health

            # Check virtual environment
            if not Path(".venv").exists():
                health["healthy"] = False
                health["issues"].append("UV virtual environment missing")
                return health

            # Test UV command
            result = subprocess.run(
                ["uv", "run", "python", "-c", "import sys; print(sys.version)"],
                check=False, capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                health["healthy"] = False
                health["issues"].append("UV environment not functional")

            health["python_version"] = (
                result.stdout.strip() if result.returncode == 0 else "unknown"
            )

        except Exception as e:
            health["healthy"] = False
            health["issues"].append(f"UV health check failed: {e!s}")
        finally:
            os.chdir(original_cwd)

        return health


class WorktreeCleanupManager:
    """Manages worktree cleanup and resource recovery."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or self._default_config()
        self.logger = logging.getLogger(__name__)

    def _default_config(self) -> dict[str, Any]:
        """Default cleanup configuration."""
        return {
            "preserve_uncommitted": True,
            "preserve_active_days": 1,
            "backup_before_cleanup": False,
            "aggressive_cleanup_threshold": 0.95,  # Disk usage threshold
        }

    async def cleanup_worktrees(
        self,
        worktrees: list[WorktreeMetadata],
        policy: str = "completed_tasks",
        retention_days: int = 7,
        dry_run: bool = False,
    ) -> CleanupResult:
        """Clean up worktrees based on policy."""
        self.logger.info(
            f"Starting cleanup with policy '{policy}', retention {retention_days} days",
        )

        result = CleanupResult(
            removed_count=0, preserved_count=0, disk_freed_mb=0, errors=[], summary={},
        )

        # Determine which worktrees to clean
        to_cleanup = await self._select_worktrees_for_cleanup(
            worktrees, policy, retention_days,
        )

        result.summary["total_evaluated"] = len(worktrees)
        result.summary["selected_for_cleanup"] = len(to_cleanup)

        # Perform cleanup
        for worktree in to_cleanup:
            try:
                if dry_run:
                    self.logger.info(
                        f"DRY RUN: Would remove worktree {worktree.task_id}",
                    )
                    result.removed_count += 1
                    result.disk_freed_mb += worktree.disk_usage_mb
                else:
                    cleanup_success = await self._remove_worktree(worktree)
                    if cleanup_success:
                        result.removed_count += 1
                        result.disk_freed_mb += worktree.disk_usage_mb
                        self.logger.info(f"Removed worktree {worktree.task_id}")
                    else:
                        result.errors.append(f"Failed to remove {worktree.task_id}")
                        result.preserved_count += 1

            except Exception as e:
                error_msg = f"Error cleaning {worktree.task_id}: {e!s}"
                result.errors.append(error_msg)
                result.preserved_count += 1
                self.logger.exception(error_msg)

        # Count preserved worktrees
        result.preserved_count += len(worktrees) - len(to_cleanup)

        result.summary["cleanup_policy"] = policy
        result.summary["retention_days"] = retention_days
        result.summary["dry_run"] = dry_run

        self.logger.info(
            f"Cleanup complete: removed {result.removed_count}, "
            f"preserved {result.preserved_count}, freed {result.disk_freed_mb}MB",
        )

        return result

    async def _select_worktrees_for_cleanup(
        self, worktrees: list[WorktreeMetadata], policy: str, retention_days: int,
    ) -> list[WorktreeMetadata]:
        """Select worktrees for cleanup based on policy."""
        to_cleanup = []
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        for worktree in worktrees:
            should_cleanup = False

            # Check basic age criteria
            if worktree.created_at < cutoff_date:
                if policy == "all_old":
                    should_cleanup = True
                elif policy == "completed_tasks":
                    # Check if task appears to be completed (simplified)
                    should_cleanup = await self._is_task_completed(worktree)
                elif policy == "inactive":
                    # Check if inactive
                    inactive_hours = (
                        datetime.now() - worktree.last_accessed
                    ).total_seconds() / 3600
                    should_cleanup = inactive_hours > (retention_days * 24)

            # Safety checks - never cleanup if preserve conditions met
            if should_cleanup and self.config["preserve_uncommitted"]:
                has_uncommitted = await self._has_uncommitted_changes(worktree)
                if has_uncommitted:
                    self.logger.info(
                        f"Preserving {worktree.task_id} - has uncommitted changes",
                    )
                    should_cleanup = False

            # Preserve active worktrees
            if should_cleanup:
                preserve_hours = self.config["preserve_active_days"] * 24
                hours_since_access = (
                    datetime.now() - worktree.last_accessed
                ).total_seconds() / 3600
                if hours_since_access < preserve_hours:
                    self.logger.info(f"Preserving {worktree.task_id} - recently active")
                    should_cleanup = False

            if should_cleanup:
                to_cleanup.append(worktree)

        return to_cleanup

    async def _is_task_completed(self, worktree: WorktreeMetadata) -> bool:
        """Check if task appears to be completed (simplified heuristic)."""
        try:
            # Check if branch has been merged or deleted upstream
            original_cwd = os.getcwd()
            os.chdir(worktree.worktree_path)

            # Fetch latest from origin
            subprocess.run(["git", "fetch", "origin"], check=False, capture_output=True)

            # Check if branch exists on origin
            result = subprocess.run(
                ["git", "ls-remote", "--heads", "origin", worktree.branch_name],
                check=False, capture_output=True,
                text=True,
            )

            branch_exists_remote = bool(result.stdout.strip())

            # If branch doesn't exist on remote, likely merged/deleted
            if not branch_exists_remote:
                return True

            # Check if ahead/behind main
            result = subprocess.run(
                [
                    "git",
                    "rev-list",
                    "--count",
                    "--left-right",
                    f"origin/{worktree.base_branch}...{worktree.branch_name}",
                ],
                check=False, capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                counts = result.stdout.strip().split("\t")
                if len(counts) == 2:
                    behind, ahead = counts
                    # If no commits ahead, might be merged
                    if ahead == "0":
                        return True

            return False

        except Exception as e:
            self.logger.warning(f"Could not determine task completion status: {e!s}")
            return False
        finally:
            os.chdir(original_cwd)

    async def _has_uncommitted_changes(self, worktree: WorktreeMetadata) -> bool:
        """Check if worktree has uncommitted changes."""
        try:
            original_cwd = os.getcwd()
            os.chdir(worktree.worktree_path)

            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"], check=False, capture_output=True, text=True,
            )

            return bool(result.stdout.strip())

        except Exception:
            return True  # Err on side of caution
        finally:
            os.chdir(original_cwd)

    async def _remove_worktree(self, worktree: WorktreeMetadata) -> bool:
        """Remove a worktree safely."""
        try:
            # Final safety check for uncommitted changes
            if self.config["preserve_uncommitted"]:
                if await self._has_uncommitted_changes(worktree):
                    self.logger.warning(
                        f"Skipping removal of {worktree.task_id} - uncommitted changes",
                    )
                    return False

            # Create backup if configured
            if self.config["backup_before_cleanup"]:
                await self._backup_worktree(worktree)

            # Remove git worktree
            result = subprocess.run(
                ["git", "worktree", "remove", "--force", worktree.worktree_path],
                check=False, capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self.logger.error(f"Git worktree remove failed: {result.stderr}")

                # Try manual removal as fallback
                if Path(worktree.worktree_path).exists():
                    shutil.rmtree(worktree.worktree_path)
                    self.logger.info(
                        f"Manually removed directory {worktree.worktree_path}",
                    )

            # Clean up tracking metadata
            await self._cleanup_metadata(worktree)

            return True

        except Exception as e:
            self.logger.exception(f"Failed to remove worktree {worktree.task_id}: {e!s}")
            return False

    async def _backup_worktree(self, worktree: WorktreeMetadata) -> None:
        """Create backup of worktree before removal."""
        try:
            backup_dir = Path(".gadugi/backups/worktrees")
            backup_dir.mkdir(parents=True, exist_ok=True)

            backup_name = (
                f"{worktree.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
            )
            backup_path = backup_dir / backup_name

            import tarfile

            with tarfile.open(backup_path, "w:gz") as tar:
                tar.add(worktree.worktree_path, arcname=worktree.task_id)

            self.logger.info(f"Created backup: {backup_path}")

        except Exception as e:
            self.logger.warning(f"Backup creation failed: {e!s}")

    async def _cleanup_metadata(self, worktree: WorktreeMetadata) -> None:
        """Clean up tracking metadata."""
        # Remove from registry (implementation depends on storage)


class WorktreeManagerEngine:
    """Main worktree manager engine."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or self._load_default_config()
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.environment_setup = WorktreeEnvironmentSetup(
            self.config.get("environment"),
        )
        self.health_monitor = WorktreeHealthMonitor(self.config.get("monitoring"))
        self.cleanup_manager = WorktreeCleanupManager(self.config.get("cleanup"))

        # Initialize worktree registry
        self.registry_path = Path(".gadugi/worktree-registry.json")
        self.worktrees: dict[str, WorktreeMetadata] = {}
        self._load_registry()

    async def _run_command_async(self, cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
        """Run command asynchronously and return result."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            # Create a CompletedProcess-like result for compatibility
            result = subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else ""
            )
            return result
        except asyncio.TimeoutError:
            raise subprocess.TimeoutExpired(cmd, timeout)

    def _load_default_config(self) -> dict[str, Any]:
        """Load default configuration."""
        return {
            "worktree": {
                "base_path": ".worktrees",
                "max_worktrees": 50,
                "default_cleanup_days": 7,
                "disk_limit_gb": 10,
                "auto_cleanup": True,
            },
            "environment": {
                "default_uv_extras": ["dev", "test"],
                "development_tools": ["pytest", "ruff", "mypy"],
                "container_policy": "standard",
            },
            "monitoring": {
                "health_check_interval": 300,
                "disk_check_threshold": 0.9,
                "inactive_threshold": 86400,
            },
            "cleanup": {
                "preserve_uncommitted": True,
                "preserve_active_days": 1,
                "backup_before_cleanup": False,
            },
        }

    def _load_registry(self) -> None:
        """Load worktree registry from disk."""
        try:
            if self.registry_path.exists():
                with open(self.registry_path) as f:
                    data = json.load(f)

                for task_id, wt_data in data.items():
                    # Convert datetime strings back to datetime objects
                    wt_data["created_at"] = datetime.fromisoformat(
                        wt_data["created_at"],
                    )
                    wt_data["last_accessed"] = datetime.fromisoformat(
                        wt_data["last_accessed"],
                    )
                    wt_data["status"] = WorktreeStatus(wt_data["status"])

                    # Convert requirements dict to dataclass
                    if "requirements" in wt_data:
                        req_data = wt_data["requirements"]
                        wt_data["requirements"] = WorktreeRequirements(**req_data)

                    self.worktrees[task_id] = WorktreeMetadata(**wt_data)

        except Exception as e:
            self.logger.warning(f"Failed to load registry: {e!s}")
            self.worktrees = {}

    def _save_registry(self) -> None:
        """Save worktree registry to disk."""
        try:
            # Ensure directory exists
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to serializable format
            data = {}
            for task_id, metadata in self.worktrees.items():
                wt_data = asdict(metadata)
                wt_data["created_at"] = metadata.created_at.isoformat()
                wt_data["last_accessed"] = metadata.last_accessed.isoformat()
                wt_data["status"] = metadata.status.value
                data[task_id] = wt_data

            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.exception(f"Failed to save registry: {e!s}")

    async def create_worktree(
        self,
        task_id: str,
        branch_name: str,
        base_branch: str = "main",
        requirements: WorktreeRequirements = None,
    ) -> WorktreeResult:
        """Create new worktree for task."""
        self.logger.info(f"Creating worktree for task {task_id}")

        if requirements is None:
            requirements = WorktreeRequirements()

        # Generate worktree path
        base_path = self.config["worktree"]["base_path"]
        worktree_path = str(Path(base_path) / task_id)

        # Check if worktree already exists
        if task_id in self.worktrees:
            existing = self.worktrees[task_id]
            if existing.status != WorktreeStatus.ERROR:
                return self._create_result(existing, "Worktree already exists")

        # Check limits
        if len(self.worktrees) >= self.config["worktree"]["max_worktrees"]:
            return WorktreeResult(
                task_id=task_id,
                worktree_path=worktree_path,
                branch_name=branch_name,
                status="error",
                environment={},
                metadata={},
                error_message="Maximum worktree limit reached",
            )

        # Create metadata
        metadata = WorktreeMetadata(
            task_id=task_id,
            worktree_path=worktree_path,
            branch_name=branch_name,
            base_branch=base_branch,
            base_commit="",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            status=WorktreeStatus.CREATING,
            requirements=requirements,
        )

        try:
            # Create git worktree
            success = await self._create_git_worktree(metadata)
            if not success:
                metadata.status = WorktreeStatus.ERROR
                metadata.error_message = "Failed to create git worktree"
                return self._create_result(metadata)

            # Set up environment
            environment = await self.environment_setup.setup_environment(
                worktree_path, requirements,
            )

            # Update status
            metadata.status = WorktreeStatus.READY
            metadata.last_accessed = datetime.now()

            # Register worktree
            self.worktrees[task_id] = metadata
            self._save_registry()

            return WorktreeResult(
                task_id=task_id,
                worktree_path=worktree_path,
                branch_name=branch_name,
                status="ready",
                environment=environment,
                metadata={
                    "created_at": metadata.created_at.isoformat(),
                    "base_commit": metadata.base_commit,
                    "disk_usage_mb": metadata.disk_usage_mb,
                    "estimated_cleanup": (
                        metadata.created_at
                        + timedelta(
                            days=self.config["worktree"]["default_cleanup_days"],
                        )
                    ).isoformat(),
                },
            )

        except Exception as e:
            metadata.status = WorktreeStatus.ERROR
            metadata.error_message = str(e)
            self.logger.exception(f"Worktree creation failed: {e!s}")
            return self._create_result(metadata)

    async def _create_git_worktree(self, metadata: WorktreeMetadata) -> bool:
        """Create git worktree with proper branch setup."""
        try:
            # Ensure base branch exists and is up to date
            subprocess.run(
                ["git", "fetch", "origin", metadata.base_branch],
                check=True,
                capture_output=True,
            )

            # Get base commit
            result = subprocess.run(
                ["git", "rev-parse", f"origin/{metadata.base_branch}"],
                capture_output=True,
                text=True,
                check=True,
            )
            metadata.base_commit = result.stdout.strip()

            # Create worktree with new branch
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-b",
                    metadata.branch_name,
                    metadata.worktree_path,
                    f"origin/{metadata.base_branch}",
                ],
                check=True,
                capture_output=True,
            )

            self.logger.info(f"Created git worktree at {metadata.worktree_path}")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.exception(f"Git worktree creation failed: {e.stderr}")
            return False

    def _create_result(
        self, metadata: WorktreeMetadata, error_message: str | None = None,
    ) -> WorktreeResult:
        """Create WorktreeResult from metadata."""
        return WorktreeResult(
            task_id=metadata.task_id,
            worktree_path=metadata.worktree_path,
            branch_name=metadata.branch_name,
            status=metadata.status.value,
            environment={},
            metadata={
                "created_at": metadata.created_at.isoformat(),
                "base_commit": metadata.base_commit,
                "disk_usage_mb": metadata.disk_usage_mb,
            },
            error_message=error_message or metadata.error_message,
        )

    async def list_worktrees(self) -> list[WorktreeMetadata]:
        """List all registered worktrees."""
        # Update last_accessed for health monitoring
        for metadata in self.worktrees.values():
            if Path(metadata.worktree_path).exists():
                # Check if there's recent activity (simplified)
                try:
                    mtime = Path(metadata.worktree_path).stat().st_mtime
                    last_modified = datetime.fromtimestamp(mtime)
                    metadata.last_accessed = max(metadata.last_accessed, last_modified)
                except OSError:
                    pass

        self._save_registry()
        return list(self.worktrees.values())

    async def cleanup_worktrees(
        self,
        policy: str = "completed_tasks",
        retention_days: int | None = None,
        dry_run: bool = False,
    ) -> CleanupResult:
        """Clean up worktrees based on policy."""
        if retention_days is None:
            retention_days = self.config["worktree"]["default_cleanup_days"]

        worktree_list = await self.list_worktrees()
        result = await self.cleanup_manager.cleanup_worktrees(
            worktree_list, policy, retention_days, dry_run,
        )

        # Update registry to remove cleaned worktrees
        if not dry_run:
            remaining_worktrees = {}
            for task_id, metadata in self.worktrees.items():
                if Path(metadata.worktree_path).exists():
                    remaining_worktrees[task_id] = metadata

            self.worktrees = remaining_worktrees
            self._save_registry()

        return result

    async def health_check(self, task_id: str | None = None) -> dict[str, Any]:
        """Check health of worktrees."""
        if task_id:
            # Check specific worktree
            if task_id not in self.worktrees:
                return {"error": f"Worktree {task_id} not found"}

            metadata = self.worktrees[task_id]
            return await self.health_monitor.check_worktree_health(metadata)
        # Check all worktrees
        results = {}
        for task_id, metadata in self.worktrees.items():
            results[task_id] = await self.health_monitor.check_worktree_health(
                metadata,
            )

        # Generate summary
        healthy_count = sum(1 for r in results.values() if r["status"] == "healthy")
        total_count = len(results)

        return {
            "summary": {
                "total_worktrees": total_count,
                "healthy": healthy_count,
                "unhealthy": total_count - healthy_count,
                "disk_usage_mb": sum(
                    m.disk_usage_mb for m in self.worktrees.values()
                ),
            },
            "worktrees": results,
        }


# CLI Interface
async def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="WorktreeManager Agent")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new worktree")
    create_parser.add_argument("--task-id", required=True, help="Task identifier")
    create_parser.add_argument("--branch-name", required=True, help="Branch name")
    create_parser.add_argument("--base-branch", default="main", help="Base branch")
    create_parser.add_argument(
        "--uv-project", action="store_true", help="Set up UV project",
    )
    create_parser.add_argument("--tools", help="Comma-separated development tools")

    # List command
    list_parser = subparsers.add_parser("list", help="List worktrees")
    list_parser.add_argument("--format", choices=["table", "json"], default="table")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up worktrees")
    cleanup_parser.add_argument(
        "--policy",
        default="completed_tasks",
        choices=["all_old", "completed_tasks", "inactive"],
    )
    cleanup_parser.add_argument("--retention-days", type=int, default=7)
    cleanup_parser.add_argument("--dry-run", action="store_true")

    # Health command
    health_parser = subparsers.add_parser("health", help="Check worktree health")
    health_parser.add_argument("--task-id", help="Check specific task")
    health_parser.add_argument(
        "--format", choices=["summary", "detailed"], default="summary",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    manager = WorktreeManagerEngine()

    if args.command == "create":
        requirements = WorktreeRequirements(
            uv_project=args.uv_project,
            development_tools=args.tools.split(",")
            if args.tools
            else ["pytest", "ruff"],
        )

        result = await manager.create_worktree(
            args.task_id, args.branch_name, args.base_branch, requirements,
        )


    elif args.command == "list":
        worktrees = await manager.list_worktrees()

        if args.format == "json":
            data = [asdict(wt) for wt in worktrees]
            for item in data:
                item["created_at"] = item["created_at"].isoformat()
                item["last_accessed"] = item["last_accessed"].isoformat()
                item["status"] = item["status"].value
        else:
            # Table format
            for wt in worktrees:
                (datetime.now() - wt.created_at).days

    elif args.command == "cleanup":
        result = await manager.cleanup_worktrees(
            args.policy, args.retention_days, args.dry_run,
        )

        if result.errors:
            for _error in result.errors:
                pass

    elif args.command == "health":
        health = await manager.health_check(args.task_id)

        if args.format == "detailed":
            pass
        elif "summary" in health:
            health["summary"]
        elif health.get("issues"):
            for _issue in health["issues"]:
                pass

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
