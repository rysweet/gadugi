#!/usr/bin/env python3
"""
Gadugi Agent Engine for Gadugi v0.3

This engine implements comprehensive system bootstrap, installation, configuration
management, and system health monitoring for the Gadugi multi-agent platform.
"""

import json
import logging
import os
import sys
import subprocess
import shutil
import tarfile
import yaml
import psutil
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor


class OperationType(Enum):
    """Types of operations supported by Gadugi agent."""
    INSTALL = "install"
    CONFIGURE = "configure"
    START = "start"
    STOP = "stop"
    STATUS = "status"
    UPDATE = "update"
    BACKUP = "backup"
    RESTORE = "restore"
    HEALTH = "health"
    OPTIMIZE = "optimize"


class TargetType(Enum):
    """Types of targets for operations."""
    SYSTEM = "system"
    AGENT = "agent"
    SERVICE = "service"
    ALL = "all"


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class ServiceStatus(Enum):
    """Service status types."""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    UNKNOWN = "unknown"


class HealthStatus(Enum):
    """Health status types."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SystemStatus:
    """System status information."""
    system_status: HealthStatus
    services_running: List[str]
    services_stopped: List[str]
    agents_active: int
    memory_usage: str
    cpu_usage: str
    disk_usage: str
    uptime: str


@dataclass
class ServiceInfo:
    """Service information."""
    name: str
    status: ServiceStatus
    port: Optional[int]
    pid: Optional[int]
    uptime: Optional[str]
    memory_usage: Optional[str]
    cpu_usage: Optional[str]


@dataclass
class AgentInfo:
    """Agent information."""
    name: str
    version: str
    status: str
    capabilities: List[str]
    resource_usage: Dict[str, str]
    last_heartbeat: str


@dataclass
class Recommendation:
    """System recommendation."""
    priority: str
    category: str
    message: str
    action: str


@dataclass
class BackupInfo:
    """Backup information."""
    filename: str
    size: str
    created_at: str
    backup_type: str
    compressed: bool


@dataclass
class OperationResult:
    """Result of a Gadugi operation."""
    success: bool
    operation: str
    status: Optional[SystemStatus]
    results: Dict[str, Any]
    recommendations: List[Recommendation]
    warnings: List[str]
    errors: List[str]


class GadugiEngine:
    """Main Gadugi agent engine for system management and bootstrap operations."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the Gadugi engine."""
        self.logger = self._setup_logging()
        
        # System paths
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.base_dir / "config"
        self.data_dir = self.base_dir / "data"
        self.log_dir = self.base_dir / "logs"
        self.backup_dir = self.base_dir / "backups"
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # System state
        self.services = {}
        self.agents = {}
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Database for persistent state
        self.db_path = self.data_dir / "gadugi.db"
        self._init_database()
        
        # Core services configuration
        self.core_services = {
            "event-router": {
                "port": 8080,
                "executable": "python",
                "args": ["src/services/event_router.py"],
                "health_check": "/health",
                "dependencies": []
            },
            "neo4j-graph": {
                "port": 7687,
                "executable": "neo4j",
                "args": ["console"],
                "health_check": "/db/data/graph.db",
                "dependencies": ["java"]
            },
            "mcp-service": {
                "port": 8082,
                "executable": "python",
                "args": ["src/services/mcp_service.py"],
                "health_check": "/mcp/status",
                "dependencies": ["neo4j-graph"]
            },
            "llm-proxy": {
                "port": 8081,
                "executable": "python",
                "args": ["src/services/llm_proxy.py"],
                "health_check": "/proxy/health",
                "dependencies": []
            },
            "gadugi-cli": {
                "port": 8083,
                "executable": "python",
                "args": ["src/services/gadugi_cli.py"],
                "health_check": "/cli/status",
                "dependencies": ["event-router"]
            }
        }
        
        # Available agents
        self.available_agents = {
            "orchestrator": {
                "version": "0.3.0",
                "capabilities": ["parallel_execution", "task_coordination"],
                "memory_limit": "512MB",
                "executable": "python",
                "args": ["src/orchestrator/run_agent.py", "orchestrator"]
            },
            "architect": {
                "version": "0.3.0",
                "capabilities": ["system_design", "architecture_planning"],
                "memory_limit": "256MB",
                "executable": "python",
                "args": ["src/orchestrator/architect_engine.py"]
            },
            "task-decomposer": {
                "version": "0.3.0",
                "capabilities": ["task_analysis", "decomposition"],
                "memory_limit": "128MB",
                "executable": "python",
                "args": ["src/orchestrator/simple_decomposer.py"]
            },
            "workflow-manager": {
                "version": "0.3.0",
                "capabilities": ["workflow_management", "phase_coordination"],
                "memory_limit": "256MB",
                "executable": "python",
                "args": ["src/orchestrator/workflow_manager_engine.py"]
            },
            "code-writer": {
                "version": "0.3.0",
                "capabilities": ["code_generation", "implementation"],
                "memory_limit": "256MB",
                "executable": "python",
                "args": ["src/orchestrator/code_writer_engine.py"]
            },
            "code-reviewer": {
                "version": "0.3.0",
                "capabilities": ["code_review", "quality_analysis"],
                "memory_limit": "128MB",
                "executable": "python",
                "args": ["src/orchestrator/code_reviewer_engine.py"]
            },
            "memory-manager": {
                "version": "0.3.0",
                "capabilities": ["memory_management", "state_tracking"],
                "memory_limit": "128MB",
                "executable": "python",
                "args": ["src/orchestrator/memory_manager_engine.py"]
            },
            "team-coach": {
                "version": "0.3.0",
                "capabilities": ["team_coordination", "performance_optimization"],
                "memory_limit": "256MB",
                "executable": "python",
                "args": ["src/orchestrator/team_coach_engine.py"]
            },
            "prompt-writer": {
                "version": "0.3.0",
                "capabilities": ["prompt_generation", "template_management"],
                "memory_limit": "128MB",
                "executable": "python",
                "args": ["src/orchestrator/prompt_writer_engine.py"]
            },
            "worktree-manager": {
                "version": "0.3.0",
                "capabilities": ["git_management", "worktree_isolation"],
                "memory_limit": "128MB",
                "executable": "python",
                "args": ["src/orchestrator/worktree_manager_engine.py"]
            }
        }

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the Gadugi engine."""
        logger = logging.getLogger("gadugi_engine")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.config_dir,
            self.data_dir,
            self.log_dir,
            self.backup_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load system configuration."""
        default_config = {
            "gadugi": {
                "version": "0.3.0",
                "environment": "development",
                "log_level": "info",
                "max_agents": 50,
                "max_memory": "8GB",
                "data_directory": str(self.data_dir),
                "log_directory": str(self.log_dir)
            },
            "services": {
                "event-router": {"enabled": True, "auto_start": True},
                "neo4j-graph": {"enabled": True, "auto_start": True},
                "mcp-service": {"enabled": True, "auto_start": True},
                "llm-proxy": {"enabled": True, "auto_start": True},
                "gadugi-cli": {"enabled": True, "auto_start": True}
            },
            "agents": {
                "orchestrator": {"enabled": True, "max_instances": 3},
                "architect": {"enabled": True, "max_instances": 2},
                "workflow-manager": {"enabled": True, "max_instances": 5}
            },
            "monitoring": {
                "enabled": True,
                "interval": 30,
                "cpu_threshold": 80,
                "memory_threshold": 85,
                "disk_threshold": 90
            },
            "backup": {
                "enabled": True,
                "interval": "24h",
                "retention_days": 30,
                "compression": True
            }
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Merge with default config
                    default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config file {config_file}: {e}")
        
        return default_config

    def _init_database(self):
        """Initialize SQLite database for persistent state."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Services table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    name TEXT PRIMARY KEY,
                    status TEXT,
                    pid INTEGER,
                    port INTEGER,
                    started_at TEXT,
                    config TEXT
                )
            ''')
            
            # Agents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    name TEXT PRIMARY KEY,
                    version TEXT,
                    status TEXT,
                    pid INTEGER,
                    started_at TEXT,
                    last_heartbeat TEXT,
                    config TEXT
                )
            ''')
            
            # System events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_type TEXT,
                    component TEXT,
                    message TEXT,
                    details TEXT
                )
            ''')
            
            # Backups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    backup_type TEXT,
                    size INTEGER,
                    created_at TEXT,
                    checksum TEXT,
                    metadata TEXT
                )
            ''')
            
            conn.commit()

    def execute_operation(self, request: Dict[str, Any]) -> OperationResult:
        """Execute a Gadugi operation based on the request."""
        try:
            operation = OperationType(request.get("command", "status"))
            target = TargetType(request.get("target", "system"))
            parameters = request.get("parameters", {})
            options = request.get("options", {})
            
            self.logger.info(f"Executing operation: {operation.value} on {target.value}")
            
            # Route to appropriate handler
            if operation == OperationType.INSTALL:
                return self._handle_install(target, parameters, options)
            elif operation == OperationType.CONFIGURE:
                return self._handle_configure(target, parameters, options)
            elif operation == OperationType.START:
                return self._handle_start(target, parameters, options)
            elif operation == OperationType.STOP:
                return self._handle_stop(target, parameters, options)
            elif operation == OperationType.STATUS:
                return self._handle_status(target, parameters, options)
            elif operation == OperationType.UPDATE:
                return self._handle_update(target, parameters, options)
            elif operation == OperationType.BACKUP:
                return self._handle_backup(target, parameters, options)
            elif operation == OperationType.RESTORE:
                return self._handle_restore(target, parameters, options)
            elif operation == OperationType.HEALTH:
                return self._handle_health(target, parameters, options)
            elif operation == OperationType.OPTIMIZE:
                return self._handle_optimize(target, parameters, options)
            else:
                return OperationResult(
                    success=False,
                    operation=operation.value,
                    status=None,
                    results={},
                    recommendations=[],
                    warnings=[],
                    errors=[f"Unsupported operation: {operation.value}"]
                )
                
        except Exception as e:
            self.logger.error(f"Error executing operation: {e}")
            return OperationResult(
                success=False,
                operation=request.get("command", "unknown"),
                status=None,
                results={},
                recommendations=[],
                warnings=[],
                errors=[str(e)]
            )

    def _handle_install(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle install operations."""
        results = {}
        warnings = []
        errors = []
        recommendations = []
        
        if target == TargetType.SYSTEM:
            # Fresh system installation
            results = self._install_system(parameters, options)
        elif target == TargetType.SERVICE:
            # Install specific service
            service_name = parameters.get("component")
            if service_name in self.core_services:
                results = self._install_service(service_name, parameters, options)
            else:
                errors.append(f"Unknown service: {service_name}")
        elif target == TargetType.AGENT:
            # Install specific agent
            agent_name = parameters.get("component")
            if agent_name in self.available_agents:
                results = self._install_agent(agent_name, parameters, options)
            else:
                errors.append(f"Unknown agent: {agent_name}")
        elif target == TargetType.ALL:
            # Install everything
            results = self._install_all(parameters, options)
        
        # Generate recommendations
        if not errors:
            recommendations.append(Recommendation(
                priority="medium",
                category="maintenance",
                message="Consider running health check after installation",
                action="gadugi health --detailed"
            ))
        
        return OperationResult(
            success=len(errors) == 0,
            operation="install",
            status=self._get_system_status(),
            results=results,
            recommendations=recommendations,
            warnings=warnings,
            errors=errors
        )

    def _handle_configure(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle configuration operations."""
        results = {}
        warnings = []
        errors = []
        recommendations = []
        
        if target == TargetType.SYSTEM:
            results = self._configure_system(parameters, options)
        elif target == TargetType.SERVICE:
            service_name = parameters.get("component")
            results = self._configure_service(service_name, parameters, options)
        elif target == TargetType.AGENT:
            agent_name = parameters.get("component")
            results = self._configure_agent(agent_name, parameters, options)
        
        return OperationResult(
            success=len(errors) == 0,
            operation="configure",
            status=self._get_system_status(),
            results=results,
            recommendations=recommendations,
            warnings=warnings,
            errors=errors
        )

    def _handle_start(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle start operations."""
        results = {}
        warnings = []
        errors = []
        recommendations = []
        
        try:
            if target == TargetType.ALL:
                # Start all services and agents
                results["started_services"] = self._start_all_services()
                results["started_agents"] = self._start_enabled_agents()
            elif target == TargetType.SERVICE:
                service_name = parameters.get("component", "all")
                if service_name == "all":
                    results["started_services"] = self._start_all_services()
                else:
                    if self._start_service(service_name):
                        results["started_services"] = [service_name]
                    else:
                        errors.append(f"Failed to start service: {service_name}")
            elif target == TargetType.AGENT:
                agent_name = parameters.get("component", "all")
                if agent_name == "all":
                    results["started_agents"] = self._start_enabled_agents()
                else:
                    if self._start_agent(agent_name):
                        results["started_agents"] = [agent_name]
                    else:
                        errors.append(f"Failed to start agent: {agent_name}")
            
            # Start monitoring if not already running
            if not self.is_monitoring:
                self._start_monitoring()
                
        except Exception as e:
            errors.append(f"Error starting components: {str(e)}")
        
        return OperationResult(
            success=len(errors) == 0,
            operation="start",
            status=self._get_system_status(),
            results=results,
            recommendations=recommendations,
            warnings=warnings,
            errors=errors
        )

    def _handle_stop(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle stop operations."""
        results = {}
        warnings = []
        errors = []
        
        try:
            if target == TargetType.ALL:
                results["stopped_services"] = self._stop_all_services()
                results["stopped_agents"] = self._stop_all_agents()
            elif target == TargetType.SERVICE:
                service_name = parameters.get("component", "all")
                if service_name == "all":
                    results["stopped_services"] = self._stop_all_services()
                else:
                    if self._stop_service(service_name):
                        results["stopped_services"] = [service_name]
                    else:
                        errors.append(f"Failed to stop service: {service_name}")
            elif target == TargetType.AGENT:
                agent_name = parameters.get("component", "all")
                if agent_name == "all":
                    results["stopped_agents"] = self._stop_all_agents()
                else:
                    if self._stop_agent(agent_name):
                        results["stopped_agents"] = [agent_name]
                    else:
                        errors.append(f"Failed to stop agent: {agent_name}")
                        
        except Exception as e:
            errors.append(f"Error stopping components: {str(e)}")
        
        return OperationResult(
            success=len(errors) == 0,
            operation="stop",
            status=self._get_system_status(),
            results=results,
            recommendations=[],
            warnings=warnings,
            errors=errors
        )

    def _handle_status(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle status operations."""
        results = {}
        
        if target == TargetType.SYSTEM or target == TargetType.ALL:
            results["system_info"] = self._get_system_info()
            results["resource_usage"] = self._get_resource_usage()
        
        if target == TargetType.SERVICE or target == TargetType.ALL:
            results["services"] = self._get_services_status()
        
        if target == TargetType.AGENT or target == TargetType.ALL:
            results["agents"] = self._get_agents_status()
        
        return OperationResult(
            success=True,
            operation="status",
            status=self._get_system_status(),
            results=results,
            recommendations=[],
            warnings=[],
            errors=[]
        )

    def _handle_health(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle health check operations."""
        results = {}
        warnings = []
        errors = []
        recommendations = []
        
        # Perform comprehensive health check
        health_data = self._perform_health_check()
        results.update(health_data)
        
        # Generate recommendations based on health status
        if health_data.get("overall_status") == "degraded":
            recommendations.append(Recommendation(
                priority="medium",
                category="performance",
                message="System is in degraded state",
                action="Check resource usage and service logs"
            ))
        elif health_data.get("overall_status") == "critical":
            recommendations.append(Recommendation(
                priority="high",
                category="security",
                message="System is in critical state",
                action="Immediate attention required - check logs and restart services"
            ))
        
        # Check resource thresholds
        resource_usage = self._get_resource_usage()
        if resource_usage.get("cpu_percent", 0) > 80:
            warnings.append("High CPU usage detected")
            recommendations.append(Recommendation(
                priority="medium",
                category="performance",
                message="High CPU usage detected",
                action="Consider optimizing or scaling system"
            ))
        
        if resource_usage.get("memory_percent", 0) > 85:
            warnings.append("High memory usage detected")
            recommendations.append(Recommendation(
                priority="high",
                category="performance",
                message="High memory usage detected",
                action="Free up memory or add more RAM"
            ))
        
        return OperationResult(
            success=True,
            operation="health",
            status=self._get_system_status(),
            results=results,
            recommendations=recommendations,
            warnings=warnings,
            errors=errors
        )

    def _handle_backup(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle backup operations."""
        results = {}
        errors = []
        warnings = []
        
        try:
            backup_type = parameters.get("backup_type", "full")
            compress = parameters.get("compress", True)
            include_data = parameters.get("include_data", True)
            
            backup_file = self._create_backup(backup_type, compress, include_data)
            
            if backup_file:
                results["backup_created"] = backup_file
                results["backup_size"] = self._get_file_size(backup_file)
                results["backup_location"] = str(self.backup_dir / backup_file)
            else:
                errors.append("Failed to create backup")
                
        except Exception as e:
            errors.append(f"Error creating backup: {str(e)}")
        
        return OperationResult(
            success=len(errors) == 0,
            operation="backup",
            status=self._get_system_status(),
            results=results,
            recommendations=[],
            warnings=warnings,
            errors=errors
        )

    def _handle_restore(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle restore operations."""
        results = {}
        errors = []
        warnings = []
        
        try:
            backup_file = parameters.get("backup_file")
            if not backup_file:
                errors.append("Backup file not specified")
                return OperationResult(
                    success=False,
                    operation="restore",
                    status=None,
                    results={},
                    recommendations=[],
                    warnings=warnings,
                    errors=errors
                )
            
            success = self._restore_backup(backup_file)
            if success:
                results["restored_from"] = backup_file
                results["restoration_time"] = datetime.now().isoformat()
            else:
                errors.append(f"Failed to restore from backup: {backup_file}")
                
        except Exception as e:
            errors.append(f"Error restoring backup: {str(e)}")
        
        return OperationResult(
            success=len(errors) == 0,
            operation="restore",
            status=self._get_system_status(),
            results=results,
            recommendations=[],
            warnings=warnings,
            errors=errors
        )

    def _handle_update(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle update operations."""
        results = {}
        warnings = []
        errors = []
        
        # Placeholder for update implementation
        warnings.append("Update functionality not yet implemented")
        
        return OperationResult(
            success=True,
            operation="update",
            status=self._get_system_status(),
            results=results,
            recommendations=[],
            warnings=warnings,
            errors=errors
        )

    def _handle_optimize(self, target: TargetType, parameters: Dict, options: Dict) -> OperationResult:
        """Handle optimization operations."""
        results = {}
        warnings = []
        errors = []
        recommendations = []
        
        try:
            # Perform system optimization
            optimization_results = self._optimize_system()
            results.update(optimization_results)
            
            recommendations.append(Recommendation(
                priority="low",
                category="performance",
                message="System optimization completed",
                action="Monitor performance metrics for improvements"
            ))
            
        except Exception as e:
            errors.append(f"Error during optimization: {str(e)}")
        
        return OperationResult(
            success=len(errors) == 0,
            operation="optimize",
            status=self._get_system_status(),
            results=results,
            recommendations=recommendations,
            warnings=warnings,
            errors=errors
        )

    def _install_system(self, parameters: Dict, options: Dict) -> Dict[str, Any]:
        """Install the complete Gadugi system."""
        results = {
            "installed_components": [],
            "configured_services": [],
            "installation_time": datetime.now().isoformat()
        }
        
        # Install dependencies
        self._install_dependencies()
        results["installed_components"].append("dependencies")
        
        # Create configuration files
        self._create_default_configs()
        results["configured_services"].extend(list(self.core_services.keys()))
        
        # Initialize database
        self._init_database()
        results["installed_components"].append("database")
        
        return results

    def _install_service(self, service_name: str, parameters: Dict, options: Dict) -> Dict[str, Any]:
        """Install a specific service."""
        results = {"installed_service": service_name}
        
        # Service-specific installation logic would go here
        service_config = self.core_services.get(service_name, {})
        
        # Create service configuration
        config_file = self.config_dir / f"{service_name}.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(service_config, f)
        
        results["config_file"] = str(config_file)
        return results

    def _install_agent(self, agent_name: str, parameters: Dict, options: Dict) -> Dict[str, Any]:
        """Install a specific agent."""
        results = {"installed_agent": agent_name}
        
        # Agent-specific installation logic would go here
        agent_config = self.available_agents.get(agent_name, {})
        
        # Create agent configuration
        config_file = self.config_dir / f"agent_{agent_name}.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agent_config, f)
        
        results["config_file"] = str(config_file)
        return results

    def _install_all(self, parameters: Dict, options: Dict) -> Dict[str, Any]:
        """Install all system components."""
        results = {
            "installed_services": [],
            "installed_agents": [],
            "installation_time": datetime.now().isoformat()
        }
        
        # Install all services
        for service_name in self.core_services.keys():
            self._install_service(service_name, parameters, options)
            results["installed_services"].append(service_name)
        
        # Install enabled agents
        for agent_name, config in self.available_agents.items():
            if self.config.get("agents", {}).get(agent_name, {}).get("enabled", True):
                self._install_agent(agent_name, parameters, options)
                results["installed_agents"].append(agent_name)
        
        return results

    def _install_dependencies(self):
        """Install system dependencies."""
        # This would install required system packages
        # For now, just log that dependencies are being checked
        self.logger.info("Checking and installing system dependencies")

    def _create_default_configs(self):
        """Create default configuration files."""
        # Create main configuration file
        main_config = self.config_dir / "gadugi.yaml"
        with open(main_config, 'w') as f:
            yaml.dump(self.config, f)

    def _configure_system(self, parameters: Dict, options: Dict) -> Dict[str, Any]:
        """Configure the system."""
        results = {"configured_components": ["system"]}
        
        # Apply system configuration
        environment = parameters.get("environment", "development")
        if environment in [e.value for e in Environment]:
            self.config["gadugi"]["environment"] = environment
            results["environment"] = environment
        
        return results

    def _configure_service(self, service_name: str, parameters: Dict, options: Dict) -> Dict[str, Any]:
        """Configure a specific service."""
        results = {"configured_service": service_name}
        
        if service_name not in self.core_services:
            raise ValueError(f"Unknown service: {service_name}")
        
        # Apply service-specific configuration
        service_config = self.core_services[service_name].copy()
        service_config.update(parameters)
        
        # Save updated configuration
        config_file = self.config_dir / f"{service_name}.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(service_config, f)
        
        results["config_file"] = str(config_file)
        return results

    def _configure_agent(self, agent_name: str, parameters: Dict, options: Dict) -> Dict[str, Any]:
        """Configure a specific agent."""
        results = {"configured_agent": agent_name}
        
        if agent_name not in self.available_agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # Apply agent-specific configuration
        agent_config = self.available_agents[agent_name].copy()
        agent_config.update(parameters)
        
        # Save updated configuration
        config_file = self.config_dir / f"agent_{agent_name}.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agent_config, f)
        
        results["config_file"] = str(config_file)
        return results

    def _start_service(self, service_name: str) -> bool:
        """Start a specific service."""
        if service_name not in self.core_services:
            return False
        
        try:
            service_config = self.core_services[service_name]
            
            # Check if service is already running
            if self._is_service_running(service_name):
                self.logger.info(f"Service {service_name} is already running")
                return True
            
            # Start the service
            cmd = [service_config["executable"]] + service_config["args"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.base_dir)
            )
            
            # Store process information
            self.services[service_name] = {
                "process": process,
                "pid": process.pid,
                "status": ServiceStatus.STARTING,
                "started_at": datetime.now()
            }
            
            # Update database
            self._update_service_in_db(service_name, ServiceStatus.STARTING, process.pid)
            
            # Give service time to start
            time.sleep(2)
            
            # Check if service started successfully
            if process.poll() is None:
                self.services[service_name]["status"] = ServiceStatus.RUNNING
                self._update_service_in_db(service_name, ServiceStatus.RUNNING, process.pid)
                self.logger.info(f"Service {service_name} started successfully")
                return True
            else:
                self.logger.error(f"Service {service_name} failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting service {service_name}: {e}")
            return False

    def _stop_service(self, service_name: str) -> bool:
        """Stop a specific service."""
        try:
            if service_name not in self.services:
                self.logger.info(f"Service {service_name} is not running")
                return True
            
            service_info = self.services[service_name]
            process = service_info.get("process")
            
            if process and process.poll() is None:
                # Graceful shutdown
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    process.kill()
                    process.wait()
                
                self.logger.info(f"Service {service_name} stopped")
            
            # Update status
            self.services[service_name]["status"] = ServiceStatus.STOPPED
            self._update_service_in_db(service_name, ServiceStatus.STOPPED, None)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping service {service_name}: {e}")
            return False

    def _start_agent(self, agent_name: str) -> bool:
        """Start a specific agent."""
        if agent_name not in self.available_agents:
            return False
        
        try:
            agent_config = self.available_agents[agent_name]
            
            # Check if agent is already running
            if self._is_agent_running(agent_name):
                self.logger.info(f"Agent {agent_name} is already running")
                return True
            
            # Start the agent
            cmd = [agent_config["executable"]] + agent_config["args"]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.base_dir)
            )
            
            # Store process information
            self.agents[agent_name] = {
                "process": process,
                "pid": process.pid,
                "status": "starting",
                "started_at": datetime.now()
            }
            
            # Update database
            self._update_agent_in_db(agent_name, "starting", process.pid)
            
            # Give agent time to start
            time.sleep(1)
            
            # Check if agent started successfully
            if process.poll() is None:
                self.agents[agent_name]["status"] = "active"
                self._update_agent_in_db(agent_name, "active", process.pid)
                self.logger.info(f"Agent {agent_name} started successfully")
                return True
            else:
                self.logger.error(f"Agent {agent_name} failed to start")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting agent {agent_name}: {e}")
            return False

    def _stop_agent(self, agent_name: str) -> bool:
        """Stop a specific agent."""
        try:
            if agent_name not in self.agents:
                self.logger.info(f"Agent {agent_name} is not running")
                return True
            
            agent_info = self.agents[agent_name]
            process = agent_info.get("process")
            
            if process and process.poll() is None:
                # Graceful shutdown
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if graceful shutdown failed
                    process.kill()
                    process.wait()
                
                self.logger.info(f"Agent {agent_name} stopped")
            
            # Update status
            self.agents[agent_name]["status"] = "stopped"
            self._update_agent_in_db(agent_name, "stopped", None)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping agent {agent_name}: {e}")
            return False

    def _start_all_services(self) -> List[str]:
        """Start all enabled services."""
        started = []
        
        for service_name in self.core_services.keys():
            if self.config.get("services", {}).get(service_name, {}).get("enabled", True):
                if self._start_service(service_name):
                    started.append(service_name)
        
        return started

    def _stop_all_services(self) -> List[str]:
        """Stop all running services."""
        stopped = []
        
        for service_name in list(self.services.keys()):
            if self._stop_service(service_name):
                stopped.append(service_name)
        
        return stopped

    def _start_enabled_agents(self) -> List[str]:
        """Start all enabled agents."""
        started = []
        
        for agent_name in self.available_agents.keys():
            if self.config.get("agents", {}).get(agent_name, {}).get("enabled", True):
                if self._start_agent(agent_name):
                    started.append(agent_name)
        
        return started

    def _stop_all_agents(self) -> List[str]:
        """Stop all running agents."""
        stopped = []
        
        for agent_name in list(self.agents.keys()):
            if self._stop_agent(agent_name):
                stopped.append(agent_name)
        
        return stopped

    def _is_service_running(self, service_name: str) -> bool:
        """Check if a service is running."""
        if service_name not in self.services:
            return False
        
        process = self.services[service_name].get("process")
        return process and process.poll() is None

    def _is_agent_running(self, agent_name: str) -> bool:
        """Check if an agent is running."""
        if agent_name not in self.agents:
            return False
        
        process = self.agents[agent_name].get("process")
        return process and process.poll() is None

    def _get_system_status(self) -> SystemStatus:
        """Get current system status."""
        # Get service status
        services_running = []
        services_stopped = []
        
        for service_name in self.core_services.keys():
            if self._is_service_running(service_name):
                services_running.append(service_name)
            else:
                services_stopped.append(service_name)
        
        # Get agent count
        agents_active = len([name for name in self.agents.keys() if self._is_agent_running(name)])
        
        # Get resource usage
        resource_usage = self._get_resource_usage()
        
        # Determine overall system status
        system_status = HealthStatus.HEALTHY
        if len(services_stopped) > len(services_running):
            system_status = HealthStatus.CRITICAL
        elif len(services_stopped) > 0:
            system_status = HealthStatus.DEGRADED
        
        return SystemStatus(
            system_status=system_status,
            services_running=services_running,
            services_stopped=services_stopped,
            agents_active=agents_active,
            memory_usage=f"{resource_usage.get('memory_percent', 0):.1f}%",
            cpu_usage=f"{resource_usage.get('cpu_percent', 0):.1f}%",
            disk_usage=f"{resource_usage.get('disk_percent', 0):.1f}%",
            uptime=self._get_system_uptime()
        )

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            "gadugi_version": self.config.get("gadugi", {}).get("version", "0.3.0"),
            "python_version": sys.version,
            "platform": sys.platform,
            "hostname": os.uname().nodename if hasattr(os, 'uname') else "unknown",
            "pid": os.getpid(),
            "working_directory": str(self.base_dir),
            "config_directory": str(self.config_dir),
            "data_directory": str(self.data_dir),
            "log_directory": str(self.log_dir)
        }

    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # Disk usage
            disk = psutil.disk_usage(str(self.base_dir))
            disk_percent = (disk.used / disk.total) * 100
            disk_used = disk.used
            disk_total = disk.total
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used": memory_used,
                "memory_total": memory_total,
                "memory_used_gb": memory_used / (1024**3),
                "memory_total_gb": memory_total / (1024**3),
                "disk_percent": disk_percent,
                "disk_used": disk_used,
                "disk_total": disk_total,
                "disk_used_gb": disk_used / (1024**3),
                "disk_total_gb": disk_total / (1024**3),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv
            }
            
        except Exception as e:
            self.logger.error(f"Error getting resource usage: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            }

    def _get_services_status(self) -> List[Dict[str, Any]]:
        """Get status of all services."""
        services_status = []
        
        for service_name, config in self.core_services.items():
            status = ServiceStatus.STOPPED
            pid = None
            uptime = None
            
            if self._is_service_running(service_name):
                status = ServiceStatus.RUNNING
                service_info = self.services.get(service_name, {})
                pid = service_info.get("pid")
                started_at = service_info.get("started_at")
                if started_at:
                    uptime = str(datetime.now() - started_at)
            
            services_status.append({
                "name": service_name,
                "status": status.value,
                "port": config.get("port"),
                "pid": pid,
                "uptime": uptime,
                "enabled": self.config.get("services", {}).get(service_name, {}).get("enabled", True),
                "auto_start": self.config.get("services", {}).get(service_name, {}).get("auto_start", False)
            })
        
        return services_status

    def _get_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents."""
        agents_status = []
        
        for agent_name, config in self.available_agents.items():
            status = "stopped"
            pid = None
            uptime = None
            
            if self._is_agent_running(agent_name):
                status = "active"
                agent_info = self.agents.get(agent_name, {})
                pid = agent_info.get("pid")
                started_at = agent_info.get("started_at")
                if started_at:
                    uptime = str(datetime.now() - started_at)
            
            agents_status.append({
                "name": agent_name,
                "version": config.get("version", "0.3.0"),
                "status": status,
                "capabilities": config.get("capabilities", []),
                "pid": pid,
                "uptime": uptime,
                "memory_limit": config.get("memory_limit", "128MB"),
                "enabled": self.config.get("agents", {}).get(agent_name, {}).get("enabled", True),
                "max_instances": self.config.get("agents", {}).get(agent_name, {}).get("max_instances", 1)
            })
        
        return agents_status

    def _get_system_uptime(self) -> str:
        """Get system uptime."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            return str(uptime).split('.')[0]  # Remove microseconds
        except Exception:
            return "unknown"

    def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": [],
            "agents": [],
            "resources": self._get_resource_usage(),
            "warnings": [],
            "errors": []
        }
        
        # Check services health
        unhealthy_services = 0
        for service_name in self.core_services.keys():
            service_health = {
                "name": service_name,
                "status": "healthy" if self._is_service_running(service_name) else "unhealthy",
                "response_time": "N/A"
            }
            
            if not self._is_service_running(service_name):
                unhealthy_services += 1
                health_data["errors"].append(f"Service {service_name} is not running")
            
            health_data["services"].append(service_health)
        
        # Check agents health
        inactive_agents = 0
        for agent_name in self.available_agents.keys():
            agent_health = {
                "name": agent_name,
                "status": "healthy" if self._is_agent_running(agent_name) else "unhealthy",
                "last_heartbeat": "N/A"
            }
            
            if not self._is_agent_running(agent_name):
                inactive_agents += 1
                health_data["warnings"].append(f"Agent {agent_name} is not active")
            
            health_data["agents"].append(agent_health)
        
        # Determine overall status
        if unhealthy_services > len(self.core_services) / 2:
            health_data["overall_status"] = "critical"
        elif unhealthy_services > 0 or inactive_agents > len(self.available_agents) / 2:
            health_data["overall_status"] = "degraded"
        
        # Check resource thresholds
        resources = health_data["resources"]
        if resources.get("cpu_percent", 0) > 90:
            health_data["overall_status"] = "critical"
            health_data["errors"].append("Critical CPU usage")
        elif resources.get("cpu_percent", 0) > 80:
            health_data["overall_status"] = "degraded"
            health_data["warnings"].append("High CPU usage")
        
        if resources.get("memory_percent", 0) > 95:
            health_data["overall_status"] = "critical"
            health_data["errors"].append("Critical memory usage")
        elif resources.get("memory_percent", 0) > 85:
            health_data["overall_status"] = "degraded"
            health_data["warnings"].append("High memory usage")
        
        return health_data

    def _create_backup(self, backup_type: str, compress: bool, include_data: bool) -> Optional[str]:
        """Create a system backup."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"gadugi_backup_{backup_type}_{timestamp}"
            
            if compress:
                backup_filename += ".tar.gz"
                backup_path = self.backup_dir / backup_filename
                
                with tarfile.open(backup_path, "w:gz") as tar:
                    # Add configuration files
                    if self.config_dir.exists():
                        tar.add(self.config_dir, arcname="config")
                    
                    # Add data files if requested
                    if include_data and self.data_dir.exists():
                        tar.add(self.data_dir, arcname="data")
                    
                    # Add logs
                    if self.log_dir.exists():
                        tar.add(self.log_dir, arcname="logs")
            else:
                backup_filename += ".tar"
                backup_path = self.backup_dir / backup_filename
                
                with tarfile.open(backup_path, "w") as tar:
                    if self.config_dir.exists():
                        tar.add(self.config_dir, arcname="config")
                    if include_data and self.data_dir.exists():
                        tar.add(self.data_dir, arcname="data")
                    if self.log_dir.exists():
                        tar.add(self.log_dir, arcname="logs")
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(backup_path)
            
            # Store backup info in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO backups (filename, backup_type, size, created_at, checksum, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    backup_filename,
                    backup_type,
                    backup_path.stat().st_size,
                    datetime.now().isoformat(),
                    checksum,
                    json.dumps({"compressed": compress, "include_data": include_data})
                ))
                conn.commit()
            
            self.logger.info(f"Backup created: {backup_filename}")
            return backup_filename
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None

    def _restore_backup(self, backup_filename: str) -> bool:
        """Restore from a backup."""
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_filename}")
                return False
            
            # Verify checksum
            stored_checksum = self._get_backup_checksum(backup_filename)
            current_checksum = self._calculate_file_checksum(backup_path)
            
            if stored_checksum and stored_checksum != current_checksum:
                self.logger.error(f"Backup checksum verification failed: {backup_filename}")
                return False
            
            # Stop all services before restore
            self._stop_all_services()
            self._stop_all_agents()
            
            # Extract backup
            with tarfile.open(backup_path, "r:*") as tar:
                tar.extractall(path=self.base_dir)
            
            # Reload configuration
            self.config = self._load_config(None)
            
            self.logger.info(f"Backup restored: {backup_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False

    def _optimize_system(self) -> Dict[str, Any]:
        """Optimize system performance."""
        results = {
            "optimizations_applied": [],
            "performance_improvements": {}
        }
        
        # Memory optimization
        try:
            # Force garbage collection
            import gc
            collected = gc.collect()
            results["optimizations_applied"].append(f"Memory cleanup: {collected} objects collected")
        except Exception as e:
            self.logger.warning(f"Memory optimization failed: {e}")
        
        # Database optimization
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                results["optimizations_applied"].append("Database optimized")
        except Exception as e:
            self.logger.warning(f"Database optimization failed: {e}")
        
        # Log file cleanup
        try:
            log_files_cleaned = self._cleanup_old_logs()
            results["optimizations_applied"].append(f"Log files cleaned: {log_files_cleaned}")
        except Exception as e:
            self.logger.warning(f"Log cleanup failed: {e}")
        
        return results

    def _cleanup_old_logs(self) -> int:
        """Clean up old log files."""
        cleaned = 0
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for log_file in self.log_dir.glob("*.log"):
            try:
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                    log_file.unlink()
                    cleaned += 1
            except Exception as e:
                self.logger.warning(f"Failed to clean log file {log_file}: {e}")
        
        return cleaned

    def _start_monitoring(self):
        """Start system monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitor_thread.start()
        self.logger.info("System monitoring started")

    def _stop_monitoring(self):
        """Stop system monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("System monitoring stopped")

    def _monitor_system(self):
        """Monitor system continuously."""
        interval = self.config.get("monitoring", {}).get("interval", 30)
        
        while self.is_monitoring:
            try:
                # Update service status
                for service_name in self.services.keys():
                    if not self._is_service_running(service_name):
                        self.services[service_name]["status"] = ServiceStatus.STOPPED
                        self._update_service_in_db(service_name, ServiceStatus.STOPPED, None)
                
                # Update agent status
                for agent_name in self.agents.keys():
                    if not self._is_agent_running(agent_name):
                        self.agents[agent_name]["status"] = "stopped"
                        self._update_agent_in_db(agent_name, "stopped", None)
                
                # Log system event
                self._log_system_event("monitoring", "system", "System monitoring check", {
                    "services_running": len([s for s in self.services.values() if s["status"] == ServiceStatus.RUNNING]),
                    "agents_active": len([a for a in self.agents.values() if a["status"] == "active"])
                })
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in system monitoring: {e}")
                time.sleep(interval)

    def _update_service_in_db(self, service_name: str, status: ServiceStatus, pid: Optional[int]):
        """Update service status in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO services (name, status, pid, port, started_at, config)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    service_name,
                    status.value,
                    pid,
                    self.core_services.get(service_name, {}).get("port"),
                    datetime.now().isoformat(),
                    json.dumps(self.core_services.get(service_name, {}))
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating service in database: {e}")

    def _update_agent_in_db(self, agent_name: str, status: str, pid: Optional[int]):
        """Update agent status in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO agents (name, version, status, pid, started_at, last_heartbeat, config)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent_name,
                    self.available_agents.get(agent_name, {}).get("version", "0.3.0"),
                    status,
                    pid,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps(self.available_agents.get(agent_name, {}))
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error updating agent in database: {e}")

    def _log_system_event(self, event_type: str, component: str, message: str, details: Dict[str, Any]):
        """Log a system event."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_events (timestamp, event_type, component, message, details)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    event_type,
                    component,
                    message,
                    json.dumps(details)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error logging system event: {e}")

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_backup_checksum(self, backup_filename: str) -> Optional[str]:
        """Get stored checksum for a backup."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT checksum FROM backups WHERE filename = ?', (backup_filename,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception:
            return None

    def _get_file_size(self, filename: str) -> str:
        """Get human-readable file size."""
        try:
            size = (self.backup_dir / filename).stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except Exception:
            return "unknown"

    def list_backups(self) -> List[BackupInfo]:
        """List available backups."""
        backups = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT filename, backup_type, size, created_at, metadata
                    FROM backups
                    ORDER BY created_at DESC
                ''')
                
                for row in cursor.fetchall():
                    filename, backup_type, size, created_at, metadata_json = row
                    metadata = json.loads(metadata_json) if metadata_json else {}
                    
                    backups.append(BackupInfo(
                        filename=filename,
                        size=self._format_size(size),
                        created_at=created_at,
                        backup_type=backup_type,
                        compressed=metadata.get("compressed", False)
                    ))
                    
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
        
        return backups

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes as human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def shutdown(self):
        """Shutdown the Gadugi system gracefully."""
        self.logger.info("Initiating Gadugi system shutdown")
        
        # Stop monitoring
        self._stop_monitoring()
        
        # Stop all agents
        self._stop_all_agents()
        
        # Stop all services
        self._stop_all_services()
        
        self.logger.info("Gadugi system shutdown completed")


def main():
    """Main function for testing the Gadugi engine."""
    gadugi = GadugiEngine()
    
    # Test system status
    status_request = {
        "command": "status",
        "target": "system",
        "parameters": {},
        "options": {}
    }
    
    result = gadugi.execute_operation(status_request)
    
    if result.success:
        print("Gadugi System Status:")
        print(f"System Status: {result.status.system_status.value}")
        print(f"Services Running: {len(result.status.services_running)}")
        print(f"Services Stopped: {len(result.status.services_stopped)}")
        print(f"Agents Active: {result.status.agents_active}")
        print(f"Memory Usage: {result.status.memory_usage}")
        print(f"CPU Usage: {result.status.cpu_usage}")
        print(f"Disk Usage: {result.status.disk_usage}")
    else:
        print(f"Error getting system status: {result.errors}")


if __name__ == "__main__":
    main()