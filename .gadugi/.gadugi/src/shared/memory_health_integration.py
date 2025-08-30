#!/usr/bin/env python3
"""
Memory Health Integration for Gadugi v0.3

Integrates the memory health check system with the existing memory infrastructure.
Provides a unified interface that automatically manages backend health and failover.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

try:
    from .memory_health import (
        MemoryHealthMonitor,
        MemoryBackendType,
        BackendConfig,
        HealthMonitorConfig,
        create_memory_health_monitor,
    )
    from .memory_integration import AgentMemoryInterface
except ImportError:
    from memory_health import (
        MemoryHealthMonitor,
        MemoryBackendType,
        HealthMonitorConfig,
        create_memory_health_monitor,
    )
    from memory_integration import AgentMemoryInterface


class HealthAwareMemoryInterface(AgentMemoryInterface):
    """
    Enhanced memory interface with health monitoring and automatic failover.

    This extends the standard AgentMemoryInterface to include:
    - Automatic backend health monitoring
    - Transparent failover between backends
    - Health status reporting
    - Backend-specific connection management
    """

    def __init__(
        self,
        agent_id: str,
        mcp_base_url: str = "http://localhost:8000",
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        enable_health_monitoring: bool = True,
        health_check_interval: int = 30,
        auto_failover: bool = True,
    ):
        super().__init__(agent_id, mcp_base_url, project_id, task_id)

        # Health monitoring setup
        self._enable_health_monitoring = enable_health_monitoring
        self._health_monitor: Optional[MemoryHealthMonitor] = None
        self._health_check_interval = health_check_interval
        self._auto_failover = auto_failover
        self._logger = logging.getLogger(f"{__name__}.{agent_id}")

        # Backend connections cache
        self._backend_connections: Dict[MemoryBackendType, Any] = {}

    async def __aenter__(self):
        """Enhanced async context manager with health monitoring."""
        # Initialize base interface
        await super().__aenter__()

        # Initialize health monitoring if enabled
        if self._enable_health_monitoring:
            await self._initialize_health_monitoring()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Enhanced cleanup with health monitoring."""
        # Cleanup health monitoring
        if self._health_monitor:
            await self._health_monitor.cleanup()
            self._health_monitor = None

        # Cleanup backend connections
        await self._cleanup_backend_connections()

        # Call parent cleanup
        await super().__aexit__(exc_type, exc_val, exc_tb)

    async def _initialize_health_monitoring(self) -> None:
        """Initialize the health monitoring system."""
        try:
            # Create health monitor configuration
            config = HealthMonitorConfig(
                check_interval=self._health_check_interval,
                enable_auto_failover=self._auto_failover,
                enable_periodic_monitoring=True,
                log_backend_switches=True,
                emit_events=True,
            )

            # Event handler for backend changes
            def on_health_event(event_type: str, event_data: Dict[str, Any]) -> None:
                if event_type == "backend_failover":
                    self._logger.warning(
                        f"Memory backend failover: {event_data.get('from_backend')} -> "
                        f"{event_data.get('to_backend')} (count: {event_data.get('failover_count')})"
                    )
                    # Could emit agent-level events here for upstream handlers

            # Create health monitor
            self._health_monitor = create_memory_health_monitor(
                config=config, event_callback=on_health_event, logger=self._logger
            )

            # Start monitoring
            await self._health_monitor.start_monitoring()

            self._logger.info(
                f"Memory health monitoring initialized for agent {self.agent_id} "
                f"(current backend: {self._health_monitor.current_backend_type.value if self._health_monitor.current_backend_type else 'none'})"
            )

        except Exception as e:
            self._logger.error(f"Failed to initialize health monitoring: {e}")
            # Continue without health monitoring rather than fail completely
            self._enable_health_monitoring = False

    async def _cleanup_backend_connections(self) -> None:
        """Clean up any cached backend connections."""
        for backend_type, connection in self._backend_connections.items():
            try:
                if hasattr(connection, "close"):
                    if asyncio.iscoroutinefunction(connection.close):
                        await connection.close()
                    else:
                        connection.close()
            except Exception as e:
                self._logger.warning(
                    f"Error closing {backend_type.value} connection: {e}"
                )

        self._backend_connections.clear()

    # ========== Health Status Methods ==========

    def get_memory_health_status(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive memory backend health status."""
        if not self._health_monitor:
            return None

        return self._health_monitor.get_status()

    def get_current_backend(self) -> Optional[str]:
        """Get the currently active memory backend."""
        if not self._health_monitor or not self._health_monitor.current_backend_type:
            return None

        return self._health_monitor.current_backend_type.value

    async def force_health_check(self) -> Dict[str, Any]:
        """Force an immediate health check of all backends."""
        if not self._health_monitor:
            return {"error": "Health monitoring not enabled"}

        health_results = await self._health_monitor.check_all_backends_health()
        return {
            backend_type.value: {
                "status": result.status.value,
                "healthy": result.is_healthy,
                "response_time_ms": result.response_time_ms,
                "error": result.error_message,
                "details": result.details,
            }
            for backend_type, result in health_results.items()
        }

    async def trigger_failover(self, from_backend: str) -> bool:
        """Manually trigger a failover from the specified backend."""
        if not self._health_monitor:
            self._logger.warning(
                "Cannot trigger failover: health monitoring not enabled"
            )
            return False

        try:
            backend_type = MemoryBackendType(from_backend)
            success = await self._health_monitor.handle_backend_failure(backend_type)
            if success:
                self._logger.info(f"Manual failover from {from_backend} successful")
            else:
                self._logger.warning(f"Manual failover from {from_backend} failed")
            return success
        except ValueError:
            self._logger.error(f"Invalid backend type: {from_backend}")
            return False

    # ========== Enhanced Memory Operations ==========

    async def remember_short_term(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        retry_on_failure: bool = True,
    ) -> str:
        """Store short-term memory with automatic retry on backend failure."""
        try:
            return await super().remember_short_term(content, tags, importance)
        except Exception as e:
            if retry_on_failure and self._health_monitor:
                self._logger.warning(f"Short-term memory storage failed: {e}")

                # Check if current backend is healthy
                if self._health_monitor.current_backend_type:
                    health_result = await self._health_monitor.check_backend_health(
                        self._health_monitor.current_backend_type
                    )

                    if not health_result.is_healthy:
                        # Attempt failover
                        await self._health_monitor.handle_backend_failure(
                            self._health_monitor.current_backend_type
                        )

                        # Retry with new backend
                        return await super().remember_short_term(
                            content, tags, importance
                        )

            raise  # Re-raise original exception if retry not enabled or failed

    async def remember_long_term(
        self,
        content: str,
        memory_type: str = "semantic",
        tags: Optional[List[str]] = None,
        importance: float = 0.7,
        retry_on_failure: bool = True,
    ) -> str:
        """Store long-term memory with automatic retry on backend failure."""
        try:
            return await super().remember_long_term(
                content, memory_type, tags, importance
            )
        except Exception as e:
            if retry_on_failure and self._health_monitor:
                self._logger.warning(f"Long-term memory storage failed: {e}")

                # Check if current backend is healthy and attempt failover if needed
                if self._health_monitor.current_backend_type:
                    health_result = await self._health_monitor.check_backend_health(
                        self._health_monitor.current_backend_type
                    )

                    if not health_result.is_healthy:
                        await self._health_monitor.handle_backend_failure(
                            self._health_monitor.current_backend_type
                        )

                        # Retry with new backend
                        return await super().remember_long_term(
                            content, memory_type, tags, importance
                        )

            raise

    async def recall_memories(
        self,
        memory_type: Optional[str] = None,
        short_term_only: bool = False,
        long_term_only: bool = False,
        limit: int = 50,
        retry_on_failure: bool = True,
    ) -> List[Dict[str, Any]]:
        """Recall memories with automatic retry on backend failure."""
        try:
            return await super().recall_memories(
                memory_type, short_term_only, long_term_only, limit
            )
        except Exception as e:
            if retry_on_failure and self._health_monitor:
                self._logger.warning(f"Memory recall failed: {e}")

                # Check backend health and failover if needed
                if self._health_monitor.current_backend_type:
                    health_result = await self._health_monitor.check_backend_health(
                        self._health_monitor.current_backend_type
                    )

                    if not health_result.is_healthy:
                        await self._health_monitor.handle_backend_failure(
                            self._health_monitor.current_backend_type
                        )

                        # Retry with new backend
                        return await super().recall_memories(
                            memory_type, short_term_only, long_term_only, limit
                        )

            raise

    # ========== Diagnostic Methods ==========

    async def run_memory_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive memory system diagnostics."""
        diagnostics = {
            "agent_id": self.agent_id,
            "timestamp": asyncio.get_event_loop().time(),
            "health_monitoring_enabled": self._enable_health_monitoring,
            "backend_health": None,
            "connection_test": None,
            "memory_operations_test": None,
        }

        # Health status
        if self._health_monitor:
            diagnostics["backend_health"] = await self.force_health_check()

        # Connection test
        try:
            if self._client:
                # Test basic connection
                response = await self._client.get("/health", timeout=5.0)
                diagnostics["connection_test"] = {
                    "status": "success",
                    "response_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                    if response.elapsed
                    else 0,
                }
        except Exception as e:
            diagnostics["connection_test"] = {"status": "failed", "error": str(e)}

        # Memory operations test
        try:
            # Try storing and retrieving a test memory
            test_content = f"Diagnostic test memory for {self.agent_id}"
            memory_id = await self.remember_short_term(
                test_content, tags=["diagnostic"], importance=0.1
            )

            # Try retrieving it
            memories = await self.recall_memories(short_term_only=True, limit=1)

            diagnostics["memory_operations_test"] = {
                "status": "success",
                "test_memory_id": memory_id,
                "retrieved_memories": len(memories),
            }

        except Exception as e:
            diagnostics["memory_operations_test"] = {
                "status": "failed",
                "error": str(e),
            }

        return diagnostics


# ========== Helper Functions ==========


def create_health_aware_memory_interface(
    agent_id: str,
    mcp_base_url: str = "http://localhost:8000",
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    **health_options,
) -> HealthAwareMemoryInterface:
    """Factory function to create a health-aware memory interface."""
    return HealthAwareMemoryInterface(
        agent_id=agent_id,
        mcp_base_url=mcp_base_url,
        project_id=project_id,
        task_id=task_id,
        **health_options,
    )


@asynccontextmanager
async def memory_with_health_monitoring(
    agent_id: str,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    **kwargs,
):
    """Context manager for memory interface with health monitoring."""
    interface = create_health_aware_memory_interface(
        agent_id=agent_id, project_id=project_id, task_id=task_id, **kwargs
    )

    async with interface:
        yield interface


# ========== Enhanced Memory-Enabled Agent ==========


class HealthAwareMemoryAgent:
    """Enhanced agent with health-aware memory management."""

    def __init__(
        self,
        agent_id: str,
        agent_type: str = "worker",
        project_id: Optional[str] = None,
        enable_health_monitoring: bool = True,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.project_id = project_id
        self.current_task_id: Optional[str] = None
        self.memory: Optional[HealthAwareMemoryInterface] = None
        self._enable_health_monitoring = enable_health_monitoring
        self._logger = logging.getLogger(f"{__name__}.{agent_id}")

    async def initialize(self):
        """Initialize agent with health-aware memory."""
        self.memory = HealthAwareMemoryInterface(
            agent_id=self.agent_id,
            project_id=self.project_id,
            enable_health_monitoring=self._enable_health_monitoring,
        )

        self._logger.info(f"Initialized health-aware memory agent: {self.agent_id}")

    async def start_task(self, task_id: str, task_description: str):
        """Start a task with memory health monitoring."""
        self.current_task_id = task_id

        if self.memory:
            self.memory.task_id = task_id

            async with self.memory as mem:
                # Store task start with backend health info
                backend_info = mem.get_current_backend()
                await mem.remember_short_term(
                    f"Started task: {task_description} (backend: {backend_info})",
                    tags=["task_start", "event", "backend_info"],
                    importance=0.8,
                )

                # Run initial diagnostics
                diagnostics = await mem.run_memory_diagnostics()
                self._logger.debug(f"Memory diagnostics: {diagnostics}")

    async def get_memory_status(self) -> Dict[str, Any]:
        """Get detailed memory system status."""
        if not self.memory:
            return {"error": "Memory not initialized"}

        async with self.memory as mem:
            status = mem.get_memory_health_status()
            diagnostics = await mem.run_memory_diagnostics()

            return {
                "agent_id": self.agent_id,
                "health_status": status,
                "diagnostics": diagnostics,
            }

    async def handle_memory_emergency(self) -> bool:
        """Handle memory system emergencies with diagnostics and recovery."""
        if not self.memory:
            return False

        self._logger.warning("Memory emergency detected, running diagnostics...")

        async with self.memory as mem:
            # Run full diagnostics
            diagnostics = await mem.run_memory_diagnostics()
            self._logger.info(f"Emergency diagnostics: {diagnostics}")

            # Force health check
            health_status = await mem.force_health_check()

            # Find unhealthy backends
            unhealthy_backends = [
                backend
                for backend, status in health_status.items()
                if not status.get("healthy", False)
            ]

            if unhealthy_backends:
                self._logger.warning(
                    f"Unhealthy backends detected: {unhealthy_backends}"
                )

                # Try to trigger failover from first unhealthy backend
                if unhealthy_backends:
                    success = await mem.trigger_failover(unhealthy_backends[0])
                    if success:
                        self._logger.info("Emergency failover successful")
                        return True

            return False


# ========== Example Usage ==========


async def example_health_aware_usage():
    """Example of using the health-aware memory system."""

    # Create agent with health monitoring
    agent = HealthAwareMemoryAgent(
        agent_id="health_demo_agent",
        project_id="gadugi_v03",
        enable_health_monitoring=True,
    )

    await agent.initialize()

    # Use memory with health monitoring context
    async with memory_with_health_monitoring(
        agent_id="test_agent",
        project_id="demo_project",
        enable_health_monitoring=True,
        health_check_interval=15,
    ) as memory:
        # Store some memories
        await memory.remember_short_term("Testing health-aware memory system")
        await memory.remember_long_term(
            "This is a persistent memory with health monitoring"
        )

        # Check memory health
        health_status = memory.get_memory_health_status()
        print(f"Current backend: {memory.get_current_backend()}")
        print(f"Health status: {health_status}")

        # Run diagnostics
        diagnostics = await memory.run_memory_diagnostics()
        print(f"Diagnostics: {diagnostics}")

        # Recall memories
        memories = await memory.recall_memories(limit=10)
        print(f"Retrieved {len(memories)} memories")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run example
    asyncio.run(example_health_aware_usage())
