"""
Task tracking and TodoWrite integration for Gadugi multi-agent system.
Provides comprehensive task management, workflow tracking, and Claude Code integration.
"""

import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskError(Exception):
    """Base exception for task tracking errors."""
    pass


class TaskValidationError(TaskError):
    """Exception for task validation errors."""
    pass


@dataclass
class Task:
    """Represents a single task with comprehensive tracking."""

    id: str
    content: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # in minutes
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, id: str, content: str = None, status = TaskStatus.PENDING,
                 priority = TaskPriority.MEDIUM, title: str = None, **kwargs):
        """Initialize task with compatibility for title parameter."""
        self.id = id
        # Support both content and title parameters for API compatibility
        if content is not None:
            self.content = content
        elif title is not None:
            self.content = title
        else:
            raise ValueError("Either 'content' or 'title' must be provided")

        # Ensure status and priority are enums
        if isinstance(status, str):
            self.status = TaskStatus(status)
        else:
            self.status = status

        if isinstance(priority, str):
            self.priority = TaskPriority(priority)
        else:
            self.priority = priority

        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.estimated_duration = kwargs.get('estimated_duration')
        self.dependencies = kwargs.get('dependencies', [])
        self.tags = kwargs.get('tags', [])
        self.metadata = kwargs.get('metadata', {})

    @property
    def title(self) -> str:
        """Get title (alias for content for API compatibility)."""
        return self.content

    @title.setter
    def title(self, value: str) -> None:
        """Set title (alias for content for API compatibility)."""
        self.content = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary format."""
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status.value if hasattr(self.status, 'value') else self.status,
            "priority": self.priority.value if hasattr(self.priority, 'value') else self.priority
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary format."""
        return cls(
            id=data["id"],
            content=data["content"],
            status=TaskStatus(data["status"]),
            priority=TaskPriority(data["priority"])
        )

    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status with timestamp tracking."""
        old_status = self.status
        self.status = new_status

        if new_status == TaskStatus.IN_PROGRESS and old_status != TaskStatus.IN_PROGRESS:
            self.started_at = datetime.now()
        elif new_status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
            self.completed_at = datetime.now()

        logger.debug(f"Task {self.id} status changed: {old_status.value} -> {new_status.value}")

    def update_priority(self, new_priority: TaskPriority) -> None:
        """Update task priority."""
        old_priority = self.priority
        self.priority = new_priority
        logger.debug(f"Task {self.id} priority changed: {old_priority.value} -> {new_priority.value}")

    def is_active(self) -> bool:
        """Check if task is in an active state."""
        return self.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]

    def validate(self) -> None:
        """Validate task data."""
        if not self.id or not self.id.strip():
            raise TaskValidationError("Task ID cannot be empty")

        if not self.content or not self.content.strip():
            raise TaskValidationError("Task content cannot be empty")

    def set_estimated_duration(self, minutes: int) -> None:
        """Set estimated duration in minutes."""
        if minutes <= 0:
            raise ValueError("Duration must be positive")
        self.estimated_duration = minutes

    def add_dependency(self, task_id: str) -> None:
        """Add a task dependency."""
        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def remove_dependency(self, task_id: str) -> None:
        """Remove a task dependency."""
        if task_id in self.dependencies:
            self.dependencies.remove(task_id)

    def start(self) -> None:
        """Mark task as started."""
        self.update_status(TaskStatus.IN_PROGRESS)

    def complete(self) -> None:
        """Mark task as completed."""
        self.update_status(TaskStatus.COMPLETED)

    def block(self, reason: str = "") -> None:
        """Mark task as blocked."""
        self.update_status(TaskStatus.BLOCKED)
        if reason:
            self.metadata["block_reason"] = reason

    def cancel(self, reason: str = "") -> None:
        """Mark task as cancelled."""
        self.update_status(TaskStatus.CANCELLED)
        if reason:
            self.metadata["cancel_reason"] = reason


class TaskList:
    """Manages a collection of tasks."""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.created_at = datetime.now()

    def add_task(self, task: Task) -> None:
        """Add a task to the list."""
        if task.id in self.tasks:
            raise TaskError(f"Task with ID {task.id} already exists")

        task.validate()
        self.tasks[task.id] = task
        logger.debug(f"Added task {task.id}: {task.content}")

    def remove_task(self, task_id: str) -> Task:
        """Remove and return a task from the list."""
        if task_id not in self.tasks:
            raise TaskError(f"Task with ID {task_id} not found")

        task = self.tasks.pop(task_id)
        logger.debug(f"Removed task {task_id}")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> None:
        """Update task properties."""
        task = self.get_task(task_id)
        if not task:
            raise TaskError(f"Task with ID {task_id} not found")

        if 'status' in kwargs:
            task.update_status(kwargs['status'])
        if 'priority' in kwargs:
            task.update_priority(kwargs['priority'])
        if 'content' in kwargs:
            task.content = kwargs['content']

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks.values() if task.status == status]

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Get all tasks with a specific priority."""
        return [task for task in self.tasks.values() if task.priority == priority]

    def get_active_tasks(self) -> List[Task]:
        """Get all active tasks."""
        return [task for task in self.tasks.values() if task.is_active()]

    def count(self) -> int:
        """Get total number of tasks."""
        return len(self.tasks)

    def to_todowrite_format(self) -> List[Dict[str, Any]]:
        """Convert task list to TodoWrite format."""
        return [task.to_dict() for task in self.tasks.values()]

    @classmethod
    def from_todowrite_format(cls, data: List[Dict[str, Any]]) -> 'TaskList':
        """Create task list from TodoWrite format."""
        task_list = cls()
        for task_data in data:
            task = Task.from_dict(task_data)
            task_list.add_task(task)
        return task_list

    def get_completion_stats(self) -> Dict[str, int]:
        """Get completion statistics."""
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "blocked": 0,
            "cancelled": 0
        }

        for task in self.tasks.values():
            stats[task.status.value] += 1

        return stats


def claude_function_call(function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock function for Claude Code function calls.
    In real implementation, this would call the actual Claude Code function.
    """
    logger.info(f"Claude function call: {function_name} with parameters: {parameters}")
    return {"success": True, "function": function_name, "parameters": parameters}


class TodoWriteIntegration:
    """Integration with Claude Code's TodoWrite function."""

    def __init__(self):
        self.current_task_list: Optional[TaskList] = None
        self.call_count = 0
        self.last_update_time: Optional[datetime] = None
        self.call_history: List[Dict[str, Any]] = []

    def submit_task_list(self, task_list: TaskList) -> Dict[str, Any]:
        """Submit a complete task list via TodoWrite."""
        if task_list.count() == 0:
            raise TaskValidationError("Cannot submit empty task list")

        # Validate all tasks
        for task in task_list.tasks.values():
            task.validate()

        # Convert to TodoWrite format
        todowrite_data = task_list.to_todowrite_format()

        # Call TodoWrite function
        result = claude_function_call("TodoWrite", {"todos": todowrite_data})

        if result.get("success"):
            self.current_task_list = task_list
            self.call_count += 1
            self.last_update_time = datetime.now()

            self.call_history.append({
                "timestamp": self.last_update_time,
                "action": "submit_task_list",
                "task_count": task_list.count()
            })

            logger.info(f"Successfully submitted task list with {task_list.count()} tasks")

        return result

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> Dict[str, Any]:
        """Update a single task's status."""
        if not self.current_task_list:
            raise TaskError("No current task list to update")

        task = self.current_task_list.get_task(task_id)
        if not task:
            raise TaskError(f"Task {task_id} not found in current task list")

        # Update the task
        task.update_status(new_status)

        # Submit updated task list
        return self.submit_task_list(self.current_task_list)

    def add_task(self, task: Task) -> Dict[str, Any]:
        """Add a new task to the current task list."""
        if not self.current_task_list:
            self.current_task_list = TaskList()

        self.current_task_list.add_task(task)
        return self.submit_task_list(self.current_task_list)

    def remove_task(self, task_id: str) -> Dict[str, Any]:
        """Remove a task from the current task list."""
        if not self.current_task_list:
            raise TaskError("No current task list to modify")

        self.current_task_list.remove_task(task_id)
        return self.submit_task_list(self.current_task_list)

    def batch_update(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform batch updates on multiple tasks."""
        if not self.current_task_list:
            raise TaskError("No current task list to update")

        for update in updates:
            task_id = update.get("id")
            if not task_id:
                continue

            update_params = {k: v for k, v in update.items() if k != "id"}
            self.current_task_list.update_task(task_id, **update_params)

        return self.submit_task_list(self.current_task_list)

    def get_statistics(self) -> Dict[str, Any]:
        """Get TodoWrite usage statistics."""
        return {
            "total_calls": self.call_count,
            "last_update": self.last_update_time.isoformat() if self.last_update_time else None,
            "current_task_count": self.current_task_list.count() if self.current_task_list else 0,
            "call_history": self.call_history[-10:]  # Last 10 calls
        }

    def validate_task_list(self, task_list: TaskList) -> bool:
        """Validate a task list before submission."""
        try:
            if task_list.count() == 0:
                return False

            # Validate all tasks
            for task in task_list.tasks.values():
                task.validate()

            return True
        except Exception as e:
            logger.error(f"Task list validation failed: {e}")
            return False


class WorkflowPhaseTracker:
    """Tracks workflow phases and their associated tasks."""

    def __init__(self, workflow_id: Optional[str] = None):
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.current_phase: Optional[str] = None
        self.phase_history: List[Dict[str, Any]] = []
        self.created_at = datetime.now()

    def start_phase(self, phase_name: str, description: str = "") -> None:
        """Start a new workflow phase."""
        if self.current_phase:
            logger.warning(f"Starting new phase '{phase_name}' while '{self.current_phase}' is still active")

        self.current_phase = phase_name

        phase_entry = {
            "phase": phase_name,
            "description": description,
            "status": "in_progress",
            "started_at": datetime.now(),
            "completed_at": None,
            "duration_seconds": None,
            "completion_note": None,
            "failure_reason": None,
            "error_context": None
        }

        self.phase_history.append(phase_entry)
        logger.info(f"Started workflow phase: {phase_name}")

    def complete_phase(self, completion_note: str = "") -> None:
        """Complete the current workflow phase."""
        if not self.current_phase:
            raise TaskError("No active phase to complete")

        # Find the current phase entry
        current_entry = None
        for entry in reversed(self.phase_history):
            if entry["phase"] == self.current_phase and entry["status"] == "in_progress":
                current_entry = entry
                break

        if current_entry:
            now = datetime.now()
            current_entry["status"] = "completed"
            current_entry["completed_at"] = now
            current_entry["completion_note"] = completion_note
            current_entry["duration_seconds"] = (now - current_entry["started_at"]).total_seconds()

        logger.info(f"Completed workflow phase: {self.current_phase}")
        self.current_phase = None

    def fail_phase(self, failure_reason: str, error_context: Optional[Dict[str, Any]] = None) -> None:
        """Mark the current workflow phase as failed."""
        if not self.current_phase:
            raise TaskError("No active phase to fail")

        # Find the current phase entry
        current_entry = None
        for entry in reversed(self.phase_history):
            if entry["phase"] == self.current_phase and entry["status"] == "in_progress":
                current_entry = entry
                break

        if current_entry:
            now = datetime.now()
            current_entry["status"] = "failed"
            current_entry["completed_at"] = now
            current_entry["failure_reason"] = failure_reason
            current_entry["error_context"] = error_context or {}
            current_entry["duration_seconds"] = (now - current_entry["started_at"]).total_seconds()

        logger.error(f"Failed workflow phase: {self.current_phase} - {failure_reason}")
        self.current_phase = None

    def get_phase_summary(self) -> Dict[str, Any]:
        """Get summary of all workflow phases."""
        completed_phases = sum(1 for p in self.phase_history if p["status"] == "completed")
        failed_phases = sum(1 for p in self.phase_history if p["status"] == "failed")
        total_phases = len(self.phase_history)

        total_duration = sum(
            p["duration_seconds"] or 0
            for p in self.phase_history
            if p["duration_seconds"] is not None
        )

        return {
            "workflow_id": self.workflow_id,
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "failed_phases": failed_phases,
            "in_progress_phases": total_phases - completed_phases - failed_phases,
            "success_rate": completed_phases / total_phases if total_phases > 0 else 0,
            "total_duration_seconds": total_duration,
            "current_phase": self.current_phase
        }

    def create_phase_task_list(self, phase_name: str, tasks: List[Dict[str, Any]]) -> TaskList:
        """Create a task list for a specific phase."""
        task_list = TaskList()

        for i, task_data in enumerate(tasks, 1):
            task_id = f"{phase_name}-{i}"
            content = task_data["content"]
            priority_str = task_data.get("priority", "medium")

            # Convert string priority to enum
            priority = TaskPriority(priority_str.lower())

            task = Task(
                id=task_id,
                content=content,
                priority=priority
            )

            # Add any additional metadata
            if "estimated_duration" in task_data:
                task.set_estimated_duration(task_data["estimated_duration"])

            task_list.add_task(task)

        return task_list


class TaskMetrics:
    """Collects and analyzes task performance metrics."""

    def __init__(self):
        self.start_time = datetime.now()
        self.task_completion_times: List[Dict[str, Any]] = []
        self.status_change_count: Dict[str, int] = {}
        self.priority_distribution: Dict[str, int] = {}

    def record_task_completion(self, task: Task) -> None:
        """Record task completion time."""
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()

            self.task_completion_times.append({
                "task_id": task.id,
                "duration_seconds": duration,
                "priority": task.priority.value,
                "completed_at": task.completed_at
            })

            logger.debug(f"Recorded completion for task {task.id}: {duration:.1f}s")

    def record_status_change(self, from_status: TaskStatus, to_status: TaskStatus) -> None:
        """Record status change for analytics."""
        change_key = f"{from_status.value}->{to_status.value}"
        self.status_change_count[change_key] = self.status_change_count.get(change_key, 0) + 1

    def calculate_completion_rate(self, task_list: TaskList) -> float:
        """Calculate task completion rate."""
        if task_list.count() == 0:
            return 0.0

        completed_count = len(task_list.get_tasks_by_status(TaskStatus.COMPLETED))
        return completed_count / task_list.count()

    def calculate_average_completion_time(self) -> float:
        """Calculate average task completion time."""
        if not self.task_completion_times:
            return 0.0

        total_time = sum(record["duration_seconds"] for record in self.task_completion_times)
        return total_time / len(self.task_completion_times)

    def get_productivity_metrics(self, task_list: TaskList) -> Dict[str, Any]:
        """Get comprehensive productivity metrics."""
        stats = task_list.get_completion_stats()

        return {
            "completion_rate": self.calculate_completion_rate(task_list),
            "average_completion_time": self.calculate_average_completion_time(),
            "total_status_changes": sum(self.status_change_count.values()),
            "total_tasks": stats["total"],
            "completed_tasks": stats["completed"],
            "tasks_in_progress": stats["in_progress"],
            "blocked_tasks": stats["blocked"],
            "task_completion_count": len(self.task_completion_times)
        }

    def start_workflow_phase(self, phase_name: str, description: str = None) -> None:
        """Start tracking a workflow phase."""
        self.current_phase = phase_name
        self.phase_start_time = datetime.now()
        log_msg = f"Started workflow phase: {phase_name}"
        if description:
            log_msg += f" - {description}"
        logger.debug(log_msg)

    def record_phase_start(self, phase_name: str) -> None:
        """Record the start of a workflow phase."""
        self.start_workflow_phase(phase_name)


class TaskTracker:
    """Main task tracking coordinator that integrates all components."""

    def __init__(self, workflow_id: Optional[str] = None):
        self.task_list = TaskList()
        self.todowrite = TodoWriteIntegration()
        self.phase_tracker = WorkflowPhaseTracker(workflow_id)
        self.metrics = TaskMetrics()
        self.created_at = datetime.now()

    def create_task(self, content: str, priority: TaskPriority = TaskPriority.MEDIUM,
                   **kwargs) -> Task:
        """Create and add a new task."""
        task_id = kwargs.get("id") or str(uuid.uuid4())[:8]

        task = Task(
            id=task_id,
            content=content,
            priority=priority,
            **{k: v for k, v in kwargs.items() if k != "id"}
        )

        self.task_list.add_task(task)

        # Submit to TodoWrite
        result = self.todowrite.add_task(task)

        if not result.get("success"):
            # Remove from local list if TodoWrite failed
            self.task_list.remove_task(task_id)
            raise TaskError(f"Failed to create task in TodoWrite: {result}")

        logger.info(f"Created task: {task.content}")
        return task

    def add_task(self, task: Task) -> None:
        """Add an existing task to the tracker."""
        self.task_list.add_task(task)

        # Submit to TodoWrite
        result = self.todowrite.add_task(task)

        if not result.get("success"):
            # Remove from local list if TodoWrite failed
            self.task_list.remove_task(task.id)
            raise TaskError(f"Failed to add task to TodoWrite: {result}")

        logger.info(f"Added task: {task.content}")

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.task_list.get_task(task_id)

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
        """Update task status with metrics tracking."""
        task = self.task_list.get_task(task_id)
        if not task:
            raise TaskError(f"Task {task_id} not found")

        old_status = task.status

        # Update locally
        task.update_status(new_status)

        # Record metrics
        self.metrics.record_status_change(old_status, new_status)

        if new_status == TaskStatus.COMPLETED:
            self.metrics.record_task_completion(task)

        # Update TodoWrite
        result = self.todowrite.update_task_status(task_id, new_status)

        if not result.get("success"):
            # Revert local change if TodoWrite failed
            task.update_status(old_status)
            raise TaskError(f"Failed to update task status in TodoWrite: {result}")

    def start_workflow_phase(self, phase_name: str, description: str,
                           phase_tasks: Optional[List[Dict[str, Any]]] = None) -> None:
        """Start a new workflow phase with associated tasks."""
        # Start the phase
        self.phase_tracker.start_phase(phase_name, description)

        try:
            # Create task list for this phase (if tasks provided)
            if phase_tasks:
                phase_task_list = self.phase_tracker.create_phase_task_list(phase_name, phase_tasks)

                # Add tasks to main task list
                for task in phase_task_list.tasks.values():
                    self.task_list.add_task(task)

                # Submit to TodoWrite
                result = self.todowrite.submit_task_list(self.task_list)

            if not result.get("success"):
                raise TaskError(f"Failed to submit phase tasks to TodoWrite: {result}")

            logger.info(f"Started workflow phase '{phase_name}' with {len(phase_tasks)} tasks")

        except Exception as e:
            # If anything fails, don't start the phase
            self.phase_tracker.current_phase = None
            self.phase_tracker.phase_history.pop()  # Remove the failed phase entry
            raise e

    def complete_workflow_phase(self, completion_note: str = "") -> None:
        """Complete the current workflow phase."""
        self.phase_tracker.complete_phase(completion_note)

        logger.info(f"Completed workflow phase with note: {completion_note}")

    def fail_workflow_phase(self, failure_reason: str,
                          error_context: Optional[Dict[str, Any]] = None) -> None:
        """Mark the current workflow phase as failed."""
        self.phase_tracker.fail_phase(failure_reason, error_context)

        logger.error(f"Failed workflow phase: {failure_reason}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        completion_stats = self.task_list.get_completion_stats()

        # Transform completion stats to match expected format
        task_summary = {
            "total_tasks": completion_stats["total"],
            "completed_tasks": completion_stats["completed"],
            "active_tasks": completion_stats["pending"] + completion_stats["in_progress"] + completion_stats["blocked"],
            "pending_tasks": completion_stats["pending"],
            "in_progress_tasks": completion_stats["in_progress"],
            "blocked_tasks": completion_stats["blocked"],
            "cancelled_tasks": completion_stats["cancelled"]
        }

        return {
            "task_summary": task_summary,
            "phase_summary": self.phase_tracker.get_phase_summary(),
            "productivity_metrics": self.metrics.get_productivity_metrics(self.task_list),
            "todowrite_stats": self.todowrite.get_statistics(),
            "created_at": self.created_at.isoformat()
        }

    def export_data(self, include_history: bool = True) -> Dict[str, Any]:
        """Export all tracking data for backup or analysis."""
        data = {
            "workflow_id": self.phase_tracker.workflow_id,
            "created_at": self.created_at.isoformat(),
            "task_list": self.task_list.to_todowrite_format(),
            "phase_summary": self.phase_tracker.get_phase_summary(),
            "metrics": self.metrics.get_productivity_metrics(self.task_list)
        }

        if include_history:
            data["phase_history"] = self.phase_tracker.phase_history
            data["task_completion_history"] = self.metrics.task_completion_times
            data["todowrite_history"] = self.todowrite.call_history

        return data
