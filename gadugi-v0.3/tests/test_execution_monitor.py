#!/usr/bin/env python3
"""Tests for Execution Monitor Engine."""

import sys
import threading
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "orchestrator"))

from execution_monitor_engine import (
    Alert,
    AlertThresholds,
    AlertType,
    ExecutionMonitorEngine,
    HealthState,
    MonitoredProcess,
    MonitoringConfiguration,
    ProcessState,
    ResourceLimits,
    ResourceUsage,
)


class TestExecutionMonitorEngine(unittest.TestCase):
    """Test cases for Execution Monitor Engine."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = ExecutionMonitorEngine()
        self.test_process_id = "test_process_001"
        self.test_agent_type = "test-agent"
        self.test_task_id = "task_001"

        # Sample configuration
        self.test_config = MonitoringConfiguration(
            monitoring_interval=1,
            collect_metrics=True,
            enable_real_time=True,
            auto_restart=True,
            max_restart_attempts=2,
            notification_channels=["file"],
        )

        # Sample resource limits
        self.test_limits = ResourceLimits(
            cpu_limit="100m",
            memory_limit="256MB",
            timeout=30,
        )

        # Sample alert thresholds
        self.test_thresholds = AlertThresholds(
            cpu_threshold=50.0,
            memory_threshold=128.0,
            error_rate_threshold=10.0,
        )

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        # Stop monitoring if running
        if self.engine.monitoring_active:
            self.engine.stop_monitoring()

        # Clean up any test processes
        for process_id in list(self.engine.process_registry.keys()):
            try:
                process = self.engine.process_registry[process_id]
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except Exception:
                pass

    def test_engine_initialization(self) -> None:
        """Test engine initializes properly."""
        assert self.engine is not None
        assert self.engine.logger is not None
        assert isinstance(self.engine.monitored_processes, dict)
        assert isinstance(self.engine.configuration, MonitoringConfiguration)
        assert not self.engine.monitoring_active
        assert self.engine.alert_handlers is not None

    def test_monitoring_configuration(self) -> None:
        """Test monitoring configuration."""
        config = MonitoringConfiguration(
            monitoring_interval=5,
            collect_metrics=False,
            auto_restart=False,
        )

        assert config.monitoring_interval == 5
        assert not config.collect_metrics
        assert not config.auto_restart
        assert config.notification_channels == ["email"]  # Default

    def test_resource_limits_dataclass(self) -> None:
        """Test ResourceLimits dataclass."""
        limits = ResourceLimits(
            cpu_limit="200m",
            memory_limit="512MB",
            timeout=600,
            disk_limit="1GB",
        )

        assert limits.cpu_limit == "200m"
        assert limits.memory_limit == "512MB"
        assert limits.timeout == 600
        assert limits.disk_limit == "1GB"

    def test_alert_thresholds_dataclass(self) -> None:
        """Test AlertThresholds dataclass."""
        thresholds = AlertThresholds(
            cpu_threshold=80.0,
            memory_threshold=512.0,
            error_rate_threshold=5.0,
            response_time_threshold=10.0,
        )

        assert thresholds.cpu_threshold == 80.0
        assert thresholds.memory_threshold == 512.0
        assert thresholds.error_rate_threshold == 5.0
        assert thresholds.response_time_threshold == 10.0

    def test_process_state_enum(self) -> None:
        """Test ProcessState enum."""
        assert ProcessState.INITIALIZING.value == "initializing"
        assert ProcessState.RUNNING.value == "running"
        assert ProcessState.COMPLETED.value == "completed"
        assert ProcessState.FAILED.value == "failed"

    def test_health_state_enum(self) -> None:
        """Test HealthState enum."""
        assert HealthState.HEALTHY.value == "healthy"
        assert HealthState.WARNING.value == "warning"
        assert HealthState.CRITICAL.value == "critical"
        assert HealthState.UNKNOWN.value == "unknown"

    def test_alert_type_enum(self) -> None:
        """Test AlertType enum."""
        assert AlertType.RESOURCE.value == "resource"
        assert AlertType.PERFORMANCE.value == "performance"
        assert AlertType.PROCESS.value == "process"
        assert AlertType.SYSTEM.value == "system"

    def test_start_stop_monitoring(self) -> None:
        """Test starting and stopping monitoring system."""
        # Initially not active
        assert not self.engine.monitoring_active

        # Start monitoring
        self.engine.start_monitoring(self.test_config)
        assert self.engine.monitoring_active
        assert self.engine.configuration.monitoring_interval == 1

        # Stop monitoring
        self.engine.stop_monitoring()
        assert not self.engine.monitoring_active

    def test_monitor_process_simple(self) -> None:
        """Test monitoring a simple process."""
        # Use a simple command that will complete quickly
        command = ["echo", "Hello World"]

        result = self.engine.monitor_process(
            process_id=self.test_process_id,
            agent_type=self.test_agent_type,
            task_id=self.test_task_id,
            command=command,
            working_directory=".",
            resource_limits=self.test_limits,
            alert_thresholds=self.test_thresholds,
        )

        assert result["success"]
        assert result["process_id"] == self.test_process_id
        assert "pid" in result

        # Check that process is registered
        assert self.test_process_id in self.engine.monitored_processes
        assert self.test_process_id in self.engine.process_registry

        # Wait for process to complete
        time.sleep(1)

        # Check process status
        monitored_process = self.engine.monitored_processes[self.test_process_id]
        # Process should complete quickly
        assert monitored_process is not None

    def test_monitor_process_duplicate(self) -> None:
        """Test monitoring the same process twice."""
        command = ["sleep", "1"]

        # Start first monitoring
        result1 = self.engine.monitor_process(
            process_id=self.test_process_id,
            agent_type=self.test_agent_type,
            task_id=self.test_task_id,
            command=command,
            working_directory=".",
        )

        assert result1["success"]

        # Try to start monitoring same process ID again
        result2 = self.engine.monitor_process(
            process_id=self.test_process_id,
            agent_type=self.test_agent_type,
            task_id="different_task",
            command=command,
            working_directory=".",
        )

        assert not result2["success"]
        assert "already being monitored" in result2["error"]

    @patch("subprocess.Popen")
    def test_monitor_process_start_failure(self, mock_popen) -> None:
        """Test handling process start failure."""
        # Mock subprocess.Popen to raise an exception
        mock_popen.side_effect = FileNotFoundError("Command not found")

        result = self.engine.monitor_process(
            process_id=self.test_process_id,
            agent_type=self.test_agent_type,
            task_id=self.test_task_id,
            command=["nonexistent_command"],
            working_directory=".",
        )

        assert not result["success"]
        assert "Failed to start process" in result["error"]

    def test_stop_process_monitoring(self) -> None:
        """Test stopping monitoring of a specific process."""
        command = ["sleep", "5"]

        # Start monitoring
        result = self.engine.monitor_process(
            process_id=self.test_process_id,
            agent_type=self.test_agent_type,
            task_id=self.test_task_id,
            command=command,
            working_directory=".",
        )

        assert result["success"]

        # Stop monitoring
        stop_result = self.engine.stop_process_monitoring(
            self.test_process_id,
            cleanup_resources=True,
        )

        assert stop_result["success"]
        assert stop_result["process_id"] == self.test_process_id
        assert stop_result["final_state"] == ProcessState.TERMINATED.value

        # Process should be removed from monitoring
        assert self.test_process_id not in self.engine.monitored_processes

    def test_stop_process_monitoring_nonexistent(self) -> None:
        """Test stopping monitoring of non-existent process."""
        result = self.engine.stop_process_monitoring("nonexistent_process")

        assert not result["success"]
        assert "not being monitored" in result["error"]

    def test_get_process_status_single(self) -> None:
        """Test getting status of a single process."""
        command = ["sleep", "2"]

        # Start monitoring
        self.engine.monitor_process(
            process_id=self.test_process_id,
            agent_type=self.test_agent_type,
            task_id=self.test_task_id,
            command=command,
            working_directory=".",
        )

        # Get status
        status = self.engine.get_process_status(
            process_id=self.test_process_id,
            include_metrics=True,
            include_history=False,
        )

        assert status["success"]
        assert "process_status" in status

        process_status = status["process_status"]
        assert process_status["process_id"] == self.test_process_id
        assert process_status["agent_type"] == self.test_agent_type
        assert process_status["task_id"] == self.test_task_id
        assert "state" in process_status
        assert "duration" in process_status

    def test_get_process_status_all(self) -> None:
        """Test getting status of all processes."""
        # Start multiple processes
        for i in range(3):
            process_id = f"test_process_{i:03d}"
            self.engine.monitor_process(
                process_id=process_id,
                agent_type=f"agent-{i}",
                task_id=f"task_{i}",
                command=["echo", f"test {i}"],
                working_directory=".",
            )

        # Get status of all processes
        status = self.engine.get_process_status(
            process_id=None,
            include_metrics=False,
            include_history=False,
        )

        assert status["success"]
        assert "processes" in status
        assert "summary" in status

        # Should have 3 processes
        assert len(status["processes"]) == 3

        # Check summary
        summary = status["summary"]
        assert "total_processes" in summary
        assert "agent_breakdown" in summary

    def test_get_process_status_nonexistent(self) -> None:
        """Test getting status of non-existent process."""
        status = self.engine.get_process_status("nonexistent_process")

        assert not status["success"]
        assert "not found" in status["error"]

    def test_monitored_process_dataclass(self) -> None:
        """Test MonitoredProcess dataclass functionality."""
        now = datetime.now()

        process = MonitoredProcess(
            process_id="test_001",
            agent_type="test-agent",
            task_id="task_001",
            pid=12345,
            state=ProcessState.RUNNING,
            health_state=HealthState.HEALTHY,
            start_time=now,
            end_time=None,
            command=["echo", "test"],
            working_directory="/tmp",
            resource_limits=ResourceLimits(),
            alert_thresholds=AlertThresholds(),
            resource_usage=None,
            performance_metrics=None,
            progress=None,
            alerts=[],
        )

        assert process.process_id == "test_001"
        assert process.state == ProcessState.RUNNING
        assert process.restart_count == 0  # Default value
        assert process.last_heartbeat is None  # Default value

    def test_alert_dataclass(self) -> None:
        """Test Alert dataclass functionality."""
        now = datetime.now()

        alert = Alert(
            type=AlertType.RESOURCE,
            severity="warning",
            message="High CPU usage",
            threshold=80.0,
            current_value=85.5,
            timestamp=now,
            process_id="test_001",
        )

        assert alert.type == AlertType.RESOURCE
        assert alert.severity == "warning"
        assert alert.current_value == 85.5
        assert not alert.acknowledged  # Default value

    @patch("psutil.Process")
    def test_collect_process_metrics(self, mock_psutil_process) -> None:
        """Test collection of process metrics."""
        # Mock psutil.Process
        mock_process_instance = MagicMock()
        mock_process_instance.cpu_percent.return_value = 25.5
        mock_process_instance.memory_info.return_value = MagicMock(
            rss=134217728,
        )  # 128MB
        mock_process_instance.io_counters.return_value = MagicMock(
            read_bytes=1000,
            write_bytes=2000,
        )
        mock_process_instance.num_threads.return_value = 5
        mock_process_instance.num_fds.return_value = 10

        mock_psutil_process.return_value = mock_process_instance

        # Create a monitored process
        monitored_process = MonitoredProcess(
            process_id="test_001",
            agent_type="test-agent",
            task_id="task_001",
            pid=12345,
            state=ProcessState.RUNNING,
            health_state=HealthState.HEALTHY,
            start_time=datetime.now(),
            end_time=None,
            command=["echo", "test"],
            working_directory="/tmp",
            resource_limits=ResourceLimits(),
            alert_thresholds=AlertThresholds(),
            resource_usage=None,
            performance_metrics=None,
            progress=None,
            alerts=[],
        )

        # Collect metrics
        self.engine._collect_process_metrics(monitored_process)

        # Check metrics were collected
        assert monitored_process.resource_usage is not None
        assert monitored_process.resource_usage.cpu_usage == 25.5
        assert monitored_process.resource_usage.memory_usage == 128.0  # MB
        assert monitored_process.resource_usage.threads == 5

    def test_determine_health_state(self) -> None:
        """Test health state determination."""
        thresholds = AlertThresholds(cpu_threshold=80.0, memory_threshold=100.0)

        process = MonitoredProcess(
            process_id="test_001",
            agent_type="test-agent",
            task_id="task_001",
            pid=12345,
            state=ProcessState.RUNNING,
            health_state=HealthState.UNKNOWN,
            start_time=datetime.now(),
            end_time=None,
            command=["echo", "test"],
            working_directory="/tmp",
            resource_limits=ResourceLimits(),
            alert_thresholds=thresholds,
            resource_usage=None,
            performance_metrics=None,
            progress=None,
            alerts=[],
        )

        # Test unknown state (no resource usage)
        health = self.engine._determine_health_state(process)
        assert health == HealthState.UNKNOWN

        # Test healthy state
        process.resource_usage = ResourceUsage(
            cpu_usage=50.0,
            memory_usage=50.0,
            disk_io=1000,
            network_io=500,
            open_files=10,
            threads=3,
        )
        health = self.engine._determine_health_state(process)
        assert health == HealthState.HEALTHY

        # Test warning state
        process.resource_usage.cpu_usage = 70.0  # 70% (above 80% * 0.8 = 64%)
        health = self.engine._determine_health_state(process)
        assert health == HealthState.WARNING

        # Test critical state
        process.resource_usage.cpu_usage = 90.0  # Above threshold
        health = self.engine._determine_health_state(process)
        assert health == HealthState.CRITICAL

    def test_alert_already_exists(self) -> None:
        """Test checking for duplicate alerts."""
        now = datetime.now()

        process = MonitoredProcess(
            process_id="test_001",
            agent_type="test-agent",
            task_id="task_001",
            pid=12345,
            state=ProcessState.RUNNING,
            health_state=HealthState.WARNING,
            start_time=now,
            end_time=None,
            command=["echo", "test"],
            working_directory="/tmp",
            resource_limits=ResourceLimits(),
            alert_thresholds=AlertThresholds(),
            resource_usage=None,
            performance_metrics=None,
            progress=None,
            alerts=[],
        )

        # Add an existing alert
        existing_alert = Alert(
            type=AlertType.RESOURCE,
            severity="warning",
            message="High CPU usage",
            threshold=80.0,
            current_value=85.0,
            timestamp=now,
            process_id="test_001",
        )
        process.alerts.append(existing_alert)

        # Check for duplicate
        new_alert = Alert(
            type=AlertType.RESOURCE,
            severity="warning",
            message="High CPU usage",
            threshold=80.0,
            current_value=87.0,
            timestamp=datetime.now(),
            process_id="test_001",
        )

        duplicate_exists = self.engine._alert_already_exists(process, new_alert)
        assert duplicate_exists

        # Check for non-duplicate
        different_alert = Alert(
            type=AlertType.RESOURCE,
            severity="warning",
            message="High memory usage",
            threshold=100.0,
            current_value=105.0,
            timestamp=datetime.now(),
            process_id="test_001",
        )

        duplicate_exists = self.engine._alert_already_exists(process, different_alert)
        assert not duplicate_exists

    def test_configure_monitoring(self) -> None:
        """Test monitoring configuration update."""
        new_config = {
            "monitoring_interval": 10,
            "collect_metrics": False,
            "auto_restart": False,
            "notification_channels": ["email", "webhook"],
            "alert_thresholds": {"cpu_threshold": 90.0, "memory_threshold": 200.0},
        }

        result = self.engine.configure_monitoring(new_config)

        assert result["success"]
        assert self.engine.configuration.monitoring_interval == 10
        assert not self.engine.configuration.collect_metrics
        assert not self.engine.configuration.auto_restart
        assert self.engine.configuration.notification_channels == ["email", "webhook"]

    def test_generate_dashboard_data(self) -> None:
        """Test dashboard data generation."""
        # Add some test processes
        for i in range(3):
            process_id = f"test_process_{i:03d}"
            self.engine.monitor_process(
                process_id=process_id,
                agent_type=f"agent-type-{i % 2}",
                task_id=f"task_{i}",
                command=["echo", f"test {i}"],
                working_directory=".",
            )

        dashboard_data = self.engine.generate_dashboard_data()

        assert "timestamp" in dashboard_data
        assert "summary" in dashboard_data
        assert "recent_activity" in dashboard_data
        assert "performance_trends" in dashboard_data
        assert "monitoring_config" in dashboard_data

        # Check summary
        summary = dashboard_data["summary"]
        assert summary["total_processes"] == 3
        assert "agent_breakdown" in summary

    def test_process_request_monitor(self) -> None:
        """Test processing monitor operation request."""
        request = {
            "operation": "monitor",
            "target": {
                "process_id": "api_test_001",
                "agent_type": "api-agent",
                "task_id": "api_task_001",
            },
            "parameters": {
                "command": ["echo", "API test"],
                "working_directory": ".",
                "resource_limits": {
                    "cpu_limit": "100m",
                    "memory_limit": "128MB",
                    "timeout": 30,
                },
                "alert_thresholds": {"cpu_threshold": 60.0, "memory_threshold": 100.0},
            },
        }

        response = self.engine.process_request(request)

        assert response["success"]
        assert response["process_id"] == "api_test_001"
        assert "pid" in response

    def test_process_request_start(self) -> None:
        """Test processing start monitoring request."""
        request = {
            "operation": "start",
            "parameters": {
                "monitoring_interval": 2,
                "collect_metrics": True,
                "auto_restart": True,
                "notification_channels": ["file"],
            },
        }

        response = self.engine.process_request(request)

        assert response["success"]
        assert "Monitoring started" in response["message"]
        assert "configuration" in response

        # Check that monitoring is active
        assert self.engine.monitoring_active

    def test_process_request_stop(self) -> None:
        """Test processing stop monitoring request."""
        # Start monitoring first
        self.engine.start_monitoring()
        assert self.engine.monitoring_active

        # Stop monitoring
        request = {"operation": "stop"}
        response = self.engine.process_request(request)

        assert response["success"]
        assert "Monitoring stopped" in response["message"]
        assert not self.engine.monitoring_active

    def test_process_request_status(self) -> None:
        """Test processing status request."""
        # Add a test process
        self.engine.monitor_process(
            process_id="status_test_001",
            agent_type="status-agent",
            task_id="status_task",
            command=["echo", "status test"],
            working_directory=".",
        )

        # Request status
        request = {
            "operation": "status",
            "target": {"process_id": "status_test_001"},
            "parameters": {"include_metrics": True, "include_history": False},
        }

        response = self.engine.process_request(request)

        assert response["success"]
        assert "process_status" in response

    def test_process_request_configure(self) -> None:
        """Test processing configure request."""
        request = {
            "operation": "configure",
            "parameters": {"monitoring_interval": 15, "collect_metrics": False},
        }

        response = self.engine.process_request(request)

        assert response["success"]
        assert self.engine.configuration.monitoring_interval == 15
        assert not self.engine.configuration.collect_metrics

    def test_process_request_alert(self) -> None:
        """Test processing alert request."""
        # Add a process with alerts
        process = MonitoredProcess(
            process_id="alert_test_001",
            agent_type="alert-agent",
            task_id="alert_task",
            pid=12345,
            state=ProcessState.RUNNING,
            health_state=HealthState.CRITICAL,
            start_time=datetime.now(),
            end_time=None,
            command=["echo", "test"],
            working_directory="/tmp",
            resource_limits=ResourceLimits(),
            alert_thresholds=AlertThresholds(),
            resource_usage=None,
            performance_metrics=None,
            progress=None,
            alerts=[
                Alert(
                    type=AlertType.RESOURCE,
                    severity="critical",
                    message="High CPU usage",
                    threshold=80.0,
                    current_value=95.0,
                    timestamp=datetime.now(),
                    process_id="alert_test_001",
                ),
            ],
        )

        self.engine.monitored_processes["alert_test_001"] = process

        # Request alerts
        request = {
            "operation": "alert",
            "parameters": {"alert_types": ["resource", "performance"]},
        }

        response = self.engine.process_request(request)

        assert response["success"]
        assert "alerts" in response
        assert "alert_count" in response
        assert response["alert_count"] > 0

    def test_process_request_unsupported(self) -> None:
        """Test processing unsupported operation."""
        request = {"operation": "unsupported_operation"}
        response = self.engine.process_request(request)

        assert not response["success"]
        assert "Unsupported operation" in response["error"]

    def test_alert_handlers_setup(self) -> None:
        """Test that alert handlers are properly set up."""
        handlers = self.engine.alert_handlers

        assert "email" in handlers
        assert "webhook" in handlers
        assert "slack" in handlers
        assert "file" in handlers

        # Test file alert handler
        test_alert = Alert(
            type=AlertType.RESOURCE,
            severity="warning",
            message="Test alert",
            threshold=80.0,
            current_value=85.0,
            timestamp=datetime.now(),
            process_id="test_001",
        )

        # Should not raise an exception
        handlers["file"](test_alert)

    def test_process_progress_update(self) -> None:
        """Test process progress updates."""
        now = datetime.now()

        process = MonitoredProcess(
            process_id="progress_test",
            agent_type="progress-agent",
            task_id="progress_task",
            pid=12345,
            state=ProcessState.RUNNING,
            health_state=HealthState.HEALTHY,
            start_time=now - timedelta(seconds=60),  # 1 minute ago
            end_time=None,
            command=["echo", "test"],
            working_directory="/tmp",
            resource_limits=ResourceLimits(),
            alert_thresholds=AlertThresholds(),
            resource_usage=None,
            performance_metrics=None,
            progress=None,
            alerts=[],
        )

        # Update progress
        self.engine._update_process_progress(process)

        # Check that progress was updated
        assert process.progress is not None
        assert process.progress.current_phase == "execution"
        assert process.progress.completion_percentage > 0
        assert "started" in process.progress.milestones_completed

    def test_logging_setup(self) -> None:
        """Test that logging is set up correctly."""
        assert self.engine.logger is not None
        assert self.engine.logger.name == "execution_monitor"

        import logging

        assert self.engine.logger.level == logging.INFO

    def test_thread_safety(self) -> None:
        """Test thread safety of concurrent operations."""

        # This test checks basic thread safety during concurrent process additions
        def add_process(process_num):
            try:
                result = self.engine.monitor_process(
                    process_id=f"concurrent_test_{process_num}",
                    agent_type="concurrent-agent",
                    task_id=f"task_{process_num}",
                    command=["echo", f"test {process_num}"],
                    working_directory=".",
                )
                return result["success"]
            except Exception:
                return False

        # Start multiple threads to add processes concurrently
        threads = []
        results = []

        for i in range(5):
            thread = threading.Thread(target=lambda i=i: results.append(add_process(i)))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(results)
        assert len(self.engine.monitored_processes) == 5

    def test_system_summary_calculation(self) -> None:
        """Test system summary calculations."""
        # Add processes with different agent types
        agents = ["workflow-manager", "code-writer", "code-reviewer"]
        for i, agent_type in enumerate(agents):
            for j in range(2):  # 2 processes per agent type
                process_id = f"summary_test_{agent_type}_{j}"
                self.engine.monitor_process(
                    process_id=process_id,
                    agent_type=agent_type,
                    task_id=f"task_{i}_{j}",
                    command=["echo", f"test {i} {j}"],
                    working_directory=".",
                )

        summary = self.engine._build_system_summary()

        # Check summary structure
        assert "total_processes" in summary
        assert "agent_breakdown" in summary
        assert summary["total_processes"] == 6

        # Check agent breakdown
        breakdown = summary["agent_breakdown"]
        for agent_type in agents:
            assert agent_type in breakdown
            assert breakdown[agent_type]["count"] == 2


if __name__ == "__main__":
    unittest.main()
