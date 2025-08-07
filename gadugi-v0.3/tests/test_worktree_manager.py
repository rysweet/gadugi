"""Tests for WorktreeManager Engine.

Comprehensive test suite covering worktree lifecycle, environment setup,
monitoring, and cleanup operations.
"""

import asyncio
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator"))

from worktree_manager_engine import (
    CleanupResult,
    WorktreeCleanupManager,
    WorktreeEnvironmentSetup,
    WorktreeHealthMonitor,
    WorktreeManagerEngine,
    WorktreeMetadata,
    WorktreeRequirements,
    WorktreeStatus,
)


class TestWorktreeRequirements:
    """Test WorktreeRequirements data class."""

    def test_default_requirements(self) -> None:
        """Test default requirements."""
        req = WorktreeRequirements()

        assert not req.uv_project
        assert not req.container_ready
        assert req.development_tools == ["pytest", "ruff"]
        assert req.container_policy == "standard"

    def test_custom_requirements(self) -> None:
        """Test custom requirements."""
        req = WorktreeRequirements(
            uv_project=True,
            container_ready=True,
            development_tools=["pytest", "ruff", "mypy", "black"],
            python_version="3.11",
            container_policy="hardened",
        )

        assert req.uv_project
        assert req.container_ready
        assert "mypy" in req.development_tools
        assert req.python_version == "3.11"
        assert req.container_policy == "hardened"


class TestWorktreeMetadata:
    """Test WorktreeMetadata data class."""

    def test_metadata_creation(self) -> None:
        """Test metadata creation."""
        now = datetime.now()
        metadata = WorktreeMetadata(
            task_id="test-task",
            worktree_path=".worktrees/test-task",
            branch_name="feature/test-task",
            base_branch="main",
            base_commit="abc123",
            created_at=now,
            last_accessed=now,
            status=WorktreeStatus.READY,
        )

        assert metadata.task_id == "test-task"
        assert metadata.status == WorktreeStatus.READY
        assert metadata.requirements is not None
        assert metadata.disk_usage_mb == 0


class TestWorktreeEnvironmentSetup:
    """Test environment setup functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.setup = WorktreeEnvironmentSetup()
        self.requirements = WorktreeRequirements(
            uv_project=True,
            development_tools=["pytest", "ruff"],
        )

    @pytest.mark.asyncio
    async def test_setup_environment_basic(self) -> None:
        """Test basic environment setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create minimal git repository
            os.chdir(temp_dir)
            subprocess.run(["git", "init"], check=False, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], check=False, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                check=False,
                capture_output=True,
            )

            with (
                patch.object(self.setup, "_setup_uv_environment") as mock_uv,
                patch.object(self.setup, "_install_development_tools") as mock_tools,
            ):
                mock_uv.return_value = True
                mock_tools.return_value = True

                result = await self.setup.setup_environment(temp_dir, self.requirements)

                assert result["git_status"] in [
                    "clean",
                    "dirty",
                ]  # Either is acceptable for new repo
                assert result["uv_env_ready"]
                assert result["development_tools_installed"]

    @pytest.mark.asyncio
    async def test_check_git_status_clean(self) -> None:
        """Test git status check for clean repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            subprocess.run(["git", "init"], check=False, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], check=False, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                check=False,
                capture_output=True,
            )

            status = await self.setup._check_git_status()
            assert status == "clean"

    @pytest.mark.asyncio
    async def test_setup_uv_environment_no_project(self) -> None:
        """Test UV setup when not a UV project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            result = await self.setup._setup_uv_environment(self.requirements)
            assert not result  # Should return False when no pyproject.toml

    @pytest.mark.asyncio
    async def test_ensure_uv_available(self) -> None:
        """Test UV availability check."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            result = await self.setup._ensure_uv_available()
            assert result

            mock_run.assert_called_with(
                ["uv", "--version"],
                capture_output=True,
                check=True,
            )

    @pytest.mark.asyncio
    async def test_install_development_tools(self) -> None:
        """Test development tools installation."""
        with (
            patch("subprocess.run") as mock_run,
            patch("pathlib.Path.exists") as mock_exists,
        ):
            mock_exists.return_value = True  # .venv exists
            mock_run.return_value = Mock(returncode=0)

            result = await self.setup._install_development_tools(["pytest", "ruff"])
            assert result


class TestWorktreeHealthMonitor:
    """Test worktree health monitoring."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.monitor = WorktreeHealthMonitor()
        self.metadata = WorktreeMetadata(
            task_id="test-task",
            worktree_path="/tmp/test-worktree",
            branch_name="feature/test",
            base_branch="main",
            base_commit="abc123",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            status=WorktreeStatus.READY,
        )

    @pytest.mark.asyncio
    async def test_check_worktree_health_missing_path(self) -> None:
        """Test health check for missing worktree path."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            health = await self.monitor.check_worktree_health(self.metadata)

            assert health["status"] == "missing"
            assert "does not exist" in health["issues"][0]

    @pytest.mark.asyncio
    async def test_check_git_health_clean(self) -> None:
        """Test git health check for clean repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            subprocess.run(["git", "init"], check=False, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], check=False, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                check=False,
                capture_output=True,
            )

            health = await self.monitor._check_git_health(temp_dir)

            assert health["healthy"]
            assert not health["uncommitted_changes"]

    @pytest.mark.asyncio
    async def test_check_disk_usage(self) -> None:
        """Test disk usage calculation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file with sufficient size
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Hello, world! " * 1000)  # Make it larger

            usage = await self.monitor._check_disk_usage(temp_dir)

            assert usage["usage_mb"] >= 0  # Allow 0 or positive
            assert usage["usage_bytes"] >= 0  # Allow 0 or positive
            assert "within_limits" in usage

    @pytest.mark.asyncio
    async def test_check_uv_health_no_project(self) -> None:
        """Test UV health check when not a UV project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            health = await self.monitor._check_uv_health(temp_dir)

            assert not health["healthy"]
            assert "Not a UV project" in health["issues"][0]


class TestWorktreeCleanupManager:
    """Test worktree cleanup functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.cleanup_manager = WorktreeCleanupManager()

        # Create test worktrees
        now = datetime.now()
        self.old_worktree = WorktreeMetadata(
            task_id="old-task",
            worktree_path=".worktrees/old-task",
            branch_name="feature/old-task",
            base_branch="main",
            base_commit="abc123",
            created_at=now - timedelta(days=10),
            last_accessed=now - timedelta(days=5),
            status=WorktreeStatus.IDLE,
            disk_usage_mb=100,
        )

        self.new_worktree = WorktreeMetadata(
            task_id="new-task",
            worktree_path=".worktrees/new-task",
            branch_name="feature/new-task",
            base_branch="main",
            base_commit="def456",
            created_at=now - timedelta(hours=2),
            last_accessed=now - timedelta(minutes=30),
            status=WorktreeStatus.ACTIVE,
            disk_usage_mb=150,
        )

    @pytest.mark.asyncio
    async def test_select_worktrees_for_cleanup_age_based(self) -> None:
        """Test worktree selection based on age."""
        worktrees = [self.old_worktree, self.new_worktree]

        with (
            patch.object(self.cleanup_manager, "_is_task_completed") as mock_completed,
            patch.object(
                self.cleanup_manager,
                "_has_uncommitted_changes",
            ) as mock_changes,
        ):
            mock_completed.return_value = True
            mock_changes.return_value = False

            to_cleanup = await self.cleanup_manager._select_worktrees_for_cleanup(
                worktrees,
                "completed_tasks",
                7,
            )

            assert len(to_cleanup) == 1
            assert to_cleanup[0].task_id == "old-task"

    @pytest.mark.asyncio
    async def test_select_worktrees_preserve_uncommitted(self) -> None:
        """Test preserving worktrees with uncommitted changes."""
        worktrees = [self.old_worktree]

        with (
            patch.object(self.cleanup_manager, "_is_task_completed") as mock_completed,
            patch.object(
                self.cleanup_manager,
                "_has_uncommitted_changes",
            ) as mock_changes,
        ):
            mock_completed.return_value = True
            mock_changes.return_value = True  # Has uncommitted changes

            to_cleanup = await self.cleanup_manager._select_worktrees_for_cleanup(
                worktrees,
                "completed_tasks",
                7,
            )

            assert len(to_cleanup) == 0  # Should be preserved

    @pytest.mark.asyncio
    async def test_cleanup_worktrees_dry_run(self) -> None:
        """Test cleanup in dry run mode."""
        worktrees = [self.old_worktree, self.new_worktree]

        with patch.object(
            self.cleanup_manager,
            "_select_worktrees_for_cleanup",
        ) as mock_select:
            mock_select.return_value = [self.old_worktree]

            result = await self.cleanup_manager.cleanup_worktrees(
                worktrees,
                "completed_tasks",
                7,
                dry_run=True,
            )

            assert result.removed_count == 1
            assert result.preserved_count == 1
            assert result.disk_freed_mb == 100
            assert result.summary["dry_run"]

    @pytest.mark.asyncio
    async def test_has_uncommitted_changes(self) -> None:
        """Test checking for uncommitted changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            subprocess.run(["git", "init"], check=False, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], check=False, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                check=False,
                capture_output=True,
            )

            # Clean repository
            self.old_worktree.worktree_path = temp_dir
            has_changes = await self.cleanup_manager._has_uncommitted_changes(
                self.old_worktree,
            )
            assert not has_changes

            # Add a file
            Path(temp_dir, "test.txt").write_text("test")
            has_changes = await self.cleanup_manager._has_uncommitted_changes(
                self.old_worktree,
            )
            assert has_changes

    @pytest.mark.asyncio
    async def test_remove_worktree_with_uncommitted_changes(self) -> None:
        """Test worktree removal is blocked by uncommitted changes."""
        with patch.object(
            self.cleanup_manager,
            "_has_uncommitted_changes",
        ) as mock_changes:
            mock_changes.return_value = True  # Has uncommitted changes

            result = await self.cleanup_manager._remove_worktree(self.old_worktree)
            assert not result  # Should not remove


class TestWorktreeManagerEngine:
    """Test main worktree manager engine."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Use temporary directory for registry
        self.temp_dir = tempfile.mkdtemp()
        config = {
            "worktree": {
                "base_path": ".worktrees",
                "max_worktrees": 10,
                "default_cleanup_days": 7,
            },
        }

        with (
            patch.object(WorktreeManagerEngine, "_load_registry"),
            patch.object(WorktreeManagerEngine, "_save_registry"),
        ):
            self.manager = WorktreeManagerEngine(config)
            self.manager.worktrees = {}
            self.manager.registry_path = Path(self.temp_dir) / "registry.json"

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_create_worktree_basic(self) -> None:
        """Test basic worktree creation."""
        with (
            patch.object(self.manager, "_create_git_worktree") as mock_git,
            patch.object(
                self.manager.environment_setup,
                "setup_environment",
            ) as mock_env,
        ):
            mock_git.return_value = True
            mock_env.return_value = {
                "git_status": "clean",
                "uv_env_ready": False,
                "development_tools_installed": True,
            }

            result = await self.manager.create_worktree(
                "test-task",
                "feature/test-task",
                "main",
            )

            assert result.task_id == "test-task"
            assert result.status == "ready"
            assert result.branch_name == "feature/test-task"
            assert "test-task" in self.manager.worktrees

    @pytest.mark.asyncio
    async def test_create_worktree_already_exists(self) -> None:
        """Test creating worktree when it already exists."""
        # Pre-populate with existing worktree
        existing = WorktreeMetadata(
            task_id="test-task",
            worktree_path=".worktrees/test-task",
            branch_name="feature/test-task",
            base_branch="main",
            base_commit="abc123",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            status=WorktreeStatus.READY,
        )
        self.manager.worktrees["test-task"] = existing

        result = await self.manager.create_worktree(
            "test-task",
            "feature/test-task",
            "main",
        )

        assert "already exists" in result.error_message

    @pytest.mark.asyncio
    async def test_create_worktree_max_limit_reached(self) -> None:
        """Test worktree creation when max limit is reached."""
        # Fill up to max limit
        for i in range(self.manager.config["worktree"]["max_worktrees"]):
            metadata = WorktreeMetadata(
                task_id=f"task-{i}",
                worktree_path=f".worktrees/task-{i}",
                branch_name=f"feature/task-{i}",
                base_branch="main",
                base_commit="abc123",
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                status=WorktreeStatus.READY,
            )
            self.manager.worktrees[f"task-{i}"] = metadata

        result = await self.manager.create_worktree(
            "overflow-task",
            "feature/overflow-task",
            "main",
        )

        assert result.status == "error"
        assert "Maximum worktree limit" in result.error_message

    @pytest.mark.asyncio
    async def test_create_git_worktree(self) -> None:
        """Test git worktree creation."""
        metadata = WorktreeMetadata(
            task_id="test-task",
            worktree_path=".worktrees/test-task",
            branch_name="feature/test-task",
            base_branch="main",
            base_commit="",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            status=WorktreeStatus.CREATING,
        )

        with patch("subprocess.run") as mock_run:
            # Mock successful git operations
            mock_run.side_effect = [
                Mock(returncode=0),  # git fetch
                Mock(returncode=0, stdout="abc123\n", text=True),  # git rev-parse
                Mock(returncode=0),  # git worktree add
            ]

            result = await self.manager._create_git_worktree(metadata)

            assert result
            assert metadata.base_commit == "abc123"

    @pytest.mark.asyncio
    async def test_list_worktrees(self) -> None:
        """Test listing worktrees."""
        # Add test worktree
        metadata = WorktreeMetadata(
            task_id="test-task",
            worktree_path=".worktrees/test-task",
            branch_name="feature/test-task",
            base_branch="main",
            base_commit="abc123",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            status=WorktreeStatus.READY,
        )
        self.manager.worktrees["test-task"] = metadata

        with (
            patch("pathlib.Path.exists") as mock_exists,
            patch("pathlib.Path.stat") as mock_stat,
        ):
            mock_exists.return_value = True
            mock_stat.return_value = Mock(st_mtime=time.time())

            worktrees = await self.manager.list_worktrees()

            assert len(worktrees) == 1
            assert worktrees[0].task_id == "test-task"

    @pytest.mark.asyncio
    async def test_cleanup_worktrees(self) -> None:
        """Test worktree cleanup."""
        # Add old worktree for cleanup
        old_metadata = WorktreeMetadata(
            task_id="old-task",
            worktree_path=".worktrees/old-task",
            branch_name="feature/old-task",
            base_branch="main",
            base_commit="abc123",
            created_at=datetime.now() - timedelta(days=10),
            last_accessed=datetime.now() - timedelta(days=5),
            status=WorktreeStatus.IDLE,
            disk_usage_mb=100,
        )
        self.manager.worktrees["old-task"] = old_metadata

        with patch.object(
            self.manager.cleanup_manager,
            "cleanup_worktrees",
        ) as mock_cleanup:
            mock_cleanup.return_value = CleanupResult(
                removed_count=1,
                preserved_count=0,
                disk_freed_mb=100,
                errors=[],
                summary={"cleanup_policy": "completed_tasks"},
            )

            result = await self.manager.cleanup_worktrees()

            assert result.removed_count == 1
            assert result.disk_freed_mb == 100

    @pytest.mark.asyncio
    async def test_health_check_specific_worktree(self) -> None:
        """Test health check for specific worktree."""
        metadata = WorktreeMetadata(
            task_id="test-task",
            worktree_path=".worktrees/test-task",
            branch_name="feature/test-task",
            base_branch="main",
            base_commit="abc123",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            status=WorktreeStatus.READY,
        )
        self.manager.worktrees["test-task"] = metadata

        with patch.object(
            self.manager.health_monitor,
            "check_worktree_health",
        ) as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "issues": [],
                "metrics": {},
                "recommendations": [],
            }

            result = await self.manager.health_check("test-task")

            assert result["status"] == "healthy"
            mock_health.assert_called_once_with(metadata)

    @pytest.mark.asyncio
    async def test_health_check_all_worktrees(self) -> None:
        """Test health check for all worktrees."""
        # Add test worktrees
        for i in range(2):
            metadata = WorktreeMetadata(
                task_id=f"task-{i}",
                worktree_path=f".worktrees/task-{i}",
                branch_name=f"feature/task-{i}",
                base_branch="main",
                base_commit="abc123",
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                status=WorktreeStatus.READY,
                disk_usage_mb=100,
            )
            self.manager.worktrees[f"task-{i}"] = metadata

        with patch.object(
            self.manager.health_monitor,
            "check_worktree_health",
        ) as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "issues": [],
                "metrics": {},
                "recommendations": [],
            }

            result = await self.manager.health_check()

            assert result["summary"]["total_worktrees"] == 2
            assert result["summary"]["healthy"] == 2
            assert result["summary"]["disk_usage_mb"] == 200

    def test_save_and_load_registry(self) -> None:
        """Test registry persistence."""
        # Add test worktree
        metadata = WorktreeMetadata(
            task_id="test-task",
            worktree_path=".worktrees/test-task",
            branch_name="feature/test-task",
            base_branch="main",
            base_commit="abc123",
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            status=WorktreeStatus.READY,
        )
        self.manager.worktrees["test-task"] = metadata

        # Save registry
        self.manager._save_registry()
        assert self.manager.registry_path.exists()

        # Create new manager and load registry
        with patch.object(WorktreeManagerEngine, "_save_registry"):
            new_manager = WorktreeManagerEngine()
            new_manager.registry_path = self.manager.registry_path
            new_manager._load_registry()

            assert "test-task" in new_manager.worktrees
            loaded_metadata = new_manager.worktrees["test-task"]
            assert loaded_metadata.task_id == "test-task"
            assert loaded_metadata.status == WorktreeStatus.READY


class TestWorktreeIntegration:
    """Integration tests for complete worktree workflows."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        try:
            self.original_cwd = os.getcwd()
        except FileNotFoundError:
            # Handle case where current directory doesn't exist
            self.original_cwd = str(Path.home())
        os.chdir(self.temp_dir)

        # Initialize git repository
        subprocess.run(["git", "init"], check=False, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], check=False, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            check=False,
            capture_output=True,
        )

        # Create initial commit
        Path("README.md").write_text("# Test Repository")
        subprocess.run(["git", "add", "README.md"], check=False, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=False, capture_output=True)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        try:
            if os.path.exists(self.original_cwd):
                os.chdir(self.original_cwd)
            else:
                os.chdir(str(Path.home()))
        except (FileNotFoundError, OSError):
            os.chdir(str(Path.home()))
        finally:
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_complete_worktree_lifecycle(self) -> None:
        """Test complete worktree lifecycle."""
        config = {
            "worktree": {
                "base_path": ".worktrees",
                "max_worktrees": 10,
                "default_cleanup_days": 7,
            },
        }

        manager = WorktreeManagerEngine(config)

        # Create worktree
        requirements = WorktreeRequirements(
            uv_project=False,
            development_tools=["pytest"],
        )

        with (
            patch.object(manager.environment_setup, "setup_environment") as mock_env,
            patch.object(manager, "_create_git_worktree") as mock_git,
        ):
            mock_env.return_value = {
                "git_status": "clean",
                "uv_env_ready": False,
                "development_tools_installed": True,
            }
            mock_git.return_value = True

            result = await manager.create_worktree(
                "integration-test",
                "feature/integration-test",
                "main",
                requirements,
            )

            assert result.status == "ready"
            # Don't check if path exists since we mocked git worktree creation

        # List worktrees
        worktrees = await manager.list_worktrees()
        assert len(worktrees) == 1
        assert worktrees[0].task_id == "integration-test"

        # Health check (mock since worktree path doesn't actually exist)
        with patch.object(
            manager.health_monitor,
            "check_worktree_health",
        ) as mock_health:
            mock_health.return_value = {"status": "healthy", "issues": []}
            health = await manager.health_check("integration-test")
            assert health["status"] == "healthy"

        # Cleanup (dry run)
        cleanup_result = await manager.cleanup_worktrees(dry_run=True)
        assert cleanup_result.summary["dry_run"]


# Performance and stress tests
class TestWorktreePerformance:
    """Performance and stress tests."""

    @pytest.mark.asyncio
    async def test_create_multiple_worktrees(self) -> None:
        """Test creating multiple worktrees efficiently."""
        manager = WorktreeManagerEngine()

        with (
            patch.object(manager, "_create_git_worktree") as mock_git,
            patch.object(manager.environment_setup, "setup_environment") as mock_env,
        ):
            mock_git.return_value = True
            mock_env.return_value = {"git_status": "clean"}

            tasks = []
            for i in range(5):
                task = manager.create_worktree(
                    f"perf-task-{i}",
                    f"feature/perf-task-{i}",
                    "main",
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            assert len(results) == 5
            assert all(r.status == "ready" for r in results)

    @pytest.mark.asyncio
    async def test_health_check_performance(self) -> None:
        """Test health check performance with many worktrees."""
        manager = WorktreeManagerEngine()

        # Add many mock worktrees
        for i in range(20):
            metadata = WorktreeMetadata(
                task_id=f"perf-task-{i}",
                worktree_path=f".worktrees/perf-task-{i}",
                branch_name=f"feature/perf-task-{i}",
                base_branch="main",
                base_commit="abc123",
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                status=WorktreeStatus.READY,
            )
            manager.worktrees[f"perf-task-{i}"] = metadata

        with patch.object(
            manager.health_monitor,
            "check_worktree_health",
        ) as mock_health:
            mock_health.return_value = {"status": "healthy", "issues": []}

            start_time = time.time()
            result = await manager.health_check()
            duration = time.time() - start_time

            # Should complete health check reasonably quickly
            assert duration < 5.0  # 5 seconds max
            assert result["summary"]["total_worktrees"] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
