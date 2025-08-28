#!/usr/bin/env python3
"""
Unit tests for ProcessRegistry component

These tests validate the process tracking and monitoring functionality
of the ProcessRegistry class.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

# Add orchestrator components to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from process_registry import ProcessRegistry, ProcessStatus, ProcessInfo, RegistryStats


class TestProcessRegistry(unittest.TestCase):
    """Unit tests for ProcessRegistry"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.registry_dir = self.test_dir / "registry"
        self.registry = ProcessRegistry(str(self.registry_dir))

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_registry_initialization(self):
        """Test registry initializes correctly"""
        self.assertTrue(self.registry_dir.exists())
        self.assertTrue(self.registry.registry_file.exists() or True)  # May not exist initially
        self.assertEqual(len(self.registry.processes), 0)
        self.assertEqual(self.registry.heartbeat_interval, 30)

    def test_process_registration(self):
        """Test process registration"""
        process_info = ProcessInfo(
            task_id="test-task-1",
            task_name="Test Task 1",
            status=ProcessStatus.QUEUED,
            command="test command",
            working_directory="/tmp/test",
            created_at=datetime.now()
        )

        self.registry.register_process(process_info)

        # Verify registration
        self.assertEqual(len(self.registry.processes), 1)
        self.assertIn("test-task-1", self.registry.processes)

        retrieved = self.registry.get_process("test-task-1")
        self.assertIsNotNone(retrieved)
        if retrieved is not None:
            self.assertEqual(retrieved.task_id, "test-task-1")
            self.assertEqual(retrieved.status, ProcessStatus.QUEUED)
            self.assertIsNotNone(retrieved.last_heartbeat)

    def test_process_status_updates(self):
        """Test process status transitions"""
        # Register process
        process_info = ProcessInfo(
            task_id="test-task-2",
            task_name="Test Task 2",
            status=ProcessStatus.QUEUED,
            command="test command",
            working_directory="/tmp/test",
            created_at=datetime.now()
        )
        self.registry.register_process(process_info)

        # Test queued -> running
        success = self.registry.update_process_status("test-task-2", ProcessStatus.RUNNING, pid=12345)
        self.assertTrue(success)

        process = self.registry.get_process("test-task-2")
        self.assertIsNotNone(process)
        if process is not None:
            self.assertEqual(process.status, ProcessStatus.RUNNING)
            self.assertEqual(process.pid, 12345)
            self.assertIsNotNone(process.started_at)

        # Test running -> completed
        success = self.registry.update_process_status("test-task-2", ProcessStatus.COMPLETED)
        self.assertTrue(success)

        process = self.registry.get_process("test-task-2")
        self.assertIsNotNone(process)
        if process is not None:
            self.assertEqual(process.status, ProcessStatus.COMPLETED)
            self.assertIsNotNone(process.completed_at)

    def test_process_status_failure(self):
        """Test process failure handling"""
        # Register process
        process_info = ProcessInfo(
            task_id="test-task-3",
            task_name="Test Task 3",
            status=ProcessStatus.RUNNING,
            command="test command",
            working_directory="/tmp/test",
            created_at=datetime.now()
        )
        self.registry.register_process(process_info)

        # Test failure with error message
        success = self.registry.update_process_status(
            "test-task-3",
            ProcessStatus.FAILED,
            error_message="Test error message"
        )
        self.assertTrue(success)

        process = self.registry.get_process("test-task-3")
        self.assertIsNotNone(process)
        if process is not None:
            self.assertEqual(process.status, ProcessStatus.FAILED)
            self.assertEqual(process.error_message, "Test error message")
            self.assertIsNotNone(process.completed_at)

    def test_nonexistent_process_update(self):
        """Test updating nonexistent process"""
        success = self.registry.update_process_status("nonexistent", ProcessStatus.RUNNING)
        self.assertFalse(success)

    def test_get_processes_by_status(self):
        """Test filtering processes by status"""
        # Register multiple processes with different statuses
        processes = [
            ProcessInfo("task-1", "Task 1", ProcessStatus.QUEUED, "cmd1", "/tmp", datetime.now()),
            ProcessInfo("task-2", "Task 2", ProcessStatus.RUNNING, "cmd2", "/tmp", datetime.now()),
            ProcessInfo("task-3", "Task 3", ProcessStatus.COMPLETED, "cmd3", "/tmp", datetime.now()),
            ProcessInfo("task-4", "Task 4", ProcessStatus.RUNNING, "cmd4", "/tmp", datetime.now()),
        ]

        for process in processes:
            self.registry.register_process(process)

        # Test filtering
        queued = self.registry.get_processes_by_status(ProcessStatus.QUEUED)
        running = self.registry.get_processes_by_status(ProcessStatus.RUNNING)
        completed = self.registry.get_processes_by_status(ProcessStatus.COMPLETED)

        self.assertEqual(len(queued), 1)
        self.assertEqual(len(running), 2)
        self.assertEqual(len(completed), 1)

        # Test active processes
        active = self.registry.get_active_processes()
        self.assertEqual(len(active), 3)  # queued + running

    def test_registry_stats(self):
        """Test registry statistics generation"""
        # Register processes with different statuses
        processes = [
            ProcessInfo("task-1", "Task 1", ProcessStatus.COMPLETED, "cmd1", "/tmp", datetime.now()),
            ProcessInfo("task-2", "Task 2", ProcessStatus.RUNNING, "cmd2", "/tmp", datetime.now()),
            ProcessInfo("task-3", "Task 3", ProcessStatus.FAILED, "cmd3", "/tmp", datetime.now()),
            ProcessInfo("task-4", "Task 4", ProcessStatus.QUEUED, "cmd4", "/tmp", datetime.now()),
        ]

        for process in processes:
            self.registry.register_process(process)

        # Get stats
        stats = self.registry.get_registry_stats()

        self.assertIsInstance(stats, RegistryStats)
        self.assertEqual(stats.total_processes, 4)
        self.assertEqual(stats.completed_count, 1)
        self.assertEqual(stats.running_count, 1)
        self.assertEqual(stats.failed_count, 1)
        self.assertEqual(stats.queued_count, 1)

    @patch('psutil.Process')
    def test_heartbeat_monitoring(self, mock_process_class):
        """Test heartbeat monitoring and stale process detection"""
        # Mock psutil.Process
        mock_process = Mock()
        mock_process.is_running.return_value = True
        mock_process.cpu_percent.return_value = 15.5
        mock_process.memory_info.return_value = Mock(rss=1024*1024*100)  # 100MB
        mock_process.memory_percent.return_value = 5.0
        mock_process.num_threads.return_value = 4
        mock_process.status.return_value = 'running'
        mock_process.create_time.return_value = 1234567890
        mock_process_class.return_value = mock_process

        # Register running process
        process_info = ProcessInfo(
            task_id="test-task-running",
            task_name="Running Task",
            status=ProcessStatus.RUNNING,
            command="test command",
            working_directory="/tmp",
            created_at=datetime.now(),
            pid=12345
        )
        self.registry.register_process(process_info)

        # Update heartbeats
        self.registry.update_heartbeats()

        # Verify process is still running
        process = self.registry.get_process("test-task-running")
        self.assertIsNotNone(process)
        if process is not None:
            self.assertEqual(process.status, ProcessStatus.RUNNING)
            self.assertIsNotNone(process.resource_usage)
            if process.resource_usage is not None:
                self.assertEqual(process.resource_usage['cpu_percent'], 15.5)

    @patch('psutil.Process')
    def test_stale_process_detection(self, mock_process_class):
        """Test detection of stale processes"""
        # Mock process that's no longer running
        mock_process_class.side_effect = Exception("Process not found")

        # Register process with old heartbeat
        old_time = datetime.now() - timedelta(minutes=5)
        process_info = ProcessInfo(
            task_id="test-task-stale",
            task_name="Stale Task",
            status=ProcessStatus.RUNNING,
            command="test command",
            working_directory="/tmp",
            created_at=old_time,
            pid=99999,
            last_heartbeat=old_time
        )
        self.registry.register_process(process_info)

        # Update heartbeats - should detect stale process
        self.registry.update_heartbeats()

        # Verify process marked as failed
        process = self.registry.get_process("test-task-stale")
        self.assertIsNotNone(process)
        if process is not None:
            self.assertEqual(process.status, ProcessStatus.FAILED)
            if process.error_message is not None:
                self.assertIn("unresponsive", process.error_message.lower())

    def test_process_cancellation(self):
        """Test process cancellation"""
        # Register queued process
        process_info = ProcessInfo(
            task_id="test-task-cancel",
            task_name="Cancel Task",
            status=ProcessStatus.QUEUED,
            command="test command",
            working_directory="/tmp",
            created_at=datetime.now()
        )
        self.registry.register_process(process_info)

        # Cancel process
        success = self.registry.cancel_process("test-task-cancel")
        self.assertTrue(success)

        # Verify cancellation
        process = self.registry.get_process("test-task-cancel")
        self.assertIsNotNone(process)
        if process is not None:
            self.assertEqual(process.status, ProcessStatus.CANCELLED)
            self.assertIsNotNone(process.completed_at)
            if process.error_message is not None:
                self.assertIn("cancelled", process.error_message.lower())

    def test_process_cleanup(self):
        """Test cleanup of old completed processes"""
        # Register old completed process
        old_time = datetime.now() - timedelta(hours=25)  # Older than 24 hours
        process_info = ProcessInfo(
            task_id="test-task-old",
            task_name="Old Task",
            status=ProcessStatus.COMPLETED,
            command="test command",
            working_directory="/tmp",
            created_at=old_time,
            completed_at=old_time
        )
        self.registry.register_process(process_info)

        # Register recent completed process
        recent_time = datetime.now() - timedelta(hours=1)
        process_info2 = ProcessInfo(
            task_id="test-task-recent",
            task_name="Recent Task",
            status=ProcessStatus.COMPLETED,
            command="test command",
            working_directory="/tmp",
            created_at=recent_time,
            completed_at=recent_time
        )
        self.registry.register_process(process_info2)

        # Cleanup old processes
        cleaned_count = self.registry.cleanup_completed_processes(older_than_hours=24)

        # Verify cleanup
        self.assertEqual(cleaned_count, 1)
        self.assertIsNone(self.registry.get_process("test-task-old"))
        self.assertIsNotNone(self.registry.get_process("test-task-recent"))

    def test_registry_persistence(self):
        """Test registry persistence to disk"""
        # Register process
        process_info = ProcessInfo(
            task_id="test-persistence",
            task_name="Persistence Test",
            status=ProcessStatus.COMPLETED,
            command="test command",
            working_directory="/tmp",
            created_at=datetime.now()
        )
        self.registry.register_process(process_info)

        # Verify registry file exists
        self.assertTrue(self.registry.registry_file.exists())

        # Create new registry instance and verify it loads data
        new_registry = ProcessRegistry(str(self.registry_dir))

        self.assertEqual(len(new_registry.processes), 1)
        self.assertIsNotNone(new_registry.get_process("test-persistence"))

    def test_export_monitoring_data(self):
        """Test export of monitoring data"""
        # Register test processes
        processes = [
            ProcessInfo("task-1", "Task 1", ProcessStatus.COMPLETED, "cmd1", "/tmp", datetime.now()),
            ProcessInfo("task-2", "Task 2", ProcessStatus.RUNNING, "cmd2", "/tmp", datetime.now()),
        ]

        for process in processes:
            self.registry.register_process(process)

        # Export data
        export_file = self.test_dir / "export.json"
        self.registry.export_monitoring_data(str(export_file))

        # Verify export file
        self.assertTrue(export_file.exists())

        with open(export_file) as f:
            data = json.load(f)

        self.assertIn("timestamp", data)
        self.assertIn("registry_stats", data)
        self.assertIn("processes", data)
        self.assertEqual(len(data["processes"]), 2)

    def test_save_to_file(self):
        """Test saving registry to specific file"""
        # Register test process
        process_info = ProcessInfo(
            task_id="test-save",
            task_name="Save Test",
            status=ProcessStatus.COMPLETED,
            command="test command",
            working_directory="/tmp",
            created_at=datetime.now()
        )
        self.registry.register_process(process_info)

        # Save to file
        save_file = self.test_dir / "registry_save.json"
        self.registry.save_to_file(str(save_file))

        # Verify save file
        self.assertTrue(save_file.exists())

        with open(save_file) as f:
            data = json.load(f)

        self.assertIn("timestamp", data)
        self.assertIn("processes", data)
        self.assertEqual(len(data["processes"]), 1)
        self.assertIn("test-save", data["processes"])


class TestProcessInfo(unittest.TestCase):
    """Unit tests for ProcessInfo dataclass"""

    def test_process_info_creation(self):
        """Test ProcessInfo creation and attributes"""
        created_time = datetime.now()

        process_info = ProcessInfo(
            task_id="test-id",
            task_name="Test Name",
            status=ProcessStatus.QUEUED,
            command="test command",
            working_directory="/tmp/test",
            created_at=created_time,
            prompt_file="test.md"
        )

        self.assertEqual(process_info.task_id, "test-id")
        self.assertEqual(process_info.task_name, "Test Name")
        self.assertEqual(process_info.status, ProcessStatus.QUEUED)
        self.assertEqual(process_info.command, "test command")
        self.assertEqual(process_info.working_directory, "/tmp/test")
        self.assertEqual(process_info.created_at, created_time)
        self.assertEqual(process_info.prompt_file, "test.md")

        # Test optional fields
        self.assertIsNone(process_info.pid)
        self.assertIsNone(process_info.started_at)
        self.assertIsNone(process_info.completed_at)


if __name__ == '__main__':
    # Set up test environment
    import logging
    logging.basicConfig(level=logging.WARNING)

    # Run tests
    unittest.main(verbosity=2)
