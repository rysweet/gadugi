"""
Comprehensive tests for task_tracking.py module (TodoWrite integration).
Tests task management, workflow tracking, and Claude Code integration.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, call, MagicMock
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Import the module we're testing
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '.claude', 'shared'))

try:
    from task_tracking import (
        TaskStatus,
        TaskPriority,
        Task,
        TaskList,
        TodoWriteIntegration,
        WorkflowPhaseTracker,
        TaskMetrics,
        TaskError,
        TaskValidationError,
        TaskTracker
    )
except ImportError:
    # If import fails, create stub classes to show what needs to be implemented
    print("Warning: Could not import task_tracking module. Tests will define what needs to be implemented.")
    
    from enum import Enum
    
    class TaskStatus(Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        BLOCKED = "blocked"
        CANCELLED = "cancelled"
    
    class TaskPriority(Enum):
        LOW = "low"
        MEDIUM = "medium" 
        HIGH = "high"
        CRITICAL = "critical"
        
    class Task:
        def __init__(self, id: str, content: str, status: TaskStatus = TaskStatus.PENDING, 
                     priority: TaskPriority = TaskPriority.MEDIUM):
            self.id = id
            self.content = content
            self.status = status
            self.priority = priority
            
    class TaskList:
        def __init__(self):
            self.tasks = []
            
    class TodoWriteIntegration:
        def __init__(self):
            pass
            
    class WorkflowPhaseTracker:
        def __init__(self):
            pass
            
    class TaskMetrics:
        def __init__(self):
            pass
            
    class TaskError(Exception):
        pass
        
    class TaskValidationError(TaskError):
        pass
        
    class TaskTracker:
        def __init__(self):
            pass


class TestTaskStatus:
    """Test TaskStatus enum."""
    
    def test_task_status_values(self):
        """Test task status enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.BLOCKED.value == "blocked"
        assert TaskStatus.CANCELLED.value == "cancelled"
        
    def test_task_status_count(self):
        """Test all task statuses are defined."""
        statuses = list(TaskStatus)
        assert len(statuses) == 5
        
    def test_task_status_ordering(self):
        """Test that we can work with different statuses."""
        assert TaskStatus.PENDING != TaskStatus.COMPLETED
        assert TaskStatus.IN_PROGRESS != TaskStatus.BLOCKED


class TestTaskPriority:
    """Test TaskPriority enum."""
    
    def test_task_priority_values(self):
        """Test task priority enum values."""
        assert TaskPriority.LOW.value == "low"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.CRITICAL.value == "critical"
        
    def test_task_priority_count(self):
        """Test all task priorities are defined."""
        priorities = list(TaskPriority)
        assert len(priorities) == 4


class TestTask:
    """Test Task class."""
    
    def test_task_creation_minimal(self):
        """Test creating a task with minimal parameters."""
        task = Task("1", "Test task")
        assert task.id == "1"
        assert task.content == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        
    def test_task_creation_full(self):
        """Test creating a task with all parameters."""
        task = Task(
            id="task-123",
            content="Critical task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.CRITICAL
        )
        assert task.id == "task-123"
        assert task.content == "Critical task"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.CRITICAL
        
    def test_task_to_dict(self):
        """Test converting task to dictionary."""
        task = Task("1", "Test task", TaskStatus.COMPLETED, TaskPriority.HIGH)
        task_dict = task.to_dict()
        
        expected = {
            "id": "1",
            "content": "Test task",
            "status": "completed",
            "priority": "high"
        }
        assert task_dict == expected
        
    def test_task_from_dict(self):
        """Test creating task from dictionary."""
        task_dict = {
            "id": "2",
            "content": "From dict task",
            "status": "in_progress",
            "priority": "low"
        }
        task = Task.from_dict(task_dict)
        
        assert task.id == "2"
        assert task.content == "From dict task"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.LOW
        
    def test_task_update_status(self):
        """Test updating task status."""
        task = Task("1", "Test task")
        assert task.status == TaskStatus.PENDING
        
        task.update_status(TaskStatus.IN_PROGRESS)
        assert task.status == TaskStatus.IN_PROGRESS
        
    def test_task_update_priority(self):
        """Test updating task priority."""
        task = Task("1", "Test task")
        assert task.priority == TaskPriority.MEDIUM
        
        task.update_priority(TaskPriority.HIGH)
        assert task.priority == TaskPriority.HIGH
        
    def test_task_is_active(self):
        """Test checking if task is active."""
        task = Task("1", "Test task")
        
        task.status = TaskStatus.PENDING
        assert task.is_active()
        
        task.status = TaskStatus.IN_PROGRESS
        assert task.is_active()
        
        task.status = TaskStatus.BLOCKED
        assert task.is_active()
        
        task.status = TaskStatus.COMPLETED
        assert not task.is_active()
        
        task.status = TaskStatus.CANCELLED
        assert not task.is_active()
        
    def test_task_validation(self):
        """Test task validation."""
        # Valid task
        task = Task("valid-id", "Valid content")
        task.validate()  # Should not raise
        
        # Invalid ID
        with pytest.raises(TaskValidationError):
            invalid_task = Task("", "Content")
            invalid_task.validate()
            
        # Invalid content
        with pytest.raises(TaskValidationError):
            invalid_task = Task("id", "")
            invalid_task.validate()
            
    def test_task_estimated_duration(self):
        """Test task estimated duration functionality."""
        task = Task("1", "Test task")
        
        # Default no duration
        assert task.estimated_duration is None
        
        # Set duration
        task.set_estimated_duration(120)  # 2 hours in minutes
        assert task.estimated_duration == 120
        
    def test_task_dependencies(self):
        """Test task dependencies."""
        task = Task("1", "Test task")
        
        # No dependencies initially
        assert task.dependencies == []
        
        # Add dependencies
        task.add_dependency("task-0")
        task.add_dependency("task-2")
        assert task.dependencies == ["task-0", "task-2"]
        
        # Remove dependency
        task.remove_dependency("task-0")
        assert task.dependencies == ["task-2"]
        
    def test_task_timestamps(self):
        """Test task timestamps."""
        task = Task("1", "Test task")
        
        # Should have created timestamp
        assert task.created_at is not None
        assert isinstance(task.created_at, datetime)
        
        # No start/end timestamps initially
        assert task.started_at is None
        assert task.completed_at is None
        
        # Start task
        task.start()
        assert task.started_at is not None
        assert task.status == TaskStatus.IN_PROGRESS
        
        # Complete task
        task.complete()
        assert task.completed_at is not None
        assert task.status == TaskStatus.COMPLETED


class TestTaskList:
    """Test TaskList class."""
    
    def test_task_list_creation(self):
        """Test creating an empty task list."""
        task_list = TaskList()
        assert len(task_list.tasks) == 0
        assert task_list.count() == 0
        
    def test_add_task(self):
        """Test adding tasks to list."""
        task_list = TaskList()
        task = Task("1", "Test task")
        
        task_list.add_task(task)
        assert task_list.count() == 1
        assert task_list.get_task("1") == task
        
    def test_add_task_duplicate_id(self):
        """Test adding task with duplicate ID raises error."""
        task_list = TaskList()
        task1 = Task("1", "First task")
        task2 = Task("1", "Second task")
        
        task_list.add_task(task1)
        with pytest.raises(TaskError, match="Task with ID 1 already exists"):
            task_list.add_task(task2)
            
    def test_remove_task(self):
        """Test removing tasks from list."""
        task_list = TaskList()
        task = Task("1", "Test task")
        
        task_list.add_task(task)
        assert task_list.count() == 1
        
        removed_task = task_list.remove_task("1")
        assert removed_task == task
        assert task_list.count() == 0
        
    def test_remove_nonexistent_task(self):
        """Test removing non-existent task."""
        task_list = TaskList()
        
        with pytest.raises(TaskError, match="Task with ID nonexistent not found"):
            task_list.remove_task("nonexistent")
            
    def test_get_task(self):
        """Test getting task by ID."""
        task_list = TaskList()
        task = Task("1", "Test task")
        task_list.add_task(task)
        
        retrieved_task = task_list.get_task("1")
        assert retrieved_task == task
        
        assert task_list.get_task("nonexistent") is None
        
    def test_update_task(self):
        """Test updating task in list."""
        task_list = TaskList()
        task = Task("1", "Test task")
        task_list.add_task(task)
        
        task_list.update_task("1", status=TaskStatus.COMPLETED)
        updated_task = task_list.get_task("1")
        assert updated_task.status == TaskStatus.COMPLETED
        
    def test_get_tasks_by_status(self):
        """Test getting tasks by status."""
        task_list = TaskList()
        task1 = Task("1", "Pending task", TaskStatus.PENDING)
        task2 = Task("2", "In progress task", TaskStatus.IN_PROGRESS)
        task3 = Task("3", "Another pending task", TaskStatus.PENDING)
        
        task_list.add_task(task1)
        task_list.add_task(task2)
        task_list.add_task(task3)
        
        pending_tasks = task_list.get_tasks_by_status(TaskStatus.PENDING)
        assert len(pending_tasks) == 2
        assert task1 in pending_tasks
        assert task3 in pending_tasks
        
        in_progress_tasks = task_list.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        assert len(in_progress_tasks) == 1
        assert task2 in in_progress_tasks
        
    def test_get_tasks_by_priority(self):
        """Test getting tasks by priority."""
        task_list = TaskList()
        task1 = Task("1", "High priority", TaskStatus.PENDING, TaskPriority.HIGH)
        task2 = Task("2", "Low priority", TaskStatus.PENDING, TaskPriority.LOW)
        task3 = Task("3", "Another high priority", TaskStatus.PENDING, TaskPriority.HIGH)
        
        task_list.add_task(task1)
        task_list.add_task(task2)
        task_list.add_task(task3)
        
        high_priority_tasks = task_list.get_tasks_by_priority(TaskPriority.HIGH)
        assert len(high_priority_tasks) == 2
        assert task1 in high_priority_tasks
        assert task3 in high_priority_tasks
        
    def test_get_active_tasks(self):
        """Test getting active tasks."""
        task_list = TaskList()
        task1 = Task("1", "Pending", TaskStatus.PENDING)
        task2 = Task("2", "In Progress", TaskStatus.IN_PROGRESS)
        task3 = Task("3", "Completed", TaskStatus.COMPLETED)
        task4 = Task("4", "Blocked", TaskStatus.BLOCKED)
        
        for task in [task1, task2, task3, task4]:
            task_list.add_task(task)
            
        active_tasks = task_list.get_active_tasks()
        assert len(active_tasks) == 3  # pending, in_progress, blocked
        assert task1 in active_tasks
        assert task2 in active_tasks
        assert task4 in active_tasks
        assert task3 not in active_tasks
        
    def test_to_todowrite_format(self):
        """Test converting task list to TodoWrite format."""
        task_list = TaskList()
        task1 = Task("1", "First task", TaskStatus.PENDING, TaskPriority.HIGH)
        task2 = Task("2", "Second task", TaskStatus.COMPLETED, TaskPriority.MEDIUM)
        
        task_list.add_task(task1)
        task_list.add_task(task2)
        
        todowrite_format = task_list.to_todowrite_format()
        
        expected = [
            {
                "id": "1",
                "content": "First task",
                "status": "pending",
                "priority": "high"
            },
            {
                "id": "2", 
                "content": "Second task",
                "status": "completed",
                "priority": "medium"
            }
        ]
        
        assert todowrite_format == expected
        
    def test_from_todowrite_format(self):
        """Test creating task list from TodoWrite format."""
        todowrite_data = [
            {
                "id": "1",
                "content": "First task",
                "status": "pending",
                "priority": "high"
            },
            {
                "id": "2",
                "content": "Second task", 
                "status": "completed",
                "priority": "medium"
            }
        ]
        
        task_list = TaskList.from_todowrite_format(todowrite_data)
        
        assert task_list.count() == 2
        
        task1 = task_list.get_task("1")
        assert task1.content == "First task"
        assert task1.status == TaskStatus.PENDING
        assert task1.priority == TaskPriority.HIGH
        
        task2 = task_list.get_task("2")
        assert task2.content == "Second task"
        assert task2.status == TaskStatus.COMPLETED
        assert task2.priority == TaskPriority.MEDIUM


class TestTodoWriteIntegration:
    """Test TodoWrite integration functionality."""
    
    def test_todowrite_integration_init(self):
        """Test TodoWrite integration initialization."""
        integration = TodoWriteIntegration()
        assert integration.current_task_list is None
        assert integration.call_count == 0
        
    def test_submit_task_list(self):
        """Test submitting task list via TodoWrite."""
        integration = TodoWriteIntegration()
        
        # Mock the Claude Code function call
        with patch('task_tracking.claude_function_call') as mock_call:
            mock_call.return_value = {"success": True}
            
            task_list = TaskList()
            task_list.add_task(Task("1", "Test task", priority=TaskPriority.HIGH))
            
            result = integration.submit_task_list(task_list)
            
            assert result["success"] is True
            assert integration.call_count == 1
            assert integration.current_task_list == task_list
            
            # Verify TodoWrite was called with correct format
            mock_call.assert_called_once_with(
                "TodoWrite",
                {
                    "todos": [
                        {
                            "id": "1",
                            "content": "Test task",
                            "status": "pending",
                            "priority": "high"
                        }
                    ]
                }
            )
            
    def test_submit_empty_task_list(self):
        """Test submitting empty task list."""
        integration = TodoWriteIntegration()
        
        with pytest.raises(TaskValidationError, match="Cannot submit empty task list"):
            integration.submit_task_list(TaskList())
            
    def test_submit_invalid_task_list(self):
        """Test submitting invalid task list."""
        integration = TodoWriteIntegration()
        
        task_list = TaskList()
        invalid_task = Task("", "Invalid task")  # Empty ID
        
        # The validation should fail when adding to task list
        with pytest.raises(TaskValidationError):
            task_list.add_task(invalid_task)
            
    def test_update_task_status(self):
        """Test updating single task status."""
        integration = TodoWriteIntegration()
        
        # Set up existing task list
        task_list = TaskList()
        task_list.add_task(Task("1", "Test task"))
        task_list.add_task(Task("2", "Another task"))
        integration.current_task_list = task_list
        
        with patch('task_tracking.claude_function_call') as mock_call:
            mock_call.return_value = {"success": True}
            
            result = integration.update_task_status("1", TaskStatus.COMPLETED)
            
            assert result["success"] is True
            assert integration.call_count == 1
            
            # Verify task was updated in current list
            updated_task = integration.current_task_list.get_task("1")
            assert updated_task.status == TaskStatus.COMPLETED
            
    def test_add_task(self):
        """Test adding single task."""
        integration = TodoWriteIntegration()
        
        # Initialize with existing task list
        existing_list = TaskList()
        existing_list.add_task(Task("1", "Existing task"))
        integration.current_task_list = existing_list
        
        with patch('task_tracking.claude_function_call') as mock_call:
            mock_call.return_value = {"success": True}
            
            new_task = Task("2", "New task", priority=TaskPriority.HIGH)
            result = integration.add_task(new_task)
            
            assert result["success"] is True
            assert integration.current_task_list.count() == 2
            assert integration.current_task_list.get_task("2") == new_task
            
    def test_remove_task(self):
        """Test removing single task."""
        integration = TodoWriteIntegration()
        
        # Set up task list
        task_list = TaskList()
        task_list.add_task(Task("1", "Keep this"))
        task_list.add_task(Task("2", "Remove this"))
        integration.current_task_list = task_list
        
        with patch('task_tracking.claude_function_call') as mock_call:
            mock_call.return_value = {"success": True}
            
            result = integration.remove_task("2")
            
            assert result["success"] is True
            assert integration.current_task_list.count() == 1
            assert integration.current_task_list.get_task("2") is None
            
    def test_batch_update(self):
        """Test batch updating multiple tasks."""
        integration = TodoWriteIntegration()
        
        task_list = TaskList()
        task_list.add_task(Task("1", "Task 1"))
        task_list.add_task(Task("2", "Task 2"))
        task_list.add_task(Task("3", "Task 3"))
        integration.current_task_list = task_list
        
        with patch('task_tracking.claude_function_call') as mock_call:
            mock_call.return_value = {"success": True}
            
            updates = [
                {"id": "1", "status": TaskStatus.COMPLETED},
                {"id": "2", "status": TaskStatus.IN_PROGRESS},
                {"id": "3", "priority": TaskPriority.HIGH}
            ]
            
            result = integration.batch_update(updates)
            
            assert result["success"] is True
            assert integration.call_count == 1
            
            # Verify updates
            task1 = integration.current_task_list.get_task("1")
            assert task1.status == TaskStatus.COMPLETED
            
            task2 = integration.current_task_list.get_task("2")
            assert task2.status == TaskStatus.IN_PROGRESS
            
            task3 = integration.current_task_list.get_task("3")
            assert task3.priority == TaskPriority.HIGH
            
    def test_get_statistics(self):
        """Test getting TodoWrite usage statistics."""
        integration = TodoWriteIntegration()
        
        # Simulate some calls
        integration.call_count = 5
        integration.last_update_time = datetime.now()
        
        stats = integration.get_statistics()
        
        assert stats["total_calls"] == 5
        assert "last_update" in stats
        assert "current_task_count" in stats


class TestWorkflowPhaseTracker:
    """Test workflow phase tracking functionality."""
    
    def test_workflow_phase_tracker_init(self):
        """Test workflow phase tracker initialization."""
        tracker = WorkflowPhaseTracker()
        assert tracker.current_phase is None
        assert len(tracker.phase_history) == 0
        assert tracker.workflow_id is not None
        
    def test_start_phase(self):
        """Test starting a workflow phase."""
        tracker = WorkflowPhaseTracker()
        
        tracker.start_phase("setup", "Initial setup phase")
        
        assert tracker.current_phase == "setup"
        assert len(tracker.phase_history) == 1
        
        phase_entry = tracker.phase_history[0]
        assert phase_entry["phase"] == "setup"
        assert phase_entry["description"] == "Initial setup phase"
        assert phase_entry["status"] == "in_progress"
        assert "started_at" in phase_entry
        
    def test_complete_phase(self):
        """Test completing a workflow phase."""
        tracker = WorkflowPhaseTracker()
        
        tracker.start_phase("setup", "Initial setup")
        tracker.complete_phase("Setup completed successfully")
        
        assert tracker.current_phase is None
        
        phase_entry = tracker.phase_history[0]
        assert phase_entry["status"] == "completed"
        assert phase_entry["completion_note"] == "Setup completed successfully"
        assert "completed_at" in phase_entry
        assert "duration_seconds" in phase_entry
        
    def test_fail_phase(self):
        """Test failing a workflow phase."""
        tracker = WorkflowPhaseTracker()
        
        tracker.start_phase("implementation", "Code implementation")
        tracker.fail_phase("Build failed", {"error": "syntax error"})
        
        assert tracker.current_phase is None
        
        phase_entry = tracker.phase_history[0]
        assert phase_entry["status"] == "failed"
        assert phase_entry["failure_reason"] == "Build failed"
        assert phase_entry["error_context"] == {"error": "syntax error"}
        
    def test_phase_transitions(self):
        """Test multiple phase transitions."""
        tracker = WorkflowPhaseTracker()
        
        # Phase 1
        tracker.start_phase("setup", "Setup")
        tracker.complete_phase("Setup done")
        
        # Phase 2
        tracker.start_phase("implementation", "Implementation")
        tracker.complete_phase("Implementation done")
        
        # Phase 3
        tracker.start_phase("testing", "Testing")
        tracker.fail_phase("Tests failed")
        
        assert len(tracker.phase_history) == 3
        assert all(phase["status"] in ["completed", "failed"] for phase in tracker.phase_history)
        
    def test_get_phase_summary(self):
        """Test getting phase summary."""
        tracker = WorkflowPhaseTracker()
        
        tracker.start_phase("setup", "Setup")
        tracker.complete_phase("Done")
        
        tracker.start_phase("implementation", "Implementation")
        tracker.fail_phase("Failed")
        
        summary = tracker.get_phase_summary()
        
        assert summary["total_phases"] == 2
        assert summary["completed_phases"] == 1
        assert summary["failed_phases"] == 1
        assert summary["success_rate"] == 0.5
        assert "total_duration_seconds" in summary
        
    def test_create_phase_task_list(self):
        """Test creating task list for a phase."""
        tracker = WorkflowPhaseTracker()
        
        tasks = [
            {"content": "Task 1", "priority": "high"},
            {"content": "Task 2", "priority": "medium"},
            {"content": "Task 3", "priority": "low"}
        ]
        
        task_list = tracker.create_phase_task_list("setup", tasks)
        
        assert task_list.count() == 3
        
        # Check task IDs are generated properly
        task1 = task_list.get_task("setup-1")
        assert task1 is not None
        assert task1.content == "Task 1"
        assert task1.priority == TaskPriority.HIGH
        
    def test_integration_with_todowrite(self):
        """Test integration between phase tracker and TodoWrite."""
        tracker = WorkflowPhaseTracker()
        integration = TodoWriteIntegration()
        
        with patch('task_tracking.claude_function_call') as mock_call:
            mock_call.return_value = {"success": True}
            
            # Start phase and create tasks
            tracker.start_phase("implementation", "Implementation phase")
            
            tasks = [
                {"content": "Implement feature A", "priority": "high"},
                {"content": "Write tests", "priority": "medium"}
            ]
            
            task_list = tracker.create_phase_task_list("implementation", tasks)
            result = integration.submit_task_list(task_list)
            
            assert result["success"] is True
            assert integration.current_task_list.count() == 2


class TestTaskMetrics:
    """Test task metrics and analytics."""
    
    def test_task_metrics_init(self):
        """Test task metrics initialization."""
        metrics = TaskMetrics()
        assert metrics.start_time is not None
        assert metrics.task_completion_times == []
        assert metrics.status_change_count == {}
        
    def test_record_task_completion(self):
        """Test recording task completion."""
        metrics = TaskMetrics()
        
        task = Task("1", "Test task")
        task.start()
        time.sleep(0.1)  # Small delay
        task.complete()
        
        metrics.record_task_completion(task)
        
        assert len(metrics.task_completion_times) == 1
        completion_record = metrics.task_completion_times[0]
        assert completion_record["task_id"] == "1"
        assert completion_record["duration_seconds"] > 0
        
    def test_record_status_change(self):
        """Test recording status changes."""
        metrics = TaskMetrics()
        
        metrics.record_status_change(TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        metrics.record_status_change(TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED)
        metrics.record_status_change(TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        
        assert metrics.status_change_count["pending->in_progress"] == 2
        assert metrics.status_change_count["in_progress->completed"] == 1
        
    def test_calculate_completion_rate(self):
        """Test calculating task completion rate."""
        metrics = TaskMetrics()
        
        task_list = TaskList()
        task_list.add_task(Task("1", "Task 1", TaskStatus.COMPLETED))
        task_list.add_task(Task("2", "Task 2", TaskStatus.COMPLETED))
        task_list.add_task(Task("3", "Task 3", TaskStatus.IN_PROGRESS))
        task_list.add_task(Task("4", "Task 4", TaskStatus.PENDING))
        
        completion_rate = metrics.calculate_completion_rate(task_list)
        assert completion_rate == 0.5  # 2 completed out of 4 total
        
    def test_calculate_average_completion_time(self):
        """Test calculating average completion time."""
        metrics = TaskMetrics()
        
        # Simulate completion times
        metrics.task_completion_times = [
            {"task_id": "1", "duration_seconds": 100},
            {"task_id": "2", "duration_seconds": 200},
            {"task_id": "3", "duration_seconds": 300}
        ]
        
        avg_time = metrics.calculate_average_completion_time()
        assert avg_time == 200.0  # (100 + 200 + 300) / 3
        
    def test_get_productivity_metrics(self):
        """Test getting comprehensive productivity metrics."""
        metrics = TaskMetrics()
        
        # Set up some data
        metrics.task_completion_times = [
            {"task_id": "1", "duration_seconds": 120}
        ]
        metrics.status_change_count = {
            "pending->in_progress": 5,
            "in_progress->completed": 3
        }
        
        task_list = TaskList()
        task_list.add_task(Task("1", "Task 1", TaskStatus.COMPLETED))
        task_list.add_task(Task("2", "Task 2", TaskStatus.IN_PROGRESS))
        
        productivity_metrics = metrics.get_productivity_metrics(task_list)
        
        assert "completion_rate" in productivity_metrics
        assert "average_completion_time" in productivity_metrics
        assert "total_status_changes" in productivity_metrics
        assert "tasks_in_progress" in productivity_metrics
        assert productivity_metrics["total_tasks"] == 2


class TestTaskError:
    """Test task error classes."""
    
    def test_task_error_creation(self):
        """Test creating task error."""
        error = TaskError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
        
    def test_task_validation_error_creation(self):
        """Test creating task validation error."""
        error = TaskValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert isinstance(error, TaskError)
        assert isinstance(error, Exception)


class TestTaskTracker:
    """Test the main TaskTracker class."""
    
    def test_task_tracker_init(self):
        """Test TaskTracker initialization."""
        tracker = TaskTracker()
        
        assert isinstance(tracker.task_list, TaskList)
        assert isinstance(tracker.todowrite, TodoWriteIntegration)
        assert isinstance(tracker.phase_tracker, WorkflowPhaseTracker)
        assert isinstance(tracker.metrics, TaskMetrics)
        
    def test_create_task(self):
        """Test creating a task through tracker."""
        tracker = TaskTracker()
        
        with patch.object(tracker.todowrite, 'add_task') as mock_add:
            mock_add.return_value = {"success": True}
            
            task = tracker.create_task("Test task", priority=TaskPriority.HIGH)
            
            assert task.content == "Test task"
            assert task.priority == TaskPriority.HIGH
            assert tracker.task_list.get_task(task.id) == task
            mock_add.assert_called_once_with(task)
            
    def test_update_task_status(self):
        """Test updating task status through tracker."""
        tracker = TaskTracker()
        
        # Add a task first
        task = Task("1", "Test task")
        tracker.task_list.add_task(task)
        
        with patch.object(tracker.todowrite, 'update_task_status') as mock_update:
            mock_update.return_value = {"success": True}
            
            with patch.object(tracker.metrics, 'record_status_change') as mock_record:
                tracker.update_task_status("1", TaskStatus.COMPLETED)
                
                updated_task = tracker.task_list.get_task("1")
                assert updated_task.status == TaskStatus.COMPLETED
                
                mock_update.assert_called_once_with("1", TaskStatus.COMPLETED)
                mock_record.assert_called_once_with(TaskStatus.PENDING, TaskStatus.COMPLETED)
                
    def test_start_workflow_phase(self):
        """Test starting a workflow phase."""
        tracker = TaskTracker()
        
        phase_tasks = [
            {"content": "Task 1", "priority": "high"},
            {"content": "Task 2", "priority": "medium"}
        ]
        
        with patch.object(tracker.todowrite, 'submit_task_list') as mock_submit:
            mock_submit.return_value = {"success": True}
            
            tracker.start_workflow_phase("implementation", "Implementation phase", phase_tasks)
            
            assert tracker.phase_tracker.current_phase == "implementation"
            assert tracker.task_list.count() == 2
            mock_submit.assert_called_once()
            
    def test_complete_workflow_phase(self):
        """Test completing a workflow phase."""
        tracker = TaskTracker()
        
        # Start a phase first
        tracker.phase_tracker.start_phase("setup", "Setup phase")
        
        tracker.complete_workflow_phase("Setup completed successfully")
        
        assert tracker.phase_tracker.current_phase is None
        assert len(tracker.phase_tracker.phase_history) == 1
        assert tracker.phase_tracker.phase_history[0]["status"] == "completed"
        
    def test_get_dashboard_data(self):
        """Test getting dashboard data."""
        tracker = TaskTracker()
        
        # Add some tasks
        tracker.task_list.add_task(Task("1", "Task 1", TaskStatus.COMPLETED))
        tracker.task_list.add_task(Task("2", "Task 2", TaskStatus.IN_PROGRESS))
        tracker.task_list.add_task(Task("3", "Task 3", TaskStatus.PENDING))
        
        dashboard = tracker.get_dashboard_data()
        
        assert "task_summary" in dashboard
        assert "phase_summary" in dashboard
        assert "productivity_metrics" in dashboard
        assert dashboard["task_summary"]["total_tasks"] == 3
        assert dashboard["task_summary"]["completed_tasks"] == 1
        assert dashboard["task_summary"]["active_tasks"] == 2


class TestTaskTrackingIntegration:
    """Integration tests for task tracking components."""
    
    @pytest.mark.integration
    def test_complete_workflow_with_tracking(self):
        """Test complete workflow with task tracking."""
        tracker = TaskTracker()
        
        with patch('task_tracking.claude_function_call') as mock_call:
            mock_call.return_value = {"success": True}
            
            # Start workflow phase
            phase_tasks = [
                {"content": "Setup environment", "priority": "high"},
                {"content": "Configure settings", "priority": "medium"},
                {"content": "Verify installation", "priority": "low"}
            ]
            
            tracker.start_workflow_phase("setup", "Setup phase", phase_tasks)
            
            # Update task statuses
            setup_task_id = "setup-1"
            config_task_id = "setup-2" 
            verify_task_id = "setup-3"
            
            # Complete tasks one by one
            tracker.update_task_status(setup_task_id, TaskStatus.COMPLETED)
            tracker.update_task_status(config_task_id, TaskStatus.COMPLETED)
            tracker.update_task_status(verify_task_id, TaskStatus.COMPLETED)
            
            # Complete phase
            tracker.complete_workflow_phase("Setup phase completed")
            
            # Verify final state
            dashboard = tracker.get_dashboard_data()
            assert dashboard["task_summary"]["completed_tasks"] == 3
            assert dashboard["phase_summary"]["completed_phases"] == 1
            
    @pytest.mark.integration
    def test_error_recovery_in_task_tracking(self):
        """Test error recovery in task tracking."""
        tracker = TaskTracker()
        
        # Simulate TodoWrite failure
        with patch.object(tracker.todowrite, 'submit_task_list') as mock_submit:
            mock_submit.side_effect = Exception("TodoWrite failed")
            
            phase_tasks = [{"content": "Test task", "priority": "medium"}]
            
            with pytest.raises(Exception, match="TodoWrite failed"):
                tracker.start_workflow_phase("test", "Test phase", phase_tasks)
                
            # Verify graceful state - phase should not be started
            assert tracker.phase_tracker.current_phase is None
            
    @pytest.mark.integration  
    def test_metrics_collection_during_workflow(self):
        """Test metrics collection during workflow execution."""
        tracker = TaskTracker()
        
        with patch('task_tracking.claude_function_call') as mock_call:
            mock_call.return_value = {"success": True}
            
            # Create and start tasks
            task1 = tracker.create_task("Task 1", TaskPriority.HIGH)
            task2 = tracker.create_task("Task 2", TaskPriority.MEDIUM)
            
            # Simulate task execution
            task1.start()
            time.sleep(0.1)
            task1.complete()
            tracker.metrics.record_task_completion(task1)
            
            task2.start()
            tracker.update_task_status(task2.id, TaskStatus.IN_PROGRESS)
            
            # Get metrics
            productivity_metrics = tracker.metrics.get_productivity_metrics(tracker.task_list)
            
            assert productivity_metrics["completion_rate"] == 0.5  # 1 of 2 completed
            assert productivity_metrics["tasks_in_progress"] == 1
            assert len(tracker.metrics.task_completion_times) == 1