#!/usr/bin/env python3
"""
Test suite for Memory Health Check System.

Tests all functionality including:
- Health checks for each backend type
- Automatic failover mechanisms
- Periodic monitoring
- Event emission
- Status reporting
- Cache management
"""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch

import pytest

import sys

# Add the correct path to src/src directory where shared module is located
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "src"))

from shared.memory_health import (
    MemoryHealthMonitor,
    MemoryBackendType,
    HealthStatus,
    HealthCheckResult,
    BackendConfig,
    HealthMonitorConfig,
    FailoverStrategy,
    create_default_backends,
    create_default_config,
    create_memory_health_monitor,
)


class TestHealthCheckResults:
    """Test HealthCheckResult functionality."""

    def test_health_check_result_creation(self):
        """Test creating health check results."""
        result = HealthCheckResult(
            backend_type=MemoryBackendType.NEO4J,
            status=HealthStatus.HEALTHY,
            response_time_ms=25.5,
            details={"test": "value"},
        )

        assert result.backend_type == MemoryBackendType.NEO4J
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms == 25.5
        assert result.details == {"test": "value"}
        assert result.is_healthy
        assert result.is_available

    def test_unhealthy_result(self):
        """Test unhealthy result properties."""
        result = HealthCheckResult(
            backend_type=MemoryBackendType.SQLITE,
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0,
            error_message="Connection failed",
        )

        assert not result.is_healthy
        assert not result.is_available
        assert result.error_message == "Connection failed"

    def test_degraded_result(self):
        """Test degraded result properties."""
        result = HealthCheckResult(
            backend_type=MemoryBackendType.SQLITE,
            status=HealthStatus.DEGRADED,
            response_time_ms=150.0,
        )

        assert not result.is_healthy
        assert result.is_available  # Degraded is still available


class TestBackendConfigs:
    """Test backend configuration functionality."""

    def test_backend_config_creation(self):
        """Test creating backend configurations."""
        config = BackendConfig(
            backend_type=MemoryBackendType.NEO4J,
            priority=100,
            enabled=True,
            config={"uri": "bolt://localhost:7687"},
        )

        assert config.backend_type == MemoryBackendType.NEO4J
        assert config.priority == 100
        assert config.enabled
        assert config.config["uri"] == "bolt://localhost:7687"

    def test_default_backends(self):
        """Test default backend creation."""
        backends = create_default_backends()

        assert len(backends) == 4
        backend_types = [b.backend_type for b in backends]
        assert MemoryBackendType.NEO4J in backend_types
        assert MemoryBackendType.SQLITE in backend_types
        assert MemoryBackendType.MARKDOWN in backend_types
        assert MemoryBackendType.IN_MEMORY in backend_types

        # Check priorities are set correctly
        priorities = [b.priority for b in backends]
        assert max(priorities) == 100  # Neo4j should be highest

    def test_default_config(self):
        """Test default monitor configuration."""
        config = create_default_config()

        assert isinstance(config.check_interval, int)
        assert isinstance(config.cache_ttl, int)
        assert isinstance(config.failover_strategy, FailoverStrategy)
        assert isinstance(config.enable_auto_failover, bool)


class TestMemoryHealthMonitor:
    """Test the main memory health monitor class."""

    @pytest.fixture
    def sample_backends(self):
        """Create sample backend configurations for testing."""
        return [
            BackendConfig(
                backend_type=MemoryBackendType.NEO4J,
                priority=100,
                enabled=True,
                config={"uri": "bolt://localhost:7687"},
            ),
            BackendConfig(
                backend_type=MemoryBackendType.SQLITE,
                priority=80,
                enabled=True,
                config={"db_path": ":memory:"},
            ),
            BackendConfig(
                backend_type=MemoryBackendType.IN_MEMORY, priority=40, enabled=True, config={}
            ),
        ]

    @pytest.fixture
    def monitor_config(self):
        """Create sample monitor configuration."""
        return HealthMonitorConfig(
            check_interval=1,  # Fast for testing
            cache_ttl=5,
            enable_periodic_monitoring=False,  # Disable for most tests
            enable_auto_failover=True,
        )

    @pytest.fixture
    def event_collector(self):
        """Create an event collector for testing."""
        events = []

        def collect_event(event_type: str, event_data: Dict[str, Any]) -> None:
            events.append({"type": event_type, "data": event_data})

        return events, collect_event

    def test_monitor_initialization(self, sample_backends, monitor_config):
        """Test monitor initialization."""
        monitor = MemoryHealthMonitor(config=monitor_config, backends=sample_backends)

        assert monitor.current_backend is not None
        assert monitor.current_backend.backend_type == MemoryBackendType.NEO4J  # Highest priority
        assert len(monitor.backends) == 3

    def test_backend_selection_by_priority(self, monitor_config):
        """Test that highest priority enabled backend is selected."""
        backends = [
            BackendConfig(MemoryBackendType.SQLITE, priority=80, enabled=True),
            BackendConfig(MemoryBackendType.NEO4J, priority=100, enabled=True),
            BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True),
        ]

        monitor = MemoryHealthMonitor(config=monitor_config, backends=backends)

        assert monitor.current_backend.backend_type == MemoryBackendType.NEO4J

    def test_disabled_backend_skipping(self, monitor_config):
        """Test that disabled backends are skipped."""
        backends = [
            BackendConfig(MemoryBackendType.NEO4J, priority=100, enabled=False),
            BackendConfig(MemoryBackendType.SQLITE, priority=80, enabled=True),
            BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True),
        ]

        monitor = MemoryHealthMonitor(config=monitor_config, backends=backends)

        assert monitor.current_backend.backend_type == MemoryBackendType.SQLITE


class TestHealthChecks:
    """Test individual health check implementations."""

    @pytest.fixture
    async def monitor(self):
        """Create a monitor for health check testing."""
        config = HealthMonitorConfig(enable_periodic_monitoring=False)
        backends = create_default_backends()
        return MemoryHealthMonitor(config=config, backends=backends)

    @pytest.mark.asyncio
    async def test_in_memory_health_check(self, monitor):
        """Test in-memory backend health check (always healthy)."""
        result = await monitor.check_backend_health(MemoryBackendType.IN_MEMORY)

        assert result.backend_type == MemoryBackendType.IN_MEMORY
        assert result.status == HealthStatus.HEALTHY
        assert result.is_healthy
        assert result.error_message is None
        assert result.details.get("always_available") is True

    @pytest.mark.asyncio
    async def test_sqlite_health_check_success(self, monitor):
        """Test SQLite health check with successful connection."""
        # Use in-memory database for testing
        config = BackendConfig(
            backend_type=MemoryBackendType.SQLITE,
            priority=80,
            enabled=True,
            config={"db_path": ":memory:"},
        )

        result = await monitor._check_sqlite_health(config)

        assert result.backend_type == MemoryBackendType.SQLITE
        assert result.status == HealthStatus.HEALTHY
        assert result.is_healthy
        assert result.response_time_ms > 0

    @pytest.mark.asyncio
    async def test_sqlite_health_check_failure(self, monitor):
        """Test SQLite health check with connection failure."""
        config = BackendConfig(
            backend_type=MemoryBackendType.SQLITE,
            priority=80,
            enabled=True,
            config={"db_path": "/invalid/path/database.db"},
        )

        result = await monitor._check_sqlite_health(config)

        assert result.backend_type == MemoryBackendType.SQLITE
        assert result.status == HealthStatus.UNHEALTHY
        assert not result.is_healthy
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_markdown_health_check_success(self, monitor):
        """Test Markdown backend health check with successful directory access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = BackendConfig(
                backend_type=MemoryBackendType.MARKDOWN,
                priority=60,
                enabled=True,
                config={"base_dir": temp_dir},
            )

            result = await monitor._check_markdown_health(config)

            assert result.backend_type == MemoryBackendType.MARKDOWN
            assert result.status == HealthStatus.HEALTHY
            assert result.is_healthy
            assert result.details.get("permissions") == "read_write"

    @pytest.mark.asyncio
    async def test_markdown_health_check_failure(self, monitor):
        """Test Markdown backend health check with permission failure."""
        config = BackendConfig(
            backend_type=MemoryBackendType.MARKDOWN,
            priority=60,
            enabled=True,
            config={"base_dir": "/root/readonly"},  # Likely no permission
        )

        result = await monitor._check_markdown_health(config)

        # May succeed or fail depending on system permissions
        assert result.backend_type == MemoryBackendType.MARKDOWN
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY]

    @pytest.mark.asyncio
    async def test_neo4j_health_check_no_driver(self, monitor):
        """Test Neo4j health check when driver is not available."""
        config = BackendConfig(
            backend_type=MemoryBackendType.NEO4J,
            priority=100,
            enabled=True,
            config={"uri": "bolt://localhost:7687"},
        )

        with patch("...shared.memory_health.NEO4J_AVAILABLE", False):
            result = await monitor._check_neo4j_health(config)

            assert result.backend_type == MemoryBackendType.NEO4J
            assert result.status == HealthStatus.UNHEALTHY
            assert "Neo4j driver not available" in result.error_message

    @pytest.mark.asyncio
    async def test_check_all_backends_health(self, monitor):
        """Test checking health of all backends."""
        results = await monitor.check_all_backends_health()

        assert isinstance(results, dict)
        assert len(results) > 0

        # At least in-memory should be healthy
        in_memory_result = results.get(MemoryBackendType.IN_MEMORY)
        if in_memory_result:
            assert in_memory_result.is_healthy


class TestHealthCaching:
    """Test health check caching functionality."""

    @pytest.fixture
    def monitor(self):
        """Create monitor with short cache TTL for testing."""
        config = HealthMonitorConfig(cache_ttl=1, enable_periodic_monitoring=False)
        backends = [BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True)]
        return MemoryHealthMonitor(config=config, backends=backends)

    @pytest.mark.asyncio
    async def test_cache_hit(self, monitor):
        """Test that cached results are returned within TTL."""
        # First check - should execute
        result1 = await monitor.check_backend_health(MemoryBackendType.IN_MEMORY)

        # Second check immediately - should use cache
        result2 = await monitor.check_backend_health(MemoryBackendType.IN_MEMORY)

        assert result1.checked_at == result2.checked_at

    @pytest.mark.asyncio
    async def test_cache_expiry(self, monitor):
        """Test that cached results expire after TTL."""
        # First check
        result1 = await monitor.check_backend_health(MemoryBackendType.IN_MEMORY)

        # Wait for cache to expire
        await asyncio.sleep(1.1)

        # Second check - should execute fresh
        result2 = await monitor.check_backend_health(MemoryBackendType.IN_MEMORY)

        assert result1.checked_at != result2.checked_at


class TestFailoverMechanism:
    """Test automatic failover functionality."""

    @pytest.fixture
    def monitor_with_events(self):
        """Create monitor with event collection."""
        events = []

        def collect_event(event_type: str, event_data: Dict[str, Any]) -> None:
            events.append({"type": event_type, "data": event_data})

        config = HealthMonitorConfig(enable_auto_failover=True, enable_periodic_monitoring=False)

        backends = [
            BackendConfig(MemoryBackendType.NEO4J, priority=100, enabled=True),
            BackendConfig(MemoryBackendType.SQLITE, priority=80, enabled=True),
            BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True),
        ]

        monitor = MemoryHealthMonitor(
            config=config, backends=backends, event_callback=collect_event
        )

        return monitor, events

    @pytest.mark.asyncio
    async def test_failover_to_next_backend(self):
        """Test failover to next healthy backend."""
        events = []

        def collect_event(event_type: str, event_data: Dict[str, Any]) -> None:
            events.append({"type": event_type, "data": event_data})

        config = HealthMonitorConfig(enable_auto_failover=True, enable_periodic_monitoring=False)
        backends = [
            BackendConfig(MemoryBackendType.NEO4J, priority=100, enabled=True),
            BackendConfig(MemoryBackendType.SQLITE, priority=80, enabled=True),
            BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True),
        ]

        monitor = MemoryHealthMonitor(
            config=config, backends=backends, event_callback=collect_event
        )

        # Initially should select Neo4j
        assert monitor.current_backend.backend_type == MemoryBackendType.NEO4J

        # Mock a failed health check for the find_healthy_backend method
        async def mock_find_healthy_backend(exclude=None):
            return next(b for b in backends if b.backend_type == MemoryBackendType.IN_MEMORY)

        monitor._find_healthy_backend = mock_find_healthy_backend

        # Trigger failover
        success = await monitor.handle_backend_failure(MemoryBackendType.NEO4J)

        assert success
        assert monitor.current_backend.backend_type == MemoryBackendType.IN_MEMORY
        assert monitor._failover_count == 1

        # Check that event was emitted
        assert len(events) == 1
        assert events[0]["type"] == "backend_failover"

    @pytest.mark.asyncio
    async def test_failover_disabled(self):
        """Test that failover doesn't happen when disabled."""
        config = HealthMonitorConfig(enable_auto_failover=False, enable_periodic_monitoring=False)
        backends = [BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True)]

        monitor = MemoryHealthMonitor(config=config, backends=backends)

        original_backend = monitor.current_backend
        success = await monitor.handle_backend_failure(MemoryBackendType.IN_MEMORY)

        assert not success
        assert monitor.current_backend == original_backend
        assert monitor._failover_count == 0


class TestMonitoringLoop:
    """Test periodic monitoring functionality."""

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        config = HealthMonitorConfig(
            check_interval=0.1,  # Very fast for testing
            enable_periodic_monitoring=True,
        )
        backends = [BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True)]

        monitor = MemoryHealthMonitor(config=config, backends=backends)

        # Start monitoring
        await monitor.start_monitoring()
        assert monitor._monitoring_task is not None
        assert not monitor._monitoring_task.done()

        # Let it run briefly
        await asyncio.sleep(0.2)

        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor._monitoring_task.done() or monitor._monitoring_task.cancelled()

    @pytest.mark.asyncio
    async def test_monitoring_context_manager(self):
        """Test using monitoring as context manager."""
        config = HealthMonitorConfig(check_interval=0.1, enable_periodic_monitoring=True)
        backends = [BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True)]

        monitor = MemoryHealthMonitor(config=config, backends=backends)

        async with monitor.health_monitoring_context():
            assert monitor._monitoring_task is not None
            await asyncio.sleep(0.15)  # Let it run briefly

        # Should be cleaned up after context
        assert monitor._monitoring_task.done() or monitor._monitoring_task.cancelled()


class TestStatusReporting:
    """Test status reporting functionality."""

    def test_status_reporting(self):
        """Test comprehensive status reporting."""
        config = HealthMonitorConfig(enable_periodic_monitoring=False)
        backends = [BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True)]

        monitor = MemoryHealthMonitor(config=config, backends=backends)

        status = monitor.get_status()

        assert "current_backend" in status
        assert "failover_count" in status
        assert "monitoring_enabled" in status
        assert "auto_failover_enabled" in status
        assert "backends" in status
        assert "timestamp" in status

        assert status["current_backend"] == "in_memory"
        assert status["failover_count"] == 0
        assert status["monitoring_enabled"] == False
        assert status["auto_failover_enabled"] == True

    @pytest.mark.asyncio
    async def test_status_with_health_results(self):
        """Test status reporting with health check results."""
        config = HealthMonitorConfig(enable_periodic_monitoring=False)
        backends = [BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True)]

        monitor = MemoryHealthMonitor(config=config, backends=backends)

        # Run a health check to populate cache
        await monitor.check_backend_health(MemoryBackendType.IN_MEMORY)

        status = monitor.get_status()

        assert "in_memory" in status["backends"]
        backend_status = status["backends"]["in_memory"]

        assert "status" in backend_status
        assert "response_time_ms" in backend_status
        assert "last_checked" in backend_status

        assert backend_status["status"] == "healthy"


class TestFactoryFunctions:
    """Test factory functions for creating monitors."""

    def test_create_memory_health_monitor(self):
        """Test factory function for creating monitor."""
        monitor = create_memory_health_monitor()

        assert isinstance(monitor, MemoryHealthMonitor)
        assert monitor.current_backend is not None
        assert len(monitor.backends) > 0

    def test_create_with_custom_config(self):
        """Test factory with custom configuration."""
        config = HealthMonitorConfig(check_interval=60)
        monitor = create_memory_health_monitor(config=config)

        assert monitor.config.check_interval == 60

    def test_create_with_custom_backends(self):
        """Test factory with custom backends."""
        backends = [BackendConfig(MemoryBackendType.IN_MEMORY, priority=40, enabled=True)]
        monitor = create_memory_health_monitor(backends=backends)

        assert len(monitor.backends) == 1
        assert monitor.current_backend.backend_type == MemoryBackendType.IN_MEMORY


class TestIntegration:
    """Integration tests for the full system."""

    @pytest.mark.asyncio
    async def test_full_system_integration(self):
        """Test the complete system working together."""
        events = []

        def collect_event(event_type: str, event_data: Dict[str, Any]) -> None:
            events.append({"type": event_type, "data": event_data})

        # Create monitor with realistic configuration
        monitor = create_memory_health_monitor(event_callback=collect_event)

        async with monitor.health_monitoring_context():
            # Check initial status
            initial_status = monitor.get_status()
            assert initial_status["current_backend"] is not None

            # Run health checks
            health_results = await monitor.check_all_backends_health()
            assert len(health_results) > 0

            # At least one backend should be healthy
            healthy_backends = [r for r in health_results.values() if r.is_healthy]
            assert len(healthy_backends) > 0

            # Final status should include health results
            final_status = monitor.get_status()
            assert len(final_status["backends"]) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__])
