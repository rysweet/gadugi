#!/usr/bin/env python3
"""
Test suite for WorktreeManager component of OrchestratorAgent

Tests git worktree creation, management, and cleanup operations.
"""

import shutil
import subprocess

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch
import importlib.util

# Set up path for imports
orchestrator_dir = Path(__file__).parent.parent
components_dir = orchestrator_dir / 'components'

# Import worktree_manager directly (it doesn't have problematic relative imports)
spec = importlib.util.spec_from_file_location(
    "worktree_manager",
    components_dir / "worktree_manager.py"
)
worktree_manager_module = importlib.util.module_from_spec(spec)
sys.modules['worktree_manager'] = worktree_manager_module
spec.loader.exec_module(worktree_manager_module)

# Import the classes we need
WorktreeInfo = worktree_manager_module.WorktreeInfo
WorktreeManager = worktree_manager_module.WorktreeManager


class TestWorktreeManager(unittest.TestCase):
    """Test cases for WorktreeManager"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.worktrees_dir = self.project_root / ".worktrees"

        # Initialize a fake git repository
        self.init_fake_git_repo()

        self.manager = WorktreeManager(
            project_root=str(self.project_root),
            worktrees_dir=".worktrees"
        )

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def init_fake_git_repo(self):
        """Initialize a fake git repository for testing"""
        # Create basic git structure
        git_dir = self.project_root / ".git"
        git_dir.mkdir()

        # Create some basic files
        (self.project_root / "README.md").write_text("Test repository")
        (self.project_root / "pyproject.toml").write_text("[build-system]\nrequires = []")

    @patch('subprocess.run')
    def test_create_worktree_success(self, mock_run):
        """Test successful worktree creation"""
        # Mock successful git worktree add command
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        worktree_info = self.manager.create_worktree("task1", "Test Task")

        # Verify worktree info
        self.assertEqual(worktree_info.task_id, "task1")
        self.assertEqual(worktree_info.task_name, "Test Task")
        self.assertEqual(worktree_info.status, "active")
        self.assertEqual(worktree_info.branch_name, "feature/parallel-test-task-task1")

        # Verify git command was called correctly
        expected_cmd = [
            "git", "worktree", "add",
            str(self.worktrees_dir / "task-task1"),
            "-b", "feature/parallel-test-task-task1",
            "main"
        ]
        mock_run.assert_called_with(
            expected_cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=True
        )

        # Verify worktree is tracked
        self.assertIn("task1", self.manager.worktrees)

    @patch('subprocess.run')
    def test_create_worktree_failure(self, mock_run):
        """Test worktree creation failure"""
        # Mock failed git worktree add command
        error = subprocess.CalledProcessError(1, 'git worktree add')
        error.stderr = "fatal: 'feature/parallel-test-task-task1' is already checked out"
        mock_run.side_effect = error

        with self.assertRaises(RuntimeError) as context:
            self.manager.create_worktree("task1", "Test Task")

        self.assertIn("Failed to create worktree", str(context.exception))
        self.assertNotIn("task1", self.manager.worktrees)

    def test_list_worktrees(self):
        """Test listing worktrees"""
        # Add some worktrees manually to test
        worktree1 = WorktreeInfo(
            task_id="task1",
            task_name="Task 1",
            worktree_path=self.worktrees_dir / "task-task1",
            branch_name="feature/parallel-task1",
            status="active",
            created_at="2025-08-01T12:00:00"
        )

        worktree2 = WorktreeInfo(
            task_id="task2",
            task_name="Task 2",
            worktree_path=self.worktrees_dir / "task-task2",
            branch_name="feature/parallel-task2",
            status="completed",
            created_at="2025-08-01T12:30:00"
        )

        self.manager.worktrees = {"task1": worktree1, "task2": worktree2}

        worktrees = self.manager.list_worktrees()
        self.assertEqual(len(worktrees), 2)
        self.assertIn(worktree1, worktrees)
        self.assertIn(worktree2, worktrees)

    def test_get_worktree(self):
        """Test getting specific worktree"""
        worktree_info = WorktreeInfo(
            task_id="task1",
            task_name="Task 1",
            worktree_path=self.worktrees_dir / "task-task1",
            branch_name="feature/parallel-task1",
            status="active",
            created_at="2025-08-01T12:00:00"
        )

        self.manager.worktrees["task1"] = worktree_info

        retrieved = self.manager.get_worktree("task1")
        self.assertEqual(retrieved, worktree_info)

        # Test non-existent worktree
        not_found = self.manager.get_worktree("nonexistent")
        self.assertIsNone(not_found)

    def test_update_worktree_status(self):
        """Test updating worktree status"""
        worktree_info = WorktreeInfo(
            task_id="task1",
            task_name="Task 1",
            worktree_path=self.worktrees_dir / "task-task1",
            branch_name="feature/parallel-task1",
            status="active",
            created_at="2025-08-01T12:00:00"
        )

        self.manager.worktrees["task1"] = worktree_info

        # Update status
        self.manager.update_worktree_status("task1", "completed", pid=12345)

        self.assertEqual(worktree_info.status, "completed")
        self.assertEqual(worktree_info.pid, 12345)

    @patch('subprocess.run')
    def test_sync_worktree_from_main_success(self, mock_run):
        """Test successful worktree sync"""
        # Create a worktree
        worktree_info = WorktreeInfo(
            task_id="task1",
            task_name="Task 1",
            worktree_path=self.worktrees_dir / "task-task1",
            branch_name="feature/parallel-task1",
            status="active",
            created_at="2025-08-01T12:00:00"
        )
        self.manager.worktrees["task1"] = worktree_info

        # Mock successful git commands
        mock_run.return_value = MagicMock(returncode=0)

        result = self.manager.sync_worktree_from_main("task1")

        self.assertTrue(result)

        # Verify git commands were called
        expected_calls = [
            call(
                ["git", "fetch", "origin"],
                cwd=worktree_info.worktree_path,
                check=True,
                capture_output=True
            ),
            call(
                ["git", "merge", "origin/main"],
                cwd=worktree_info.worktree_path,
                check=True,
                capture_output=True
            )
        ]
        mock_run.assert_has_calls(expected_calls)

    @patch('subprocess.run')
    def test_sync_worktree_failure(self, mock_run):
        """Test worktree sync failure"""
        # Create a worktree
        worktree_info = WorktreeInfo(
            task_id="task1",
            task_name="Task 1",
            worktree_path=self.worktrees_dir / "task-task1",
            branch_name="feature/parallel-task1",
            status="active",
            created_at="2025-08-01T12:00:00"
        )
        self.manager.worktrees["task1"] = worktree_info

        # Mock failed git command
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git merge')

        result = self.manager.sync_worktree_from_main("task1")

        self.assertFalse(result)

    @patch('subprocess.run')
    def test_collect_worktree_results(self, mock_run):
        """Test collecting results from worktree"""
        # Create a worktree
        worktree_info = WorktreeInfo(
            task_id="task1",
            task_name="Task 1",
            worktree_path=self.worktrees_dir / "task-task1",
            branch_name="feature/parallel-task1",
            status="completed",
            created_at="2025-08-01T12:00:00"
        )
        self.manager.worktrees["task1"] = worktree_info

        # Create the worktree directory and some result files
        worktree_info.worktree_path.mkdir(parents=True)
        results_dir = worktree_info.worktree_path / "results"
        results_dir.mkdir()
        (results_dir / "output.json").write_text('{"status": "success"}')

        # Mock git commands for file changes and commits
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="file1.py\nfile2.py"),  # git diff --name-only
            MagicMock(returncode=0, stdout="abcd123 First commit\nefgh456 Second commit")  # git log --oneline
        ]

        results = self.manager.collect_worktree_results("task1")

        self.assertIsNotNone(results)
        self.assertEqual(results['task_id'], "task1")
        self.assertEqual(results['task_name'], "Task 1")
        self.assertEqual(results['status'], "completed")
        self.assertEqual(results['files_changed'], ["file1.py", "file2.py"])
        self.assertEqual(len(results['commits']), 2)
        self.assertEqual(len(results['artifacts']), 1)

    @patch('os.kill')
    @patch('subprocess.run')
    def test_cleanup_worktree_success(self, mock_run, mock_kill):
        """Test successful worktree cleanup"""
        # Create a worktree with a running process
        worktree_path = self.worktrees_dir / "task-task1"
        worktree_path.mkdir(parents=True)

        worktree_info = WorktreeInfo(
            task_id="task1",
            task_name="Task 1",
            worktree_path=worktree_path,
            branch_name="feature/parallel-task1",
            status="completed",
            created_at="2025-08-01T12:00:00",
            pid=12345
        )
        self.manager.worktrees["task1"] = worktree_info

        # Mock successful cleanup
        mock_run.return_value = MagicMock(returncode=0)

        result = self.manager.cleanup_worktree("task1")

        self.assertTrue(result)
        self.assertNotIn("task1", self.manager.worktrees)

        # Verify process was killed
        mock_kill.assert_called_once_with(12345, 15)

        # Verify git worktree remove was called
        mock_run.assert_called()

    @patch('subprocess.run')
    def test_cleanup_all_worktrees(self, mock_run):
        """Test cleanup of all worktrees"""
        # Create multiple worktrees
        for i in range(3):
            task_id = f"task{i+1}"
            worktree_path = self.worktrees_dir / f"task-{task_id}"
            worktree_path.mkdir(parents=True)

            worktree_info = WorktreeInfo(
                task_id=task_id,
                task_name=f"Task {i+1}",
                worktree_path=worktree_path,
                branch_name=f"feature/parallel-task{i+1}",
                status="completed",
                created_at="2025-08-01T12:00:00"
            )
            self.manager.worktrees[task_id] = worktree_info

        # Mock successful cleanup
        mock_run.return_value = MagicMock(returncode=0)

        cleaned = self.manager.cleanup_all_worktrees()

        self.assertEqual(cleaned, 3)
        self.assertEqual(len(self.manager.worktrees), 0)

    @patch('subprocess.run')
    def test_get_system_worktrees(self, mock_run):
        """Test getting system worktrees"""
        # Mock git worktree list output
        mock_output = """worktree /path/to/main
HEAD abc123
branch refs/heads/main

worktree /path/to/feature
HEAD def456
branch refs/heads/feature-branch

worktree /path/to/detached
HEAD ghi789
detached
"""
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)

        worktrees = self.manager.get_system_worktrees()

        self.assertEqual(len(worktrees), 3)

        # Check first worktree
        self.assertEqual(worktrees[0]['path'], '/path/to/main')
        self.assertEqual(worktrees[0]['head'], 'abc123')
        self.assertEqual(worktrees[0]['branch'], 'refs/heads/main')

        # Check detached worktree
        self.assertTrue(worktrees[2].get('detached', False))

    def test_validate_worktrees(self):
        """Test worktree validation"""
        # Create a worktree that exists in manager but not in system
        worktree_info = WorktreeInfo(
            task_id="task1",
            task_name="Task 1",
            worktree_path=self.worktrees_dir / "task-task1",
            branch_name="feature/parallel-task1",
            status="active",
            created_at="2025-08-01T12:00:00"
        )
        self.manager.worktrees["task1"] = worktree_info

        with patch.object(self.manager, 'get_system_worktrees') as mock_get_system:
            mock_get_system.return_value = []  # No system worktrees

            issues = self.manager.validate_worktrees()

            self.assertEqual(len(issues), 1)
            self.assertIn("not found in git worktree list", issues[0])

    def test_state_persistence(self):
        """Test state save and load"""
        # Create a worktree
        worktree_info = WorktreeInfo(
            task_id="task1",
            task_name="Task 1",
            worktree_path=self.worktrees_dir / "task-task1",
            branch_name="feature/parallel-task1",
            status="active",
            created_at="2025-08-01T12:00:00",
            pid=12345
        )
        self.manager.worktrees["task1"] = worktree_info

        # Save state
        self.manager._save_state()

        # Create new manager and load state
        new_manager = WorktreeManager(
            project_root=str(self.project_root),
            worktrees_dir=".worktrees"
        )

        # Verify state was loaded
        self.assertIn("task1", new_manager.worktrees)
        loaded_worktree = new_manager.worktrees["task1"]
        self.assertEqual(loaded_worktree.task_id, "task1")
        self.assertEqual(loaded_worktree.task_name, "Task 1")
        self.assertEqual(loaded_worktree.status, "active")
        self.assertEqual(loaded_worktree.pid, 12345)

    def test_get_status_summary(self):
        """Test status summary generation"""
        # Create worktrees with different statuses
        statuses = ['active', 'completed', 'failed', 'active']
        for i, status in enumerate(statuses):
            task_id = f"task{i+1}"
            worktree_info = WorktreeInfo(
                task_id=task_id,
                task_name=f"Task {i+1}",
                worktree_path=self.worktrees_dir / f"task-{task_id}",
                branch_name=f"feature/parallel-task{i+1}",
                status=status,
                created_at="2025-08-01T12:00:00"
            )
            self.manager.worktrees[task_id] = worktree_info

        summary = self.manager.get_status_summary()

        self.assertEqual(summary['total'], 4)
        self.assertEqual(summary['active'], 2)
        self.assertEqual(summary['completed'], 1)
        self.assertEqual(summary['failed'], 1)
        self.assertEqual(summary.get('cleaning', 0), 0)


class TestWorktreeManagerIntegration(unittest.TestCase):
    """Integration tests for WorktreeManager with actual git operations"""

    def setUp(self):
        """Set up test environment with real git repository"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Initialize real git repository
        subprocess.run(['git', 'init'], cwd=self.project_root, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=self.project_root, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=self.project_root, check=True)

        # Create and commit initial file
        (self.project_root / 'README.md').write_text('Test repository')
        subprocess.run(['git', 'add', 'README.md'], cwd=self.project_root, check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=self.project_root, check=True)

        self.manager = WorktreeManager(
            project_root=str(self.project_root),
            worktrees_dir=".worktrees"
        )

    def tearDown(self):
        """Clean up test environment"""
        # Clean up any worktrees first
        try:
            self.manager.cleanup_all_worktrees(force=True)
        except:
            pass  # Ignore cleanup errors

        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @unittest.skipIf(not shutil.which('git'), "Git not available")
    def test_real_worktree_creation_and_cleanup(self):
        """Test actual worktree creation and cleanup with git"""
        # Create worktree
        worktree_info = self.manager.create_worktree("test-task", "Test Task")

        # Verify worktree was created
        self.assertTrue(worktree_info.worktree_path.exists())
        self.assertEqual(worktree_info.task_id, "test-task")
        self.assertEqual(worktree_info.status, "active")

        # Verify it appears in git worktree list
        result = subprocess.run(
            ['git', 'worktree', 'list'],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        self.assertIn(str(worktree_info.worktree_path), result.stdout)

        # Test cleanup
        success = self.manager.cleanup_worktree("test-task")
        self.assertTrue(success)

        # Verify worktree was removed
        self.assertFalse(worktree_info.worktree_path.exists())
        self.assertNotIn("test-task", self.manager.worktrees)

        # Verify it's removed from git worktree list
        result = subprocess.run(
            ['git', 'worktree', 'list'],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        self.assertNotIn(str(worktree_info.worktree_path), result.stdout)


if __name__ == '__main__':
    import shutil

    # Skip integration tests if git is not available
    if not shutil.which('git'):
        print("Warning: Git not available, skipping integration tests")

    unittest.main()
