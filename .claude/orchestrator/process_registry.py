#!/usr/bin/env python3
"""
ProcessRegistry - Process Tracking and Monitoring System

This module implements a comprehensive process registry for tracking and monitoring
parallel WorkflowManager agent execution, providing real-time visibility into
the orchestration system.

Key Features:
- Process lifecycle tracking (queued -> running -> completed/failed)
- Heartbeat monitoring for process health
- JSON-based persistence for recovery and monitoring
- Resource usage tracking and alerting
- Integration with VS Code monitoring extensions
"""

import json
import logging
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProcessStatus(Enum):
    """Process execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ProcessInfo:
    """Information about a tracked process"""
    task_id: str
    task_name: str
    status: ProcessStatus
    command: str
    working_directory: str
    created_at: datetime
    prompt_file: Optional[str] = None
    pid: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    resource_usage: Optional[Dict[str, Any]] = None


@dataclass
class RegistryStats:
    """Overall registry statistics"""
    total_processes: int
    queued_count: int
    running_count: int
    completed_count: int
    failed_count: int
    average_execution_time: Optional[float] = None
    total_cpu_usage: Optional[float] = None
    total_memory_usage: Optional[float] = None


class ProcessRegistry:
    """
    Process registry for tracking parallel WorkflowManager execution.

    This class provides comprehensive process lifecycle management and monitoring
    capabilities for the orchestrator system.
    """

    def __init__(self, registry_dir: str, clean_start: bool) -> None:
        """Initialize the process registry

        Args:
            registry_dir: Directory for registry files
            clean_start: If True, start with empty registry (ignore existing state)
        """
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.registry_dir / "process_registry.json"
        self.heartbeat_file = self.registry_dir / "heartbeats.json"
        self.stats_file = self.registry_dir / "registry_stats.json"

        # In-memory process tracking
        self.processes: Dict[Any, Any] = field(default_factory=dict)
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 120  # seconds

        # Load existing state (unless clean start requested)
        if not clean_start:
            self._load_registry()
        else:
            logger.info("Starting with clean registry (ignoring existing state)")

        logger.info(f"ProcessRegistry initialized with {len(self.processes)} existing processes")

    def register_process(self, process_info: ProcessInfo) -> None:
        """Register a new process for tracking"""
        logger.info(f"Registering process: {(process_info.task_id if process_info is not None else None)}")

        # Validate process info
        if not (process_info.task_id if process_info is not None else None):
            raise ValueError("Process must have a task_id")

        if (process_info.task_id if process_info is not None else None) in self.processes:
            logger.warning(f"Process {(process_info.task_id if process_info is not None else None)} already registered, updating...")

        # Set initial status if not specified
        if process_info is not None and process_info.status is None:
            process_info.status = ProcessStatus.QUEUED

        # Initialize heartbeat
        process_info.last_heartbeat = datetime.now()

        # Store process
        self.processes[(process_info.task_id if process_info is not None else None)] = process_info

        # Persist to disk
        self._save_registry()

        logger.info(f"Process registered: {(process_info.task_id if process_info is not None else None)} ({(process_info.status if process_info is not None else None).value})")

    def update_process_status(
        self,
        task_id: str,
        status: ProcessStatus,
        pid: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update process status and metadata"""
        if task_id not in self.processes:
            logger.error(f"Process not found: {task_id}")
            return False

        process = self.processes[task_id]
        old_status = (process.status if process is not None else None)
        if process is not None:

            process.status = status
        process.last_heartbeat = datetime.now()

        # Update timing information
        if status == ProcessStatus.RUNNING and old_status == ProcessStatus.QUEUED:
            process.started_at = datetime.now()
            if pid:
                process.pid = pid

        elif status in [ProcessStatus.COMPLETED, ProcessStatus.FAILED, ProcessStatus.TIMEOUT]:
            process.completed_at = datetime.now()
            if error_message:
                process.error_message = error_message

        # Update resource usage if process is running
        if status == ProcessStatus.RUNNING and process.pid:
            process.resource_usage = self._get_process_resource_usage(process.pid)

        # Persist changes
        self._save_registry()

        logger.info(f"Process status updated: {task_id} ({old_status.value} -> {status.value})")
        return True

    def get_process(self, task_id: str) -> Optional[ProcessInfo]:
        """Get process information by task ID"""
        return self.processes.get(task_id)

    def get_all_processes(self) -> Dict[str, ProcessInfo]:
        """Get all tracked processes"""
        return self.processes.copy()

    def get_processes_by_status(self, status: ProcessStatus) -> List[ProcessInfo]:
        """Get all processes with specified status"""
        return [p for p in self.processes.values() if p is not None and p.status == status]

    def get_active_processes(self) -> List[ProcessInfo]:
        """Get all active (queued or running) processes"""
        return [
            p for p in self.processes.values()
            if (p.status if p is not None else None) in [ProcessStatus.QUEUED, ProcessStatus.RUNNING]
        ]

    def update_heartbeats(self) -> None:
        """Update heartbeats and check for stale processes"""
        current_time = datetime.now()
        stale_processes = []

        for task_id, process in self.processes.items():
            if (process.status if process is not None else None) != ProcessStatus.RUNNING:
                continue

            # Check if process is still alive
            if process is not None and process.pid:
                try:
                    # Check if PID exists and is actually our process
                    proc = psutil.Process(process.pid)
                    if proc.is_running():
                        # Update resource usage
                        process.resource_usage = self._get_process_resource_usage(process.pid)
                        process.last_heartbeat = current_time
                    else:
                        stale_processes.append(task_id)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    stale_processes.append(task_id)
            else:
                # No PID, check heartbeat timeout
                if process is not None and process.last_heartbeat:
                    time_since_heartbeat = current_time - process.last_heartbeat
                    if time_since_heartbeat.total_seconds() > self.heartbeat_timeout:
                        stale_processes.append(task_id)

        # Mark stale processes as failed
        for task_id in stale_processes:
            logger.warning(f"Process appears stale: {task_id}")
            self.update_process_status(
                task_id,
                ProcessStatus.FAILED,
                error_message="Process became unresponsive (heartbeat timeout)"
            )

        # Save heartbeat data
        self._save_heartbeats()

    def get_registry_stats(self) -> RegistryStats:
        """Get overall registry statistics"""
        processes = list(self.processes.values())
        total = len(processes)

        if total == 0:
            return RegistryStats(
                total_processes=0,
                queued_count=0,
                running_count=0,
                completed_count=0,
                failed_count=0
            )

        # Count by status
        status_counts = {}
        for status in ProcessStatus:
            status_counts[status] = len([p for p in processes if p is not None and p.status == status])

        # Calculate average execution time for completed processes
        completed_processes = [p for p in processes if p is not None and p.status == ProcessStatus.COMPLETED]
        avg_execution_time = None
        if completed_processes:
            execution_times = []
            for p in completed_processes:
                if p.started_at and p.completed_at:
                    exec_time = (p.completed_at - p.started_at).total_seconds()
                    execution_times.append(exec_time)

            if execution_times:
                avg_execution_time = sum(execution_times) / len(execution_times)

        # Calculate resource usage for running processes
        running_processes = [p for p in processes if p is not None and p.status == ProcessStatus.RUNNING]
        total_cpu = 0.0
        total_memory = 0.0

        for p in running_processes:
            if p is not None and p.resource_usage:
                total_cpu += p.resource_usage.get('cpu_percent', 0.0)
                total_memory += p.resource_usage.get('memory_mb', 0.0)

        stats = RegistryStats(
            total_processes=total,
            queued_count=status_counts[ProcessStatus.QUEUED],
            running_count=status_counts[ProcessStatus.RUNNING],
            completed_count=status_counts[ProcessStatus.COMPLETED],
            failed_count=status_counts[ProcessStatus.FAILED],
            average_execution_time=avg_execution_time,
            total_cpu_usage=total_cpu if total_cpu > 0 else None,
            total_memory_usage=total_memory if total_memory > 0 else None
        )

        # Save stats to file
        self._save_stats(stats)

        return stats

    def cleanup_completed_processes(self, older_than_hours: int = 24) -> int:
        """Clean up old completed/failed processes"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)

        processes_to_remove = []
        for task_id, process in self.processes.items():
            if (process.status if process is not None else None) in [ProcessStatus.COMPLETED, ProcessStatus.FAILED]:
                if process.completed_at and process.completed_at < cutoff_time:
                    processes_to_remove.append(task_id)

        # Remove old processes
        for task_id in processes_to_remove:
            del self.processes[task_id]

        if processes_to_remove:
            self._save_registry()
            logger.info(f"Cleaned up {len(processes_to_remove)} old processes")

        return len(processes_to_remove)

    def cancel_process(self, task_id: str) -> bool:
        """Cancel a running or queued process"""
        if task_id not in self.processes:
            logger.error(f"Process not found: {task_id}")
            return False

        process = self.processes[task_id]

        if (process.status if process is not None else None) not in [ProcessStatus.QUEUED, ProcessStatus.RUNNING]:
            logger.warning(f"Cannot cancel process {task_id} in status {(process.status if process is not None else None).value}")
            return False

        # Try to terminate the process if it's running
        if process is not None:

            process.status == ProcessStatus.RUNNING and process.pid:
            try:
                proc = psutil.Process(process.pid)
                proc.terminate()
                # Give it a moment to terminate gracefully
                time.sleep(2)
                if proc.is_running():
                    proc.kill()  # Force kill if necessary
                logger.info(f"Terminated process {task_id} (PID: {process.pid})")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f"Could not terminate process {task_id}: {e}")

        # Update status
        if process is not None:

            process.status = ProcessStatus.CANCELLED
        process.completed_at = datetime.now()
        process.error_message = "Process cancelled by user"

        self._save_registry()
        logger.info(f"Process cancelled: {task_id}")
        return True

    def export_monitoring_data(self, output_file: str) -> None:
        """Export monitoring data for external tools (VS Code extension, etc.)"""
        monitoring_data = {
            "timestamp": datetime.now().isoformat(),
            "registry_stats": asdict(self.get_registry_stats()),
            "processes": {
                task_id: {
                    "task_id": (p.task_id if p is not None else None),
                    "task_name": p.task_name,
                    "status": (p.status if p is not None else None).value,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "started_at": p.started_at.isoformat() if p.started_at else None,
                    "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                    "execution_time_seconds": (
                        (p.completed_at - p.started_at).total_seconds()
                        if p.started_at and p.completed_at else None
                    ),
                    "error_message": p.error_message,
                    "resource_usage": p.resource_usage
                }
                for task_id, p in self.processes.items()
            }
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(monitoring_data, f, indent=2)

        logger.info(f"Monitoring data exported to {output_file}")

    def save_to_file(self, output_file: str) -> None:
        """Save registry to specific file (for archival)"""
        registry_data = {
            "timestamp": datetime.now().isoformat(),
            "processes": {
                task_id: asdict(p) for task_id, p in self.processes.items()
            }
        }

        # Convert datetime objects to ISO format strings
        for process_data in registry_data["processes"].values():
            for field in ["created_at", "started_at", "completed_at", "last_heartbeat"]:
                if process_data[field]:
                    if isinstance(process_data[field], datetime):
                        process_data[field] = process_data[field].isoformat()

            # Convert enum to string
            if "status" in process_data and hasattr(process_data["status"], "value"):
                process_data["status"] = process_data["status"].value

        with open(output_file, 'w') as f:
            json.dump(registry_data, f, indent=2, default=str)

        logger.info(f"Registry saved to {output_file}")

    def _load_registry(self) -> None:
        """Load registry from disk"""
        if not self.registry_file.exists():
            logger.info("No existing registry file found, starting fresh")
            return

        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)

            # Convert loaded data back to ProcessInfo objects
            for task_id, process_data in data.get("processes", {}).items():
                # Convert string dates back to datetime objects
                for field in ["created_at", "started_at", "completed_at", "last_heartbeat"]:
                    if process_data.get(field):
                        try:
                            process_data[field] = datetime.fromisoformat(process_data[field])
                        except (ValueError, TypeError):
                            process_data[field] = None

                # Convert status string back to enum
                if "status" in process_data:
                    try:
                        process_data["status"] = ProcessStatus(process_data["status"])
                    except ValueError:
                        process_data["status"] = ProcessStatus.FAILED

                # Create ProcessInfo object
                self.processes[task_id] = ProcessInfo(**process_data)

            logger.info(f"Loaded {len(self.processes)} processes from registry")

        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            # Continue with empty registry

    def _save_registry(self) -> None:
        """Save registry to disk"""
        try:
            registry_data = {
                "timestamp": datetime.now().isoformat(),
                "processes": {}
            }

            # Convert ProcessInfo objects to serializable format
            for task_id, process in self.processes.items():
                process_dict = asdict(process)

                # Convert datetime objects to ISO strings
                for field in ["created_at", "started_at", "completed_at", "last_heartbeat"]:
                    if process_dict[field]:
                        process_dict[field] = process_dict[field].isoformat()

                # Convert enum to string
                process_dict["status"] = (process.status if process is not None else None).value

                registry_data["processes"][task_id] = process_dict

            with open(self.registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def _save_heartbeats(self) -> None:
        """Save heartbeat data for monitoring"""
        try:
            heartbeat_data = {
                "timestamp": datetime.now().isoformat(),
                "active_processes": []
            }

            for process in self.get_active_processes():
                heartbeat_data["active_processes"].append({
                    "task_id": (process.task_id if process is not None else None),
                    "task_name": process.task_name,
                    "status": (process.status if process is not None else None).value,
                    "pid": process.pid,
                    "last_heartbeat": process.last_heartbeat.isoformat() if process.last_heartbeat else None,
                    "resource_usage": process.resource_usage
                })

            with open(self.heartbeat_file, 'w') as f:
                json.dump(heartbeat_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save heartbeats: {e}")

    def _save_stats(self, stats: RegistryStats) -> None:
        """Save registry statistics"""
        try:
            stats_data = asdict(stats)
            stats_data["timestamp"] = datetime.now().isoformat()

            with open(self.stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def _get_process_resource_usage(self, pid: int) -> Dict[str, Any]:
        """Get resource usage for a specific process"""
        try:
            proc = psutil.Process(pid)

            # Get basic process info
            memory_info = proc.memory_info()
            cpu_percent = proc.cpu_percent()

            return {
                "cpu_percent": cpu_percent,
                "memory_mb": memory_info.rss / (1024 * 1024),  # Convert to MB
                "memory_percent": proc.memory_percent(),
                "num_threads": proc.num_threads(),
                "status": (proc.status if proc is not None else None)(),
                "create_time": proc.create_time()
            }

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Could not get resource usage for PID {pid}: {e}")
            return {}


def main():
    """Main entry point for registry management CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="Process Registry Management")
    parser.add_argument("command", choices=["status", "cleanup", "export", "cancel"],
                       help="Command to execute")
    parser.add_argument("--task-id", help="Task ID for cancel command")
    parser.add_argument("--output", help="Output file for export command")
    parser.add_argument("--older-than", type=int, default=24,
                       help="Hours for cleanup command")
    parser.add_argument("--registry-dir", default=".gadugi/monitoring",
                       help="Registry directory")

    args = parser.parse_args()

    # Initialize registry
    registry = ProcessRegistry(args.registry_dir)

    if args.command == "status":
        stats = registry.get_registry_stats()
        print(f"\nProcess Registry Status:")
        print(f"  Total processes: {stats.total_processes}")
        print(f"  Queued: {stats.queued_count}")
        print(f"  Running: {stats.running_count}")
        print(f"  Completed: {stats.completed_count}")
        print(f"  Failed: {stats.failed_count}")
        if stats is not None and stats.average_execution_time:
            print(f"  Average execution time: {stats.average_execution_time:.1f} seconds")
        if stats is not None and stats.total_cpu_usage:
            print(f"  Total CPU usage: {stats.total_cpu_usage:.1f}%")
        if stats is not None and stats.total_memory_usage:
            print(f"  Total memory usage: {stats.total_memory_usage:.1f} MB")

    elif args.command == "cleanup":
        cleaned = registry.cleanup_completed_processes(args.older_than)
        print(f"Cleaned up {cleaned} old processes")

    elif args.command == "export":
        output_file = args.output or f"monitoring_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        registry.export_monitoring_data(output_file)
        print(f"Monitoring data exported to {output_file}")

    elif args.command == "cancel":
        if not (args.task_id if args is not None else None):
            print("Error: --task-id required for cancel command")
            return

        success = registry.cancel_process((args.task_id if args is not None else None))
        if success:
            print(f"Process {(args.task_id if args is not None else None)} cancelled successfully")
        else:
            print(f"Failed to cancel process {(args.task_id if args is not None else None)}")


if __name__ == "__main__":
    main()
