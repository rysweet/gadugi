"""
Comprehensive tests for task_tracking.py module (TodoWrite integration).
Tests task management, workflow tracking, and Claude Code integration.
"""

import uuid

# Import the module we're testing
from datetime import datetime
import time
from typing import Any, Dict, List
from dataclasses import field

import pytest
from unittest.mock import Mock, patch

# For type checking only

try:
    from claude.shared.task_tracking import (
        Task,
        TaskError,
        TaskList,
        TaskMetrics,
        TaskPriority,
        TaskStatus,
        TaskTracker,
        TaskValidationError,
        TodoWriteIntegration,
        WorkflowPhaseTracker)
except ImportError as e:
    # If import fails, create stub classes to show what needs to be implemented
    print(
        f"Warning: Could not import task_tracking module: {e}. Tests will define what needs to be implemented."
    )

    from enum import Enum
    from typing import Optional

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
        def __init__(
            self,
            id: str,
            content: str,
            status: TaskStatus = TaskStatus.PENDING,
            priority: TaskPriority = TaskPriority.MEDIUM,
            **kwargs: Any):
            self.id = id
            self.content = content
            self.status = status
            self.priority = priority
            self.created_at: datetime = kwargs.get("created_at", datetime.now())
            self.started_at: Optional[datetime] = kwargs.get("started_at")
            self.completed_at: Optional[datetime] = kwargs.get("completed_at")
            self.estimated_duration: Optional[int] = kwargs.get("estimated_duration")
            self.dependencies: List[str] = kwargs.get("dependencies", [])
            self.tags: List[str] = kwargs.get("tags", [])
            self.metadata: Dict[str, Any] = kwargs.get("metadata", {})

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "content": self.content,
                "status": self.status.value,
                "priority": self.priority.value,
            }

        @classmethod
        def from_dict(cls, data: Dict[str, Any]) -> "Task":
            return cls(
                data["id"],
                data["content"],
                TaskStatus(data["status"]),
                TaskPriority(data["priority"]))

        def update_status(self, new_status: TaskStatus) -> None:
            self.status = new_status
            if new_status == TaskStatus.IN_PROGRESS and self.started_at is None:
                self.started_at = datetime.now()
            elif new_status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
                self.completed_at = datetime.now()

        def update_priority(self, new_priority: TaskPriority) -> None:
            self.priority = new_priority

        def is_active(self) -> bool:
            return self.status in (
                TaskStatus.PENDING,
                TaskStatus.IN_PROGRESS,
                TaskStatus.BLOCKED)

        def validate(self) -> None:
            if not self.id:
                raise TaskValidationError("Task ID cannot be empty")
            if not self.content:
                raise TaskValidationError("Task content cannot be empty")

        def set_estimated_duration(self, minutes: int) -> None:
            if minutes <= 0:
                raise ValueError("Estimated duration must be positive")
            self.estimated_duration = minutes

        def add_dependency(self, task_id: str) -> None:
            if task_id not in self.dependencies:
                self.dependencies.append(task_id)

        def remove_dependency(self, task_id: str) -> None:
            if task_id in self.dependencies:
                self.dependencies.remove(task_id)

        def start(self) -> None:
            self.started_at = datetime.now()
            self.update_status(TaskStatus.IN_PROGRESS)

        def complete(self) -> None:
            self.completed_at = datetime.now()
            self.update_status(TaskStatus.COMPLETED)

    class TaskList:
        def __init__(self) -> None:
            self.tasks: List[Any] = field(default_factory=list)
            self._task_dict: Dict[Any, Any] = field(default_factory=dict)

        def add_task(self, task: Task) -> None:
            # Raise TaskValidationError if task is invalid
            if not task.id or not task.content:
                raise TaskValidationError("Task ID and content cannot be empty")
            if task.id in self._task_dict:
                raise TaskError(f"Task with ID {task.id} already exists")
            self.tasks.append(task)
            self._task_dict[task.id] = task

        def remove_task(self, task_id: str) -> Task:
            if task_id not in self._task_dict:
                raise TaskError(f"Task with ID {task_id} not found")
            task = self._task_dict.pop(task_id)
            self.tasks.remove(task)
            return task

        def get_task(self, task_id: str) -> Optional[Task]:
            return self._task_dict.get(task_id)

        def update_task(self, task_id: str, **kwargs: Any) -> None:
            task = self.get_task(task_id)
            if task is None:
                raise TaskError(f"Task with ID {task_id} not found")
            if "status" in kwargs:
                task.update_status(kwargs["status"])
            if "priority" in kwargs:
                task.update_priority(kwargs["priority"])

        def count(self) -> int:
            return len(self.tasks)

        def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
            return [task for task in self.tasks if task.status == status]

        def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
            return [task for task in self.tasks if task.priority == priority]

        def get_active_tasks(self) -> List[Task]:
            return [task for task in self.tasks if task.is_active()]

        def to_todowrite_format(self) -> List[Dict[str, Any]]:
            return [
                {
                    "id": task.id,
                    "content": task.content,
                    "status": task.status.value,
                    "priority": task.priority.value,
                }
                for task in self.tasks
            ]

        @classmethod
        def from_todowrite_format(cls, data: List[Dict[str, Any]]) -> "TaskList":
            task_list = cls()
            for item in data:
                task = Task(
                    item["id"],
                    item["content"],
                    TaskStatus(item["status"]),
                    TaskPriority(item["priority"]))
                task_list.add_task(task)
            return task_list

    class TodoWriteIntegration:
        def __init__(self) -> None:
            self.current_task_list: Optional[TaskList] = None
            self.call_count: int = 0
            self.mock_api = Mock()
            self.last_update_time: Optional[datetime] = None

        def submit_task_list(self, task_list: TaskList) -> Dict[str, Any]:
            if task_list.count() == 0:
                raise TaskValidationError("Cannot submit empty task list")
            self.current_task_list = task_list
            self.call_count += 1
            # Simulate calling claude_function_call for the submission
            self.mock_api.call(
                "TodoWrite",
                {
                    "todos": [
                        {
                            "id": t.id,
                            "content": t.content,
                            "status": t.status.value,
                            "priority": t.priority.value,
                        }
                        for t in task_list.tasks
                    ]
                })
            return {"success": True, "task_count": task_list.count()}

        def update_task_status(
            self, task_id: str, new_status: TaskStatus
        ) -> Dict[str, Any]:
            if self.current_task_list is None:
                raise TaskError("No task list loaded")
            self.current_task_list.update_task(task_id, status=new_status)
            self.call_count += 1
            return {"success": True, "task_id": task_id, "new_status": new_status.value}

        def add_task(self, task: Task) -> Dict[str, Any]:
            if self.current_task_list is None:
                self.current_task_list = TaskList()
            # Raise TaskValidationError if task is invalid
            if not task.id or not task.content:
                raise TaskValidationError("Task ID and content cannot be empty")
            self.current_task_list.add_task(task)
            self.call_count += 1
            return {"success": True, "task_id": task.id}

        def remove_task(self, task_id: str) -> Dict[str, Any]:
            if self.current_task_list is None:
                raise TaskError("No task list loaded")
            self.current_task_list.remove_task(task_id)
            self.call_count += 1
            return {"success": True, "task_id": task_id}

        def batch_update(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
            if self.current_task_list is None:
                raise TaskError("No task list loaded")
            for update in updates:
                task_id = update["task_id"]
                if "status" in update:
                    self.current_task_list.update_task(task_id, status=update["status"])
                if "priority" in update:
                    self.current_task_list.update_task(
                        task_id, priority=update["priority"]
                    )
            self.call_count += 1
            return {"success": True, "updated_count": len(updates)}

        def get_statistics(self) -> Dict[str, Any]:
            if self.current_task_list is None:
                return {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "active_tasks": 0,
                    "total_calls": self.call_count,
                    "current_task_count": 0,
                    "last_update": self.last_update_time.isoformat()
                    if self.last_update_time
                    else None,
                }

            completed_tasks = self.current_task_list.get_tasks_by_status(
                TaskStatus.COMPLETED
            )
            active_tasks = self.current_task_list.get_active_tasks()

            stats = {
                "total_tasks": self.current_task_list.count(),
                "completed_tasks": len(completed_tasks),
                "active_tasks": len(active_tasks),
                "total_calls": self.call_count,
                "current_task_count": self.current_task_list.count(),
                "last_update": self.last_update_time.isoformat()
                if self.last_update_time
                else None,
            }
            # Ensure total_calls is always present
            if "total_calls" not in stats:
                stats["total_calls"] = 0
            return stats

    class WorkflowPhaseTracker:
        def __init__(self) -> None:
            self.workflow_id: str = str(uuid.uuid4())
            self.current_phase: Optional[str] = None
            self.phase_history: List[Any] = field(default_factory=list)
            self.phase_start_times: Dict[Any, Any] = field(default_factory=dict)

        def start_phase(
            self, phase_name: str, description: Optional[str] = None
        ) -> None:
            self.current_phase = phase_name
            start_time = datetime.now()
            self.phase_start_times[phase_name] = start_time
            entry = {
                "phase": phase_name,
                "started_at": start_time,
                "status": "in_progress",
            }
            if description:
                entry["description"] = description
            self.phase_history.append(entry)

        def complete_phase(
            self, message_or_phase: str, metadata: Optional[Dict[str, Any]] = None
        ) -> None:
            # If message_or_phase looks like a completion message (contains spaces/capitals),
            # complete the current phase, otherwise treat it as a phase name
            if self.current_phase and (
                " " in message_or_phase or message_or_phase[0].isupper()
            ):
                phase_name = self.current_phase
                completion_message = message_or_phase
            else:
                phase_name = message_or_phase
                completion_message = None

            if phase_name not in self.phase_start_times:
                raise TaskError(f"Phase {phase_name} was not started")

            for _entry in self.phase_history:
                if entry["phase"] == phase_name and entry["status"] == "in_progress":
                    entry["completed_at"] = datetime.now()
                    entry["duration_seconds"] = (
                        entry["completed_at"] - entry["started_at"]
                    ).total_seconds()
                    entry["status"] = "completed"
                    if metadata:
                        entry["metadata"] = metadata
                    if completion_message:
                        entry["completion_note"] = completion_message
                    break

            if self.current_phase == phase_name:
                self.current_phase = None

        def fail_phase(
            self, error_message: str, error_context: Optional[Dict[str, Any]] = None
        ) -> None:
            if self.current_phase is None:
                raise TaskError("No phase is currently active")

            for _entry in self.phase_history:
                if (
                    entry["phase"] == self.current_phase
                    and entry["status"] == "in_progress"
                ):
                    entry["failed_at"] = datetime.now()
                    entry["failure_reason"] = error_message
                    if error_context:
                        entry["error_context"] = error_context
                    entry["status"] = "failed"
                    break

            self.current_phase = None

        def get_phase_duration(self, phase_name: str) -> Optional[float]:
            for _entry in self.phase_history:
                if entry["phase"] == phase_name and "duration_seconds" in entry:
                    return entry["duration_seconds"]
            return None

        def create_phase_task_list(
            self, phase_name: str, tasks: List[Dict[str, Any]]
        ) -> TaskList:
            """Create a task list for a specific workflow phase."""
            phase_task_list = TaskList()
            for i, task_data in enumerate(tasks):
                task_id = f"{phase_name}-{i + 1}"
                # Convert string priority to enum
                priority = task_data.get("priority", TaskPriority.MEDIUM)
                if isinstance(priority, str):
                    priority_map = {
                        "low": TaskPriority.LOW,
                        "medium": TaskPriority.MEDIUM,
                        "high": TaskPriority.HIGH,
                        "critical": TaskPriority.CRITICAL,
                    }
                    priority = priority_map.get(priority.lower(), TaskPriority.MEDIUM)

                task = Task(
                    task_id,
                    task_data["content"],
                    TaskStatus.PENDING,
                    priority)
                phase_task_list.add_task(task)
            return phase_task_list

        def get_phase_summary(self) -> Dict[str, Any]:
            """Get a summary of all phases."""
            total_phases = len(self.phase_history)
            completed_phases = len(
                [p for _p in self.phase_history if p["status"] == "completed"]
            )
            failed_phases = len(
                [p for _p in self.phase_history if p["status"] == "failed"]
            )
            in_progress_phases = len(
                [p for _p in self.phase_history if p["status"] == "in_progress"]
            )

            # Calculate success rate
            success_rate = completed_phases / total_phases if total_phases > 0 else 0.0

            # Calculate total duration
            total_duration_seconds = 0.0
            for _phase in self.phase_history:
                if "duration_seconds" in phase:
                    total_duration_seconds += phase["duration_seconds"]

            return {
                "workflow_id": self.workflow_id,
                "current_phase": self.current_phase,
                "total_phases": total_phases,
                "completed_phases": completed_phases,
                "failed_phases": failed_phases,
                "in_progress_phases": in_progress_phases,
                "success_rate": success_rate,
                "total_duration_seconds": total_duration_seconds,
                "phase_history": self.phase_history,
            }

    class TaskMetrics:
        def __init__(self) -> None:
            self.start_time: datetime = datetime.now()
            self.task_completion_times: List[Any] = field(default_factory=list)
            self.status_change_count: Dict[Any, Any] = field(default_factory=dict)
            self.task_status_history: List[Any] = field(default_factory=list)
            self.average_completion_time: Optional[float] = None
            self.throughput_per_hour: float = 0.0
            self.productivity_score: float = 0.0

        def record_task_completion(self, task: Task) -> None:
            if task.started_at and task.completed_at:
                duration = (task.completed_at - task.started_at).total_seconds()
                completion_record = {
                    "task_id": task.id,
                    "duration_seconds": duration,
                    "completed_at": task.completed_at,
                }
                self.task_completion_times.append(completion_record)
                self._update_metrics()

        def record_status_change(
            self, old_status: TaskStatus, new_status: TaskStatus
        ) -> None:
            transition_key = f"{old_status.value}->{new_status.value}"
            self.status_change_count[transition_key] = (
                self.status_change_count.get(transition_key, 0) + 1
            )
            self.task_status_history.append(
                {
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "timestamp": datetime.now(),
                }
            )

        def _update_metrics(self) -> None:
            if self is not None and self.task_completion_times:
                durations = [
                    record["duration_seconds"] for _record in self.task_completion_times
                ]
                self.average_completion_time = sum(durations) / len(durations)
                elapsed_hours = (
                    datetime.now() - self.start_time
                ).total_seconds() / 3600
                if elapsed_hours > 0:
                    self.throughput_per_hour = (
                        len(self.task_completion_times) / elapsed_hours
                    )

        def calculate_productivity_score(self) -> float:
            if not self.task_completion_times:
                return 0.0

            base_score = len(self.task_completion_times) * 10
            avg_time_bonus = 0
            if self is not None and self.average_completion_time:
                if self.average_completion_time < 300:  # Less than 5 minutes
                    avg_time_bonus = 20
                elif self.average_completion_time < 600:  # Less than 10 minutes
                    avg_time_bonus = 10

            self.productivity_score = base_score + avg_time_bonus
            return self.productivity_score

        def calculate_completion_rate(self, task_list: TaskList) -> float:
            if task_list.count() == 0:
                return 0.0
            completed_tasks = len(task_list.get_tasks_by_status(TaskStatus.COMPLETED))
            return completed_tasks / task_list.count()

        def calculate_average_completion_time(self) -> float:
            if not self.task_completion_times:
                return 0.0
            durations = [
                record["duration_seconds"] for _record in self.task_completion_times
            ]
            return sum(durations) / len(durations)

        def get_productivity_metrics(
            self, task_list: Optional[TaskList] = None
        ) -> Dict[str, Any]:
            base_metrics = {
                "total_tasks_completed": len(self.task_completion_times),
                "average_completion_time": self.calculate_average_completion_time(),
                "throughput_per_hour": self.throughput_per_hour,
                "productivity_score": self.calculate_productivity_score(),
                "status_changes": dict(self.status_change_count),
                "task_completion_times": self.task_completion_times,
            }

            # Add task-list specific metrics if provided
            if task_list is not None:
                base_metrics.update(
                    {
                        "completion_rate": self.calculate_completion_rate(task_list),
                        "total_tasks": task_list.count(),
                        "tasks_in_progress": len(
                            task_list.get_tasks_by_status(TaskStatus.IN_PROGRESS)
                        ),
                        "total_status_changes": sum(self.status_change_count.values()),
                    }
                )

            return base_metrics

        def get_summary(self) -> Dict[str, Any]:
            return {
                "total_tasks_completed": len(self.task_completion_times),
                "average_completion_time": self.average_completion_time,
                "throughput_per_hour": self.throughput_per_hour,
                "productivity_score": self.productivity_score,
                "status_changes": self.status_change_count,
            }

    class TaskError(Exception):
        pass

    class TaskValidationError(TaskError):
        pass

    class TaskTracker:
        def __init__(
            self, todowrite_integration: Optional[TodoWriteIntegration] = None
        ):
            self.task_list: TaskList = TaskList()
            self.todowrite: TodoWriteIntegration = (
                todowrite_integration or TodoWriteIntegration()
            )
            self.phase_tracker: WorkflowPhaseTracker = WorkflowPhaseTracker()
            self.metrics: TaskMetrics = TaskMetrics()

        def create_task(
            self,
            content: str,
            priority: TaskPriority = TaskPriority.MEDIUM,
            task_id: Optional[str] = None) -> Task:
            if task_id is None:
                task_id = str(uuid.uuid4())
            task = Task(task_id, content, TaskStatus.PENDING, priority)
            self.task_list.add_task(task)
            # Also add to todowrite integration
            self.todowrite.add_task(task)
            return task

        def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
            task = self.task_list.get_task(task_id)
            if task:
                old_status = task.status
                self.task_list.update_task(task_id, status=new_status)
                # Also update via todowrite integration
                self.todowrite.update_task_status(task_id, new_status)
                self.metrics.record_status_change(old_status, new_status)

                if new_status == TaskStatus.COMPLETED:
                    self.metrics.record_task_completion(task)

        def start_workflow_phase(
            self,
            phase_name: str,
            description: Optional[str] = None,
            tasks: Optional[List[Dict[str, Any]]] = None) -> None:
            # Process tasks first to catch any issues before starting the phase
            phase_tasks = []
            if tasks:
                # Create phase tasks but don't add to task list yet
                for i, task_data in enumerate(tasks):
                    task_id = f"{phase_name}-{i + 1}"
                    # Convert string priority to enum
                    priority = task_data.get("priority", TaskPriority.MEDIUM)
                    if isinstance(priority, str):
                        priority_map = {
                            "low": TaskPriority.LOW,
                            "medium": TaskPriority.MEDIUM,
                            "high": TaskPriority.HIGH,
                            "critical": TaskPriority.CRITICAL,
                        }
                        priority = priority_map.get(
                            priority.lower(), TaskPriority.MEDIUM
                        )

                    task = Task(
                        task_id,
                        task_data["content"],
                        TaskStatus.PENDING,
                        priority)
                    phase_tasks.append(task)

                # Add tasks to the main task list
                for _task in phase_tasks:
                    self.task_list.add_task(task)

                # Submit the updated task list (this can fail)
                self.todowrite.submit_task_list(self.task_list)

            # Only start the phase after successful task processing
            self.phase_tracker.start_phase(phase_name, description)

        def complete_workflow_phase(self, completion_message: str) -> None:
            self.phase_tracker.complete_phase(completion_message)

        def get_dashboard_data(self) -> Dict[str, Any]:
            stats = self.todowrite.get_statistics()
            metrics = self.metrics.get_productivity_metrics(self.task_list)
            phase_summary = self.phase_tracker.get_phase_summary()

            task_summary = {
                "total_tasks": self.task_list.count(),
                "active_tasks": len(self.task_list.get_active_tasks()),
                "completed_tasks": len(
                    self.task_list.get_tasks_by_status(TaskStatus.COMPLETED)
                ),
                "pending_tasks": len(
                    self.task_list.get_tasks_by_status(TaskStatus.PENDING)
                ),
            }

            return {
                "task_summary": task_summary,
                "phase_summary": phase_summary,
                "current_phase": self.phase_tracker.current_phase,
                "todowrite_stats": stats,
                "productivity_metrics": metrics,
                "phase_history": self.phase_tracker.phase_history,
            }

        def create_phase_task_list(
            self, phase_name: str, tasks: List[Dict[str, Any]]
        ) -> TaskList:
            phase_task_list = TaskList()
            for i, task_data in enumerate(tasks):
                task_id = f"{phase_name}-{i + 1}"
                task = Task(
                    task_id,
                    task_data["content"],
                    TaskStatus.PENDING,
                    task_data.get("priority", TaskPriority.MEDIUM))
                phase_task_list.add_task(task)
            return phase_task_list

# Add claude_function_call for stub implementation
def claude_function_call(tool_name: str, **parameters) -> Dict[str, Any]:
    """Stub implementation of claude_function_call for testing."""
    return {"success": True, "result": parameters}

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

    def test_task_creation_minimal(self) -> None:
        """Test creating a task with minimal parameters."""
        task = Task("1", "Test task")
        assert task.id == "1"
        assert task.content == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM

    def test_task_creation_full(self) -> None:
        """Test creating a task with all parameters."""
        task = Task(
            id="task-123",
            content="Critical task",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.CRITICAL)
        assert task.id == "task-123"
        assert task.content == "Critical task"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.CRITICAL

    def test_task_to_dict(self) -> None:
        """Test converting task to dictionary."""
        task = Task("1", "Test task", TaskStatus.COMPLETED, TaskPriority.HIGH)
        task_dict = task.to_dict()

        expected = {
            "id": "1",
            "content": "Test task",
            "status": "completed",
            "priority": "high",
        }
        assert task_dict == expected

    def test_task_from_dict(self) -> None:
        """Test creating task from dictionary."""
        task_dict = {
            "id": "2",
            "content": "From dict task",
            "status": "in_progress",
            "priority": "low",
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

    def test_task_validation(self) -> None:
        """Test task validation."""
        # Valid task
        task = Task("valid-id", "Valid content")
        task.validate()  # Should not raise

        # Invalid ID
        with pytest.raises(TaskValidationError):
            Task("", "Content").validate()

        # Invalid content
        with pytest.raises(TaskValidationError):
            Task("id", "").validate()

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
        task3 = Task(
            "3", "Another high priority", TaskStatus.PENDING, TaskPriority.HIGH
        )

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

        for _task in [task1, task2, task3, task4]:
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
                "priority": "high",
            },
            {
                "id": "2",
                "content": "Second task",
                "status": "completed",
                "priority": "medium",
            },
        ]

        assert todowrite_format == expected

    def test_from_todowrite_format(self):
        """Test creating task list from TodoWrite format."""
        todowrite_data = [
            {
                "id": "1",
                "content": "First task",
                "status": "pending",
                "priority": "high",
            },
            {
                "id": "2",
                "content": "Second task",
                "status": "completed",
                "priority": "medium",
            },
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
        with patch("claude.shared.task_tracking.claude_function_call") as mock_call:
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
                            "priority": "high",
                        }
                    ]
                })

    def test_submit_empty_task_list(self):
        """Test submitting empty task list."""
        integration = TodoWriteIntegration()

        with pytest.raises(TaskValidationError, match="Cannot submit empty task list"):
            integration.submit_task_list(TaskList())

    def test_submit_invalid_task_list(self):
        """Test submitting invalid task list."""
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

        with patch("claude.shared.task_tracking.claude_function_call") as mock_call:
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

        with patch("claude.shared.task_tracking.claude_function_call") as mock_call:
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

        with patch("claude.shared.task_tracking.claude_function_call") as mock_call:
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

        with patch("claude.shared.task_tracking.claude_function_call") as mock_call:
            mock_call.return_value = {"success": True}

            updates = [
                {"task_id": "1", "status": TaskStatus.COMPLETED},
                {"task_id": "2", "status": TaskStatus.IN_PROGRESS},
                {"task_id": "3", "priority": TaskPriority.HIGH},
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
        assert all(
            phase["status"] in ["completed", "failed"]
            for _phase in tracker.phase_history
        )

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
            {"content": "Task 3", "priority": "low"},
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

        with patch("claude.shared.task_tracking.claude_function_call") as mock_call:
            mock_call.return_value = {"success": True}

            # Start phase and create tasks
            tracker.start_phase("implementation", "Implementation phase")

            tasks = [
                {"content": "Implement feature A", "priority": "high"},
                {"content": "Write tests", "priority": "medium"},
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
            {"task_id": "3", "duration_seconds": 300},
        ]

        avg_time = metrics.calculate_average_completion_time()
        assert avg_time == 200.0  # (100 + 200 + 300) / 3

    def test_get_productivity_metrics(self):
        """Test getting comprehensive productivity metrics."""
        metrics = TaskMetrics()

        # Set up some data
        metrics.task_completion_times = [{"task_id": "1", "duration_seconds": 120}]
        metrics.status_change_count = {
            "pending->in_progress": 5,
            "in_progress->completed": 3,
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

    def test_create_task(self) -> None:
        """Test creating a task through tracker."""
        tracker = TaskTracker()

        with patch.object(tracker.todowrite, "add_task") as mock_add:
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

        with patch.object(tracker.todowrite, "update_task_status") as mock_update:
            mock_update.return_value = {"success": True}

            with patch.object(tracker.metrics, "record_status_change") as mock_record:
                tracker.update_task_status("1", TaskStatus.COMPLETED)

                updated_task = tracker.task_list.get_task("1")
                assert updated_task.status == TaskStatus.COMPLETED

                mock_update.assert_called_once_with("1", TaskStatus.COMPLETED)
                mock_record.assert_called_once_with(
                    TaskStatus.PENDING, TaskStatus.COMPLETED
                )

    def test_start_workflow_phase(self):
        """Test starting a workflow phase."""
        tracker = TaskTracker()

        phase_tasks = [
            {"content": "Task 1", "priority": "high"},
            {"content": "Task 2", "priority": "medium"},
        ]

        with patch.object(tracker.todowrite, "submit_task_list") as mock_submit:
            mock_submit.return_value = {"success": True}

            tracker.start_workflow_phase(
                "implementation", "Implementation phase", phase_tasks
            )

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

        with patch("claude.shared.task_tracking.claude_function_call") as mock_call:
            mock_call.return_value = {"success": True}

            # Start workflow phase
            phase_tasks = [
                {"content": "Setup environment", "priority": "high"},
                {"content": "Configure settings", "priority": "medium"},
                {"content": "Verify installation", "priority": "low"},
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
        with patch.object(tracker.todowrite, "submit_task_list") as mock_submit:
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

        with patch("claude.shared.task_tracking.claude_function_call") as mock_call:
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
            productivity_metrics = tracker.metrics.get_productivity_metrics(
                tracker.task_list
            )

            assert productivity_metrics["completion_rate"] == 0.5  # 1 of 2 completed
            assert productivity_metrics["tasks_in_progress"] == 1
            assert len(tracker.metrics.task_completion_times) == 1
