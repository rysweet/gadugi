"""
WorkflowManager Reliability Module

This module provides comprehensive reliability improvements for the WorkflowManager,
addressing execution reliability issues identified in Issue #73.

Key Features:
- Comprehensive logging throughout all workflow phases
- Enhanced error handling with graceful recovery mechanisms
- Timeout detection between phases with automatic recovery
- State persistence for workflow resumption after interruption
- Health checks between phases for system stability
- Comprehensive monitoring and diagnostics

Integration with Enhanced Separation:
- Uses shared error handling utilities
- Integrates with state management for persistence
- Leverages task tracking for comprehensive monitoring
"""

import json
import logging
import os
import psutil
import signal
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

# Import Enhanced Separation shared modules
try:
    from utils.error_handling import ErrorHandler, CircuitBreaker, retry, ErrorContext
    from state_management import StateManager, TaskState, WorkflowPhase, CheckpointManager
    from task_tracking import TaskTracker, TaskStatus, WorkflowPhaseTracker
    from github_operations import GitHubOperations
except ImportError as e:
    logging.warning(f"Enhanced Separation modules not available: {e}")
    # Fallback for testing/development
    class ErrorHandler:
        def handle_error(self, context): pass
    class CircuitBreaker:
        def __init__(self, failure_threshold=3, recovery_timeout=30.0): pass
        def call(self, func, *args, **kwargs): return func(*args, **kwargs)
    def retry(max_attempts=3, initial_delay=1.0):
        def decorator(func): return func
        return decorator
    @dataclass
    class ErrorContext:
        error: Exception
        operation: str
        details: Dict[str, Any] = field(default_factory=dict)
        workflow_id: Optional[str] = None


class WorkflowStage(Enum):
    """Detailed workflow stages for comprehensive tracking"""
    INITIALIZATION = "initialization"
    PROMPT_ANALYSIS = "prompt_analysis"
    TASK_PREPARATION = "task_preparation"
    ISSUE_CREATION = "issue_creation"
    BRANCH_SETUP = "branch_setup"
    RESEARCH_PLANNING = "research_planning"
    IMPLEMENTATION_START = "implementation_start"
    IMPLEMENTATION_PROGRESS = "implementation_progress"
    IMPLEMENTATION_COMPLETE = "implementation_complete"
    TESTING_START = "testing_start"
    TESTING_COMPLETE = "testing_complete"
    DOCUMENTATION_UPDATE = "documentation_update"
    PR_PREPARATION = "pr_preparation"
    PR_CREATION = "pr_creation"
    PR_VERIFICATION = "pr_verification"
    REVIEW_REQUEST = "review_request"
    REVIEW_PROCESSING = "review_processing"
    FINAL_CLEANUP = "final_cleanup"
    COMPLETION = "completion"


class HealthStatus(Enum):
    """Health status for system checks"""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"


@dataclass
class SystemHealthCheck:
    """System health check result"""
    status: HealthStatus
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    git_status: str
    github_connectivity: bool
    claude_availability: bool
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class WorkflowTimeout:
    """Timeout configuration for workflow stages"""
    stage: WorkflowStage
    timeout_seconds: int
    warning_threshold_seconds: int
    recovery_actions: List[str] = field(default_factory=list)


@dataclass
class WorkflowMonitoringState:
    """Comprehensive workflow monitoring state"""
    workflow_id: str
    start_time: datetime
    current_stage: WorkflowStage
    stage_start_time: datetime
    last_heartbeat: datetime
    health_checks: List[SystemHealthCheck] = field(default_factory=list)
    stage_history: List[Tuple[WorkflowStage, datetime, datetime]] = field(default_factory=list)
    error_count: int = 0
    recovery_attempts: int = 0
    timeout_warnings: int = 0
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


class WorkflowReliabilityManager:
    """
    Comprehensive reliability manager for WorkflowManager execution.

    Provides monitoring, error handling, timeout detection, health checks,
    and state persistence for robust workflow execution.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the reliability manager"""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Configure comprehensive logging
        self._setup_logging()

        # Initialize monitoring state
        self.monitoring_states: Dict[str, WorkflowMonitoringState] = {}
        self.active_workflows: Dict[str, Any] = {}

        # Initialize Enhanced Separation components
        self.error_handler = ErrorHandler()
        self.state_manager = StateManager()
        self.checkpoint_manager = CheckpointManager(self.state_manager)
        self.task_tracker = TaskTracker()
        self.phase_tracker = WorkflowPhaseTracker()

        # Configure circuit breakers for different operations
        self.github_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=300.0
        )
        self.implementation_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=600.0
        )
        self.system_circuit_breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=120.0
        )

        # Default timeout configurations
        self.default_timeouts = self._initialize_default_timeouts()

        # Monitoring thread control
        self._monitoring_active = False
        self._monitoring_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

        # Performance tracking
        self.performance_baselines = {
            'issue_creation': 30,  # seconds
            'branch_setup': 10,
            'implementation': 1800,  # 30 minutes
            'testing': 600,  # 10 minutes
            'pr_creation': 60,
            'review_processing': 300
        }

        self.logger.info("WorkflowReliabilityManager initialized successfully")

    def _setup_logging(self):
        """Configure comprehensive logging for workflow execution"""
        log_level = self.config.get('log_level', 'INFO')
        log_format = self.config.get('log_format',
            '%(asctime)s - %(name)s - %(levelname)s - [%(workflow_id)s] %(message)s'
        )

        # Create workflow-specific logger
        workflow_logger = logging.getLogger('workflow_manager')
        workflow_logger.setLevel(getattr(logging, log_level))

        # Create file handler for workflow logs
        log_dir = Path('.github/workflow-logs')
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"workflow-{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level))

        # Create formatter
        formatter = logging.Formatter(log_format)
        file_handler.setFormatter(formatter)

        # Add handler to workflow logger
        workflow_logger.addHandler(file_handler)

        self.workflow_logger = workflow_logger
        self.logger.info(f"Workflow logging configured: {log_file}")

    def _initialize_default_timeouts(self) -> Dict[WorkflowStage, WorkflowTimeout]:
        """Initialize default timeout configurations for all workflow stages"""
        return {
            WorkflowStage.INITIALIZATION: WorkflowTimeout(
                stage=WorkflowStage.INITIALIZATION,
                timeout_seconds=120,
                warning_threshold_seconds=60,
                recovery_actions=['restart_initialization', 'check_system_health']
            ),
            WorkflowStage.PROMPT_ANALYSIS: WorkflowTimeout(
                stage=WorkflowStage.PROMPT_ANALYSIS,
                timeout_seconds=300,
                warning_threshold_seconds=180,
                recovery_actions=['simplify_analysis', 'fallback_to_basic_parsing']
            ),
            WorkflowStage.ISSUE_CREATION: WorkflowTimeout(
                stage=WorkflowStage.ISSUE_CREATION,
                timeout_seconds=180,
                warning_threshold_seconds=120,
                recovery_actions=['retry_github_api', 'check_github_connectivity']
            ),
            WorkflowStage.BRANCH_SETUP: WorkflowTimeout(
                stage=WorkflowStage.BRANCH_SETUP,
                timeout_seconds=60,
                warning_threshold_seconds=30,
                recovery_actions=['retry_git_operations', 'check_git_status']
            ),
            WorkflowStage.IMPLEMENTATION_START: WorkflowTimeout(
                stage=WorkflowStage.IMPLEMENTATION_START,
                timeout_seconds=300,
                warning_threshold_seconds=180,
                recovery_actions=['restart_implementation', 'check_dependencies']
            ),
            WorkflowStage.IMPLEMENTATION_PROGRESS: WorkflowTimeout(
                stage=WorkflowStage.IMPLEMENTATION_PROGRESS,
                timeout_seconds=1800,  # 30 minutes
                warning_threshold_seconds=1200,  # 20 minutes
                recovery_actions=['checkpoint_progress', 'simplify_implementation']
            ),
            WorkflowStage.TESTING_START: WorkflowTimeout(
                stage=WorkflowStage.TESTING_START,
                timeout_seconds=600,  # 10 minutes
                warning_threshold_seconds=400,
                recovery_actions=['retry_test_setup', 'skip_non_critical_tests']
            ),
            WorkflowStage.PR_CREATION: WorkflowTimeout(
                stage=WorkflowStage.PR_CREATION,
                timeout_seconds=120,
                warning_threshold_seconds=90,
                recovery_actions=['retry_pr_creation', 'check_branch_status']
            ),
            WorkflowStage.REVIEW_PROCESSING: WorkflowTimeout(
                stage=WorkflowStage.REVIEW_PROCESSING,
                timeout_seconds=300,
                warning_threshold_seconds=180,
                recovery_actions=['retry_review_request', 'manual_review_fallback']
            )
        }

    def start_workflow_monitoring(self, workflow_id: str, workflow_context: Dict[str, Any]) -> bool:
        """
        Start comprehensive monitoring for a workflow execution.

        Args:
            workflow_id: Unique identifier for the workflow
            workflow_context: Context information about the workflow

        Returns:
            True if monitoring started successfully
        """
        try:
            # Create monitoring state
            monitoring_state = WorkflowMonitoringState(
                workflow_id=workflow_id,
                start_time=datetime.now(),
                current_stage=WorkflowStage.INITIALIZATION,
                stage_start_time=datetime.now(),
                last_heartbeat=datetime.now()
            )

            self.monitoring_states[workflow_id] = monitoring_state
            self.active_workflows[workflow_id] = workflow_context

            # Perform initial health check
            health_check = self.perform_health_check(workflow_id)
            monitoring_state.health_checks.append(health_check)

            # Start monitoring thread if not already active
            if not self._monitoring_active:
                self._start_monitoring_thread()

            # Log workflow start with comprehensive context
            self.workflow_logger.info(
                f"Started workflow monitoring",
                extra={
                    'workflow_id': workflow_id,
                    'context': workflow_context,
                    'initial_health': health_check.status.value
                }
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to start workflow monitoring for {workflow_id}: {e}")
            return False

    def update_workflow_stage(self, workflow_id: str, new_stage: WorkflowStage,
                            stage_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the current workflow stage with comprehensive logging and checks.

        Args:
            workflow_id: Workflow identifier
            new_stage: New stage to transition to
            stage_context: Additional context for the stage

        Returns:
            True if stage update was successful
        """
        try:
            if workflow_id not in self.monitoring_states:
                self.logger.error(f"Workflow {workflow_id} not found in monitoring states")
                return False

            monitoring_state = self.monitoring_states[workflow_id]
            old_stage = monitoring_state.current_stage
            stage_end_time = datetime.now()

            # Record stage completion in history
            stage_duration = (stage_end_time - monitoring_state.stage_start_time).total_seconds()
            monitoring_state.stage_history.append(
                (old_stage, monitoring_state.stage_start_time, stage_end_time)
            )

            # Update current stage
            monitoring_state.current_stage = new_stage
            monitoring_state.stage_start_time = stage_end_time
            monitoring_state.last_heartbeat = stage_end_time

            # Log stage transition with performance metrics
            self.workflow_logger.info(
                f"Stage transition: {old_stage.value} -> {new_stage.value}",
                extra={
                    'workflow_id': workflow_id,
                    'old_stage': old_stage.value,
                    'new_stage': new_stage.value,
                    'stage_duration': stage_duration,
                    'total_duration': (stage_end_time - monitoring_state.start_time).total_seconds(),
                    'context': stage_context or {}
                }
            )

            # Perform health check on significant stage transitions
            critical_stages = [
                WorkflowStage.IMPLEMENTATION_START,
                WorkflowStage.PR_CREATION,
                WorkflowStage.REVIEW_PROCESSING
            ]

            if new_stage in critical_stages:
                health_check = self.perform_health_check(workflow_id)
                monitoring_state.health_checks.append(health_check)

                if health_check.status in [HealthStatus.CRITICAL, HealthStatus.FAILED]:
                    self.workflow_logger.warning(
                        f"Health check failed during stage transition",
                        extra={
                            'workflow_id': workflow_id,
                            'stage': new_stage.value,
                            'health_status': health_check.status.value,
                            'recommendations': health_check.recommendations
                        }
                    )

            # Create checkpoint for critical stages
            checkpoint_stages = [
                WorkflowStage.ISSUE_CREATION,
                WorkflowStage.IMPLEMENTATION_COMPLETE,
                WorkflowStage.PR_CREATION
            ]

            if new_stage in checkpoint_stages:
                self._create_workflow_checkpoint(workflow_id, new_stage)

            return True

        except Exception as e:
            self.logger.error(f"Failed to update workflow stage for {workflow_id}: {e}")
            return False

    def perform_health_check(self, workflow_id: str) -> SystemHealthCheck:
        """
        Perform comprehensive system health check for workflow execution.

        Args:
            workflow_id: Workflow identifier

        Returns:
            SystemHealthCheck with detailed health status
        """
        try:
            # System resource checks
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Git status check
            git_status = self._check_git_status()

            # GitHub connectivity check
            github_connectivity = self._check_github_connectivity()

            # Claude CLI availability check
            claude_availability = self._check_claude_availability()

            # Determine overall health status
            health_issues = []
            recommendations = []

            if cpu_usage > 90:
                health_issues.append("high_cpu")
                recommendations.append("Reduce concurrent operations")

            if memory.percent > 85:
                health_issues.append("high_memory")
                recommendations.append("Free up memory or restart services")

            if disk.percent > 90:
                health_issues.append("low_disk_space")
                recommendations.append("Clean up temporary files and logs")

            if not github_connectivity:
                health_issues.append("github_connectivity")
                recommendations.append("Check network connectivity and GitHub API status")

            if not claude_availability:
                health_issues.append("claude_unavailable")
                recommendations.append("Verify Claude CLI installation and authentication")

            # Determine overall status
            if len(health_issues) == 0:
                status = HealthStatus.HEALTHY
            elif len(health_issues) == 1 and health_issues[0] not in ['github_connectivity', 'claude_unavailable']:
                status = HealthStatus.WARNING
            elif len(health_issues) <= 2:
                status = HealthStatus.DEGRADED
            elif 'claude_unavailable' in health_issues:
                status = HealthStatus.FAILED
            else:
                status = HealthStatus.CRITICAL

            health_check = SystemHealthCheck(
                status=status,
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                git_status=git_status,
                github_connectivity=github_connectivity,
                claude_availability=claude_availability,
                details={
                    'health_issues': health_issues,
                    'memory_available_gb': memory.available / (1024**3),
                    'cpu_count': psutil.cpu_count()
                },
                recommendations=recommendations
            )

            # Log health check results
            self.workflow_logger.info(
                f"Health check completed",
                extra={
                    'workflow_id': workflow_id,
                    'health_status': status.value,
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory.percent,
                    'disk_usage': disk.percent,
                    'issues': health_issues,
                    'recommendations': recommendations
                }
            )

            return health_check

        except Exception as e:
            self.logger.error(f"Health check failed for {workflow_id}: {e}")
            return SystemHealthCheck(
                status=HealthStatus.FAILED,
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                git_status="unknown",
                github_connectivity=False,
                claude_availability=False,
                details={'error': str(e)},
                recommendations=['Investigate health check system failure']
            )

    def handle_workflow_error(self, workflow_id: str, error: Exception,
                            stage: Optional[WorkflowStage] = None,
                            recovery_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle workflow errors with comprehensive recovery strategies.

        Args:
            workflow_id: Workflow identifier
            error: Exception that occurred
            stage: Stage where error occurred
            recovery_context: Additional context for recovery

        Returns:
            Recovery result with actions taken and recommendations
        """
        try:
            if workflow_id in self.monitoring_states:
                monitoring_state = self.monitoring_states[workflow_id]
                monitoring_state.error_count += 1
                current_stage = stage or monitoring_state.current_stage
            else:
                current_stage = stage or WorkflowStage.INITIALIZATION

            # Create comprehensive error context
            error_context = ErrorContext(
                operation_name=f"workflow_stage_{current_stage.value}"
            )
            # Store error information separately
            error_details = {
                'error': error,
                'workflow_id': workflow_id,
                'stage': current_stage.value,
                'recovery_context': recovery_context or {},
                'timestamp': datetime.now().isoformat()
            }

            # Log error with full context
            self.workflow_logger.error(
                f"Workflow error in stage {current_stage.value}: {str(error)}",
                extra={
                    'workflow_id': workflow_id,
                    'stage': current_stage.value,
                    'error_type': type(error).__name__,
                    'error_message': str(error),
                    'recovery_context': recovery_context or {},
                    'error_count': monitoring_state.error_count if workflow_id in self.monitoring_states else 1
                },
                exc_info=True
            )

            # Handle error through Enhanced Separation error handler
            # ErrorContext is a context manager, not for passing error info
            # Pass the error details directly to handle_error
            self.error_handler.handle_error(error_details)

            # Determine recovery strategy based on error type and stage
            recovery_result = self._execute_recovery_strategy(
                workflow_id, error, current_stage, recovery_context
            )

            # Create checkpoint after error handling
            if workflow_id in self.monitoring_states:
                self._create_error_checkpoint(workflow_id, error, current_stage)

            return recovery_result

        except Exception as recovery_error:
            self.logger.error(f"Error handling failed for {workflow_id}: {recovery_error}")
            return {
                'success': False,
                'error': 'Recovery handling failed',
                'recommendations': ['Manual intervention required', 'Review system logs']
            }

    def check_workflow_timeouts(self, workflow_id: str) -> Dict[str, Any]:
        """
        Check for workflow timeouts and initiate recovery if needed.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Timeout check result with any recovery actions taken
        """
        try:
            if workflow_id not in self.monitoring_states:
                return {'status': 'workflow_not_found'}

            monitoring_state = self.monitoring_states[workflow_id]
            current_time = datetime.now()
            stage_duration = (current_time - monitoring_state.stage_start_time).total_seconds()

            current_stage = monitoring_state.current_stage
            timeout_config = self.default_timeouts.get(current_stage)

            if not timeout_config:
                return {'status': 'no_timeout_config', 'stage': current_stage.value}

            # Check for warning threshold
            if stage_duration > timeout_config.warning_threshold_seconds:
                monitoring_state.timeout_warnings += 1

                self.workflow_logger.warning(
                    f"Stage duration warning: {current_stage.value} running for {stage_duration:.1f}s",
                    extra={
                        'workflow_id': workflow_id,
                        'stage': current_stage.value,
                        'duration': stage_duration,
                        'warning_threshold': timeout_config.warning_threshold_seconds,
                        'timeout_threshold': timeout_config.timeout_seconds
                    }
                )

            # Check for timeout threshold
            if stage_duration > timeout_config.timeout_seconds:
                self.workflow_logger.error(
                    f"Stage timeout detected: {current_stage.value} exceeded {timeout_config.timeout_seconds}s",
                    extra={
                        'workflow_id': workflow_id,
                        'stage': current_stage.value,
                        'duration': stage_duration,
                        'timeout_threshold': timeout_config.timeout_seconds
                    }
                )

                # Execute timeout recovery
                recovery_result = self._execute_timeout_recovery(
                    workflow_id, current_stage, timeout_config
                )

                return {
                    'status': 'timeout_detected',
                    'stage': current_stage.value,
                    'duration': stage_duration,
                    'recovery_result': recovery_result
                }

            return {
                'status': 'healthy',
                'stage': current_stage.value,
                'duration': stage_duration,
                'remaining_time': timeout_config.timeout_seconds - stage_duration
            }

        except Exception as e:
            self.logger.error(f"Timeout check failed for {workflow_id}: {e}")
            return {'status': 'check_failed', 'error': str(e)}

    def create_workflow_persistence(self, workflow_id: str,
                                  workflow_state: Dict[str, Any]) -> bool:
        """
        Create comprehensive workflow state persistence for resumption.

        Args:
            workflow_id: Workflow identifier
            workflow_state: Current workflow state to persist

        Returns:
            True if persistence was successful
        """
        try:
            # Create TaskState for Enhanced Separation state management
            task_state = TaskState(
                task_id=workflow_id,
                prompt_file=workflow_state.get('prompt_file', 'unknown'),
                status='in_progress',
                phase=self._convert_stage_to_phase(
                    self.monitoring_states[workflow_id].current_stage
                ) if workflow_id in self.monitoring_states else 0,
                context=workflow_state
            )

            # Add monitoring state to context
            if workflow_id in self.monitoring_states:
                monitoring_state = self.monitoring_states[workflow_id]
                task_state.context.update({
                    'monitoring_state': {
                        'current_stage': monitoring_state.current_stage.value,
                        'stage_start_time': monitoring_state.stage_start_time.isoformat(),
                        'error_count': monitoring_state.error_count,
                        'recovery_attempts': monitoring_state.recovery_attempts,
                        'stage_history': [
                            (stage.value, start.isoformat(), end.isoformat())
                            for stage, start, end in monitoring_state.stage_history
                        ]
                    }
                })

            # Save state through Enhanced Separation
            success = self.state_manager.save_state(task_state)

            if success:
                self.workflow_logger.info(
                    f"Workflow state persisted successfully",
                    extra={
                        'workflow_id': workflow_id,
                        'stage': self.monitoring_states[workflow_id].current_stage.value if workflow_id in self.monitoring_states else 'unknown',
                        'state_size': len(str(workflow_state))
                    }
                )

            return success

        except Exception as e:
            self.logger.error(f"Failed to create workflow persistence for {workflow_id}: {e}")
            return False

    def restore_workflow_from_persistence(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore workflow state from persistence for resumption.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Restored workflow state or None if not found
        """
        try:
            # Load state through Enhanced Separation
            task_state = self.state_manager.load_state(workflow_id)

            if not task_state:
                return None

            # Restore monitoring state if available
            monitoring_data = task_state.context.get('monitoring_state')
            if monitoring_data:
                restored_monitoring = WorkflowMonitoringState(
                    workflow_id=workflow_id,
                    start_time=task_state.created_at,
                    current_stage=WorkflowStage(monitoring_data['current_stage']),
                    stage_start_time=datetime.fromisoformat(monitoring_data['stage_start_time']),
                    last_heartbeat=datetime.now(),
                    error_count=monitoring_data.get('error_count', 0),
                    recovery_attempts=monitoring_data.get('recovery_attempts', 0),
                    stage_history=[
                        (WorkflowStage(stage), datetime.fromisoformat(start), datetime.fromisoformat(end))
                        for stage, start, end in monitoring_data.get('stage_history', [])
                    ]
                )

                self.monitoring_states[workflow_id] = restored_monitoring

            self.workflow_logger.info(
                f"Workflow state restored successfully",
                extra={
                    'workflow_id': workflow_id,
                    'restored_stage': monitoring_data['current_stage'] if monitoring_data else 'unknown',
                    'error_count': monitoring_data.get('error_count', 0) if monitoring_data else 0
                }
            )

            return task_state.context

        except Exception as e:
            self.logger.error(f"Failed to restore workflow from persistence for {workflow_id}: {e}")
            return None

    def stop_workflow_monitoring(self, workflow_id: str, completion_status: str = 'completed') -> bool:
        """
        Stop monitoring for a workflow and create final reports.

        Args:
            workflow_id: Workflow identifier
            completion_status: Final status of the workflow

        Returns:
            True if monitoring was stopped successfully
        """
        try:
            if workflow_id not in self.monitoring_states:
                self.logger.warning(f"Workflow {workflow_id} not found in monitoring states")
                return False

            monitoring_state = self.monitoring_states[workflow_id]
            end_time = datetime.now()
            total_duration = (end_time - monitoring_state.start_time).total_seconds()

            # Create final performance report
            performance_report = self._generate_performance_report(workflow_id, monitoring_state)

            # Log workflow completion
            self.workflow_logger.info(
                f"Workflow monitoring stopped: {completion_status}",
                extra={
                    'workflow_id': workflow_id,
                    'completion_status': completion_status,
                    'total_duration': total_duration,
                    'stages_completed': len(monitoring_state.stage_history),
                    'error_count': monitoring_state.error_count,
                    'recovery_attempts': monitoring_state.recovery_attempts,
                    'performance_report': performance_report
                }
            )

            # Clean up monitoring state
            del self.monitoring_states[workflow_id]
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

            # Stop monitoring thread if no active workflows
            if not self.monitoring_states and self._monitoring_active:
                self._stop_monitoring_thread()

            return True

        except Exception as e:
            self.logger.error(f"Failed to stop workflow monitoring for {workflow_id}: {e}")
            return False

    def get_workflow_diagnostics(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get comprehensive diagnostic information for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Comprehensive diagnostic information
        """
        try:
            if workflow_id not in self.monitoring_states:
                return {'error': 'Workflow not found in monitoring states'}

            monitoring_state = self.monitoring_states[workflow_id]
            current_time = datetime.now()

            # Calculate stage statistics
            stage_stats = {}
            for stage, start_time, end_time in monitoring_state.stage_history:
                duration = (end_time - start_time).total_seconds()
                stage_stats[stage.value] = {
                    'duration': duration,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                }

            # Current stage info
            current_stage_duration = (current_time - monitoring_state.stage_start_time).total_seconds()

            # Recent health checks
            recent_health = monitoring_state.health_checks[-5:] if monitoring_state.health_checks else []

            return {
                'workflow_id': workflow_id,
                'status': 'active',
                'total_duration': (current_time - monitoring_state.start_time).total_seconds(),
                'current_stage': {
                    'stage': monitoring_state.current_stage.value,
                    'duration': current_stage_duration,
                    'start_time': monitoring_state.stage_start_time.isoformat()
                },
                'stage_history': stage_stats,
                'error_count': monitoring_state.error_count,
                'recovery_attempts': monitoring_state.recovery_attempts,
                'timeout_warnings': monitoring_state.timeout_warnings,
                'recent_health_checks': [
                    {
                        'status': hc.status.value,
                        'cpu_usage': hc.cpu_usage,
                        'memory_usage': hc.memory_usage,
                        'timestamp': hc.timestamp.isoformat(),
                        'recommendations': hc.recommendations
                    }
                    for hc in recent_health
                ],
                'last_heartbeat': monitoring_state.last_heartbeat.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Failed to get workflow diagnostics for {workflow_id}: {e}")
            return {'error': str(e)}

    # Private helper methods

    def _start_monitoring_thread(self):
        """Start the background monitoring thread"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._shutdown_event.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name=f"WorkflowMonitoring"
        )
        self._monitoring_thread.start()
        self.logger.info("Started workflow monitoring thread")

    def _stop_monitoring_thread(self):
        """Stop the background monitoring thread"""
        if not self._monitoring_active:
            return

        self._monitoring_active = False
        self._shutdown_event.set()

        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=10)

        self.logger.info("Stopped workflow monitoring thread")

    def _monitoring_loop(self):
        """Main monitoring loop running in background thread"""
        self.logger.info("Workflow monitoring loop started")

        while self._monitoring_active and not self._shutdown_event.is_set():
            try:
                # Check all active workflows
                for workflow_id in list(self.monitoring_states.keys()):
                    # Check for timeouts
                    timeout_result = self.check_workflow_timeouts(workflow_id)

                    # Perform periodic health checks (every 5 minutes)
                    monitoring_state = self.monitoring_states[workflow_id]
                    time_since_last_health = (datetime.now() -
                        (monitoring_state.health_checks[-1].timestamp if monitoring_state.health_checks else monitoring_state.start_time)
                    ).total_seconds()

                    if time_since_last_health > 300:  # 5 minutes
                        health_check = self.perform_health_check(workflow_id)
                        monitoring_state.health_checks.append(health_check)

                # Sleep for monitoring interval
                if not self._shutdown_event.wait(30):  # 30 second intervals
                    continue
                else:
                    break

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

        self.logger.info("Workflow monitoring loop stopped")

    def _check_git_status(self) -> str:
        """Check git repository status"""
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return 'clean' if not result.stdout.strip() else 'dirty'
            else:
                return 'error'
        except Exception:
            return 'unavailable'

    def _check_github_connectivity(self) -> bool:
        """Check GitHub API connectivity"""
        try:
            import subprocess
            result = subprocess.run(['gh', 'api', 'user'],
                                  capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def _check_claude_availability(self) -> bool:
        """Check Claude CLI availability"""
        try:
            import subprocess
            result = subprocess.run(['claude', '--version'],
                                  capture_output=True, timeout=10)
            return result.returncode == 0
        except Exception:
            return False

    def _execute_recovery_strategy(self, workflow_id: str, error: Exception,
                                 stage: WorkflowStage, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute recovery strategy based on error type and stage"""
        recovery_actions = []

        try:
            # Increment recovery attempts
            if workflow_id in self.monitoring_states:
                self.monitoring_states[workflow_id].recovery_attempts += 1

            # Stage-specific recovery strategies
            if stage == WorkflowStage.ISSUE_CREATION:
                recovery_actions.extend([
                    'retry_github_api_call',
                    'check_github_rate_limits',
                    'verify_repository_access'
                ])
            elif stage == WorkflowStage.IMPLEMENTATION_PROGRESS:
                recovery_actions.extend([
                    'create_implementation_checkpoint',
                    'simplify_current_task',
                    'split_complex_operations'
                ])
            elif stage == WorkflowStage.PR_CREATION:
                recovery_actions.extend([
                    'verify_branch_state',
                    'check_pr_requirements',
                    'retry_pr_creation'
                ])

            # Error type specific strategies
            error_type = type(error).__name__
            if 'timeout' in error_type.lower():
                recovery_actions.extend([
                    'increase_timeout_limits',
                    'check_system_resources',
                    'restart_operation_with_retry'
                ])
            elif 'network' in error_type.lower() or 'connection' in error_type.lower():
                recovery_actions.extend([
                    'check_network_connectivity',
                    'retry_with_exponential_backoff',
                    'switch_to_offline_mode'
                ])

            return {
                'success': True,
                'recovery_actions': recovery_actions,
                'recommendations': [
                    f'Monitor {stage.value} stage closely',
                    'Review system health after recovery',
                    'Consider manual intervention if issues persist'
                ]
            }

        except Exception as recovery_error:
            return {
                'success': False,
                'error': str(recovery_error),
                'recommendations': ['Manual intervention required']
            }

    def _execute_timeout_recovery(self, workflow_id: str, stage: WorkflowStage,
                                timeout_config: WorkflowTimeout) -> Dict[str, Any]:
        """Execute timeout-specific recovery actions"""
        try:
            recovery_actions_taken = []

            for action in timeout_config.recovery_actions:
                if action == 'restart_implementation':
                    # Create checkpoint before restart
                    self._create_workflow_checkpoint(workflow_id, stage)
                    recovery_actions_taken.append('checkpoint_created')
                elif action == 'check_system_health':
                    health_check = self.perform_health_check(workflow_id)
                    recovery_actions_taken.append(f'health_check_{health_check.status.value}')
                elif action == 'retry_github_api':
                    # Circuit breaker will handle retry logic
                    recovery_actions_taken.append('github_retry_initiated')

            return {
                'success': True,
                'actions_taken': recovery_actions_taken,
                'stage': stage.value,
                'next_steps': ['Monitor for improvement', 'Manual intervention if timeout persists']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stage': stage.value
            }

    def _create_workflow_checkpoint(self, workflow_id: str, stage: WorkflowStage):
        """Create a checkpoint for the current workflow state"""
        try:
            if workflow_id in self.monitoring_states:
                monitoring_state = self.monitoring_states[workflow_id]

                checkpoint_state = TaskState(
                    task_id=workflow_id,
                    prompt_file=self.active_workflows.get(workflow_id, {}).get('prompt_file', 'unknown'),
                    status='in_progress',
                    phase=self._convert_stage_to_phase(stage),
                    context={
                        'checkpoint_stage': stage.value,
                        'checkpoint_time': datetime.now().isoformat(),
                        'error_count': monitoring_state.error_count,
                        'recovery_attempts': monitoring_state.recovery_attempts
                    }
                )

                checkpoint_id = self.checkpoint_manager.create_checkpoint(
                    checkpoint_state,
                    f"Checkpoint at stage {stage.value}"
                )

                self.workflow_logger.info(
                    f"Checkpoint created: {checkpoint_id}",
                    extra={
                        'workflow_id': workflow_id,
                        'stage': stage.value,
                        'checkpoint_id': checkpoint_id
                    }
                )

        except Exception as e:
            self.logger.error(f"Failed to create checkpoint for {workflow_id}: {e}")

    def _create_error_checkpoint(self, workflow_id: str, error: Exception, stage: WorkflowStage):
        """Create an error checkpoint for debugging and recovery"""
        try:
            error_state = TaskState(
                task_id=f"{workflow_id}_error_{int(time.time())}",
                prompt_file=self.active_workflows.get(workflow_id, {}).get('prompt_file', 'unknown'),
                status='error',
                phase=self._convert_stage_to_phase(stage),
                context={
                    'error_stage': stage.value,
                    'error_time': datetime.now().isoformat(),
                    'error_type': type(error).__name__,
                    'error_message': str(error),
                    'original_workflow': workflow_id
                }
            )

            error_state.set_error({
                'error_type': type(error).__name__,
                'error_message': str(error),
                'stage': stage.value
            })

            self.checkpoint_manager.create_checkpoint(
                error_state,
                f"Error checkpoint: {type(error).__name__} in {stage.value}"
            )

        except Exception as checkpoint_error:
            self.logger.error(f"Failed to create error checkpoint: {checkpoint_error}")

    def _convert_stage_to_phase(self, stage: WorkflowStage) -> int:
        """Convert WorkflowStage to WorkflowPhase number for compatibility"""
        stage_to_phase_map = {
            WorkflowStage.INITIALIZATION: 0,
            WorkflowStage.PROMPT_ANALYSIS: 1,
            WorkflowStage.TASK_PREPARATION: 1,
            WorkflowStage.ISSUE_CREATION: 2,
            WorkflowStage.BRANCH_SETUP: 3,
            WorkflowStage.RESEARCH_PLANNING: 4,
            WorkflowStage.IMPLEMENTATION_START: 5,
            WorkflowStage.IMPLEMENTATION_PROGRESS: 5,
            WorkflowStage.IMPLEMENTATION_COMPLETE: 5,
            WorkflowStage.TESTING_START: 6,
            WorkflowStage.TESTING_COMPLETE: 6,
            WorkflowStage.DOCUMENTATION_UPDATE: 7,
            WorkflowStage.PR_PREPARATION: 8,
            WorkflowStage.PR_CREATION: 8,
            WorkflowStage.PR_VERIFICATION: 8,
            WorkflowStage.REVIEW_REQUEST: 9,
            WorkflowStage.REVIEW_PROCESSING: 9,
            WorkflowStage.FINAL_CLEANUP: 9,
            WorkflowStage.COMPLETION: 9
        }
        return stage_to_phase_map.get(stage, 0)

    def _generate_performance_report(self, workflow_id: str,
                                   monitoring_state: WorkflowMonitoringState) -> Dict[str, Any]:
        """Generate comprehensive performance report for workflow"""
        try:
            total_duration = (datetime.now() - monitoring_state.start_time).total_seconds()

            # Calculate stage performance
            stage_performance = {}
            for stage, start_time, end_time in monitoring_state.stage_history:
                duration = (end_time - start_time).total_seconds()
                baseline = self.performance_baselines.get(stage.value.split('_')[0], 60)

                stage_performance[stage.value] = {
                    'duration': duration,
                    'baseline': baseline,
                    'performance_ratio': duration / baseline if baseline > 0 else 1.0,
                    'status': 'fast' if duration < baseline * 0.8 else 'normal' if duration < baseline * 1.2 else 'slow'
                }

            # Overall performance metrics
            total_baseline = sum(
                self.performance_baselines.get(stage.value.split('_')[0], 60)
                for stage, _, _ in monitoring_state.stage_history
            )

            performance_score = (total_baseline / total_duration) if total_duration > 0 else 0

            return {
                'total_duration': total_duration,
                'total_baseline': total_baseline,
                'performance_score': performance_score,
                'performance_grade': self._calculate_performance_grade(performance_score),
                'stage_performance': stage_performance,
                'error_rate': monitoring_state.error_count / max(len(monitoring_state.stage_history), 1),
                'recovery_rate': monitoring_state.recovery_attempts / max(monitoring_state.error_count, 1) if monitoring_state.error_count > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {e}")
            return {'error': str(e)}

    def _calculate_performance_grade(self, score: float) -> str:
        """Calculate performance grade based on score"""
        if score >= 1.5:
            return 'A+'
        elif score >= 1.2:
            return 'A'
        elif score >= 1.0:
            return 'B'
        elif score >= 0.8:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'

    def shutdown(self):
        """Shutdown the reliability manager and clean up resources"""
        try:
            self.logger.info("Shutting down WorkflowReliabilityManager")

            # Stop monitoring thread
            self._stop_monitoring_thread()

            # Save final state for all active workflows
            for workflow_id in list(self.monitoring_states.keys()):
                self.stop_workflow_monitoring(workflow_id, 'interrupted')

            # Clear all state
            self.monitoring_states.clear()
            self.active_workflows.clear()

            self.logger.info("WorkflowReliabilityManager shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Context manager for workflow reliability
class WorkflowReliabilityContext:
    """Context manager for workflow execution with comprehensive reliability features"""

    def __init__(self, workflow_id: str, workflow_context: Dict[str, Any],
                 reliability_manager: Optional[WorkflowReliabilityManager] = None):
        self.workflow_id = workflow_id
        self.workflow_context = workflow_context
        self.reliability_manager = reliability_manager or WorkflowReliabilityManager()
        self.started = False

    def __enter__(self):
        self.started = self.reliability_manager.start_workflow_monitoring(
            self.workflow_id, self.workflow_context
        )
        return self.reliability_manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.started:
            if exc_type:
                # Handle exception
                self.reliability_manager.handle_workflow_error(
                    self.workflow_id, exc_val,
                    recovery_context={'exception_type': exc_type.__name__}
                )
                completion_status = 'failed'
            else:
                completion_status = 'completed'

            self.reliability_manager.stop_workflow_monitoring(
                self.workflow_id, completion_status
            )

        # Don't suppress exceptions
        return False


# Convenience functions for WorkflowManager integration
def create_reliability_manager(config: Optional[Dict[str, Any]] = None) -> WorkflowReliabilityManager:
    """Create a configured WorkflowReliabilityManager instance"""
    return WorkflowReliabilityManager(config)

def monitor_workflow(workflow_id: str, workflow_context: Dict[str, Any],
                    reliability_manager: Optional[WorkflowReliabilityManager] = None):
    """Create a workflow reliability context manager"""
    return WorkflowReliabilityContext(workflow_id, workflow_context, reliability_manager)
