#!/usr/bin/env python3
"""
Memory Service Health Check System for Gadugi v0.3

Monitors and reports memory backend availability with automatic failover.
Provides health checks for:
- Neo4j: Connection and query capability
- SQLite: File access and query capability
- Markdown: Directory permissions
- In-Memory: Always available

Features:
- Periodic health monitoring with configurable intervals
- Automatic failover when primary backend fails
- Health check result caching to avoid excessive checking
- Event emission when backend changes
- Logging for debugging backend switches
- Status endpoint/method for monitoring
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import threading
from contextlib import asynccontextmanager

try:
    from neo4j import AsyncGraphDatabase, AsyncDriver
    from neo4j.exceptions import Neo4jError

    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    AsyncDriver = Any
    Neo4jError = Exception

try:
    import aiosqlite

    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


class MemoryBackendType(Enum):
    """Memory backend types."""

    NEO4J = "neo4j"
    SQLITE = "sqlite"
    MARKDOWN = "markdown"
    IN_MEMORY = "in_memory"


class HealthStatus(Enum):
    """Health check status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class FailoverStrategy(Enum):
    """Failover strategy options."""

    IMMEDIATE = "immediate"  # Switch immediately on first failure
    RETRY_THEN_SWITCH = "retry"  # Retry a few times before switching
    GRACEFUL = "graceful"  # Wait for ongoing operations before switching


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    backend_type: MemoryBackendType
    status: HealthStatus
    response_time_ms: float
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.now)

    @property
    def is_healthy(self) -> bool:
        """Check if backend is healthy."""
        return self.status == HealthStatus.HEALTHY

    @property
    def is_available(self) -> bool:
        """Check if backend is available (healthy or degraded)."""
        return self.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]


@dataclass
class BackendConfig:
    """Configuration for a memory backend."""

    backend_type: MemoryBackendType
    priority: int = 0  # Higher number = higher priority
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    health_check_interval: int = 30  # seconds
    max_retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds
    timeout: float = 5.0  # seconds


@dataclass
class HealthMonitorConfig:
    """Configuration for health monitoring."""

    check_interval: int = 30  # seconds between health checks
    cache_ttl: int = 10  # seconds to cache health results
    failover_strategy: FailoverStrategy = FailoverStrategy.RETRY_THEN_SWITCH
    enable_auto_failover: bool = True
    enable_periodic_monitoring: bool = True
    log_backend_switches: bool = True
    emit_events: bool = True


class MemoryHealthMonitor:
    """Memory service health check system with automatic failover."""

    def __init__(
        self,
        config: HealthMonitorConfig,
        backends: List[BackendConfig],
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.config = config
        self.backends = sorted(backends, key=lambda x: x.priority, reverse=True)
        self.event_callback = event_callback
        self.logger = logger or logging.getLogger(__name__)

        # Health state
        self._health_cache: Dict[MemoryBackendType, HealthCheckResult] = {}
        self._cache_lock = threading.RLock()
        self._current_backend: Optional[BackendConfig] = None
        self._failover_count = 0
        self._last_failover: Optional[datetime] = None

        # Monitoring control
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()

        # Backend connections
        self._neo4j_driver: Optional[AsyncDriver] = None
        self._sqlite_connections: Dict[str, str] = {}  # path -> connection_id

        # Initialize current backend
        self._select_initial_backend()

    def _select_initial_backend(self) -> None:
        """Select the initial backend based on priority and availability."""
        for backend in self.backends:
            if backend.enabled:
                self._current_backend = backend
                self.logger.info(
                    f"Selected initial backend: {backend.backend_type.value}"
                )
                break

        if not self._current_backend:
            raise RuntimeError("No enabled backends configured")

    # ========== Health Check Implementations ==========

    async def _check_neo4j_health(self, config: BackendConfig) -> HealthCheckResult:
        """Check Neo4j backend health."""
        start_time = time.time()

        if not NEO4J_AVAILABLE:
            return HealthCheckResult(
                backend_type=MemoryBackendType.NEO4J,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message="Neo4j driver not available",
            )

        try:
            backend_config = config.config
            uri = backend_config.get("uri", "bolt://localhost:7687")
            user = backend_config.get("user", "neo4j")
            password = backend_config.get("password", "gadugi123!")
            database = backend_config.get("database", "neo4j")

            # Reuse existing driver or create new one
            if not self._neo4j_driver:
                self._neo4j_driver = AsyncGraphDatabase.driver(
                    uri, auth=(user, password)
                )

            # Test connection with a simple query
            async with self._neo4j_driver.session(database=database) as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if not record or record["test"] != 1:
                    raise Neo4jError("Invalid query result")

                # Test a memory-specific query
                result = await session.run("""
                    MATCH (m:Memory)
                    RETURN count(m) as memory_count
                    LIMIT 1
                """)
                record = await result.single()
                memory_count = record["memory_count"] if record else 0

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                backend_type=MemoryBackendType.NEO4J,
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "uri": uri,
                    "database": database,
                    "memory_count": memory_count,
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                backend_type=MemoryBackendType.NEO4J,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e),
                details={"exception_type": type(e).__name__},
            )

    async def _check_sqlite_health(self, config: BackendConfig) -> HealthCheckResult:
        """Check SQLite backend health."""
        start_time = time.time()

        if not SQLITE_AVAILABLE:
            return HealthCheckResult(
                backend_type=MemoryBackendType.SQLITE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                error_message="aiosqlite not available",
            )

        try:
            backend_config = config.config
            db_path = Path(backend_config.get("db_path", ".claude/data/memory.db"))

            # Ensure directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # Test file access and database operations
            async with aiosqlite.connect(db_path) as db:
                # Test basic query
                async with db.execute("SELECT 1 as test") as cursor:
                    row = await cursor.fetchone()
                    if not row or row[0] != 1:
                        raise sqlite3.Error("Invalid query result")

                # Test memory table access (if it exists)
                try:
                    async with db.execute("SELECT count(*) FROM memories") as cursor:
                        row = await cursor.fetchone()
                        memory_count = row[0] if row else 0
                except sqlite3.OperationalError:
                    # Table doesn't exist yet, that's OK
                    memory_count = 0

                # Check database file size
                file_size = db_path.stat().st_size if db_path.exists() else 0

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                backend_type=MemoryBackendType.SQLITE,
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "db_path": str(db_path),
                    "file_size_bytes": file_size,
                    "memory_count": memory_count,
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                backend_type=MemoryBackendType.SQLITE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e),
                details={"exception_type": type(e).__name__},
            )

    async def _check_markdown_health(self, config: BackendConfig) -> HealthCheckResult:
        """Check Markdown backend health."""
        start_time = time.time()

        try:
            backend_config = config.config
            base_dir = Path(backend_config.get("base_dir", ".claude/memory/markdown"))

            # Test directory permissions
            base_dir.mkdir(parents=True, exist_ok=True)

            # Test write permissions
            test_file = base_dir / "health_check.md"
            test_content = f"# Health Check\nTimestamp: {datetime.now().isoformat()}\n"

            test_file.write_text(test_content, encoding="utf-8")

            # Test read permissions
            read_content = test_file.read_text(encoding="utf-8")
            if test_content not in read_content:
                raise OSError("File content verification failed")

            # Clean up test file
            test_file.unlink()

            # Count existing memory files
            memory_files = list(base_dir.glob("*.md"))

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                backend_type=MemoryBackendType.MARKDOWN,
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time,
                details={
                    "base_dir": str(base_dir),
                    "memory_files_count": len(memory_files),
                    "permissions": "read_write",
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                backend_type=MemoryBackendType.MARKDOWN,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error_message=str(e),
                details={"exception_type": type(e).__name__},
            )

    async def _check_in_memory_health(self, config: BackendConfig) -> HealthCheckResult:
        """Check In-Memory backend health (always healthy)."""
        start_time = time.time()

        # In-memory is always available
        response_time = (time.time() - start_time) * 1000

        return HealthCheckResult(
            backend_type=MemoryBackendType.IN_MEMORY,
            status=HealthStatus.HEALTHY,
            response_time_ms=response_time,
            details={"type": "in_memory", "always_available": True},
        )

    # ========== Health Check Orchestration ==========

    async def check_backend_health(
        self, backend_type: MemoryBackendType
    ) -> HealthCheckResult:
        """Check health of a specific backend."""
        backend = next(
            (b for b in self.backends if b.backend_type == backend_type), None
        )
        if not backend:
            return HealthCheckResult(
                backend_type=backend_type,
                status=HealthStatus.UNKNOWN,
                response_time_ms=0,
                error_message="Backend not configured",
            )

        # Check cache first
        cached_result = self._get_cached_health_result(backend_type)
        if cached_result:
            return cached_result

        # Perform health check based on backend type
        if backend_type == MemoryBackendType.NEO4J:
            result = await self._check_neo4j_health(backend)
        elif backend_type == MemoryBackendType.SQLITE:
            result = await self._check_sqlite_health(backend)
        elif backend_type == MemoryBackendType.MARKDOWN:
            result = await self._check_markdown_health(backend)
        elif backend_type == MemoryBackendType.IN_MEMORY:
            result = await self._check_in_memory_health(backend)
        else:
            result = HealthCheckResult(
                backend_type=backend_type,
                status=HealthStatus.UNKNOWN,
                response_time_ms=0,
                error_message="Unknown backend type",
            )

        # Cache the result
        self._cache_health_result(result)

        # Log the result
        if result.is_healthy:
            self.logger.debug(
                f"{backend_type.value} health check: HEALTHY ({result.response_time_ms:.1f}ms)"
            )
        else:
            self.logger.warning(
                f"{backend_type.value} health check: {result.status.value} - {result.error_message}"
            )

        return result

    async def check_all_backends_health(
        self,
    ) -> Dict[MemoryBackendType, HealthCheckResult]:
        """Check health of all configured backends."""
        results = {}

        # Run health checks concurrently
        tasks = []
        for backend in self.backends:
            if backend.enabled:
                task = asyncio.create_task(
                    self.check_backend_health(backend.backend_type)
                )
                tasks.append((backend.backend_type, task))

        # Collect results
        for backend_type, task in tasks:
            try:
                result = await task
                results[backend_type] = result
            except Exception as e:
                results[backend_type] = HealthCheckResult(
                    backend_type=backend_type,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    error_message=f"Health check failed: {e}",
                )

        return results

    def _get_cached_health_result(
        self, backend_type: MemoryBackendType
    ) -> Optional[HealthCheckResult]:
        """Get cached health result if still valid."""
        with self._cache_lock:
            cached = self._health_cache.get(backend_type)
            if cached:
                age = (datetime.now() - cached.checked_at).total_seconds()
                if age < self.config.cache_ttl:
                    return cached
        return None

    def _cache_health_result(self, result: HealthCheckResult) -> None:
        """Cache a health check result."""
        with self._cache_lock:
            self._health_cache[result.backend_type] = result

    # ========== Failover Management ==========

    async def handle_backend_failure(self, failed_backend: MemoryBackendType) -> bool:
        """Handle backend failure and attempt failover."""
        if not self.config.enable_auto_failover:
            self.logger.warning(
                f"Backend {failed_backend.value} failed but auto-failover is disabled"
            )
            return False

        # Find next healthy backend
        healthy_backend = await self._find_healthy_backend(exclude=[failed_backend])

        if not healthy_backend:
            self.logger.error("No healthy backends available for failover")
            return False

        # Perform failover
        old_backend = self._current_backend
        self._current_backend = healthy_backend
        self._failover_count += 1
        self._last_failover = datetime.now()

        # Log failover
        if self.config.log_backend_switches:
            old_type = old_backend.backend_type.value if old_backend else "none"
            new_type = healthy_backend.backend_type.value
            self.logger.warning(
                f"FAILOVER: {old_type} -> {new_type} (failover #{self._failover_count})"
            )

        # Emit event
        if self.config.emit_events and self.event_callback:
            self.event_callback(
                "backend_failover",
                {
                    "from_backend": old_backend.backend_type.value
                    if old_backend
                    else None,
                    "to_backend": healthy_backend.backend_type.value,
                    "failover_count": self._failover_count,
                    "timestamp": self._last_failover.isoformat(),
                },
            )

        return True

    async def _find_healthy_backend(
        self, exclude: List[MemoryBackendType] = None
    ) -> Optional[BackendConfig]:
        """Find the highest priority healthy backend."""
        exclude = exclude or []

        for backend in self.backends:
            if not backend.enabled or backend.backend_type in exclude:
                continue

            health_result = await self.check_backend_health(backend.backend_type)
            if health_result.is_available:
                return backend

        return None

    # ========== Monitoring and Status ==========

    async def start_monitoring(self) -> None:
        """Start periodic health monitoring."""
        if not self.config.enable_periodic_monitoring:
            self.logger.info("Periodic monitoring is disabled")
            return

        if self._monitoring_task and not self._monitoring_task.done():
            self.logger.warning("Monitoring already running")
            return

        self.logger.info(
            f"Starting health monitoring (interval: {self.config.check_interval}s)"
        )
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self) -> None:
        """Stop periodic health monitoring."""
        self.logger.info("Stopping health monitoring")
        self._shutdown_event.set()

        if self._monitoring_task:
            try:
                await asyncio.wait_for(self._monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                self.logger.warning("Monitoring task did not stop gracefully")
                self._monitoring_task.cancel()

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_health_checks()

                # Wait for next check interval
                await asyncio.wait_for(
                    self._shutdown_event.wait(), timeout=self.config.check_interval
                )

            except asyncio.TimeoutError:
                # Normal timeout, continue monitoring
                pass
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _perform_health_checks(self) -> None:
        """Perform health checks and handle any failures."""
        health_results = await self.check_all_backends_health()

        # Check if current backend is healthy
        if self._current_backend:
            current_health = health_results.get(self._current_backend.backend_type)
            if current_health and not current_health.is_available:
                self.logger.warning(
                    f"Current backend {self._current_backend.backend_type.value} is unhealthy"
                )
                await self.handle_backend_failure(self._current_backend.backend_type)

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        with self._cache_lock:
            backend_status = {}
            for backend_type, health_result in self._health_cache.items():
                backend_status[backend_type.value] = {
                    "status": health_result.status.value,
                    "response_time_ms": health_result.response_time_ms,
                    "last_checked": health_result.checked_at.isoformat(),
                    "error": health_result.error_message,
                    "details": health_result.details,
                }

        return {
            "current_backend": self._current_backend.backend_type.value
            if self._current_backend
            else None,
            "failover_count": self._failover_count,
            "last_failover": self._last_failover.isoformat()
            if self._last_failover
            else None,
            "monitoring_enabled": self.config.enable_periodic_monitoring,
            "auto_failover_enabled": self.config.enable_auto_failover,
            "backends": backend_status,
            "timestamp": datetime.now().isoformat(),
        }

    @property
    def current_backend(self) -> Optional[BackendConfig]:
        """Get the currently active backend."""
        return self._current_backend

    @property
    def current_backend_type(self) -> Optional[MemoryBackendType]:
        """Get the currently active backend type."""
        return self._current_backend.backend_type if self._current_backend else None

    # ========== Context Management ==========

    @asynccontextmanager
    async def health_monitoring_context(self):
        """Context manager for health monitoring lifecycle."""
        try:
            await self.start_monitoring()
            yield self
        finally:
            await self.stop_monitoring()
            # Clean up connections
            if self._neo4j_driver:
                await self._neo4j_driver.close()
                self._neo4j_driver = None

    # ========== Cleanup ==========

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.stop_monitoring()

        # Close Neo4j driver
        if self._neo4j_driver:
            await self._neo4j_driver.close()
            self._neo4j_driver = None

        self.logger.info("Memory health monitor cleanup completed")


# ========== Factory Functions ==========


def create_default_backends() -> List[BackendConfig]:
    """Create default backend configurations."""
    return [
        BackendConfig(
            backend_type=MemoryBackendType.NEO4J,
            priority=100,  # Highest priority
            enabled=NEO4J_AVAILABLE,
            config={
                "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "user": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "gadugi123!"),
                "database": os.getenv("NEO4J_DATABASE", "neo4j"),
            },
        ),
        BackendConfig(
            backend_type=MemoryBackendType.SQLITE,
            priority=80,
            enabled=SQLITE_AVAILABLE,
            config={"db_path": os.getenv("SQLITE_DB_PATH", ".claude/data/memory.db")},
        ),
        BackendConfig(
            backend_type=MemoryBackendType.MARKDOWN,
            priority=60,
            enabled=True,  # Always available
            config={"base_dir": os.getenv("MARKDOWN_DIR", ".claude/memory/markdown")},
        ),
        BackendConfig(
            backend_type=MemoryBackendType.IN_MEMORY,
            priority=40,  # Lowest priority (fallback)
            enabled=True,  # Always available
            config={},
        ),
    ]


def create_default_config() -> HealthMonitorConfig:
    """Create default health monitor configuration."""
    return HealthMonitorConfig(
        check_interval=int(os.getenv("MEMORY_HEALTH_CHECK_INTERVAL", "30")),
        cache_ttl=int(os.getenv("MEMORY_HEALTH_CACHE_TTL", "10")),
        failover_strategy=FailoverStrategy.RETRY_THEN_SWITCH,
        enable_auto_failover=os.getenv("MEMORY_ENABLE_AUTO_FAILOVER", "true").lower()
        == "true",
        enable_periodic_monitoring=os.getenv("MEMORY_ENABLE_MONITORING", "true").lower()
        == "true",
        log_backend_switches=True,
        emit_events=True,
    )


def create_memory_health_monitor(
    config: Optional[HealthMonitorConfig] = None,
    backends: Optional[List[BackendConfig]] = None,
    event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    logger: Optional[logging.Logger] = None,
) -> MemoryHealthMonitor:
    """Factory function to create a memory health monitor."""
    if config is None:
        config = create_default_config()

    if backends is None:
        backends = create_default_backends()

    if logger is None:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

    return MemoryHealthMonitor(
        config=config, backends=backends, event_callback=event_callback, logger=logger
    )


# ========== Example Usage ==========


async def example_usage():
    """Example of how to use the memory health monitor."""

    def event_handler(event_type: str, event_data: Dict[str, Any]) -> None:
        print(f"EVENT: {event_type} - {json.dumps(event_data, indent=2)}")

    # Create health monitor
    monitor = create_memory_health_monitor(event_callback=event_handler)

    async with monitor.health_monitoring_context():
        print("Memory Health Monitor started")

        # Check health of all backends
        health_results = await monitor.check_all_backends_health()
        for backend_type, result in health_results.items():
            status = "✅" if result.is_healthy else "❌"
            print(
                f"{status} {backend_type.value}: {result.status.value} ({result.response_time_ms:.1f}ms)"
            )

        # Get status
        status = monitor.get_status()
        print(f"\nCurrent backend: {status['current_backend']}")
        print(f"Failover count: {status['failover_count']}")

        # Wait a bit to see monitoring in action
        await asyncio.sleep(35)

        # Final status
        final_status = monitor.get_status()
        print(f"\nFinal status: {json.dumps(final_status, indent=2)}")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run example
    asyncio.run(example_usage())
