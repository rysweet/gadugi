"""
Comprehensive tests for state_management.py module.
Tests the Enhanced Separation architecture implementation for state persistence.
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

# Import the module we're testing (will be implemented after tests)
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "shared")
)

try:
    from state_management import (
        StateManager,
        StateError,
        CheckpointManager,
        TaskState,
        WorkflowPhase,
        StateValidationError,
    )
except ImportError:
    # These will be implemented after tests pass
    pass


class TestTaskState:
    """Test suite for TaskState data class."""

    def test_task_state_creation(self):
        """Test TaskState creation with minimal data."""
        state = TaskState(
            task_id="test-task-001", prompt_file="test-feature.md", status="pending"
        )
        assert state.task_id == "test-task-001"
        assert state.prompt_file == "test-feature.md"
        assert state.status == "pending"
        assert state.created_at is not None
        assert state.updated_at is not None
        assert state.current_phase == 0
        assert state.context == {}

    def test_task_state_creation_complete(self):
        """Test TaskState creation with complete data."""
        context = {"user_request": "Add feature", "priority": "high"}
        state = TaskState(
            task_id="test-task-002",
            prompt_file="feature.md",
            status="in_progress",
            branch="feature/test-002",
            issue_number=42,
            pr_number=15,
            current_phase=3,
            context=context,
            error_info={"last_error": "Network timeout"},
        )

        assert state.task_id == "test-task-002"
        assert state.branch == "feature/test-002"
        assert state.issue_number == 42
        assert state.pr_number == 15
        assert state.current_phase == 3
        assert state.context == context
        assert state.error_info["last_error"] == "Network timeout"

    def test_task_state_to_dict(self):
        """Test TaskState serialization to dictionary."""
        state = TaskState(
            task_id="test-task-003",
            prompt_file="test.md",
            status="completed",
            branch="feature/test-003",
            issue_number=10,
            current_phase=9,
        )

        data = state.to_dict()

        assert data["task_id"] == "test-task-003"
        assert data["prompt_file"] == "test.md"
        assert data["status"] == "completed"
        assert data["branch"] == "feature/test-003"
        assert data["issue_number"] == 10
        assert data["current_phase"] == 9
        assert "created_at" in data
        assert "updated_at" in data

    def test_task_state_from_dict(self):
        """Test TaskState deserialization from dictionary."""
        data = {
            "task_id": "test-task-004",
            "prompt_file": "feature.md",
            "status": "error",
            "branch": "feature/test-004",
            "issue_number": 20,
            "pr_number": 5,
            "current_phase": 5,
            "created_at": "2025-08-01T22:00:00Z",
            "updated_at": "2025-08-01T22:30:00Z",
            "context": {"priority": "medium"},
            "error_info": {"error": "Test failed"},
        }

        state = TaskState.from_dict(data)

        assert state.task_id == "test-task-004"
        assert state.prompt_file == "feature.md"
        assert state.status == "error"
        assert state.branch == "feature/test-004"
        assert state.issue_number == 20
        assert state.pr_number == 5
        assert state.current_phase == 5
        assert state.context == {"priority": "medium"}
        assert state.error_info == {"error": "Test failed"}

    def test_task_state_update_phase(self):
        """Test updating task state phase."""
        state = TaskState(
            task_id="test-task-005", prompt_file="test.md", status="in_progress"
        )

        original_updated = state.updated_at
        state.update_phase(3, "Implementation")

        assert state.current_phase == 3
        assert state.current_phase_name == "Implementation"
        assert state.updated_at > original_updated

    def test_task_state_set_error(self):
        """Test setting error information."""
        state = TaskState(
            task_id="test-task-006", prompt_file="test.md", status="in_progress"
        )

        error_info = {
            "error_type": "network_error",
            "message": "Connection failed",
            "phase": 2,
            "retry_count": 3,
        }

        state.set_error(error_info)

        assert state.status == "error"
        # Check that original error info is preserved
        for key, value in error_info.items():
            assert state.error_info[key] == value
        # Check that timestamp was added
        assert "error_timestamp" in state.error_info

    def test_task_state_clear_error(self):
        """Test clearing error information."""
        state = TaskState(
            task_id="test-task-007",
            prompt_file="test.md",
            status="error",
            error_info={"error": "Previous error"},
        )

        state.clear_error()

        assert state.status == "pending"
        assert state.error_info == {}

    def test_task_state_validation(self):
        """Test task state validation."""
        # Valid state
        valid_state = TaskState(
            task_id="valid-task", prompt_file="valid.md", status="pending"
        )
        assert valid_state.is_valid()

        # Invalid status
        invalid_state = TaskState(
            task_id="invalid-task", prompt_file="invalid.md", status="invalid_status"
        )
        assert not invalid_state.is_valid()

        # Invalid phase
        invalid_phase = TaskState(
            task_id="invalid-phase-task",
            prompt_file="test.md",
            status="pending",
            current_phase=15,  # Phase out of range
        )
        assert not invalid_phase.is_valid()


class TestWorkflowPhase:
    """Test suite for WorkflowPhase enum."""

    def test_workflow_phases(self):
        """Test workflow phase enumeration."""
        assert WorkflowPhase.INITIALIZATION.value == 0
        assert WorkflowPhase.ISSUE_CREATION.value == 2
        assert WorkflowPhase.IMPLEMENTATION.value == 5
        assert WorkflowPhase.REVIEW.value == 9

    def test_workflow_phase_names(self):
        """Test workflow phase name mapping."""
        assert (
            WorkflowPhase.get_phase_name(0) == "Task Initialization & Resumption Check"
        )
        assert WorkflowPhase.get_phase_name(2) == "Issue Creation"
        assert WorkflowPhase.get_phase_name(5) == "Implementation"
        assert WorkflowPhase.get_phase_name(9) == "Review"
        assert WorkflowPhase.get_phase_name(99) == "Unknown Phase"

    def test_workflow_phase_validation(self):
        """Test workflow phase validation."""
        assert WorkflowPhase.is_valid_phase(0) is True
        assert WorkflowPhase.is_valid_phase(5) is True
        assert WorkflowPhase.is_valid_phase(9) is True
        assert WorkflowPhase.is_valid_phase(15) is False
        assert WorkflowPhase.is_valid_phase(-1) is False


class TestStateManager:
    """Test suite for StateManager class."""

    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary state directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def state_manager(self, temp_state_dir):
        """Create StateManager instance for testing."""
        config = {
            "state_dir": str(temp_state_dir),
            "backup_enabled": True,
            "cleanup_after_days": 7,
            "max_states_per_task": 10,
        }
        return StateManager(config)

    def test_state_manager_init_default(self):
        """Test StateManager initialization with default config."""
        sm = StateManager()
        assert sm.state_dir == Path(".github/workflow-states")
        assert sm.backup_enabled is True
        assert sm.cleanup_after_days == 30
        assert sm.max_states_per_task == 20

    def test_state_manager_init_custom(self, temp_state_dir):
        """Test StateManager initialization with custom config."""
        config = {
            "state_dir": str(temp_state_dir),
            "backup_enabled": False,
            "cleanup_after_days": 14,
            "max_states_per_task": 5,
        }
        sm = StateManager(config)
        assert sm.state_dir == temp_state_dir
        assert sm.backup_enabled is False
        assert sm.cleanup_after_days == 14
        assert sm.max_states_per_task == 5

    def test_save_state_success(self, state_manager):
        """Test successful state saving."""
        state = TaskState(
            task_id="test-save-001", prompt_file="test.md", status="pending"
        )

        result = state_manager.save_state(state)
        assert result is True

        # Verify file exists
        state_file = state_manager.state_dir / "test-save-001" / "state.json"
        assert state_file.exists()

        # Verify content
        with open(state_file, "r") as f:
            data = json.load(f)
        assert data["task_id"] == "test-save-001"
        assert data["status"] == "pending"

    def test_load_state_success(self, state_manager):
        """Test successful state loading."""
        # First save a state
        original_state = TaskState(
            task_id="test-load-001",
            prompt_file="load-test.md",
            status="in_progress",
            current_phase=3,
        )
        state_manager.save_state(original_state)

        # Load the state
        loaded_state = state_manager.load_state("test-load-001")

        assert loaded_state is not None
        assert loaded_state.task_id == "test-load-001"
        assert loaded_state.prompt_file == "load-test.md"
        assert loaded_state.status == "in_progress"
        assert loaded_state.current_phase == 3

    def test_load_state_not_found(self, state_manager):
        """Test loading non-existent state."""
        loaded_state = state_manager.load_state("non-existent-task")
        assert loaded_state is None

    def test_update_state_success(self, state_manager):
        """Test successful state update."""
        # Create and save initial state
        state = TaskState(
            task_id="test-update-001", prompt_file="update-test.md", status="pending"
        )
        state_manager.save_state(state)

        # Update the state
        state.status = "in_progress"
        state.current_phase = 2
        state.issue_number = 42

        result = state_manager.update_state(state)
        assert result is True

        # Verify update
        loaded_state = state_manager.load_state("test-update-001")
        assert loaded_state.status == "in_progress"
        assert loaded_state.current_phase == 2
        assert loaded_state.issue_number == 42

    def test_delete_state_success(self, state_manager):
        """Test successful state deletion."""
        # Create and save state
        state = TaskState(
            task_id="test-delete-001", prompt_file="delete-test.md", status="completed"
        )
        state_manager.save_state(state)

        # Verify it exists
        assert state_manager.load_state("test-delete-001") is not None

        # Delete it
        result = state_manager.delete_state("test-delete-001")
        assert result is True

        # Verify deletion
        assert state_manager.load_state("test-delete-001") is None

    def test_list_active_states(self, state_manager):
        """Test listing active states."""
        # Create multiple states
        states = [
            TaskState("task-001", "test1.md", "pending"),
            TaskState("task-002", "test2.md", "in_progress"),
            TaskState("task-003", "test3.md", "completed"),
            TaskState("task-004", "test4.md", "error"),
        ]

        for state in states:
            state_manager.save_state(state)

        # List all active states
        active_states = state_manager.list_active_states()
        assert len(active_states) == 4

        task_ids = [s.task_id for s in active_states]
        assert "task-001" in task_ids
        assert "task-002" in task_ids
        assert "task-003" in task_ids
        assert "task-004" in task_ids

    def test_list_states_by_status(self, state_manager):
        """Test listing states filtered by status."""
        # Create states with different statuses
        states = [
            TaskState("pending-001", "test1.md", "pending"),
            TaskState("pending-002", "test2.md", "pending"),
            TaskState("progress-001", "test3.md", "in_progress"),
            TaskState("complete-001", "test4.md", "completed"),
        ]

        for state in states:
            state_manager.save_state(state)

        # Filter by pending
        pending_states = state_manager.list_states_by_status("pending")
        assert len(pending_states) == 2
        assert all(s.status == "pending" for s in pending_states)

        # Filter by in_progress
        progress_states = state_manager.list_states_by_status("in_progress")
        assert len(progress_states) == 1
        assert progress_states[0].task_id == "progress-001"

    def test_cleanup_old_states(self, state_manager):
        """Test cleanup of old states."""
        # Create states with different ages
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        recent_time = datetime.now(timezone.utc) - timedelta(hours=1)

        old_state = TaskState("old-task", "old.md", "completed")
        old_state.created_at = old_time
        old_state.updated_at = old_time

        recent_state = TaskState("recent-task", "recent.md", "completed")
        recent_state.created_at = recent_time
        recent_state.updated_at = recent_time

        state_manager.save_state(old_state)
        state_manager.save_state(recent_state)

        # Cleanup with 7-day threshold
        cleaned_count = state_manager.cleanup_old_states(days=7)
        assert cleaned_count == 1

        # Verify only recent state remains
        assert state_manager.load_state("old-task") is None
        assert state_manager.load_state("recent-task") is not None

    def test_backup_state(self, state_manager):
        """Test state backup functionality."""
        state = TaskState(
            task_id="backup-test", prompt_file="backup.md", status="in_progress"
        )
        state_manager.save_state(state)

        # Create backup
        backup_path = state_manager.backup_state("backup-test")
        assert backup_path is not None
        assert backup_path.exists()

        # Verify backup content
        with open(backup_path, "r") as f:
            backup_data = json.load(f)
        assert backup_data["task_id"] == "backup-test"

    def test_restore_from_backup(self, state_manager):
        """Test restoring state from backup."""
        # Create and backup state
        original_state = TaskState(
            task_id="restore-test",
            prompt_file="restore.md",
            status="in_progress",
            current_phase=3,
        )
        state_manager.save_state(original_state)
        backup_path = state_manager.backup_state("restore-test")

        # Modify current state
        modified_state = state_manager.load_state("restore-test")
        modified_state.status = "error"
        modified_state.current_phase = 5
        state_manager.update_state(modified_state)

        # Restore from backup
        restored_state = state_manager.restore_from_backup("restore-test", backup_path)
        assert restored_state is not None
        assert restored_state.status == "in_progress"
        assert restored_state.current_phase == 3

    def test_get_state_history(self, state_manager):
        """Test retrieving state history."""
        state = TaskState(
            task_id="history-test", prompt_file="history.md", status="pending"
        )

        # Save initial state
        state_manager.save_state(state)

        # Update state multiple times - each update will create a backup of the previous state
        for i in range(3):
            state.current_phase = i + 1
            state.status = "in_progress" if i < 2 else "completed"
            state_manager.update_state(state)  # This will backup the previous state

        # Get history - check that at least some history exists
        history = state_manager.get_state_history("history-test")
        assert len(history) >= 1  # At least 1 backup should exist

        # Verify the history contains valid data
        if len(history) > 0:
            assert "timestamp" in history[0]
            assert "backup_file" in history[0]
            assert "phase" in history[0]
            assert "status" in history[0]

    def test_validate_state_integrity(self, state_manager):
        """Test state integrity validation."""
        # Valid state
        valid_state = TaskState(
            task_id="valid-integrity", prompt_file="valid.md", status="pending"
        )
        state_manager.save_state(valid_state)

        is_valid, errors = state_manager.validate_state_integrity("valid-integrity")
        assert is_valid is True
        assert len(errors) == 0

    def test_state_corruption_detection(self, state_manager):
        """Test detection of corrupted state files."""
        # Create a corrupted state file
        corrupt_dir = state_manager.state_dir / "corrupt-task"
        corrupt_dir.mkdir(parents=True, exist_ok=True)
        corrupt_file = corrupt_dir / "state.json"

        # Write invalid JSON
        corrupt_file.write_text('{"invalid": json, content}')

        # Try to load corrupted state
        with pytest.raises(StateValidationError):
            state_manager.load_state("corrupt-task")

    def test_concurrent_access_handling(self, state_manager):
        """Test handling of concurrent state access."""
        state = TaskState(
            task_id="concurrent-test", prompt_file="concurrent.md", status="pending"
        )

        # Simulate concurrent updates
        with patch("fcntl.flock") as mock_flock:
            state_manager.save_state(state)
            state_manager.update_state(state)

            # Verify file locking was used
            assert mock_flock.call_count >= 2


class TestCheckpointManager:
    """Test suite for CheckpointManager class."""

    @pytest.fixture
    def temp_checkpoint_dir(self):
        """Create temporary checkpoint directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def checkpoint_manager(self, temp_checkpoint_dir):
        """Create CheckpointManager instance for testing."""
        config = {
            "checkpoint_dir": str(temp_checkpoint_dir),
            "max_checkpoints_per_task": 5,
            "compression_enabled": True,
        }
        return CheckpointManager(config)

    def test_create_checkpoint(self, checkpoint_manager):
        """Test checkpoint creation."""
        state = TaskState(
            task_id="checkpoint-001",
            prompt_file="test.md",
            status="in_progress",
            current_phase=3,
        )

        checkpoint_id = checkpoint_manager.create_checkpoint(state, "Phase 3 completed")
        assert checkpoint_id is not None

        # Verify checkpoint file exists (could be compressed or uncompressed)
        checkpoint_dir = checkpoint_manager.checkpoint_dir / "checkpoint-001"
        checkpoint_file_compressed = checkpoint_dir / f"{checkpoint_id}.json.gz"
        checkpoint_file_uncompressed = checkpoint_dir / f"{checkpoint_id}.json"

        assert (
            checkpoint_file_compressed.exists() or checkpoint_file_uncompressed.exists()
        )

    def test_list_checkpoints(self, checkpoint_manager):
        """Test listing checkpoints for a task."""
        state = TaskState(
            task_id="list-checkpoints", prompt_file="test.md", status="in_progress"
        )

        # Create multiple checkpoints
        checkpoint_ids = []
        for i in range(3):
            state.current_phase = i + 1
            checkpoint_id = checkpoint_manager.create_checkpoint(state, f"Phase {i+1}")
            checkpoint_ids.append(checkpoint_id)

        # List checkpoints
        checkpoints = checkpoint_manager.list_checkpoints("list-checkpoints")
        assert len(checkpoints) == 3

        for checkpoint in checkpoints:
            assert checkpoint["checkpoint_id"] in checkpoint_ids
            assert "created_at" in checkpoint
            assert "description" in checkpoint

    def test_restore_checkpoint(self, checkpoint_manager):
        """Test checkpoint restoration."""
        # Create checkpoint
        original_state = TaskState(
            task_id="restore-checkpoint",
            prompt_file="restore.md",
            status="in_progress",
            current_phase=3,
        )

        checkpoint_id = checkpoint_manager.create_checkpoint(
            original_state, "Backup point"
        )

        # Restore checkpoint
        restored_state = checkpoint_manager.restore_checkpoint(
            "restore-checkpoint", checkpoint_id
        )

        assert restored_state is not None
        assert restored_state.task_id == "restore-checkpoint"
        assert restored_state.current_phase == 3
        assert restored_state.status == "in_progress"

    def test_cleanup_old_checkpoints(self, checkpoint_manager):
        """Test cleanup of old checkpoints."""
        state = TaskState(
            task_id="cleanup-checkpoints",
            prompt_file="cleanup.md",
            status="in_progress",
        )

        # Create more checkpoints than the limit
        for i in range(7):  # max_checkpoints_per_task is 5
            state.current_phase = i + 1
            checkpoint_manager.create_checkpoint(state, f"Checkpoint {i+1}")

        # Trigger cleanup
        checkpoint_manager.cleanup_old_checkpoints("cleanup-checkpoints")

        # Verify only max number remain
        checkpoints = checkpoint_manager.list_checkpoints("cleanup-checkpoints")
        assert len(checkpoints) <= 5

    def test_checkpoint_compression(self, checkpoint_manager):
        """Test checkpoint compression functionality."""
        state = TaskState(
            task_id="compression-test",
            prompt_file="compress.md",
            status="in_progress",
            context={"large_data": "x" * 10000},  # Large context for compression
        )

        checkpoint_id = checkpoint_manager.create_checkpoint(state, "Compression test")

        # Verify compressed file is smaller than uncompressed would be
        checkpoint_file = (
            checkpoint_manager.checkpoint_dir
            / "compression-test"
            / f"{checkpoint_id}.json.gz"
        )
        assert checkpoint_file.exists()

        # Verify we can still restore from compressed checkpoint
        restored_state = checkpoint_manager.restore_checkpoint(
            "compression-test", checkpoint_id
        )
        assert restored_state is not None
        assert restored_state.context["large_data"] == "x" * 10000


class TestStateError:
    """Test suite for StateError exception class."""

    def test_state_error_creation(self):
        """Test StateError exception creation."""
        error = StateError("State operation failed", "save_state", {"task_id": "test"})
        assert str(error) == "State operation failed"
        assert error.operation == "save_state"
        assert error.context == {"task_id": "test"}

    def test_state_validation_error(self):
        """Test StateValidationError exception."""
        errors = ["Invalid status", "Missing task_id"]
        error = StateValidationError("Validation failed", errors)
        assert str(error) == "Validation failed"
        assert error.validation_errors == errors


# Integration tests
class TestStateManagementIntegration:
    """Integration tests for state management system."""

    @pytest.fixture
    def integration_setup(self):
        """Setup for integration tests."""
        temp_dir = Path(tempfile.mkdtemp())

        state_config = {
            "state_dir": str(temp_dir / "states"),
            "backup_enabled": True,
            "cleanup_after_days": 7,
        }

        checkpoint_config = {
            "checkpoint_dir": str(temp_dir / "checkpoints"),
            "max_checkpoints_per_task": 5,
            "compression_enabled": True,
        }

        state_manager = StateManager(state_config)
        checkpoint_manager = CheckpointManager(checkpoint_config)

        yield state_manager, checkpoint_manager, temp_dir

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.integration
    def test_complete_workflow_state_management(self, integration_setup):
        """Test complete workflow state management."""
        state_manager, checkpoint_manager, temp_dir = integration_setup

        # Initialize task
        task_state = TaskState(
            task_id="integration-workflow",
            prompt_file="integration-test.md",
            status="pending",
        )

        # Phase 1: Initial Setup
        task_state.update_phase(1, "Initial Setup")
        state_manager.save_state(task_state)
        checkpoint_manager.create_checkpoint(task_state, "Initial setup complete")

        # Phase 2: Issue Creation
        task_state.update_phase(2, "Issue Creation")
        task_state.issue_number = 42
        state_manager.update_state(task_state)

        # Phase 3: Branch Management
        task_state.update_phase(3, "Branch Management")
        task_state.branch = "feature/integration-test-42"
        state_manager.update_state(task_state)
        checkpoint_manager.create_checkpoint(task_state, "Branch created")

        # Phase 5: Implementation
        task_state.update_phase(5, "Implementation")
        task_state.status = "in_progress"
        state_manager.update_state(task_state)

        # Phase 8: Pull Request
        task_state.update_phase(8, "Pull Request")
        task_state.pr_number = 15
        state_manager.update_state(task_state)
        checkpoint_manager.create_checkpoint(task_state, "PR created")

        # Phase 9: Review Complete
        task_state.update_phase(9, "Review")
        task_state.status = "completed"
        state_manager.update_state(task_state)

        # Verify final state
        final_state = state_manager.load_state("integration-workflow")
        assert final_state.status == "completed"
        assert final_state.current_phase == 9
        assert final_state.issue_number == 42
        assert final_state.pr_number == 15
        assert final_state.branch == "feature/integration-test-42"

        # Verify checkpoints
        checkpoints = checkpoint_manager.list_checkpoints("integration-workflow")
        assert len(checkpoints) == 3

    @pytest.mark.integration
    def test_error_recovery_integration(self, integration_setup):
        """Test error recovery and state restoration."""
        state_manager, checkpoint_manager, temp_dir = integration_setup

        # Create task progressing normally
        task_state = TaskState(
            task_id="error-recovery-test",
            prompt_file="error-test.md",
            status="in_progress",
        )

        # Progress through phases with checkpoints
        for phase in [1, 2, 3, 5]:
            task_state.update_phase(phase, f"Phase {phase}")
            state_manager.update_state(task_state)
            checkpoint_manager.create_checkpoint(
                task_state, f"Phase {phase} checkpoint"
            )

        # Simulate error in phase 6
        task_state.update_phase(6, "Testing")
        error_info = {
            "error_type": "test_failure",
            "message": "Unit tests failed",
            "phase": 6,
            "retry_count": 1,
        }
        task_state.set_error(error_info)
        state_manager.update_state(task_state)

        # Recovery: restore from last good checkpoint (phase 5)
        checkpoints = checkpoint_manager.list_checkpoints("error-recovery-test")
        phase_5_checkpoint = None
        for checkpoint in checkpoints:
            if "Phase 5" in checkpoint["description"]:
                phase_5_checkpoint = checkpoint["checkpoint_id"]
                break

        assert phase_5_checkpoint is not None

        # Restore and continue
        restored_state = checkpoint_manager.restore_checkpoint(
            "error-recovery-test", phase_5_checkpoint
        )
        restored_state.clear_error()
        restored_state.update_phase(6, "Testing - Retry")
        state_manager.update_state(restored_state)

        # Verify recovery
        current_state = state_manager.load_state("error-recovery-test")
        assert current_state.status == "pending"  # Error cleared
        assert current_state.current_phase == 6
        assert current_state.error_info == {}

    @pytest.mark.integration
    def test_concurrent_task_management(self, integration_setup):
        """Test management of multiple concurrent tasks."""
        state_manager, checkpoint_manager, temp_dir = integration_setup

        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = TaskState(
                task_id=f"concurrent-task-{i:03d}",
                prompt_file=f"task-{i}.md",
                status="in_progress",
                current_phase=i + 1,
            )
            tasks.append(task)
            state_manager.save_state(task)
            checkpoint_manager.create_checkpoint(task, f"Task {i} checkpoint")

        # Verify all tasks are tracked
        active_states = state_manager.list_active_states()
        assert len(active_states) == 5

        # Update tasks at different rates
        for i, task in enumerate(tasks):
            for phase in range(task.current_phase, min(task.current_phase + i + 1, 10)):
                task.update_phase(phase, f"Phase {phase}")
                state_manager.update_state(task)

        # Complete some tasks
        for i in [0, 2, 4]:
            tasks[i].status = "completed"
            tasks[i].update_phase(9, "Review")
            state_manager.update_state(tasks[i])

        # Verify final states
        completed_states = state_manager.list_states_by_status("completed")
        assert len(completed_states) == 3

        in_progress_states = state_manager.list_states_by_status("in_progress")
        assert len(in_progress_states) == 2
