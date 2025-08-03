"""
Resource Manager for Container Execution.

Monitors and enforces resource limits for container execution,
including CPU, memory, disk, and network usage tracking.
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import psutil

# Import Enhanced Separation shared modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '.claude', 'shared', 'utils'))
from error_handling import GadugiError, RecoverableError

logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    """Resource usage snapshot."""
    timestamp: datetime
    cpu_percent: float
    memory_bytes: int
    memory_percent: float
    disk_bytes: int
    network_rx_bytes: int
    network_tx_bytes: int
    processes: int
    open_files: int


@dataclass
class ResourceAlert:
    """Resource usage alert."""
    container_id: str
    resource_type: str
    current_value: float
    threshold: float
    timestamp: datetime
    severity: str
    message: str


class ResourceMonitor:
    """Monitors resource usage for a single container."""
    
    def __init__(self, container_id: str, container, alert_callback: Optional[Callable] = None):
        """Initialize resource monitor for a container."""
        self.container_id = container_id
        self.container = container
        self.alert_callback = alert_callback
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.usage_history: List[ResourceUsage] = []
        self.alerts: List[ResourceAlert] = []
        
        # Alert thresholds (percentages)
        self.thresholds = {
            'cpu_warning': 80.0,
            'cpu_critical': 95.0,
            'memory_warning': 80.0,
            'memory_critical': 95.0,
            'disk_warning': 80.0,
            'disk_critical': 95.0
        }
    
    def start_monitoring(self, interval: float = 5.0) -> None:
        """Start resource monitoring in background thread."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started resource monitoring for container {self.container_id[:8]}")
    
    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        logger.info(f"Stopped resource monitoring for container {self.container_id[:8]}")
    
    def _monitor_loop(self, interval: float) -> None:
        """Main monitoring loop."""
        while self.monitoring:
            try:
                usage = self._collect_usage()
                if usage:
                    self.usage_history.append(usage)
                    self._check_thresholds(usage)
                    
                    # Keep history manageable (last 1000 samples)
                    if len(self.usage_history) > 1000:
                        self.usage_history = self.usage_history[-1000:]
                
            except Exception as e:
                logger.warning(f"Error collecting usage for {self.container_id[:8]}: {e}")
            
            time.sleep(interval)
    
    def _collect_usage(self) -> Optional[ResourceUsage]:
        """Collect current resource usage."""
        try:
            stats = self.container.stats(stream=False)
            
            # Calculate CPU usage
            cpu_stats = stats.get('cpu_stats', {})
            precpu_stats = stats.get('precpu_stats', {})
            
            cpu_percent = 0.0
            if cpu_stats and precpu_stats:
                cpu_delta = cpu_stats.get('cpu_usage', {}).get('total_usage', 0) - \
                           precpu_stats.get('cpu_usage', {}).get('total_usage', 0)
                system_delta = cpu_stats.get('system_cpu_usage', 0) - \
                              precpu_stats.get('system_cpu_usage', 0)
                
                if system_delta > 0 and cpu_delta >= 0:
                    num_cpus = len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', []))
                    if num_cpus == 0:
                        num_cpus = 1
                    cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0
            
            # Memory usage
            memory_stats = stats.get('memory_stats', {})
            memory_usage = memory_stats.get('usage', 0)
            memory_limit = memory_stats.get('limit', 0)
            memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
            
            # Network usage
            networks = stats.get('networks', {})
            network_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
            network_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
            
            # Process and file descriptor counts (approximation)
            processes = 1  # Docker doesn't provide this directly
            open_files = 0  # Docker doesn't provide this directly
            
            return ResourceUsage(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_bytes=memory_usage,
                memory_percent=memory_percent,
                disk_bytes=0,  # Docker doesn't provide this directly
                network_rx_bytes=network_rx,
                network_tx_bytes=network_tx,
                processes=processes,
                open_files=open_files
            )
            
        except Exception as e:
            logger.warning(f"Failed to collect resource usage: {e}")
            return None
    
    def _check_thresholds(self, usage: ResourceUsage) -> None:
        """Check if usage exceeds thresholds and generate alerts."""
        alerts = []
        
        # CPU alerts
        if usage.cpu_percent > self.thresholds['cpu_critical']:
            alerts.append(ResourceAlert(
                container_id=self.container_id,
                resource_type='cpu',
                current_value=usage.cpu_percent,
                threshold=self.thresholds['cpu_critical'],
                timestamp=usage.timestamp,
                severity='critical',
                message=f"CPU usage {usage.cpu_percent:.1f}% exceeds critical threshold"
            ))
        elif usage.cpu_percent > self.thresholds['cpu_warning']:
            alerts.append(ResourceAlert(
                container_id=self.container_id,
                resource_type='cpu',
                current_value=usage.cpu_percent,
                threshold=self.thresholds['cpu_warning'],
                timestamp=usage.timestamp,
                severity='warning',
                message=f"CPU usage {usage.cpu_percent:.1f}% exceeds warning threshold"
            ))
        
        # Memory alerts
        if usage.memory_percent > self.thresholds['memory_critical']:
            alerts.append(ResourceAlert(
                container_id=self.container_id,
                resource_type='memory',
                current_value=usage.memory_percent,
                threshold=self.thresholds['memory_critical'],
                timestamp=usage.timestamp,
                severity='critical',
                message=f"Memory usage {usage.memory_percent:.1f}% exceeds critical threshold"
            ))
        elif usage.memory_percent > self.thresholds['memory_warning']:
            alerts.append(ResourceAlert(
                container_id=self.container_id,
                resource_type='memory',
                current_value=usage.memory_percent,
                threshold=self.thresholds['memory_warning'],
                timestamp=usage.timestamp,
                severity='warning',
                message=f"Memory usage {usage.memory_percent:.1f}% exceeds warning threshold"
            ))
        
        # Store alerts and notify callback
        for alert in alerts:
            self.alerts.append(alert)
            if self.alert_callback:
                try:
                    self.alert_callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
    
    def get_current_usage(self) -> Optional[ResourceUsage]:
        """Get current resource usage snapshot."""
        return self._collect_usage()
    
    def get_usage_history(self, duration: Optional[timedelta] = None) -> List[ResourceUsage]:
        """Get resource usage history."""
        if not duration:
            return self.usage_history.copy()
        
        cutoff = datetime.now() - duration
        return [u for u in self.usage_history if u.timestamp >= cutoff]
    
    def get_alerts(self, severity: Optional[str] = None) -> List[ResourceAlert]:
        """Get resource alerts, optionally filtered by severity."""
        if not severity:
            return self.alerts.copy()
        
        return [a for a in self.alerts if a.severity == severity]


class ResourceManager:
    """
    Manages resource monitoring and enforcement for container execution.
    
    Provides system-wide resource monitoring, enforcement of limits,
    and alerting for resource usage violations.
    """
    
    def __init__(self):
        """Initialize resource manager."""
        self.monitors: Dict[str, ResourceMonitor] = {}
        self.global_alerts: List[ResourceAlert] = []
        self.alert_handlers: List[Callable[[ResourceAlert], None]] = []
        
        # System resource limits
        self.system_limits = {
            'max_containers': 10,
            'max_total_memory_percent': 80.0,
            'max_total_cpu_percent': 80.0
        }
        
        # Track system resources
        self.system_monitor = self._start_system_monitoring()
    
    def register_container(self, container_id: str, container) -> ResourceMonitor:
        """
        Register a container for resource monitoring.
        
        Args:
            container_id: Unique container identifier
            container: Docker container object
            
        Returns:
            ResourceMonitor instance for the container
        """
        if container_id in self.monitors:
            logger.warning(f"Container {container_id[:8]} already registered for monitoring")
            return self.monitors[container_id]
        
        monitor = ResourceMonitor(
            container_id=container_id,
            container=container,
            alert_callback=self._handle_container_alert
        )
        
        self.monitors[container_id] = monitor
        monitor.start_monitoring()
        
        logger.info(f"Registered container {container_id[:8]} for resource monitoring")
        return monitor
    
    def unregister_container(self, container_id: str) -> None:
        """
        Unregister a container from resource monitoring.
        
        Args:
            container_id: Container identifier to unregister
        """
        if container_id in self.monitors:
            monitor = self.monitors[container_id]
            monitor.stop_monitoring()
            del self.monitors[container_id]
            logger.info(f"Unregistered container {container_id[:8]} from monitoring")
    
    def _handle_container_alert(self, alert: ResourceAlert) -> None:
        """Handle resource alert from container monitor."""
        self.global_alerts.append(alert)
        
        # Keep global alerts manageable
        if len(self.global_alerts) > 10000:
            self.global_alerts = self.global_alerts[-10000:]
        
        # Notify registered handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        # Log critical alerts
        if alert.severity == 'critical':
            logger.critical(f"Resource alert: {alert.message}")
        else:
            logger.warning(f"Resource alert: {alert.message}")
    
    def add_alert_handler(self, handler: Callable[[ResourceAlert], None]) -> None:
        """Add a handler for resource alerts."""
        self.alert_handlers.append(handler)
    
    def remove_alert_handler(self, handler: Callable[[ResourceAlert], None]) -> None:
        """Remove an alert handler."""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)
    
    def get_system_usage(self) -> Dict[str, Any]:
        """Get current system resource usage."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                'active_containers': len(self.monitors),
                'max_containers': self.system_limits['max_containers']
            }
        except Exception as e:
            logger.error(f"Failed to get system usage: {e}")
            return {}
    
    def check_system_capacity(self) -> bool:
        """
        Check if system can handle additional containers.
        
        Returns:
            True if system has capacity for more containers
        """
        try:
            # Check container count limit
            if len(self.monitors) >= self.system_limits['max_containers']:
                logger.warning("Maximum container count reached")
                return False
            
            # Check system resource usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > self.system_limits['max_total_cpu_percent']:
                logger.warning(f"System CPU usage {cpu_percent:.1f}% exceeds limit")
                return False
            
            if memory_percent > self.system_limits['max_total_memory_percent']:
                logger.warning(f"System memory usage {memory_percent:.1f}% exceeds limit")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking system capacity: {e}")
            return False
    
    def get_container_usage(self, container_id: str) -> Optional[ResourceUsage]:
        """Get current usage for specific container."""
        monitor = self.monitors.get(container_id)
        if monitor:
            return monitor.get_current_usage()
        return None
    
    def get_all_container_usage(self) -> Dict[str, ResourceUsage]:
        """Get current usage for all monitored containers."""
        usage = {}
        for container_id, monitor in self.monitors.items():
            current = monitor.get_current_usage()
            if current:
                usage[container_id] = current
        return usage
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of resource usage across all containers."""
        if not self.monitors:
            return {'total_containers': 0}
        
        total_cpu = 0.0
        total_memory = 0
        total_network_rx = 0
        total_network_tx = 0
        
        for monitor in self.monitors.values():
            usage = monitor.get_current_usage()
            if usage:
                total_cpu += usage.cpu_percent
                total_memory += usage.memory_bytes
                total_network_rx += usage.network_rx_bytes
                total_network_tx += usage.network_tx_bytes
        
        return {
            'total_containers': len(self.monitors),
            'total_cpu_percent': total_cpu,
            'total_memory_bytes': total_memory,
            'total_memory_mb': total_memory / (1024 * 1024),
            'total_network_rx_bytes': total_network_rx,
            'total_network_tx_bytes': total_network_tx,
            'system_usage': self.get_system_usage()
        }
    
    def get_alerts(self, container_id: Optional[str] = None, 
                   severity: Optional[str] = None,
                   since: Optional[datetime] = None) -> List[ResourceAlert]:
        """Get resource alerts with optional filtering."""
        alerts = []
        
        if container_id:
            # Get alerts for specific container
            monitor = self.monitors.get(container_id)
            if monitor:
                alerts = monitor.get_alerts(severity)
        else:
            # Get global alerts
            alerts = self.global_alerts.copy()
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
        
        # Filter by time if specified
        if since:
            alerts = [a for a in alerts if a.timestamp >= since]
        
        return alerts
    
    def _start_system_monitoring(self) -> threading.Thread:
        """Start system-level resource monitoring."""
        def monitor_system():
            while True:
                try:
                    # Check system resource usage periodically
                    usage = self.get_system_usage()
                    
                    # Generate system-level alerts if needed
                    if usage.get('cpu_percent', 0) > 90:
                        alert = ResourceAlert(
                            container_id='system',
                            resource_type='cpu',
                            current_value=usage['cpu_percent'],
                            threshold=90.0,
                            timestamp=datetime.now(),
                            severity='critical',
                            message=f"System CPU usage {usage['cpu_percent']:.1f}% is critical"
                        )
                        self._handle_container_alert(alert)
                    
                    if usage.get('memory_percent', 0) > 90:
                        alert = ResourceAlert(
                            container_id='system',
                            resource_type='memory',
                            current_value=usage['memory_percent'],
                            threshold=90.0,
                            timestamp=datetime.now(),
                            severity='critical',
                            message=f"System memory usage {usage['memory_percent']:.1f}% is critical"
                        )
                        self._handle_container_alert(alert)
                    
                except Exception as e:
                    logger.error(f"Error in system monitoring: {e}")
                
                time.sleep(30)  # Check every 30 seconds
        
        thread = threading.Thread(target=monitor_system, daemon=True)
        thread.start()
        return thread
    
    def cleanup(self) -> None:
        """Clean up all resource monitors."""
        container_ids = list(self.monitors.keys())
        for container_id in container_ids:
            self.unregister_container(container_id)
        
        logger.info("Resource manager cleanup completed")