"""
OrchestratorAgent Core Implementation

This module contains the core orchestration logic for coordinating parallel execution
of multiple WorkflowManagers to achieve 3-5x faster development workflows.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import logging

# Enhanced Separation Architecture - Shared Modules
try:
    from .claude.shared.github_operations import GitHubOperations
    from .claude.shared.state_management import WorkflowStateManager, CheckpointManager, StateBackupRestore
    from .claude.shared.error_handling import ErrorHandler, RetryManager, CircuitBreaker, RecoveryManager
    from .claude.shared.task_tracking import TaskTracker, TodoWriteManager, WorkflowPhaseTracker, ProductivityAnalyzer
    from .claude.shared.interfaces import AgentConfig, PerformanceMetrics, WorkflowState, TaskData, ErrorContext, WorkflowPhase
except ImportError:
    # Fallback for when shared modules are not available
    logging.warning("Shared modules not available, using fallback implementations")


class OrchestratorCore:
    """Core orchestration engine for parallel workflow execution."""
    
    def __init__(self):
        """Initialize shared managers and configuration."""
        # Initialize shared managers at startup
        self.github_ops = GitHubOperations()
        self.state_manager = WorkflowStateManager()
        self.error_handler = ErrorHandler(retry_manager=RetryManager())
        self.task_tracker = TaskTracker(todowrite_manager=TodoWriteManager())
        self.performance_analyzer = ProductivityAnalyzer()

        # Configure circuit breakers for resilient operations
        self.github_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=300)
        self.execution_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=600)

    @error_handler.with_circuit_breaker(github_circuit_breaker)
    def analyze_tasks_enhanced(self, prompt_files: List[str]) -> Dict[str, Any]:
        """Enhanced task analysis with Task Decomposition Analyzer integration."""
        # Initialize enhanced analysis tracking
        self.performance_analyzer.record_phase_start("enhanced_task_analysis")
        self.task_tracker.update_phase(WorkflowPhase.ANALYSIS, "in_progress")

        # Step 1: Initial task analysis with enhanced capabilities
        analysis_result = self.retry_manager.execute_with_retry(
            lambda: self.invoke_enhanced_task_analyzer(prompt_files, {
                'enable_decomposition': True,
                'ml_classification': True,
                'pattern_recognition': True,
                'historical_analysis': True
            }),
            max_attempts=3,
            backoff_strategy="exponential"
        )

        # Step 2: Process decomposition results
        enhanced_tasks = []
        for task in analysis_result.tasks:
            if task.requires_decomposition:
                # Task was automatically decomposed by TaskDecomposer
                enhanced_tasks.extend(task.subtasks)
                self.performance_analyzer.record_decomposition_benefit(
                    task.id, task.decomposition_benefit
                )
            else:
                enhanced_tasks.append(task)

        # Step 3: Apply ML-based optimizations
        ml_optimizations = self.apply_ml_optimizations(enhanced_tasks)
        for task in enhanced_tasks:
            task.apply_optimizations(ml_optimizations.get(task.id, []))

        # Step 4: Pre-validate all tasks for governance compliance
        for task in enhanced_tasks:
            try:
                self.validate_workflow_compliance(task)
                task.governance_validated = True
            except WorkflowComplianceError as e:
                self.error_handler.log_error(f"Task {task.id} failed governance validation: {e}")
                task.governance_validated = False
                task.compliance_errors = str(e)

        # Step 5: Update execution plan with enhanced insights and validated tasks
        enhanced_execution_plan = self.generate_enhanced_execution_plan(
            enhanced_tasks,
            analysis_result.dependency_graph,
            analysis_result.performance_predictions
        )

        # Track enhanced analysis completion
        self.performance_analyzer.record_phase_completion("enhanced_task_analysis", {
            'original_task_count': len(prompt_files),
            'enhanced_task_count': len(enhanced_tasks),
            'decomposition_applied': sum(1 for t in analysis_result.tasks if t.requires_decomposition),
            'research_required': sum(1 for t in analysis_result.tasks if t.requires_research),
            'ml_classifications': len([t for t in enhanced_tasks if hasattr(t, 'ml_classification')])
        })

        return enhanced_execution_plan

    def invoke_enhanced_task_analyzer(self, prompt_files: List[str], config: Dict[str, bool]) -> Dict[str, Any]:
        """Invoke task analyzer with enhanced decomposition capabilities."""
        # The enhanced task-analyzer now automatically coordinates with:
        # - TaskBoundsEval for complexity assessment
        # - TaskDecomposer for intelligent decomposition
        # - TaskResearchAgent for research requirements
        # - ML classification for pattern recognition

        analyzer_prompt = f"""
        /agent:task-analyzer

        Perform enhanced analysis with Task Decomposition Analyzer integration:
        Prompt files: {', '.join(prompt_files)}

        Enhanced Configuration:
        - Task Decomposition Analyzer integration: {config['enable_decomposition']}
        - Machine learning classification: {config['ml_classification']}
        - Pattern recognition system: {config['pattern_recognition']}
        - Historical analysis: {config['historical_analysis']}

        Required Analysis:
        1. Evaluate task bounds and complexity for each prompt
        2. Apply intelligent decomposition where beneficial
        3. Identify research requirements and suggest approaches
        4. Perform ML-based classification and pattern recognition
        5. Generate optimized parallel execution plan
        6. Provide comprehensive risk assessment

        Return enhanced analysis with all coordination results included.
        """

        return self.execute_claude_agent_invocation(analyzer_prompt)

    def setup_environments(self, task_data: TaskData) -> None:
        """Environment setup with state management."""
        # Create orchestration state checkpoint
        orchestration_state = WorkflowState(
            task_id=f"orchestration-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            phase=WorkflowPhase.ENVIRONMENT_SETUP,
            tasks=task_data.tasks
        )

        # Save state with backup
        self.state_manager.save_state(orchestration_state)
        backup_manager = StateBackupRestore(self.state_manager)
        backup_manager.create_backup(orchestration_state.task_id)

        # CRITICAL: Setup worktrees for ALL tasks - this is MANDATORY
        # The orchestrator MUST ALWAYS use worktree-manager for isolation
        for task in task_data.tasks:
            try:
                # ALWAYS invoke worktree manager - no exceptions
                worktree_result = self.invoke_worktree_manager(task)

                # UV Project Detection and Setup
                worktree_path = worktree_result.path
                if self.is_uv_project(worktree_path):
                    logging.info(f"UV project detected in {worktree_path} - setting up UV environment")
                    if not self.setup_uv_environment_for_task(task, worktree_path):
                        raise Exception(f"Failed to set up UV environment for task {task.id}")
                    task.is_uv_project = True
                else:
                    task.is_uv_project = False

                self.task_tracker.update_task_status(task.id, "worktree_ready")
            except Exception as e:
                self.error_handler.handle_error(ErrorContext(
                    error=e,
                    task_id=task.id,
                    phase="environment_setup",
                    recovery_action="retry_worktree_creation"
                ))

    @error_handler.with_graceful_degradation(fallback_sequential_execution)
    def execute_parallel_tasks(self, tasks: List[Any]) -> List[Any]:
        """Enhanced parallel execution with governance validation."""
        # Initialize parallel execution monitoring
        execution_metrics = PerformanceMetrics()
        self.performance_analyzer.start_parallel_execution_tracking(len(tasks))

        # Execute with circuit breaker protection
        results = []
        for task in tasks:
            try:
                # CRITICAL GOVERNANCE VALIDATION: Ensure task follows proper workflow
                self.validate_workflow_compliance(task)

                # MANDATORY: ALL tasks must execute through WorkflowManager
                task_result = self.execution_circuit_breaker.call(
                    lambda: self.execute_workflow_manager(task)
                )
                results.append(task_result)
                self.task_tracker.update_task_status(task.id, "completed")
            except WorkflowComplianceError as e:
                # Log governance violation and fail task
                self.error_handler.log_error(f"Governance violation for task {task.id}: {e}")
                self.task_tracker.update_task_status(task.id, "governance_violation")
                raise e
            except CircuitBreakerOpenError:
                # Fallback to sequential execution
                self.error_handler.log_warning("Circuit breaker open, falling back to sequential")
                return self.execute_sequential_fallback(tasks)

        return results

    def integrate_results(self, execution_results: List[Any]) -> Dict[str, Any]:
        """Result integration with performance analytics."""
        # Analyze performance improvements achieved
        performance_metrics = self.performance_analyzer.calculate_speedup(
            execution_results,
            baseline_sequential_time=self.estimate_sequential_time(tasks)
        )

        # GitHub operations with batch processing
        successful_tasks = [r for r in execution_results if r.success]
        self.github_manager.batch_merge_pull_requests([
            t.pr_number for t in successful_tasks
        ])

        # Create comprehensive performance report
        report = self.generate_orchestration_report(performance_metrics)

        # Clean up with state persistence
        self.cleanup_orchestration_resources(execution_results)
        self.state_manager.mark_orchestration_complete(orchestration_state.task_id)

        return report

    def analyze_file_conflicts(self, tasks: List[Any]) -> List[tuple]:
        """Detect tasks that modify the same files."""
        file_map = {}
        conflicts = []

        for task in tasks:
            target_files = self.extract_target_files(task.prompt_content)
            for file_path in target_files:
                if file_path in file_map:
                    conflicts.append((task.id, file_map[file_path]))
                file_map[file_path] = task.id

        return conflicts

    def analyze_import_dependencies(self, file_path: str) -> List[str]:
        """Map Python import relationships."""
        with open(file_path, 'r') as f:
            content = f.read()

        imports = []
        # Parse import statements
        for line in content.split('\n'):
            if line.strip().startswith(('import ', 'from ')):
                imports.append(self.parse_import_statement(line))

        return imports

    def validate_workflow_compliance(self, task: Any) -> bool:
        """Ensure task will be executed through proper WorkflowManager workflow."""
        
        # Check 1: Verify WorkflowManager will be used
        if not task.uses_workflow_manager:
            raise InvalidExecutionMethodError(task.id)

        # Check 2: Verify complete workflow phases will be followed
        required_phases = ['setup', 'issue_creation', 'branch_creation', 'implementation',
                          'testing', 'documentation', 'pr_creation', 'review']
        missing_phases = [phase for phase in required_phases if phase not in task.planned_phases]
        if missing_phases:
            raise IncompleteWorkflowError(task.id, missing_phases)

        # Check 3: Verify no direct execution bypass
        if task.execution_method in ['direct', 'claude_-p', 'shell_script']:
            raise DirectExecutionError(task.id, task.execution_method)

        return True

    # UV Environment Management
    def is_uv_project(self, worktree_path: str) -> bool:
        """Check if worktree contains a UV project."""
        path = Path(worktree_path)
        return (path / "pyproject.toml").exists() and (path / "uv.lock").exists()

    def setup_uv_environment_for_task(self, task: Any, worktree_path: str) -> bool:
        """Set up UV environment for a specific task worktree."""
        try:
            # Use shared UV setup script
            setup_script = Path(".claude/scripts/setup-uv-env.sh")
            if not setup_script.exists():
                logging.error("UV setup script not found")
                return False

            # Run UV setup
            result = subprocess.run([
                "bash", str(setup_script), "setup", worktree_path, "--all-extras"
            ], capture_output=True, text=True, check=True)

            logging.info(f"UV environment setup completed for task {task.id}")
            return True

        except subprocess.CalledProcessError as e:
            logging.error(f"UV setup failed for task {task.id}: {e.stderr}")
            return False

    def execute_uv_command(self, worktree_path: str, command_args: List[str]) -> tuple:
        """Execute command in UV environment."""
        uv_cmd = ["uv", "run"] + command_args

        result = subprocess.run(
            uv_cmd,
            cwd=worktree_path,
            capture_output=True,
            text=True
        )

        return result.returncode == 0, result.stdout, result.stderr

    def generate_workflow_prompt(self, task: Any) -> str:
        """Generate WorkflowManager prompt with UV context."""

        uv_context = ""
        if hasattr(task, 'is_uv_project') and task.is_uv_project:
            uv_context = """

            **UV PROJECT DETECTED**: This is a UV Python project.

            CRITICAL REQUIREMENTS:
            - UV environment is already set up
            - Use 'uv run' prefix for ALL Python commands
            - Examples: 'uv run pytest tests/', 'uv run python script.py'
            - NEVER run Python commands directly (will fail)
            """

        return f"""
        Execute workflow for task: {task.name}
        Worktree: {task.worktree_path}
        {uv_context}

        [Rest of prompt content...]
        """

    # Resource-aware execution with circuit breakers
    @error_handler.with_graceful_degradation(sequential_fallback)
    def handle_resource_constraints(self):
        """Advanced graceful degradation."""
        # Monitor system resources
        if self.performance_analyzer.detect_resource_exhaustion():
            # Automatically reduce parallelism
            self.reduce_concurrent_tasks()

        # Circuit breaker for disk space
        if self.disk_circuit_breaker.is_open():
            self.cleanup_temporary_files()

        # Memory pressure handling
        if self.memory_monitor.pressure_detected():
            self.switch_to_sequential_execution()

    def handle_task_failure(self, task_id: str, error: Exception) -> None:
        """Enhanced failure isolation with comprehensive error context tracking."""
        error_context = ErrorContext(
            error=error,
            task_id=task_id,
            phase="parallel_execution",
            system_state=self.get_system_state(),
            recovery_suggestions=self.generate_recovery_plan(error)
        )

        # Isolate failure with shared error handling
        self.error_handler.handle_error(error_context)

        # Clean up with state preservation
        self.cleanup_failed_task(task_id, preserve_state=True)

        # Continue with remaining tasks
        self.continue_with_healthy_tasks()


class OrchestrationRecoveryManager:
    """Multi-level recovery with backup/restore."""
    
    def __init__(self):
        self.recovery_manager = RecoveryManager()
        self.backup_restore = StateBackupRestore()

    def handle_critical_failure(self, orchestration_id: str):
        """Handle critical failure with comprehensive recovery."""
        # Immediate damage control
        self.stop_all_parallel_executions()

        # Restore from last known good state
        last_checkpoint = self.backup_restore.get_latest_backup(orchestration_id)
        self.recovery_manager.restore_from_checkpoint(last_checkpoint)

        # Generate comprehensive failure report
        failure_report = self.generate_failure_analysis(orchestration_id)
        self.github_manager.create_failure_issue(failure_report)


# Exception classes for workflow compliance
class WorkflowComplianceError(Exception):
    """Base exception for workflow compliance violations."""
    pass

class InvalidExecutionMethodError(WorkflowComplianceError):
    """Task does not use proper WorkflowManager execution."""
    pass

class IncompleteWorkflowError(WorkflowComplianceError):
    """Task is missing required workflow phases."""
    pass

class DirectExecutionError(WorkflowComplianceError):
    """Task attempts direct execution bypassing WorkflowManager."""
    pass

class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open, preventing execution."""
    pass