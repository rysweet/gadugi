#!/usr/bin/env python3
"""
Execution Monitor Engine for Gadugi v0.3

Real-time monitoring and coordination of parallel agent execution.
Provides process tracking, resource monitoring, and performance analytics.
"""

import asyncio
import json
import logging
import os
import psutil
import signal
import subprocess
import threading
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Union, Set
from enum import Enum
from pathlib import Path


class ProcessState(Enum):
    """Process lifecycle states."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    RECOVERING = "recovering"


class HealthState(Enum):
    """Process health states."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertType(Enum):
    """Alert types."""
    RESOURCE = "resource"
    PERFORMANCE = "performance"
    PROCESS = "process"
    SYSTEM = "system"


@dataclass
class ResourceLimits:
    """Resource limits for process monitoring."""
    cpu_limit: str = "100m"
    memory_limit: str = "256MB"
    timeout: int = 300
    disk_limit: Optional[str] = None
    network_limit: Optional[str] = None


@dataclass
class AlertThresholds:
    """Thresholds for generating alerts."""
    cpu_threshold: float = 80.0
    memory_threshold: float = 80.0
    error_rate_threshold: float = 10.0
    response_time_threshold: float = 5.0
    disk_threshold: float = 85.0


@dataclass
class ResourceUsage:
    """Current resource usage metrics."""
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_io: float
    open_files: int
    threads: int


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    operations_per_second: float
    average_response_time: float
    error_rate: float
    success_rate: float
    throughput: float
    last_updated: datetime


@dataclass
class ProcessProgress:
    """Process execution progress."""
    current_phase: str
    completion_percentage: float
    estimated_remaining: float
    milestones_completed: List[str]
    next_milestone: Optional[str]


@dataclass
class Alert:
    """Alert information."""
    type: AlertType
    severity: str
    message: str
    threshold: float
    current_value: float
    timestamp: datetime
    process_id: str
    acknowledged: bool = False


@dataclass
class MonitoredProcess:
    """Information about a monitored process."""
    process_id: str
    agent_type: str
    task_id: str
    pid: Optional[int]
    state: ProcessState
    health_state: HealthState
    start_time: datetime
    end_time: Optional[datetime]
    command: List[str]
    working_directory: str
    resource_limits: ResourceLimits
    alert_thresholds: AlertThresholds
    resource_usage: Optional[ResourceUsage]
    performance_metrics: Optional[PerformanceMetrics]
    progress: Optional[ProcessProgress]
    alerts: List[Alert]
    restart_count: int = 0
    last_heartbeat: Optional[datetime] = None


@dataclass
class MonitoringConfiguration:
    """Configuration for execution monitoring."""
    monitoring_interval: int = 5
    collect_metrics: bool = True
    enable_real_time: bool = True
    auto_restart: bool = True
    max_restart_attempts: int = 3
    notification_channels: List[str] = None
    alert_config: Optional[Dict[str, Any]] = None
    resource_config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = ["email"]


class ExecutionMonitorEngine:
    """Engine for monitoring parallel agent execution."""

    def __init__(self):
        """Initialize the Execution Monitor Engine."""
        self.logger = self._setup_logging()
        self.monitored_processes: Dict[str, MonitoredProcess] = {}
        self.configuration = MonitoringConfiguration()
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.alert_handlers = self._setup_alert_handlers()
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.lock = threading.Lock()
        
        # Process management
        self.process_registry: Dict[str, subprocess.Popen] = {}
        self.shutdown_event = threading.Event()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the Execution Monitor Engine."""
        logger = logging.getLogger("execution_monitor")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _setup_alert_handlers(self) -> Dict[str, Any]:
        """Set up alert notification handlers."""
        return {
            "email": self._send_email_alert,
            "webhook": self._send_webhook_alert,
            "slack": self._send_slack_alert,
            "file": self._write_file_alert
        }

    def start_monitoring(self, configuration: Optional[MonitoringConfiguration] = None):
        """Start the monitoring system."""
        if configuration:
            self.configuration = configuration
        
        self.monitoring_active = True
        self.shutdown_event.clear()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info("Execution monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring_active = False
        self.shutdown_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10)
        
        self.logger.info("Execution monitoring stopped")

    def monitor_process(self, 
                       process_id: str,
                       agent_type: str,
                       task_id: str,
                       command: List[str],
                       working_directory: str,
                       resource_limits: Optional[ResourceLimits] = None,
                       alert_thresholds: Optional[AlertThresholds] = None) -> Dict[str, Any]:
        """Start monitoring a new process."""
        try:
            with self.lock:
                if process_id in self.monitored_processes:
                    return {
                        "success": False,
                        "error": f"Process {process_id} is already being monitored"
                    }
                
                # Create monitored process entry
                monitored_process = MonitoredProcess(
                    process_id=process_id,
                    agent_type=agent_type,
                    task_id=task_id,
                    pid=None,
                    state=ProcessState.INITIALIZING,
                    health_state=HealthState.UNKNOWN,
                    start_time=datetime.now(),
                    end_time=None,
                    command=command,
                    working_directory=working_directory,
                    resource_limits=resource_limits or ResourceLimits(),
                    alert_thresholds=alert_thresholds or AlertThresholds(),
                    resource_usage=None,
                    performance_metrics=None,
                    progress=None,
                    alerts=[]
                )
                
                # Start the actual process
                process = self._start_process(monitored_process)
                if process:
                    monitored_process.pid = process.pid
                    monitored_process.state = ProcessState.RUNNING
                    monitored_process.health_state = HealthState.HEALTHY
                    monitored_process.last_heartbeat = datetime.now()
                    
                    self.monitored_processes[process_id] = monitored_process
                    self.process_registry[process_id] = process
                    
                    self.logger.info(f"Started monitoring process {process_id} (PID: {process.pid})")
                    
                    return {
                        "success": True,
                        "process_id": process_id,
                        "pid": process.pid,
                        "status": monitored_process.state.value
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to start process {process_id}"
                    }
                    
        except Exception as e:
            self.logger.error(f"Error starting process monitoring for {process_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _start_process(self, monitored_process: MonitoredProcess) -> Optional[subprocess.Popen]:
        """Start the actual process."""
        try:
            # Prepare environment
            env = os.environ.copy()
            env['GADUGI_PROCESS_ID'] = monitored_process.process_id
            env['GADUGI_TASK_ID'] = monitored_process.task_id
            
            # Start process
            process = subprocess.Popen(
                monitored_process.command,
                cwd=monitored_process.working_directory,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            return process
            
        except Exception as e:
            self.logger.error(f"Failed to start process: {e}")
            return None

    def stop_process_monitoring(self, process_id: str, cleanup_resources: bool = True) -> Dict[str, Any]:
        """Stop monitoring a specific process."""
        try:
            with self.lock:
                if process_id not in self.monitored_processes:
                    return {
                        "success": False,
                        "error": f"Process {process_id} is not being monitored"
                    }
                
                monitored_process = self.monitored_processes[process_id]
                
                # Terminate the process if still running
                if process_id in self.process_registry:
                    process = self.process_registry[process_id]
                    if process.poll() is None:  # Still running
                        self._graceful_shutdown(process)
                    
                    del self.process_registry[process_id]
                
                # Update process state
                monitored_process.state = ProcessState.TERMINATED
                monitored_process.end_time = datetime.now()
                
                # Clean up resources if requested
                if cleanup_resources:
                    del self.monitored_processes[process_id]
                    if process_id in self.metrics_history:
                        del self.metrics_history[process_id]
                
                self.logger.info(f"Stopped monitoring process {process_id}")
                
                return {
                    "success": True,
                    "process_id": process_id,
                    "final_state": monitored_process.state.value
                }
                
        except Exception as e:
            self.logger.error(f"Error stopping process monitoring for {process_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _graceful_shutdown(self, process: subprocess.Popen, timeout: int = 10):
        """Gracefully shutdown a process."""
        try:
            # Try SIGTERM first
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown failed
                process.kill()
                process.wait()
                
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")

    def get_process_status(self, 
                          process_id: Optional[str] = None,
                          include_metrics: bool = True,
                          include_history: bool = False) -> Dict[str, Any]:
        """Get status of monitored processes."""
        try:
            with self.lock:
                if process_id:
                    if process_id not in self.monitored_processes:
                        return {
                            "success": False,
                            "error": f"Process {process_id} not found"
                        }
                    
                    process = self.monitored_processes[process_id]
                    status = self._build_process_status(process, include_metrics, include_history)
                    
                    return {
                        "success": True,
                        "process_status": status
                    }
                else:
                    # Return status for all processes
                    all_status = {}
                    for pid, process in self.monitored_processes.items():
                        all_status[pid] = self._build_process_status(
                            process, include_metrics, include_history
                        )
                    
                    return {
                        "success": True,
                        "processes": all_status,
                        "summary": self._build_system_summary()
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting process status: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _build_process_status(self,
                            process: MonitoredProcess,
                            include_metrics: bool,
                            include_history: bool) -> Dict[str, Any]:
        """Build comprehensive status for a process."""
        status = {
            "process_id": process.process_id,
            "agent_type": process.agent_type,
            "task_id": process.task_id,
            "state": process.state.value,
            "health_state": process.health_state.value,
            "start_time": process.start_time.isoformat(),
            "duration": (datetime.now() - process.start_time).total_seconds(),
            "restart_count": process.restart_count
        }
        
        if process.end_time:
            status["end_time"] = process.end_time.isoformat()
            status["total_duration"] = (process.end_time - process.start_time).total_seconds()
        
        if process.progress:
            status["progress"] = asdict(process.progress)
        
        if include_metrics and process.resource_usage:
            status["resource_usage"] = asdict(process.resource_usage)
        
        if include_metrics and process.performance_metrics:
            status["performance_metrics"] = {
                **asdict(process.performance_metrics),
                "last_updated": process.performance_metrics.last_updated.isoformat()
            }
        
        if process.alerts:
            status["alerts"] = [
                {
                    **asdict(alert),
                    "timestamp": alert.timestamp.isoformat(),
                    "type": alert.type.value
                }
                for alert in process.alerts
            ]
        
        if include_history and process.process_id in self.metrics_history:
            status["metrics_history"] = self.metrics_history[process.process_id]
        
        return status

    def _build_system_summary(self) -> Dict[str, Any]:
        """Build system-wide monitoring summary."""
        active_processes = len([
            p for p in self.monitored_processes.values()
            if p.state in [ProcessState.RUNNING, ProcessState.INITIALIZING, ProcessState.PAUSED]
        ])
        
        total_cpu = sum(
            p.resource_usage.cpu_usage if p.resource_usage else 0
            for p in self.monitored_processes.values()
        )
        
        total_memory = sum(
            p.resource_usage.memory_usage if p.resource_usage else 0
            for p in self.monitored_processes.values()
        )
        
        alert_counts = {"warning": 0, "critical": 0, "info": 0}
        for process in self.monitored_processes.values():
            for alert in process.alerts:
                if not alert.acknowledged:
                    alert_counts[alert.severity] = alert_counts.get(alert.severity, 0) + 1
        
        # Process breakdown by agent type
        agent_breakdown = {}
        for process in self.monitored_processes.values():
            agent_type = process.agent_type
            if agent_type not in agent_breakdown:
                agent_breakdown[agent_type] = {"count": 0, "avg_cpu": 0.0}
            
            agent_breakdown[agent_type]["count"] += 1
            if process.resource_usage:
                current_avg = agent_breakdown[agent_type]["avg_cpu"]
                count = agent_breakdown[agent_type]["count"]
                new_avg = (current_avg * (count - 1) + process.resource_usage.cpu_usage) / count
                agent_breakdown[agent_type]["avg_cpu"] = new_avg
        
        return {
            "active_processes": active_processes,
            "total_processes": len(self.monitored_processes),
            "total_cpu_usage": total_cpu,
            "total_memory_usage": total_memory,
            "alert_counts": alert_counts,
            "agent_breakdown": agent_breakdown,
            "monitoring_uptime": (datetime.now() - datetime.now()).total_seconds() if self.monitoring_active else 0
        }

    def _monitoring_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        self.logger.info("Monitoring loop started")
        
        while self.monitoring_active and not self.shutdown_event.is_set():
            try:
                self._update_all_processes()
                self._check_alerts()
                self._cleanup_completed_processes()
                
                # Wait for next monitoring interval
                self.shutdown_event.wait(timeout=self.configuration.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)  # Brief pause on error
        
        self.logger.info("Monitoring loop stopped")

    def _update_all_processes(self):
        """Update status and metrics for all monitored processes."""
        with self.lock:
            for process_id, monitored_process in list(self.monitored_processes.items()):
                try:
                    self._update_process_status(monitored_process)
                    
                    if self.configuration.collect_metrics:
                        self._collect_process_metrics(monitored_process)
                    
                    self._update_process_progress(monitored_process)
                    
                except Exception as e:
                    self.logger.error(f"Error updating process {process_id}: {e}")

    def _update_process_status(self, process: MonitoredProcess):
        """Update the status of a monitored process."""
        if process.process_id in self.process_registry:
            sys_process = self.process_registry[process.process_id]
            
            # Check if process is still running
            if sys_process.poll() is None:
                # Process is still running
                process.state = ProcessState.RUNNING
                process.last_heartbeat = datetime.now()
                
                # Check for health issues
                if process.resource_usage:
                    process.health_state = self._determine_health_state(process)
            else:
                # Process has terminated
                exit_code = sys_process.returncode
                process.end_time = datetime.now()
                
                if exit_code == 0:
                    process.state = ProcessState.COMPLETED
                else:
                    process.state = ProcessState.FAILED
                    
                    # Attempt restart if configured
                    if (self.configuration.auto_restart and 
                        process.restart_count < self.configuration.max_restart_attempts):
                        self._restart_process(process)

    def _collect_process_metrics(self, process: MonitoredProcess):
        """Collect resource usage and performance metrics for a process."""
        if not process.pid:
            return
        
        try:
            # Get process information using psutil
            psutil_process = psutil.Process(process.pid)
            
            # Resource usage
            cpu_percent = psutil_process.cpu_percent()
            memory_info = psutil_process.memory_info()
            io_counters = psutil_process.io_counters()
            
            process.resource_usage = ResourceUsage(
                cpu_usage=cpu_percent,
                memory_usage=memory_info.rss / (1024 * 1024),  # MB
                disk_io=io_counters.read_bytes + io_counters.write_bytes,
                network_io=0,  # Would need additional tracking
                open_files=psutil_process.num_fds() if hasattr(psutil_process, 'num_fds') else 0,
                threads=psutil_process.num_threads()
            )
            
            # Store metrics history
            if process.process_id not in self.metrics_history:
                self.metrics_history[process.process_id] = []
            
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": cpu_percent,
                "memory_usage": memory_info.rss / (1024 * 1024),
                "state": process.state.value
            }
            
            self.metrics_history[process.process_id].append(history_entry)
            
            # Keep only recent history (last 100 entries)
            if len(self.metrics_history[process.process_id]) > 100:
                self.metrics_history[process.process_id] = self.metrics_history[process.process_id][-100:]
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # Process no longer exists or is not accessible
            process.resource_usage = None

    def _update_process_progress(self, process: MonitoredProcess):
        """Update process progress information."""
        # This would typically read from process output or status files
        # For now, we'll estimate progress based on runtime
        if process.state == ProcessState.RUNNING:
            runtime = (datetime.now() - process.start_time).total_seconds()
            
            # Simple progress estimation (would be more sophisticated in practice)
            estimated_total = 300  # 5 minutes default
            completion = min(runtime / estimated_total * 100, 95)  # Max 95% until actually complete
            
            process.progress = ProcessProgress(
                current_phase="execution",
                completion_percentage=completion,
                estimated_remaining=max(estimated_total - runtime, 0),
                milestones_completed=["started", "initialized"],
                next_milestone="completion"
            )

    def _determine_health_state(self, process: MonitoredProcess) -> HealthState:
        """Determine health state based on current metrics."""
        if not process.resource_usage:
            return HealthState.UNKNOWN
        
        thresholds = process.alert_thresholds
        usage = process.resource_usage
        
        critical_conditions = [
            usage.cpu_usage > thresholds.cpu_threshold,
            usage.memory_usage > thresholds.memory_threshold
        ]
        
        warning_conditions = [
            usage.cpu_usage > thresholds.cpu_threshold * 0.8,
            usage.memory_usage > thresholds.memory_threshold * 0.8
        ]
        
        if any(critical_conditions):
            return HealthState.CRITICAL
        elif any(warning_conditions):
            return HealthState.WARNING
        else:
            return HealthState.HEALTHY

    def _check_alerts(self):
        """Check all processes for alert conditions."""
        for process in self.monitored_processes.values():
            self._check_process_alerts(process)

    def _check_process_alerts(self, process: MonitoredProcess):
        """Check a specific process for alert conditions."""
        if not process.resource_usage:
            return
        
        current_time = datetime.now()
        thresholds = process.alert_thresholds
        usage = process.resource_usage
        
        # Check CPU usage
        if usage.cpu_usage > thresholds.cpu_threshold:
            alert = Alert(
                type=AlertType.RESOURCE,
                severity="critical" if usage.cpu_usage > thresholds.cpu_threshold * 1.2 else "warning",
                message=f"High CPU usage detected: {usage.cpu_usage:.1f}%",
                threshold=thresholds.cpu_threshold,
                current_value=usage.cpu_usage,
                timestamp=current_time,
                process_id=process.process_id
            )
            
            # Add alert if not already present
            if not self._alert_already_exists(process, alert):
                process.alerts.append(alert)
                self._send_alert(alert)
        
        # Check memory usage
        if usage.memory_usage > thresholds.memory_threshold:
            alert = Alert(
                type=AlertType.RESOURCE,
                severity="critical" if usage.memory_usage > thresholds.memory_threshold * 1.2 else "warning",
                message=f"High memory usage detected: {usage.memory_usage:.1f}MB",
                threshold=thresholds.memory_threshold,
                current_value=usage.memory_usage,
                timestamp=current_time,
                process_id=process.process_id
            )
            
            if not self._alert_already_exists(process, alert):
                process.alerts.append(alert)
                self._send_alert(alert)
        
        # Check for process state issues
        if process.state == ProcessState.FAILED:
            alert = Alert(
                type=AlertType.PROCESS,
                severity="critical",
                message=f"Process {process.process_id} has failed",
                threshold=0,
                current_value=1,
                timestamp=current_time,
                process_id=process.process_id
            )
            
            if not self._alert_already_exists(process, alert):
                process.alerts.append(alert)
                self._send_alert(alert)

    def _alert_already_exists(self, process: MonitoredProcess, new_alert: Alert) -> bool:
        """Check if a similar alert already exists for the process."""
        recent_alerts = [
            alert for alert in process.alerts
            if (datetime.now() - alert.timestamp).total_seconds() < 300  # Within 5 minutes
            and alert.type == new_alert.type
            and alert.message == new_alert.message
        ]
        
        return len(recent_alerts) > 0

    def _send_alert(self, alert: Alert):
        """Send alert through configured notification channels."""
        for channel in self.configuration.notification_channels:
            if channel in self.alert_handlers:
                try:
                    self.alert_handlers[channel](alert)
                except Exception as e:
                    self.logger.error(f"Failed to send alert via {channel}: {e}")

    def _send_email_alert(self, alert: Alert):
        """Send alert via email (placeholder)."""
        self.logger.info(f"EMAIL ALERT: {alert.message}")

    def _send_webhook_alert(self, alert: Alert):
        """Send alert via webhook (placeholder)."""
        self.logger.info(f"WEBHOOK ALERT: {alert.message}")

    def _send_slack_alert(self, alert: Alert):
        """Send alert via Slack (placeholder)."""
        self.logger.info(f"SLACK ALERT: {alert.message}")

    def _write_file_alert(self, alert: Alert):
        """Write alert to file."""
        alert_file = Path("alerts.log")
        with open(alert_file, "a") as f:
            f.write(f"{alert.timestamp.isoformat()} - {alert.severity.upper()} - {alert.message}\n")

    def _restart_process(self, process: MonitoredProcess):
        """Restart a failed process."""
        try:
            self.logger.info(f"Attempting to restart process {process.process_id}")
            
            process.restart_count += 1
            process.state = ProcessState.RECOVERING
            
            # Start new process instance
            new_process = self._start_process(process)
            if new_process:
                process.pid = new_process.pid
                process.state = ProcessState.RUNNING
                process.health_state = HealthState.HEALTHY
                process.last_heartbeat = datetime.now()
                
                # Update process registry
                self.process_registry[process.process_id] = new_process
                
                self.logger.info(f"Successfully restarted process {process.process_id}")
            else:
                process.state = ProcessState.FAILED
                self.logger.error(f"Failed to restart process {process.process_id}")
                
        except Exception as e:
            self.logger.error(f"Error restarting process {process.process_id}: {e}")
            process.state = ProcessState.FAILED

    def _cleanup_completed_processes(self):
        """Clean up processes that have been completed for a while."""
        cleanup_threshold = datetime.now() - timedelta(hours=1)
        
        processes_to_cleanup = [
            process_id for process_id, process in self.monitored_processes.items()
            if (process.state in [ProcessState.COMPLETED, ProcessState.FAILED, ProcessState.TERMINATED] and
                process.end_time and process.end_time < cleanup_threshold)
        ]
        
        for process_id in processes_to_cleanup:
            self.logger.info(f"Cleaning up old process {process_id}")
            del self.monitored_processes[process_id]
            
            if process_id in self.process_registry:
                del self.process_registry[process_id]
            
            if process_id in self.metrics_history:
                del self.metrics_history[process_id]

    def configure_monitoring(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update monitoring configuration."""
        try:
            # Update configuration
            if "monitoring_interval" in new_config:
                self.configuration.monitoring_interval = new_config["monitoring_interval"]
            
            if "collect_metrics" in new_config:
                self.configuration.collect_metrics = new_config["collect_metrics"]
            
            if "auto_restart" in new_config:
                self.configuration.auto_restart = new_config["auto_restart"]
            
            if "notification_channels" in new_config:
                self.configuration.notification_channels = new_config["notification_channels"]
            
            # Update alert thresholds for existing processes
            if "alert_thresholds" in new_config:
                new_thresholds = AlertThresholds(**new_config["alert_thresholds"])
                for process in self.monitored_processes.values():
                    process.alert_thresholds = new_thresholds
            
            self.logger.info("Monitoring configuration updated")
            
            return {
                "success": True,
                "message": "Configuration updated successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate real-time dashboard data."""
        with self.lock:
            summary = self._build_system_summary()
            
            # Recent activity
            recent_activity = []
            for process in self.monitored_processes.values():
                if process.alerts:
                    for alert in process.alerts[-3:]:  # Last 3 alerts
                        recent_activity.append({
                            "timestamp": alert.timestamp.isoformat(),
                            "type": "alert",
                            "process_id": process.process_id,
                            "message": alert.message,
                            "severity": alert.severity
                        })
            
            # Sort by timestamp
            recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
            recent_activity = recent_activity[:10]  # Last 10 activities
            
            # Performance trends
            performance_trends = {}
            for process_id, history in self.metrics_history.items():
                if len(history) > 1:
                    recent_cpu = [h["cpu_usage"] for h in history[-10:]]
                    recent_memory = [h["memory_usage"] for h in history[-10:]]
                    
                    performance_trends[process_id] = {
                        "cpu_trend": "increasing" if recent_cpu[-1] > recent_cpu[0] else "decreasing",
                        "memory_trend": "increasing" if recent_memory[-1] > recent_memory[0] else "decreasing",
                        "avg_cpu": sum(recent_cpu) / len(recent_cpu),
                        "avg_memory": sum(recent_memory) / len(recent_memory)
                    }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "recent_activity": recent_activity,
                "performance_trends": performance_trends,
                "monitoring_config": asdict(self.configuration)
            }

    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process monitoring requests."""
        try:
            operation = request_data.get("operation", "status")
            
            if operation == "monitor":
                return self._handle_monitor_request(request_data)
            elif operation == "start":
                return self._handle_start_request(request_data)
            elif operation == "stop":
                return self._handle_stop_request(request_data)
            elif operation == "status":
                return self._handle_status_request(request_data)
            elif operation == "configure":
                return self._handle_configure_request(request_data)
            elif operation == "alert":
                return self._handle_alert_request(request_data)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported operation: {operation}"
                }
                
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _handle_monitor_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle monitor operation request."""
        target = request_data.get("target", {})
        parameters = request_data.get("parameters", {})
        
        process_id = target.get("process_id")
        if not process_id:
            return {"success": False, "error": "process_id required for monitor operation"}
        
        # Extract monitoring parameters
        agent_type = target.get("agent_type", "unknown")
        task_id = target.get("task_id", "unknown")
        command = parameters.get("command", ["echo", "test"])
        working_directory = parameters.get("working_directory", ".")
        
        # Resource limits and alert thresholds
        resource_limits = None
        if "resource_limits" in parameters:
            resource_limits = ResourceLimits(**parameters["resource_limits"])
        
        alert_thresholds = None  
        if "alert_thresholds" in parameters:
            alert_thresholds = AlertThresholds(**parameters["alert_thresholds"])
        
        return self.monitor_process(
            process_id=process_id,
            agent_type=agent_type,
            task_id=task_id,
            command=command,
            working_directory=working_directory,
            resource_limits=resource_limits,
            alert_thresholds=alert_thresholds
        )

    def _handle_start_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle start monitoring request."""
        parameters = request_data.get("parameters", {})
        config = MonitoringConfiguration(**parameters)
        
        self.start_monitoring(config)
        
        return {
            "success": True,
            "message": "Monitoring started",
            "configuration": asdict(config)
        }

    def _handle_stop_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stop monitoring request."""
        target = request_data.get("target", {})
        process_id = target.get("process_id")
        
        if process_id:
            return self.stop_process_monitoring(process_id)
        else:
            self.stop_monitoring()
            return {
                "success": True,
                "message": "Monitoring stopped"
            }

    def _handle_status_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request."""
        target = request_data.get("target", {})
        parameters = request_data.get("parameters", {})
        
        process_id = target.get("process_id") if target.get("process_id") != "all" else None
        include_metrics = parameters.get("include_metrics", True)
        include_history = parameters.get("include_history", False)
        
        return self.get_process_status(process_id, include_metrics, include_history)

    def _handle_configure_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle configuration request."""
        parameters = request_data.get("parameters", {})
        return self.configure_monitoring(parameters)

    def _handle_alert_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alert request."""
        parameters = request_data.get("parameters", {})
        alert_types = parameters.get("alert_types", ["resource", "performance", "process"])
        
        all_alerts = []
        for process in self.monitored_processes.values():
            for alert in process.alerts:
                if alert.type.value in alert_types:
                    all_alerts.append({
                        **asdict(alert),
                        "timestamp": alert.timestamp.isoformat(),
                        "type": alert.type.value
                    })
        
        # Sort by timestamp (most recent first)
        all_alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "success": True,
            "alerts": all_alerts,
            "alert_count": len(all_alerts)
        }


def main():
    """Main function for testing the Execution Monitor Engine."""
    engine = ExecutionMonitorEngine()
    
    # Start monitoring system
    engine.start_monitoring()
    
    try:
        # Test process monitoring
        test_request = {
            "operation": "monitor",
            "target": {
                "process_id": "test_process_001",
                "agent_type": "workflow-manager",
                "task_id": "task_001"
            },
            "parameters": {
                "command": ["python", "-c", "import time; time.sleep(30); print('Done')"],
                "working_directory": ".",
                "resource_limits": {
                    "cpu_limit": "100m",
                    "memory_limit": "256MB",
                    "timeout": 60
                },
                "alert_thresholds": {
                    "cpu_threshold": 50.0,
                    "memory_threshold": 128.0
                }
            }
        }
        
        response = engine.process_request(test_request)
        
        if response["success"]:
            print("Process monitoring started successfully!")
            print(f"Process ID: {response['process_id']}")
            print(f"PID: {response['pid']}")
            
            # Wait a bit and check status
            time.sleep(10)
            
            status_request = {
                "operation": "status",
                "target": {"process_id": "test_process_001"},
                "parameters": {"include_metrics": True}
            }
            
            status_response = engine.process_request(status_request)
            print("\nProcess Status:")
            print(json.dumps(status_response, indent=2))
            
        else:
            print("Failed to start process monitoring:")
            print(f"Error: {response['error']}")
    
    finally:
        # Clean up
        engine.stop_monitoring()
        print("\nMonitoring stopped")


if __name__ == "__main__":
    main()