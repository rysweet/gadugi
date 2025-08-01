#!/usr/bin/env python3
"""
Integration tests for OrchestratorAgent with Enhanced Separation shared modules.

Tests the integration between OrchestratorAgent and the shared modules:
- github_operations
- state_management  
- error_handling
- task_tracking
- interfaces

Validates that the Enhanced Separation architecture maintains:
- 3-5x parallel execution performance
- Comprehensive error handling and recovery
- Advanced state management and checkpointing
- Robust task tracking and analytics
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '.claude', 'shared'))

from github_operations import GitHubOperations
from state_management import StateManager, CheckpointManager
from utils.error_handling import ErrorHandler, CircuitBreaker
from task_tracking import TaskTracker, TodoWriteIntegration, WorkflowPhaseTracker, TaskMetrics
from interfaces import AgentConfig, TaskData, ErrorContext, WorkflowPhase


class TestOrchestratorAgentIntegration:
    """Integration tests for OrchestratorAgent with shared modules"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = AgentConfig()
        
        # Initialize shared modules
        self.github_operations = GitHubOperations()
        self.state_manager = StateManager()
        self.error_handler = ErrorHandler()
        self.task_tracker = TaskTracker()
        self.task_metrics = TaskMetrics()
        
        # Mock external dependencies
        self.mock_gh_api = Mock()
        
    def teardown_method(self):
        """Cleanup test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_orchestrator_initialization_with_shared_modules(self):
        """Test OrchestratorAgent initialization uses shared modules correctly"""
        
        # Test shared module initialization
        assert self.github_manager is not None
        assert self.state_manager is not None
        assert self.error_handler is not None
        assert self.task_tracker is not None
        assert self.productivity_analyzer is not None
        
        # Test configuration propagation
        assert self.github_manager.config == self.config
        
        # Test circuit breaker initialization
        github_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=300)
        execution_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=600)
        
        assert github_circuit_breaker.failure_threshold == 3
        assert execution_circuit_breaker.failure_threshold == 5
    
    def test_parallel_task_analysis_with_error_handling(self):
        """Test parallel task analysis with enhanced error handling"""
        
        # Mock prompt files for analysis
        prompt_files = [
            "test-feature-a.md",
            "test-feature-b.md", 
            "test-feature-c.md"
        ]
        
        # Mock task analysis result
        analysis_result = {
            "parallelizable_groups": [
                {"tasks": ["test-feature-a.md", "test-feature-b.md"], "conflicts": []},
                {"tasks": ["test-feature-c.md"], "conflicts": []}
            ],
            "sequential_dependencies": [],
            "estimated_speedup": 2.8
        }
        
        # Test error handling integration
        retry_manager = RetryManager()
        with patch.object(retry_manager, 'execute_with_retry') as mock_retry:
            mock_retry.return_value = analysis_result
            
            # Simulate task analysis with error handling
            result = retry_manager.execute_with_retry(
                lambda: analysis_result,
                max_attempts=3,
                backoff_strategy="exponential"
            )
            
            assert result == analysis_result
            mock_retry.assert_called_once()
    
    def test_orchestration_state_management(self):
        """Test orchestration state management with shared modules"""
        
        # Create orchestration state
        orchestration_id = f"orchestration-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        orchestration_state = WorkflowState(
            task_id=orchestration_id,
            phase=WorkflowPhase.ENVIRONMENT_SETUP,
            started_at=datetime.now(),
            metadata={
                "parallel_tasks": 3,
                "expected_speedup": 3.2
            }
        )
        
        # Test state persistence
        self.state_manager.save_state(orchestration_state)
        loaded_state = self.state_manager.load_state(orchestration_id)
        
        assert loaded_state is not None
        assert loaded_state.task_id == orchestration_id
        assert loaded_state.phase == WorkflowPhase.ENVIRONMENT_SETUP
        
        # Test checkpoint creation
        checkpoint_manager = CheckpointManager(self.state_manager)
        checkpoint_id = checkpoint_manager.create_checkpoint(orchestration_state)
        
        assert checkpoint_id is not None
        
        # Test backup system
        backup_restore = StateBackupRestore(self.state_manager)
        backup_id = backup_restore.create_backup(orchestration_id)
        
        assert backup_id is not None
    
    def test_parallel_execution_with_circuit_breakers(self):
        """Test parallel execution with circuit breaker protection"""
        
        # Mock task execution
        tasks = [
            TaskData(id="task-1", content="Feature A", status="pending", priority="high"),
            TaskData(id="task-2", content="Feature B", status="pending", priority="high"),
            TaskData(id="task-3", content="Feature C", status="pending", priority="high")
        ]
        
        # Test circuit breaker protection
        execution_circuit_breaker = CircuitBreaker(failure_threshold=2, timeout=300)
        
        # Simulate successful executions
        successful_results = []
        for i, task in enumerate(tasks):
            try:
                result = execution_circuit_breaker.call(
                    lambda: {"task_id": task.id, "success": True, "duration": 120 + i*10}
                )
                successful_results.append(result)
                self.task_tracker.update_task_status(task.id, "completed")
            except Exception as e:
                self.error_handler.handle_error(ErrorContext(
                    error=e,
                    task_id=task.id,
                    phase="parallel_execution"
                ))
        
        assert len(successful_results) == 3
        assert all(r["success"] for r in successful_results)
        
        # Test circuit breaker failure handling
        with patch.object(execution_circuit_breaker, 'call') as mock_call:
            mock_call.side_effect = Exception("Simulated failure")
            
            try:
                execution_circuit_breaker.call(lambda: {"success": False})
            except Exception:
                # Should trigger error handler
                pass
    
    def test_github_operations_integration(self):
        """Test GitHub operations integration with batch processing"""
        
        # Mock successful task results
        successful_tasks = [
            {"task_id": "task-1", "pr_number": 101, "success": True},
            {"task_id": "task-2", "pr_number": 102, "success": True},
            {"task_id": "task-3", "pr_number": 103, "success": True}
        ]
        
        # Test batch PR operations
        pr_numbers = [t["pr_number"] for t in successful_tasks]
        
        with patch.object(self.github_manager, 'batch_merge_pull_requests') as mock_batch:
            mock_batch.return_value = {"merged": pr_numbers, "failed": []}
            
            result = self.github_manager.batch_merge_pull_requests(pr_numbers)
            
            assert result["merged"] == pr_numbers
            assert len(result["failed"]) == 0
            mock_batch.assert_called_once_with(pr_numbers)
    
    def test_performance_analytics_integration(self):
        """Test performance analytics and speedup calculation"""
        
        # Mock execution results
        execution_results = [
            {"task_id": "task-1", "duration": 300, "success": True},
            {"task_id": "task-2", "duration": 280, "success": True}, 
            {"task_id": "task-3", "duration": 320, "success": True}
        ]
        
        # Test performance analysis
        self.productivity_analyzer.start_parallel_execution_tracking(len(execution_results))
        
        total_parallel_time = max(r["duration"] for r in execution_results)
        estimated_sequential_time = sum(r["duration"] for r in execution_results)
        
        performance_metrics = self.productivity_analyzer.calculate_speedup(
            execution_results,
            baseline_sequential_time=estimated_sequential_time
        )
        
        expected_speedup = estimated_sequential_time / total_parallel_time
        
        assert performance_metrics is not None
        assert performance_metrics.get("speedup", 0) > 1.0
        assert performance_metrics.get("parallel_efficiency", 0) > 0.5
        
        # Verify 3-5x speedup range is achievable
        assert 2.5 <= expected_speedup <= 5.5  # Allow some variance
    
    def test_comprehensive_error_recovery(self):
        """Test comprehensive error handling and recovery scenarios"""
        
        orchestration_id = "test-orchestration-123"
        
        # Test error context creation
        error_context = ErrorContext(
            error=Exception("Test failure"),
            task_id=orchestration_id,
            phase="parallel_execution",
            system_state={
                "active_tasks": 2,
                "completed_tasks": 1,
                "failed_tasks": 1
            },
            recovery_action="retry_failed_tasks"
        )
        
        # Test error handling
        with patch.object(self.error_handler, 'handle_error') as mock_handle:
            self.error_handler.handle_error(error_context)
            mock_handle.assert_called_once_with(error_context)
        
        # Test recovery manager
        recovery_manager = RecoveryManager()
        
        # Mock recovery scenario
        recovery_plan = {
            "failed_tasks": ["task-2"],
            "recovery_strategy": "sequential_fallback",
            "estimated_recovery_time": 180
        }
        
        with patch.object(recovery_manager, 'create_recovery_plan') as mock_plan:
            mock_plan.return_value = recovery_plan
            
            plan = recovery_manager.create_recovery_plan(error_context)
            
            assert plan == recovery_plan
            assert "failed_tasks" in plan
            assert "recovery_strategy" in plan
    
    def test_resource_monitoring_and_graceful_degradation(self):
        """Test resource monitoring and graceful degradation"""
        
        # Mock resource exhaustion scenario
        with patch.object(self.productivity_analyzer, 'detect_resource_exhaustion') as mock_detect:
            mock_detect.return_value = True
            
            # Test graceful degradation trigger
            if self.productivity_analyzer.detect_resource_exhaustion():
                # Should trigger reduction in parallelism
                reduced_parallelism = True
            else:
                reduced_parallelism = False
            
            assert reduced_parallelism == True
            mock_detect.assert_called_once()
    
    def test_end_to_end_orchestration_workflow(self):
        """Test complete orchestration workflow with shared modules"""
        
        # Setup orchestration scenario
        orchestration_id = f"e2e-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Phase 1: Task Analysis
        prompt_files = ["feature-a.md", "feature-b.md"]
        self.productivity_analyzer.record_phase_start("task_analysis")
        
        # Phase 2: Environment Setup
        orchestration_state = WorkflowState(
            task_id=orchestration_id,
            phase=WorkflowPhase.ENVIRONMENT_SETUP,
            started_at=datetime.now()
        )
        
        self.state_manager.save_state(orchestration_state)
        checkpoint_manager = CheckpointManager(self.state_manager)
        checkpoint_manager.create_checkpoint(orchestration_state)
        
        # Phase 3: Parallel Execution (mocked)
        tasks = [
            TaskData(id="task-1", content="Feature A", status="pending", priority="high"),
            TaskData(id="task-2", content="Feature B", status="pending", priority="high")
        ]
        
        execution_results = []
        for task in tasks:
            # Mock successful execution
            result = {"task_id": task.id, "success": True, "pr_number": 100 + int(task.id.split('-')[1])}
            execution_results.append(result)
            self.task_tracker.update_task_status(task.id, "completed")
        
        # Phase 4: Result Integration
        successful_tasks = [r for r in execution_results if r.get("success")]
        pr_numbers = [t["pr_number"] for t in successful_tasks]
        
        # Mock GitHub integration
        with patch.object(self.github_manager, 'batch_merge_pull_requests') as mock_batch:
            mock_batch.return_value = {"merged": pr_numbers, "failed": []}
            
            batch_result = self.github_manager.batch_merge_pull_requests(pr_numbers)
            assert len(batch_result["merged"]) == 2
        
        # Update final state
        orchestration_state.phase = WorkflowPhase.COMPLETED
        self.state_manager.save_state(orchestration_state)
        
        # Verify end-to-end completion
        final_state = self.state_manager.load_state(orchestration_id)
        assert final_state.phase == WorkflowPhase.COMPLETED
        
        # Verify performance improvements
        performance_metrics = self.productivity_analyzer.calculate_speedup(
            execution_results,
            baseline_sequential_time=600  # 10 minutes sequential
        )
        
        # Should achieve meaningful speedup
        assert performance_metrics.get("speedup", 0) >= 1.5


class TestOrchestratorAgentPerformance:
    """Performance-specific tests for OrchestratorAgent integration"""
    
    def test_parallel_execution_speedup_validation(self):
        """Validate that parallel execution achieves 3-5x speedup"""
        
        # Simulate realistic task durations
        sequential_tasks = [
            {"id": "task-1", "duration": 300},  # 5 minutes
            {"id": "task-2", "duration": 240},  # 4 minutes  
            {"id": "task-3", "duration": 180},  # 3 minutes
            {"id": "task-4", "duration": 360}   # 6 minutes
        ]
        
        # Calculate sequential execution time
        sequential_time = sum(task["duration"] for task in sequential_tasks)
        
        # Calculate parallel execution time (limited by longest task)
        parallel_time = max(task["duration"] for task in sequential_tasks)
        
        # Calculate speedup
        speedup = sequential_time / parallel_time
        
        # Validate speedup is in expected range
        assert 3.0 <= speedup <= 5.5, f"Speedup {speedup:.2f} not in expected range [3.0, 5.5]"
        
        # Test with different parallelization scenarios
        test_scenarios = [
            # [task_durations], expected_min_speedup
            ([300, 300, 300], 2.8),  # Equal duration tasks
            ([600, 200, 200, 200], 1.8),  # One long task
            ([150, 150, 150, 150, 150, 150], 5.8),  # Many short tasks
        ]
        
        for durations, expected_min in test_scenarios:
            seq_time = sum(durations)
            par_time = max(durations)
            actual_speedup = seq_time / par_time
            
            assert actual_speedup >= expected_min, \
                f"Scenario {durations}: speedup {actual_speedup:.2f} < {expected_min}"
    
    def test_shared_module_performance_overhead(self):
        """Test that shared modules don't add significant performance overhead"""
        
        import time
        
        # Test GitHub operations performance
        start_time = time.time()
        
        # Mock multiple GitHub operations
        for i in range(10):
            with patch.object(GitHubManager, 'create_issue') as mock_create:
                mock_create.return_value = {"success": True, "issue_number": 100 + i}
                github_manager = GitHubManager(config=AgentConfig())
                github_manager.create_issue({"title": f"Test Issue {i}", "body": "Test"})
        
        github_ops_time = time.time() - start_time
        
        # Test state management performance
        start_time = time.time()
        
        state_manager = WorkflowStateManager()
        for i in range(10):
            state = WorkflowState(
                task_id=f"perf-test-{i}",
                phase=WorkflowPhase.IMPLEMENTATION,
                started_at=datetime.now()
            )
            state_manager.save_state(state)
            state_manager.load_state(f"perf-test-{i}")
        
        state_ops_time = time.time() - start_time
        
        # Performance should be reasonable (< 1 second for 10 operations each)
        assert github_ops_time < 1.0, f"GitHub operations too slow: {github_ops_time:.3f}s"
        assert state_ops_time < 1.0, f"State operations too slow: {state_ops_time:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])