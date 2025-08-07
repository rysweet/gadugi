#!/usr/bin/env python3
"""Comprehensive tests for the Gadugi Engine.

This test suite validates all core functionality of the GadugiEngine including
system management, service control, agent management, health monitoring,
backup operations, and configuration management.
"""

import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator"))

from gadugi_engine import (
    AgentInfo,
    BackupInfo,
    Environment,
    GadugiEngine,
    HealthStatus,
    OperationResult,
    OperationType,
    Recommendation,
    ServiceInfo,
    ServiceStatus,
    SystemStatus,
    TargetType,
)


class TestGadugiEngine:
    """Test cases for the GadugiEngine class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        # Create temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())

        # Mock the base directory to use temp directory
        with patch.object(Path, "parent", new_callable=lambda: self.temp_dir.parent):
            with patch("gadugi_engine.Path") as mock_path:
                mock_path.return_value.parent.parent.parent = self.temp_dir
                self.gadugi = GadugiEngine()

        # Override paths to use temp directory
        self.gadugi.base_dir = self.temp_dir
        self.gadugi.config_dir = self.temp_dir / "config"
        self.gadugi.data_dir = self.temp_dir / "data"
        self.gadugi.log_dir = self.temp_dir / "logs"
        self.gadugi.backup_dir = self.temp_dir / "backups"
        self.gadugi.db_path = self.gadugi.data_dir / "gadugi.db"

        # Ensure directories exist
        self.gadugi._ensure_directories()

        # Initialize database
        self.gadugi._init_database()

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        # Stop any running monitoring
        if hasattr(self.gadugi, "is_monitoring") and self.gadugi.is_monitoring:
            self.gadugi._stop_monitoring()

        # Clean up temporary directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_gadugi_engine_initialization(self) -> None:
        """Test GadugiEngine initialization."""
        assert self.gadugi is not None
        assert hasattr(self.gadugi, "logger")
        assert hasattr(self.gadugi, "config")
        assert hasattr(self.gadugi, "core_services")
        assert hasattr(self.gadugi, "available_agents")

        # Check that directories were created
        assert self.gadugi.config_dir.exists()
        assert self.gadugi.data_dir.exists()
        assert self.gadugi.log_dir.exists()
        assert self.gadugi.backup_dir.exists()

        # Check that database was initialized
        assert self.gadugi.db_path.exists()

    def test_operation_enums(self) -> None:
        """Test operation enumeration values."""
        # Test OperationType enum
        assert OperationType.INSTALL.value == "install"
        assert OperationType.CONFIGURE.value == "configure"
        assert OperationType.START.value == "start"
        assert OperationType.STOP.value == "stop"
        assert OperationType.STATUS.value == "status"
        assert OperationType.UPDATE.value == "update"
        assert OperationType.BACKUP.value == "backup"
        assert OperationType.RESTORE.value == "restore"
        assert OperationType.HEALTH.value == "health"
        assert OperationType.OPTIMIZE.value == "optimize"

        # Test TargetType enum
        assert TargetType.SYSTEM.value == "system"
        assert TargetType.AGENT.value == "agent"
        assert TargetType.SERVICE.value == "service"
        assert TargetType.ALL.value == "all"

        # Test Environment enum
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.STAGING.value == "staging"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.TESTING.value == "testing"

    def test_database_initialization(self) -> None:
        """Test database initialization and schema creation."""
        # Check if database file exists
        assert self.gadugi.db_path.exists()

        # Check if tables were created
        with sqlite3.connect(self.gadugi.db_path) as conn:
            cursor = conn.cursor()

            # Check services table
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='services'",
            )
            assert cursor.fetchone() is not None

            # Check agents table
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agents'",
            )
            assert cursor.fetchone() is not None

            # Check system_events table
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='system_events'",
            )
            assert cursor.fetchone() is not None

            # Check backups table
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='backups'",
            )
            assert cursor.fetchone() is not None

    def test_core_services_configuration(self) -> None:
        """Test core services configuration."""
        expected_services = [
            "event-router",
            "neo4j-graph",
            "mcp-service",
            "llm-proxy",
            "gadugi-cli",
        ]

        for service_name in expected_services:
            assert service_name in self.gadugi.core_services
            service_config = self.gadugi.core_services[service_name]
            assert "port" in service_config
            assert "executable" in service_config
            assert "args" in service_config
            assert "health_check" in service_config
            assert "dependencies" in service_config

    def test_available_agents_configuration(self) -> None:
        """Test available agents configuration."""
        expected_agents = [
            "orchestrator",
            "architect",
            "task-decomposer",
            "workflow-manager",
            "code-writer",
            "code-reviewer",
            "memory-manager",
            "team-coach",
            "prompt-writer",
            "worktree-manager",
        ]

        for agent_name in expected_agents:
            assert agent_name in self.gadugi.available_agents
            agent_config = self.gadugi.available_agents[agent_name]
            assert "version" in agent_config
            assert "capabilities" in agent_config
            assert "memory_limit" in agent_config
            assert "executable" in agent_config
            assert "args" in agent_config

    def test_execute_operation_status(self) -> None:
        """Test executing status operation."""
        request = {
            "command": "status",
            "target": "system",
            "parameters": {},
            "options": {},
        }

        with patch.object(self.gadugi, "_get_system_status") as mock_status:
            mock_status.return_value = SystemStatus(
                system_status=HealthStatus.HEALTHY,
                services_running=["event-router"],
                services_stopped=["neo4j-graph"],
                agents_active=5,
                memory_usage="45%",
                cpu_usage="15%",
                disk_usage="60%",
                uptime="72:15:30",
            )

            result = self.gadugi.execute_operation(request)

            assert result.success is True
            assert result.operation == "status"
            assert result.status is not None
            assert len(result.errors) == 0

    def test_execute_operation_invalid_command(self) -> None:
        """Test executing invalid operation."""
        request = {
            "command": "invalid_command",
            "target": "system",
            "parameters": {},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is False
        assert len(result.errors) > 0
        assert (
            "invalid_command" in result.errors[0].lower()
            or "unsupported" in result.errors[0].lower()
        )

    def test_handle_install_system(self) -> None:
        """Test system installation."""
        request = {
            "command": "install",
            "target": "system",
            "parameters": {"environment": "development"},
            "options": {},
        }

        with (
            patch.object(self.gadugi, "_install_dependencies") as mock_deps,
            patch.object(self.gadugi, "_create_default_configs") as mock_config,
        ):
            result = self.gadugi.execute_operation(request)

            assert result.success is True
            assert result.operation == "install"
            assert "installed_components" in result.results
            assert len(result.recommendations) > 0
            mock_deps.assert_called_once()
            mock_config.assert_called_once()

    def test_handle_install_service(self) -> None:
        """Test service installation."""
        request = {
            "command": "install",
            "target": "service",
            "parameters": {"component": "event-router"},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert result.operation == "install"
        assert "installed_service" in result.results
        assert result.results["installed_service"] == "event-router"

    def test_handle_install_agent(self) -> None:
        """Test agent installation."""
        request = {
            "command": "install",
            "target": "agent",
            "parameters": {"component": "orchestrator"},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert result.operation == "install"
        assert "installed_agent" in result.results
        assert result.results["installed_agent"] == "orchestrator"

    def test_handle_install_unknown_service(self) -> None:
        """Test installation of unknown service."""
        request = {
            "command": "install",
            "target": "service",
            "parameters": {"component": "unknown-service"},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is False
        assert len(result.errors) > 0
        assert "unknown service" in result.errors[0].lower()

    def test_handle_configure_system(self) -> None:
        """Test system configuration."""
        request = {
            "command": "configure",
            "target": "system",
            "parameters": {"environment": "production"},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert result.operation == "configure"
        assert "configured_components" in result.results
        assert self.gadugi.config["gadugi"]["environment"] == "production"

    def test_handle_configure_service(self) -> None:
        """Test service configuration."""
        request = {
            "command": "configure",
            "target": "service",
            "parameters": {"component": "event-router", "port": 9090},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert result.operation == "configure"
        assert "configured_service" in result.results
        assert result.results["configured_service"] == "event-router"

    def test_handle_configure_agent(self) -> None:
        """Test agent configuration."""
        request = {
            "command": "configure",
            "target": "agent",
            "parameters": {"component": "orchestrator", "max_instances": 5},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert result.operation == "configure"
        assert "configured_agent" in result.results
        assert result.results["configured_agent"] == "orchestrator"

    @patch("gadugi_engine.subprocess.Popen")
    def test_start_service_success(self, mock_popen) -> None:
        """Test successful service start."""
        # Mock process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process

        result = self.gadugi._start_service("event-router")

        assert result is True
        assert "event-router" in self.gadugi.services
        assert self.gadugi.services["event-router"]["pid"] == 12345
        assert self.gadugi.services["event-router"]["status"] == ServiceStatus.RUNNING

    @patch("gadugi_engine.subprocess.Popen")
    def test_start_service_failure(self, mock_popen) -> None:
        """Test service start failure."""
        # Mock failed process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = 1  # Process failed
        mock_popen.return_value = mock_process

        result = self.gadugi._start_service("event-router")

        assert result is False

    def test_start_unknown_service(self) -> None:
        """Test starting unknown service."""
        result = self.gadugi._start_service("unknown-service")
        assert result is False

    @patch("gadugi_engine.subprocess.Popen")
    def test_stop_service_success(self, mock_popen) -> None:
        """Test successful service stop."""
        # Setup running service
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.terminate = Mock()
        mock_process.wait = Mock()

        self.gadugi.services["event-router"] = {
            "process": mock_process,
            "pid": 12345,
            "status": ServiceStatus.RUNNING,
        }

        result = self.gadugi._stop_service("event-router")

        assert result is True
        mock_process.terminate.assert_called_once()
        assert self.gadugi.services["event-router"]["status"] == ServiceStatus.STOPPED

    def test_stop_non_running_service(self) -> None:
        """Test stopping non-running service."""
        result = self.gadugi._stop_service("non-existent-service")
        assert result is True  # Should succeed (no-op)

    @patch("gadugi_engine.subprocess.Popen")
    def test_start_agent_success(self, mock_popen) -> None:
        """Test successful agent start."""
        # Mock process
        mock_process = Mock()
        mock_process.pid = 54321
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process

        result = self.gadugi._start_agent("orchestrator")

        assert result is True
        assert "orchestrator" in self.gadugi.agents
        assert self.gadugi.agents["orchestrator"]["pid"] == 54321
        assert self.gadugi.agents["orchestrator"]["status"] == "active"

    @patch("gadugi_engine.subprocess.Popen")
    def test_start_agent_failure(self, mock_popen) -> None:
        """Test agent start failure."""
        # Mock failed process
        mock_process = Mock()
        mock_process.pid = 54321
        mock_process.poll.return_value = 1  # Process failed
        mock_popen.return_value = mock_process

        result = self.gadugi._start_agent("orchestrator")

        assert result is False

    def test_start_unknown_agent(self) -> None:
        """Test starting unknown agent."""
        result = self.gadugi._start_agent("unknown-agent")
        assert result is False

    @patch("gadugi_engine.subprocess.Popen")
    def test_stop_agent_success(self, mock_popen) -> None:
        """Test successful agent stop."""
        # Setup running agent
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.terminate = Mock()
        mock_process.wait = Mock()

        self.gadugi.agents["orchestrator"] = {
            "process": mock_process,
            "pid": 54321,
            "status": "active",
        }

        result = self.gadugi._stop_agent("orchestrator")

        assert result is True
        mock_process.terminate.assert_called_once()
        assert self.gadugi.agents["orchestrator"]["status"] == "stopped"

    def test_stop_non_running_agent(self) -> None:
        """Test stopping non-running agent."""
        result = self.gadugi._stop_agent("non-existent-agent")
        assert result is True  # Should succeed (no-op)

    @patch("gadugi_engine.subprocess.Popen")
    def test_handle_start_all(self, mock_popen) -> None:
        """Test starting all services and agents."""
        # Mock successful processes
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        request = {"command": "start", "target": "all", "parameters": {}, "options": {}}

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert result.operation == "start"
        assert "started_services" in result.results
        assert "started_agents" in result.results

    @patch("gadugi_engine.subprocess.Popen")
    def test_handle_start_specific_service(self, mock_popen) -> None:
        """Test starting specific service."""
        # Mock successful process
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        request = {
            "command": "start",
            "target": "service",
            "parameters": {"component": "event-router"},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert result.operation == "start"
        assert "started_services" in result.results
        assert "event-router" in result.results["started_services"]

    def test_handle_stop_all(self) -> None:
        """Test stopping all services and agents."""
        # Setup some running services and agents
        self.gadugi.services["event-router"] = {
            "process": Mock(),
            "status": ServiceStatus.RUNNING,
        }
        self.gadugi.agents["orchestrator"] = {"process": Mock(), "status": "active"}

        request = {"command": "stop", "target": "all", "parameters": {}, "options": {}}

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert result.operation == "stop"
        assert "stopped_services" in result.results or "stopped_agents" in result.results

    @patch("gadugi_engine.psutil.cpu_percent")
    @patch("gadugi_engine.psutil.virtual_memory")
    @patch("gadugi_engine.psutil.disk_usage")
    @patch("gadugi_engine.psutil.net_io_counters")
    def test_get_resource_usage(self, mock_net, mock_disk, mock_memory, mock_cpu) -> None:
        """Test resource usage collection."""
        # Mock system resource data
        mock_cpu.return_value = 25.5
        mock_memory.return_value = Mock(
            percent=60.0,
            used=8000000000,
            total=16000000000,
        )
        mock_disk.return_value = Mock(used=500000000000, total=1000000000000)
        mock_net.return_value = Mock(bytes_sent=1000000, bytes_recv=2000000)

        usage = self.gadugi._get_resource_usage()

        assert usage["cpu_percent"] == 25.5
        assert usage["memory_percent"] == 60.0
        assert usage["disk_percent"] == 50.0
        assert "memory_used_gb" in usage
        assert "disk_used_gb" in usage

    @patch("gadugi_engine.psutil.cpu_percent")
    @patch("gadugi_engine.psutil.virtual_memory")
    def test_get_resource_usage_error(self, mock_memory, mock_cpu) -> None:
        """Test resource usage collection with error."""
        mock_cpu.side_effect = Exception("CPU error")
        mock_memory.side_effect = Exception("Memory error")

        usage = self.gadugi._get_resource_usage()

        # Should return defaults on error
        assert usage["cpu_percent"] == 0
        assert usage["memory_percent"] == 0
        assert usage["disk_percent"] == 0

    def test_get_system_info(self) -> None:
        """Test system information collection."""
        info = self.gadugi._get_system_info()

        assert "gadugi_version" in info
        assert "python_version" in info
        assert "platform" in info
        assert "pid" in info
        assert "working_directory" in info

    def test_get_services_status(self) -> None:
        """Test getting services status."""
        # Add some services
        self.gadugi.services["event-router"] = {
            "status": ServiceStatus.RUNNING,
            "pid": 12345,
            "started_at": datetime.now(),
        }

        services = self.gadugi._get_services_status()

        assert isinstance(services, list)
        assert len(services) == len(self.gadugi.core_services)

        # Find event-router service
        event_router = next((s for s in services if s["name"] == "event-router"), None)
        assert event_router is not None
        assert event_router["status"] == ServiceStatus.RUNNING.value

    def test_get_agents_status(self) -> None:
        """Test getting agents status."""
        # Add some agents
        self.gadugi.agents["orchestrator"] = {
            "status": "active",
            "pid": 54321,
            "started_at": datetime.now(),
        }

        agents = self.gadugi._get_agents_status()

        assert isinstance(agents, list)
        assert len(agents) == len(self.gadugi.available_agents)

        # Find orchestrator agent
        orchestrator = next((a for a in agents if a["name"] == "orchestrator"), None)
        assert orchestrator is not None
        assert orchestrator["status"] == "active"

    @patch("gadugi_engine.psutil.cpu_percent")
    @patch("gadugi_engine.psutil.virtual_memory")
    def test_handle_health_check(self, mock_memory, mock_cpu) -> None:
        """Test health check operation."""
        mock_cpu.return_value = 15.0
        mock_memory.return_value = Mock(percent=45.0)

        request = {
            "command": "health",
            "target": "system",
            "parameters": {},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert result.operation == "health"
        assert "overall_status" in result.results
        assert "timestamp" in result.results

    @patch("gadugi_engine.psutil.cpu_percent")
    @patch("gadugi_engine.psutil.virtual_memory")
    def test_handle_health_check_high_cpu(self, mock_memory, mock_cpu) -> None:
        """Test health check with high CPU usage."""
        mock_cpu.return_value = 85.0  # High CPU
        mock_memory.return_value = Mock(percent=45.0)

        request = {
            "command": "health",
            "target": "system",
            "parameters": {},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert len(result.warnings) > 0
        assert len(result.recommendations) > 0
        assert any("cpu" in warning.lower() for warning in result.warnings)

    @patch("gadugi_engine.psutil.cpu_percent")
    @patch("gadugi_engine.psutil.virtual_memory")
    def test_handle_health_check_high_memory(self, mock_memory, mock_cpu) -> None:
        """Test health check with high memory usage."""
        mock_cpu.return_value = 15.0
        mock_memory.return_value = Mock(percent=90.0)  # High memory

        request = {
            "command": "health",
            "target": "system",
            "parameters": {},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is True
        assert len(result.warnings) > 0
        assert len(result.recommendations) > 0
        assert any("memory" in warning.lower() for warning in result.warnings)

    @patch("gadugi_engine.tarfile.open")
    def test_create_backup_success(self, mock_tarfile) -> None:
        """Test successful backup creation."""
        mock_tar = Mock()
        mock_tarfile.return_value.__enter__.return_value = mock_tar

        # Mock file operations
        with patch.object(self.gadugi.backup_dir, "exists", return_value=True):
            with patch("gadugi_engine.Path.stat") as mock_stat:
                mock_stat.return_value.st_size = 1000000

                backup_file = self.gadugi._create_backup("full", True, True)

                assert backup_file is not None
                assert "gadugi_backup_full" in backup_file
                assert backup_file.endswith(".tar.gz")

    def test_create_backup_failure(self) -> None:
        """Test backup creation failure."""
        # Mock file operations to raise exception
        with patch(
            "gadugi_engine.tarfile.open",
            side_effect=Exception("Backup failed"),
        ):
            backup_file = self.gadugi._create_backup("full", True, True)
            assert backup_file is None

    def test_handle_backup_operation(self) -> None:
        """Test backup operation handling."""
        request = {
            "command": "backup",
            "target": "system",
            "parameters": {
                "backup_type": "full",
                "compress": True,
                "include_data": True,
            },
            "options": {},
        }

        with patch.object(self.gadugi, "_create_backup") as mock_create:
            mock_create.return_value = "test_backup.tar.gz"
            with patch.object(self.gadugi, "_get_file_size") as mock_size:
                mock_size.return_value = "1.0 MB"

                result = self.gadugi.execute_operation(request)

                assert result.success is True
                assert result.operation == "backup"
                assert "backup_created" in result.results
                assert result.results["backup_created"] == "test_backup.tar.gz"

    def test_handle_restore_operation(self) -> None:
        """Test restore operation handling."""
        request = {
            "command": "restore",
            "target": "system",
            "parameters": {"backup_file": "test_backup.tar.gz"},
            "options": {},
        }

        with patch.object(self.gadugi, "_restore_backup") as mock_restore:
            mock_restore.return_value = True

            result = self.gadugi.execute_operation(request)

            assert result.success is True
            assert result.operation == "restore"
            assert "restored_from" in result.results

    def test_handle_restore_no_backup_file(self) -> None:
        """Test restore operation without backup file."""
        request = {
            "command": "restore",
            "target": "system",
            "parameters": {},
            "options": {},
        }

        result = self.gadugi.execute_operation(request)

        assert result.success is False
        assert len(result.errors) > 0
        assert "backup file not specified" in result.errors[0].lower()

    def test_handle_optimize_operation(self) -> None:
        """Test optimization operation."""
        request = {
            "command": "optimize",
            "target": "system",
            "parameters": {},
            "options": {},
        }

        with patch.object(self.gadugi, "_optimize_system") as mock_optimize:
            mock_optimize.return_value = {
                "optimizations_applied": ["test optimization"],
            }

            result = self.gadugi.execute_operation(request)

            assert result.success is True
            assert result.operation == "optimize"
            assert "optimizations_applied" in result.results
            assert len(result.recommendations) > 0

    @patch("gadugi_engine.gc.collect")
    def test_optimize_system(self, mock_gc) -> None:
        """Test system optimization."""
        mock_gc.return_value = 100  # Objects collected

        with patch.object(self.gadugi, "_cleanup_old_logs") as mock_cleanup:
            mock_cleanup.return_value = 5  # Log files cleaned

            results = self.gadugi._optimize_system()

            assert "optimizations_applied" in results
            assert len(results["optimizations_applied"]) >= 2
            assert any("memory cleanup" in opt.lower() for opt in results["optimizations_applied"])
            assert any("log files" in opt.lower() for opt in results["optimizations_applied"])

    def test_cleanup_old_logs(self) -> None:
        """Test old log cleanup."""
        # Create some test log files
        old_log = self.gadugi.log_dir / "old.log"
        recent_log = self.gadugi.log_dir / "recent.log"

        old_log.touch()
        recent_log.touch()

        # Mock file timestamps
        with patch("gadugi_engine.datetime") as mock_datetime:
            # Mock current time
            mock_now = Mock()
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromtimestamp.return_value = mock_now

            with patch.object(Path, "stat") as mock_stat:
                # Make old file appear old
                old_stat = Mock()
                old_stat.st_mtime = 0  # Very old
                recent_stat = Mock()
                recent_stat.st_mtime = 9999999999  # Very recent

                mock_stat.side_effect = lambda: old_stat if "old.log" in str(self) else recent_stat

                cleaned = self.gadugi._cleanup_old_logs()

                # Should have attempted to clean some files
                assert isinstance(cleaned, int)

    def test_system_monitoring_start_stop(self) -> None:
        """Test starting and stopping system monitoring."""
        assert self.gadugi.is_monitoring is False

        # Start monitoring
        self.gadugi._start_monitoring()
        assert self.gadugi.is_monitoring is True
        assert self.gadugi.monitor_thread is not None

        # Stop monitoring
        self.gadugi._stop_monitoring()
        assert self.gadugi.is_monitoring is False

    def test_update_service_in_db(self) -> None:
        """Test updating service status in database."""
        self.gadugi._update_service_in_db("test-service", ServiceStatus.RUNNING, 12345)

        # Verify database entry
        with sqlite3.connect(self.gadugi.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM services WHERE name = ?", ("test-service",))
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == "test-service"  # name
            assert result[1] == ServiceStatus.RUNNING.value  # status
            assert result[2] == 12345  # pid

    def test_update_agent_in_db(self) -> None:
        """Test updating agent status in database."""
        self.gadugi._update_agent_in_db("test-agent", "active", 54321)

        # Verify database entry
        with sqlite3.connect(self.gadugi.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE name = ?", ("test-agent",))
            result = cursor.fetchone()

            assert result is not None
            assert result[0] == "test-agent"  # name
            assert result[2] == "active"  # status
            assert result[3] == 54321  # pid

    def test_log_system_event(self) -> None:
        """Test logging system events."""
        details = {"component": "test", "action": "test_action"}
        self.gadugi._log_system_event(
            "test_event",
            "test_component",
            "Test message",
            details,
        )

        # Verify database entry
        with sqlite3.connect(self.gadugi.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM system_events WHERE event_type = ?",
                ("test_event",),
            )
            result = cursor.fetchone()

            assert result is not None
            assert result[2] == "test_event"  # event_type
            assert result[3] == "test_component"  # component
            assert result[4] == "Test message"  # message

    def test_calculate_file_checksum(self) -> None:
        """Test file checksum calculation."""
        # Create test file
        test_file = self.temp_dir / "test.txt"
        test_content = "test content for checksum"
        test_file.write_text(test_content)

        checksum = self.gadugi._calculate_file_checksum(test_file)

        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex digest length

    def test_get_file_size_formatting(self) -> None:
        """Test file size formatting."""
        # Create test file
        test_file = self.gadugi.backup_dir / "test.txt"
        test_file.write_text("x" * 1024)  # 1KB file

        size_str = self.gadugi._get_file_size("test.txt")
        assert "KB" in size_str or "B" in size_str

    def test_list_backups_empty(self) -> None:
        """Test listing backups when none exist."""
        backups = self.gadugi.list_backups()
        assert isinstance(backups, list)
        assert len(backups) == 0

    def test_list_backups_with_data(self) -> None:
        """Test listing backups with data."""
        # Insert test backup data
        with sqlite3.connect(self.gadugi.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backups (filename, backup_type, size, created_at, checksum, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    "test_backup.tar.gz",
                    "full",
                    1024000,
                    datetime.now().isoformat(),
                    "test_checksum",
                    json.dumps({"compressed": True}),
                ),
            )
            conn.commit()

        backups = self.gadugi.list_backups()

        assert len(backups) == 1
        assert backups[0].filename == "test_backup.tar.gz"
        assert backups[0].backup_type == "full"
        assert backups[0].compressed is True

    def test_format_size(self) -> None:
        """Test size formatting."""
        assert "B" in self.gadugi._format_size(512)
        assert "KB" in self.gadugi._format_size(1024)
        assert "MB" in self.gadugi._format_size(1024 * 1024)
        assert "GB" in self.gadugi._format_size(1024 * 1024 * 1024)

    def test_shutdown(self) -> None:
        """Test graceful shutdown."""
        # Setup some running components
        self.gadugi.services["test-service"] = {
            "process": Mock(),
            "status": ServiceStatus.RUNNING,
        }
        self.gadugi.agents["test-agent"] = {"process": Mock(), "status": "active"}
        self.gadugi.is_monitoring = True

        with (
            patch.object(self.gadugi, "_stop_monitoring") as mock_stop_monitor,
            patch.object(self.gadugi, "_stop_all_services") as mock_stop_services,
            patch.object(self.gadugi, "_stop_all_agents") as mock_stop_agents,
        ):
            self.gadugi.shutdown()

            mock_stop_monitor.assert_called_once()
            mock_stop_services.assert_called_once()
            mock_stop_agents.assert_called_once()

    def test_is_service_running_true(self) -> None:
        """Test service running check - positive case."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running

        self.gadugi.services["test-service"] = {"process": mock_process}

        assert self.gadugi._is_service_running("test-service") is True

    def test_is_service_running_false(self) -> None:
        """Test service running check - negative case."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process not running

        self.gadugi.services["test-service"] = {"process": mock_process}

        assert self.gadugi._is_service_running("test-service") is False

    def test_is_service_running_not_exists(self) -> None:
        """Test service running check - service doesn't exist."""
        assert self.gadugi._is_service_running("non-existent") is False

    def test_is_agent_running_true(self) -> None:
        """Test agent running check - positive case."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process running

        self.gadugi.agents["test-agent"] = {"process": mock_process}

        assert self.gadugi._is_agent_running("test-agent") is True

    def test_is_agent_running_false(self) -> None:
        """Test agent running check - negative case."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process not running

        self.gadugi.agents["test-agent"] = {"process": mock_process}

        assert self.gadugi._is_agent_running("test-agent") is False

    def test_is_agent_running_not_exists(self) -> None:
        """Test agent running check - agent doesn't exist."""
        assert self.gadugi._is_agent_running("non-existent") is False

    def test_perform_health_check_healthy(self) -> None:
        """Test health check - healthy system."""
        # Mock running services and agents
        self.gadugi.services = {"event-router": {"status": ServiceStatus.RUNNING}}
        self.gadugi.agents = {"orchestrator": {"status": "active"}}

        with (
            patch.object(self.gadugi, "_is_service_running", return_value=True),
            patch.object(self.gadugi, "_is_agent_running", return_value=True),
            patch.object(self.gadugi, "_get_resource_usage") as mock_resource,
        ):
            mock_resource.return_value = {"cpu_percent": 15, "memory_percent": 45}

            health = self.gadugi._perform_health_check()

            assert health["overall_status"] == "healthy"
            assert len(health["services"]) > 0
            assert len(health["agents"]) > 0

    def test_perform_health_check_critical(self) -> None:
        """Test health check - critical system."""
        # Mock all services down
        with (
            patch.object(self.gadugi, "_is_service_running", return_value=False),
            patch.object(self.gadugi, "_is_agent_running", return_value=False),
            patch.object(self.gadugi, "_get_resource_usage") as mock_resource,
        ):
            mock_resource.return_value = {"cpu_percent": 95, "memory_percent": 98}

            health = self.gadugi._perform_health_check()

            assert health["overall_status"] == "critical"
            assert len(health["errors"]) > 0

    def test_get_backup_checksum_exists(self) -> None:
        """Test getting backup checksum when it exists."""
        # Insert test backup
        with sqlite3.connect(self.gadugi.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO backups (filename, checksum)
                VALUES (?, ?)
            """,
                ("test.tar.gz", "test_checksum"),
            )
            conn.commit()

        checksum = self.gadugi._get_backup_checksum("test.tar.gz")
        assert checksum == "test_checksum"

    def test_get_backup_checksum_not_exists(self) -> None:
        """Test getting backup checksum when it doesn't exist."""
        checksum = self.gadugi._get_backup_checksum("nonexistent.tar.gz")
        assert checksum is None

    def test_restore_backup_success(self) -> None:
        """Test successful backup restoration."""
        # Create test backup file
        backup_file = "test_backup.tar.gz"
        backup_path = self.gadugi.backup_dir / backup_file

        with (
            patch.object(backup_path, "exists", return_value=True),
            patch.object(
                self.gadugi,
                "_get_backup_checksum",
                return_value="test_checksum",
            ),
            patch.object(
                self.gadugi,
                "_calculate_file_checksum",
                return_value="test_checksum",
            ),
            patch("gadugi_engine.tarfile.open") as mock_tarfile,
        ):
            mock_tar = Mock()
            mock_tarfile.return_value.__enter__.return_value = mock_tar

            with (
                patch.object(self.gadugi, "_stop_all_services"),
                patch.object(self.gadugi, "_stop_all_agents"),
                patch.object(self.gadugi, "_load_config"),
            ):
                result = self.gadugi._restore_backup(backup_file)

                assert result is True
                mock_tar.extractall.assert_called_once()

    def test_restore_backup_not_found(self) -> None:
        """Test backup restoration when file doesn't exist."""
        backup_file = "nonexistent_backup.tar.gz"
        result = self.gadugi._restore_backup(backup_file)
        assert result is False

    def test_restore_backup_checksum_mismatch(self) -> None:
        """Test backup restoration with checksum mismatch."""
        backup_file = "test_backup.tar.gz"
        backup_path = self.gadugi.backup_dir / backup_file

        with (
            patch.object(backup_path, "exists", return_value=True),
            patch.object(
                self.gadugi,
                "_get_backup_checksum",
                return_value="stored_checksum",
            ),
            patch.object(
                self.gadugi,
                "_calculate_file_checksum",
                return_value="different_checksum",
            ),
        ):
            result = self.gadugi._restore_backup(backup_file)

            assert result is False

    def test_error_handling_in_execute_operation(self) -> None:
        """Test error handling in execute_operation."""
        request = {"command": "status", "target": "system"}

        # Mock an exception in status handling
        with patch.object(
            self.gadugi,
            "_handle_status",
            side_effect=Exception("Test error"),
        ):
            result = self.gadugi.execute_operation(request)

            assert result.success is False
            assert len(result.errors) > 0
            assert "test error" in result.errors[0].lower()

    def test_load_config_with_file(self) -> None:
        """Test loading configuration from file."""
        # Create test config file
        config_file = self.temp_dir / "test_config.yaml"
        test_config = {"gadugi": {"version": "0.4.0", "environment": "testing"}}

        with open(config_file, "w") as f:
            yaml.dump(test_config, f)

        config = self.gadugi._load_config(str(config_file))

        assert config["gadugi"]["version"] == "0.4.0"
        assert config["gadugi"]["environment"] == "testing"

    def test_load_config_file_not_exists(self) -> None:
        """Test loading configuration when file doesn't exist."""
        config = self.gadugi._load_config("nonexistent_config.yaml")

        # Should return default config
        assert "gadugi" in config
        assert config["gadugi"]["version"] == "0.3.0"

    def test_load_config_invalid_yaml(self) -> None:
        """Test loading configuration with invalid YAML."""
        # Create invalid YAML file
        config_file = self.temp_dir / "invalid_config.yaml"
        config_file.write_text("invalid: yaml: content: [")

        config = self.gadugi._load_config(str(config_file))

        # Should return default config and log warning
        assert "gadugi" in config
        assert config["gadugi"]["version"] == "0.3.0"


class TestDataClasses:
    """Test the data classes used by the Gadugi engine."""

    def test_system_status_creation(self) -> None:
        """Test SystemStatus data class creation."""
        status = SystemStatus(
            system_status=HealthStatus.HEALTHY,
            services_running=["event-router"],
            services_stopped=["neo4j-graph"],
            agents_active=5,
            memory_usage="45%",
            cpu_usage="15%",
            disk_usage="60%",
            uptime="72:15:30",
        )

        assert status.system_status == HealthStatus.HEALTHY
        assert len(status.services_running) == 1
        assert len(status.services_stopped) == 1
        assert status.agents_active == 5

    def test_service_info_creation(self) -> None:
        """Test ServiceInfo data class creation."""
        service = ServiceInfo(
            name="event-router",
            status=ServiceStatus.RUNNING,
            port=8080,
            pid=12345,
            uptime="2h",
            memory_usage="256MB",
            cpu_usage="5%",
        )

        assert service.name == "event-router"
        assert service.status == ServiceStatus.RUNNING
        assert service.port == 8080
        assert service.pid == 12345

    def test_agent_info_creation(self) -> None:
        """Test AgentInfo data class creation."""
        agent = AgentInfo(
            name="orchestrator",
            version="0.3.0",
            status="active",
            capabilities=["parallel_execution", "task_coordination"],
            resource_usage={"cpu": "3%", "memory": "128MB"},
            last_heartbeat="2024-01-15T10:30:00Z",
        )

        assert agent.name == "orchestrator"
        assert agent.version == "0.3.0"
        assert agent.status == "active"
        assert len(agent.capabilities) == 2

    def test_recommendation_creation(self) -> None:
        """Test Recommendation data class creation."""
        rec = Recommendation(
            priority="high",
            category="performance",
            message="High CPU usage detected",
            action="Consider optimizing system",
        )

        assert rec.priority == "high"
        assert rec.category == "performance"
        assert "cpu" in rec.message.lower()

    def test_backup_info_creation(self) -> None:
        """Test BackupInfo data class creation."""
        backup = BackupInfo(
            filename="backup_20240115.tar.gz",
            size="1.2 GB",
            created_at="2024-01-15T10:30:00Z",
            backup_type="full",
            compressed=True,
        )

        assert backup.filename == "backup_20240115.tar.gz"
        assert backup.size == "1.2 GB"
        assert backup.backup_type == "full"
        assert backup.compressed is True

    def test_operation_result_creation(self) -> None:
        """Test OperationResult data class creation."""
        result = OperationResult(
            success=True,
            operation="start",
            status=None,
            results={"started_services": ["event-router"]},
            recommendations=[],
            warnings=["High memory usage"],
            errors=[],
        )

        assert result.success is True
        assert result.operation == "start"
        assert "started_services" in result.results
        assert len(result.warnings) == 1
        assert len(result.errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
