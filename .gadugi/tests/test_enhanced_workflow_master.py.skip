#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced WorkflowMaster

Tests all aspects of the enhanced WorkflowMaster including:
- Container execution integration
- Autonomous decision making
- State management and recovery
- TeamCoach integration
- Performance monitoring
"""

import asyncio
import json
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any, List

# Import the modules under test
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from .claude.agents.workflow_master_enhanced import (
        EnhancedWorkflowMaster, WorkflowState, TaskInfo, WorkflowDecision
    )
    from .claude.agents.workflow_master_teamcoach_integration import (
        TeamCoachIntegration, PerformanceMetrics, WorkflowOptimization, OptimizationStrategy
    )
except ImportError:
    # For running tests directly
    sys.path.append(str(Path(__file__).parent.parent / '.claude' / 'agents'))
    from workflow_master_enhanced import (
        EnhancedWorkflowMaster, WorkflowState, TaskInfo, WorkflowDecision
    )
    from workflow_master_teamcoach_integration import (
        TeamCoachIntegration, PerformanceMetrics, WorkflowOptimization, OptimizationStrategy
    )


class TestEnhancedWorkflowMaster(unittest.TestCase):
    """Test suite for Enhanced WorkflowMaster."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test state
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create test directory structure
        (Path(self.temp_dir) / '.github' / 'workflow-states').mkdir(parents=True, exist_ok=True)
        
        # Mock container executor to avoid Docker dependency
        self.mock_container_executor = Mock()
        self.mock_container_executor.execute_python_code.return_value = {
            'success': True,
            'exit_code': 0,
            'stdout': 'Test execution successful',
            'stderr': '',
            'execution_time': 1.0
        }
        self.mock_container_executor.execute_command.return_value = {
            'success': True,
            'exit_code': 0,
            'stdout': 'Command executed successfully',
            'stderr': '',
            'execution_time': 0.5
        }
        
        # Mock GitHub operations
        self.mock_github_ops = Mock()
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        self.mock_github_ops.create_issue.return_value = mock_issue
        
        mock_pr = Mock()
        mock_pr.number = 456
        mock_pr.html_url = "https://github.com/test/repo/pull/456"
        self.mock_github_ops.create_pull_request.return_value = mock_pr
        
        # Create enhanced workflow master with mocked dependencies
        with patch('workflow_master_enhanced.AgentContainerExecutor') as mock_executor_class, \
             patch('workflow_master_enhanced.GitHubOperations') as mock_github_class:
            
            mock_executor_class.return_value = self.mock_container_executor
            mock_github_class.return_value = self.mock_github_ops
            
            self.workflow_master = EnhancedWorkflowMaster({
                'autonomous_mode': True,
                'security_policy': 'testing'
            })
    
    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_task_id_generation(self):
        """Test unique task ID generation."""
        task_ids = set()
        for _ in range(100):
            task_id = self.workflow_master.generate_task_id()
            self.assertNotIn(task_id, task_ids, "Task ID should be unique")
            task_ids.add(task_id)
            
            # Verify format: task-YYYYMMDD-HHMMSS-XXXX
            parts = task_id.split('-')
            self.assertEqual(len(parts), 4)
            self.assertEqual(parts[0], 'task')
            self.assertEqual(len(parts[1]), 8)  # YYYYMMDD
            self.assertEqual(len(parts[2]), 6)   # HHMMSS
            self.assertEqual(len(parts[3]), 8)   # 4-byte hex = 8 chars
    
    def test_workflow_initialization(self):
        """Test workflow initialization."""
        prompt_file = "/test/prompt.md"
        workflow = self.workflow_master.initialize_workflow(prompt_file)
        
        self.assertIsInstance(workflow, WorkflowState)
        self.assertEqual(workflow.prompt_file, prompt_file)
        self.assertIsNotNone(workflow.task_id)
        self.assertEqual(len(workflow.tasks), 9)  # Should have 9 predefined tasks
        self.assertEqual(workflow.status, "active")
        
        # Verify tasks are properly configured
        task_names = [task.name for task in workflow.tasks]
        expected_tasks = [
            "setup", "issue_creation", "branch_management", "research_planning",
            "implementation", "testing", "documentation", "pull_request", "code_review"
        ]
        self.assertEqual(task_names, expected_tasks)
    
    def test_workflow_state_persistence(self):
        """Test workflow state saving and loading."""
        workflow = self.workflow_master.initialize_workflow("/test/prompt.md")
        workflow.issue_number = 123
        workflow.pr_number = 456
        
        # Save state
        self.workflow_master.save_workflow_state(workflow)
        
        # Verify state file exists
        state_file = Path(f".github/workflow-states/{workflow.task_id}/state.json")
        self.assertTrue(state_file.exists())
        
        # Verify state content
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        self.assertEqual(state_data['task_id'], workflow.task_id)
        self.assertEqual(state_data['issue_number'], 123)
        self.assertEqual(state_data['pr_number'], 456)
        
        # Test deserialization
        loaded_workflow = self.workflow_master.deserialize_workflow_state(state_data)
        self.assertEqual(loaded_workflow.task_id, workflow.task_id)
        self.assertEqual(loaded_workflow.issue_number, 123)
        self.assertEqual(loaded_workflow.pr_number, 456)
    
    def test_autonomous_decision_making(self):
        """Test autonomous decision making logic."""
        workflow = self.workflow_master.initialize_workflow()
        
        # Test high priority task with low retry count -> RETRY
        task = TaskInfo(
            id="test",
            name="test_task",
            description="Test task",
            phase="testing",
            priority="high",
            retry_count=1,
            max_retries=3,
            error_message="network timeout"
        )
        
        decision = self.workflow_master.make_autonomous_decision(task, workflow)
        self.assertEqual(decision, WorkflowDecision.RETRY)
        
        # Test low priority task with good workflow progress -> SKIP
        task.priority = "low"
        workflow.tasks = [
            TaskInfo(id=f"task_{i}", name=f"task_{i}", description="", phase="testing", status="completed")
            for i in range(8)
        ] + [task]  # 8 completed, 1 failed = 88% progress
        
        decision = self.workflow_master.make_autonomous_decision(task, workflow)
        self.assertEqual(decision, WorkflowDecision.SKIP)
        
        # Test high retry count -> ESCALATE
        task.retry_count = 5
        task.max_retries = 3
        decision = self.workflow_master.make_autonomous_decision(task, workflow)
        self.assertEqual(decision, WorkflowDecision.ESCALATE)
    
    def test_task_dependency_validation(self):
        """Test task dependency checking."""
        workflow = self.workflow_master.initialize_workflow()
        
        # Find tasks with dependencies
        dependent_task = next(task for task in workflow.tasks if task.dependencies)
        dependency_id = dependent_task.dependencies[0]
        dependency_task = next(task for task in workflow.tasks if task.id == dependency_id)
        
        # Dependencies not met initially
        self.assertFalse(
            self.workflow_master.are_dependencies_met(dependent_task, workflow.tasks)
        )
        
        # Complete dependency
        dependency_task.status = "completed"
        
        # Dependencies should now be met
        self.assertTrue(
            self.workflow_master.are_dependencies_met(dependent_task, workflow.tasks)
        )
    
    def test_container_execution_integration(self):
        """Test container execution integration."""
        workflow = self.workflow_master.initialize_workflow()
        task = workflow.tasks[0]  # Setup task
        
        # Execute task
        success = self.workflow_master.execute_task(task, workflow)
        
        # Verify container execution was called
        self.mock_container_executor.execute_python_code.assert_called()
        
        # Verify execution statistics updated
        self.assertGreater(self.workflow_master.execution_stats['container_executions'], 0)
        
        # Verify task status updated
        self.assertTrue(success)
    
    def test_github_integration(self):
        """Test GitHub operations integration."""
        workflow = self.workflow_master.initialize_workflow()
        
        # Test issue creation task
        issue_task = next(task for task in workflow.tasks if task.name == "issue_creation")
        success = self.workflow_master.execute_task(issue_task, workflow)
        
        # Verify GitHub issue creation was called
        self.mock_github_ops.create_issue.assert_called()
        self.assertTrue(success)
        self.assertEqual(workflow.issue_number, 123)
        
        # Test PR creation task
        pr_task = next(task for task in workflow.tasks if task.name == "pull_request")
        success = self.workflow_master.execute_task(pr_task, workflow)
        
        # Verify GitHub PR creation was called
        self.mock_github_ops.create_pull_request.assert_called()
        self.assertTrue(success)
        self.assertEqual(workflow.pr_number, 456)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        workflow = self.workflow_master.initialize_workflow()
        
        # Simulate container execution failure
        self.mock_container_executor.execute_python_code.return_value = {
            'success': False,
            'exit_code': 1,
            'stdout': '',
            'stderr': 'Container execution failed',
            'execution_time': 0.1
        }
        
        task = workflow.tasks[0]  # Setup task
        success = self.workflow_master.execute_task(task, workflow)
        
        # Task should fail initially
        self.assertFalse(success)
        
        # Verify autonomous decision is made
        decision = self.workflow_master.make_autonomous_decision(task, workflow)
        self.assertIn(decision, [WorkflowDecision.RETRY, WorkflowDecision.ESCALATE])
    
    def test_orphaned_workflow_detection(self):
        """Test detection and resumption of orphaned workflows."""
        # Create an orphaned workflow state
        orphaned_workflow = self.workflow_master.initialize_workflow("/test/orphaned.md")
        orphaned_workflow.status = "active"
        orphaned_workflow.updated_at = datetime.now() - timedelta(hours=1)  # Recent
        self.workflow_master.save_workflow_state(orphaned_workflow)
        
        # Detect orphaned workflows
        orphaned = self.workflow_master.detect_orphaned_workflows()
        self.assertEqual(len(orphaned), 1)
        self.assertEqual(orphaned[0].task_id, orphaned_workflow.task_id)
        
        # Test resumption decision
        should_resume = self.workflow_master.should_resume_workflow(orphaned[0])
        self.assertTrue(should_resume)  # Recent workflow should be resumed
        
        # Test resumption
        resumed_workflow = self.workflow_master.resume_workflow(orphaned_workflow.task_id)
        self.assertEqual(resumed_workflow.task_id, orphaned_workflow.task_id)
    
    def test_execution_statistics(self):
        """Test execution statistics collection."""
        workflow = self.workflow_master.initialize_workflow()
        
        # Execute a few tasks
        for task in workflow.tasks[:3]:
            if not task.dependencies:  # Only execute tasks without dependencies
                self.workflow_master.execute_task(task, workflow)
        
        # Get statistics
        stats = self.workflow_master.get_execution_statistics()
        
        # Verify statistics structure
        required_keys = [
            'total_tasks', 'completed_tasks', 'failed_tasks',
            'autonomous_decisions', 'container_executions', 'runtime_seconds'
        ]
        for key in required_keys:
            self.assertIn(key, stats)
        
        # Verify statistics values
        self.assertGreaterEqual(stats['total_tasks'], 1)
        self.assertGreaterEqual(stats['container_executions'], 1)
        self.assertGreaterEqual(stats['runtime_seconds'], 0)


class TestTeamCoachIntegration(unittest.TestCase):
    """Test suite for TeamCoach integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.workflow_master = Mock()
        self.teamcoach = TeamCoachIntegration(self.workflow_master, {
            'optimization_enabled': True,
            'auto_apply_optimizations': False
        })
        
        # Create test workflow
        self.test_workflow = WorkflowState(
            task_id="test-workflow-123",
            prompt_file="/test/prompt.md",
            tasks=[
                TaskInfo(id="1", name="task1", description="Test task 1", phase="testing", status="completed"),
                TaskInfo(id="2", name="task2", description="Test task 2", phase="testing", status="completed"),
                TaskInfo(id="3", name="task3", description="Test task 3", phase="testing", status="failed", retry_count=2),
                TaskInfo(id="4", name="task4", description="Test task 4", phase="testing", status="pending")
            ]
        )
    
    def test_performance_analysis(self):
        """Test workflow performance analysis."""
        metrics = self.teamcoach.analyze_workflow_performance(self.test_workflow)
        
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertEqual(metrics.task_completion_rate, 0.5)  # 2/4 completed
        self.assertEqual(metrics.error_rate, 0.25)  # 1/4 failed
        self.assertGreaterEqual(metrics.quality_score, 0.0)
        self.assertLessEqual(metrics.quality_score, 1.0)
    
    def test_optimization_recommendations(self):
        """Test generation of optimization recommendations."""
        # Create metrics with poor performance
        metrics = PerformanceMetrics(
            task_completion_rate=0.6,  # Below 0.8 threshold
            average_task_duration=400,  # Above 300s threshold
            error_rate=0.15,  # Above 0.1 threshold
            retry_rate=0.1,
            autonomous_decision_rate=0.2,
            container_execution_success_rate=0.8,
            resource_utilization={'cpu': 0.9},  # Above 0.8 threshold
            quality_score=0.7,  # Below 0.8 threshold
            user_satisfaction=0.6,
            improvement_trends={}
        )
        
        recommendations = self.teamcoach.generate_optimization_recommendations(
            self.test_workflow, metrics
        )
        
        # Should generate multiple recommendations
        self.assertGreater(len(recommendations), 3)
        
        # Verify recommendation structure
        for rec in recommendations:
            self.assertIsInstance(rec, WorkflowOptimization)
            self.assertIn(rec.strategy, OptimizationStrategy)
            self.assertGreater(rec.expected_improvement, 0)
            self.assertGreater(rec.confidence, 0)
            self.assertIn(rec.priority, ['high', 'medium', 'low'])
    
    def test_optimization_application(self):
        """Test application of optimization recommendations."""
        optimization = WorkflowOptimization(
            strategy=OptimizationStrategy.RELIABILITY,
            task_id="reliability_test",
            recommendation="Increase retry limits",
            expected_improvement=0.3,
            confidence=0.8,
            implementation_effort="low",
            priority="high",
            reasoning="Test optimization",
            metrics_impact={'error_rate': -0.3}
        )
        
        success = self.teamcoach.apply_optimization(optimization, self.test_workflow)
        self.assertTrue(success)
        
        # Verify optimization was recorded
        self.assertEqual(len(self.teamcoach.optimization_history), 1)
        self.assertEqual(
            self.teamcoach.optimization_history[0]['optimization']['strategy'],
            OptimizationStrategy.RELIABILITY.value
        )
    
    def test_continuous_learning(self):
        """Test continuous learning from optimization results."""
        metrics_before = PerformanceMetrics(
            task_completion_rate=0.6,
            average_task_duration=300,
            error_rate=0.2,
            retry_rate=0.1,
            autonomous_decision_rate=0.1,
            container_execution_success_rate=0.8,
            resource_utilization={},
            quality_score=0.6,
            user_satisfaction=0.5,
            improvement_trends={}
        )
        
        metrics_after = PerformanceMetrics(
            task_completion_rate=0.8,
            average_task_duration=250,
            error_rate=0.1,
            retry_rate=0.05,
            autonomous_decision_rate=0.15,
            container_execution_success_rate=0.9,
            resource_utilization={},
            quality_score=0.8,
            user_satisfaction=0.7,
            improvement_trends={}
        )
        
        # Add some successful optimizations to history
        self.teamcoach.optimization_history = [
            {
                'optimization': {'strategy': 'performance'},
                'result': 'success',
                'timestamp': datetime.now()
            }
        ]
        
        self.teamcoach.continuous_learning(self.test_workflow, metrics_before, metrics_after)
        
        # Verify learning data was updated
        workflow_type = self.teamcoach._categorize_workflow(self.test_workflow)
        self.assertIn(workflow_type, self.teamcoach.learning_data)
        
        learning_data = self.teamcoach.learning_data[workflow_type]
        self.assertGreater(len(learning_data['performance_patterns']), 0)
    
    def test_optimization_insights(self):
        """Test generation of optimization insights."""
        # Add some test data
        self.teamcoach.optimization_history = [
            {
                'optimization': {
                    'strategy': 'performance',
                    'expected_improvement': 0.3
                },
                'result': 'success',
                'timestamp': datetime.now()
            },
            {
                'optimization': {
                    'strategy': 'reliability',
                    'expected_improvement': 0.2
                },
                'result': 'success',
                'timestamp': datetime.now()
            }
        ]
        
        insights = self.teamcoach.get_optimization_insights()
        
        # Verify insights structure
        required_keys = [
            'total_optimizations_applied',
            'successful_optimizations',
            'most_effective_strategies',
            'learning_data_summary',
            'recommendations_for_future'
        ]
        for key in required_keys:
            self.assertIn(key, insights)
        
        self.assertEqual(insights['total_optimizations_applied'], 2)
        self.assertEqual(insights['successful_optimizations'], 2)
    
    def test_state_persistence(self):
        """Test saving and loading of integration state."""
        # Add some test data
        self.teamcoach.optimization_history = [
            {
                'optimization': {'strategy': 'performance'},
                'result': 'success',
                'timestamp': datetime.now()
            }
        ]
        
        # Save state
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            state_file = f.name
        
        self.teamcoach.save_integration_state(state_file)
        
        # Create new instance and load state
        new_teamcoach = TeamCoachIntegration(self.workflow_master)
        new_teamcoach.load_integration_state(state_file)
        
        # Verify state was restored
        self.assertEqual(
            len(new_teamcoach.optimization_history),
            len(self.teamcoach.optimization_history)
        )
        
        # Cleanup
        os.unlink(state_file)


class TestWorkflowIntegration(unittest.TestCase):
    """Integration tests for complete workflow execution."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create test directory structure
        (Path(self.temp_dir) / '.github' / 'workflow-states').mkdir(parents=True, exist_ok=True)
        
        # Mock all external dependencies
        self.mock_container_executor = Mock()
        self.mock_container_executor.execute_python_code.return_value = {'success': True, 'exit_code': 0, 'stdout': 'OK', 'stderr': '', 'execution_time': 1.0}
        self.mock_container_executor.execute_command.return_value = {'success': True, 'exit_code': 0, 'stdout': 'OK', 'stderr': '', 'execution_time': 1.0}
        
        self.mock_github_ops = Mock()
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        self.mock_github_ops.create_issue.return_value = mock_issue
        
        mock_pr = Mock()
        mock_pr.number = 456
        mock_pr.html_url = "https://github.com/test/repo/pull/456"
        self.mock_github_ops.create_pull_request.return_value = mock_pr
    
    def tearDown(self):
        """Clean up integration test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow_execution(self):
        """Test complete workflow execution from start to finish."""
        with patch('workflow_master_enhanced.AgentContainerExecutor') as mock_executor_class, \
             patch('workflow_master_enhanced.GitHubOperations') as mock_github_class:
            
            mock_executor_class.return_value = self.mock_container_executor
            mock_github_class.return_value = self.mock_github_ops
            
            # Create workflow master
            workflow_master = EnhancedWorkflowMaster({
                'autonomous_mode': True,
                'security_policy': 'testing'
            })
            
            # Initialize workflow
            workflow = workflow_master.initialize_workflow("/test/prompt.md")
            
            # Execute workflow
            success = workflow_master.execute_workflow(workflow)
            
            # Verify workflow completed successfully
            self.assertTrue(success)
            self.assertEqual(workflow.status, "completed")
            
            # Verify all high-priority tasks completed
            high_priority_tasks = [t for t in workflow.tasks if t.priority == "high"]
            completed_high_priority = [t for t in high_priority_tasks if t.status == "completed"]
            self.assertGreaterEqual(len(completed_high_priority), len(high_priority_tasks) * 0.8)
            
            # Verify GitHub integration occurred
            self.mock_github_ops.create_issue.assert_called()
            self.mock_github_ops.create_pull_request.assert_called()
            
            # Verify container execution occurred
            self.assertGreater(self.mock_container_executor.execute_python_code.call_count, 0)
    
    def test_workflow_with_teamcoach_optimization(self):
        """Test workflow execution with TeamCoach optimization."""
        with patch('workflow_master_enhanced.AgentContainerExecutor') as mock_executor_class, \
             patch('workflow_master_enhanced.GitHubOperations') as mock_github_class:
            
            mock_executor_class.return_value = self.mock_container_executor
            mock_github_class.return_value = self.mock_github_ops
            
            # Create workflow master with TeamCoach integration
            workflow_master = EnhancedWorkflowMaster({'autonomous_mode': True})
            teamcoach = TeamCoachIntegration(workflow_master, {'auto_apply_optimizations': True})
            
            # Initialize and analyze workflow
            workflow = workflow_master.initialize_workflow("/test/prompt.md")
            
            # Analyze performance and generate optimizations
            metrics = teamcoach.analyze_workflow_performance(workflow)
            recommendations = teamcoach.generate_optimization_recommendations(workflow, metrics)
            
            # Apply optimizations
            applied_count = 0
            for recommendation in recommendations[:3]:  # Apply first 3
                if teamcoach.apply_optimization(recommendation, workflow):
                    applied_count += 1
            
            # Verify optimizations were applied
            self.assertGreater(applied_count, 0)
            self.assertGreater(len(teamcoach.optimization_history), 0)
            
            # Execute optimized workflow
            success = workflow_master.execute_workflow(workflow)
            self.assertTrue(success)


class TestWorkflowRecovery(unittest.TestCase):
    """Test workflow recovery and error handling."""
    
    def setUp(self):
        """Set up recovery test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        (Path(self.temp_dir) / '.github' / 'workflow-states').mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up recovery test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_workflow_interruption_and_recovery(self):
        """Test workflow interruption and recovery."""
        with patch('workflow_master_enhanced.AgentContainerExecutor') as mock_executor_class, \
             patch('workflow_master_enhanced.GitHubOperations') as mock_github_class:
            
            # Mock successful container execution
            mock_container_executor = Mock()
            mock_container_executor.execute_python_code.return_value = {
                'success': True, 'exit_code': 0, 'stdout': 'OK', 'stderr': '', 'execution_time': 1.0
            }
            mock_executor_class.return_value = mock_container_executor
            
            # Mock GitHub operations
            mock_github_ops = Mock()
            mock_issue = Mock()
            mock_issue.number = 123
            mock_issue.html_url = "https://github.com/test/repo/issues/123"
            mock_github_ops.create_issue.return_value = mock_issue
            mock_github_class.return_value = mock_github_ops
            
            # Create first workflow master instance
            workflow_master1 = EnhancedWorkflowMaster({'autonomous_mode': True})
            workflow1 = workflow_master1.initialize_workflow("/test/prompt.md")
            
            # Partially execute workflow (complete first 3 tasks)
            for i, task in enumerate(workflow1.tasks[:3]):
                if not task.dependencies:
                    workflow_master1.execute_task(task, workflow1)
                    task.status = "completed"
            
            workflow1.status = "active"  # Still active
            workflow_master1.save_workflow_state(workflow1)
            
            # Create second workflow master instance (simulating restart)
            workflow_master2 = EnhancedWorkflowMaster({'autonomous_mode': True})
            
            # Detect and resume orphaned workflow
            orphaned = workflow_master2.detect_orphaned_workflows()
            self.assertEqual(len(orphaned), 1)
            self.assertEqual(orphaned[0].task_id, workflow1.task_id)
            
            # Resume workflow
            resumed_workflow = workflow_master2.resume_workflow(workflow1.task_id)
            self.assertEqual(resumed_workflow.task_id, workflow1.task_id)
            
            # Verify partial progress is preserved
            completed_tasks = [t for t in resumed_workflow.tasks if t.status == "completed"]
            self.assertGreater(len(completed_tasks), 0)


def run_performance_benchmarks():
    """Run performance benchmarks for enhanced WorkflowMaster."""
    print("Running Enhanced WorkflowMaster Performance Benchmarks...")
    
    # Mock dependencies for benchmarking
    mock_container_executor = Mock()
    mock_container_executor.execute_python_code.return_value = {
        'success': True, 'exit_code': 0, 'stdout': 'OK', 'stderr': '', 'execution_time': 0.1
    }
    
    mock_github_ops = Mock()
    mock_issue = Mock()
    mock_issue.number = 123
    mock_issue.html_url = "https://github.com/test/repo/issues/123"
    mock_github_ops.create_issue.return_value = mock_issue
    
    with patch('workflow_master_enhanced.AgentContainerExecutor') as mock_executor_class, \
         patch('workflow_master_enhanced.GitHubOperations') as mock_github_class:
        
        mock_executor_class.return_value = mock_container_executor
        mock_github_class.return_value = mock_github_ops
        
        # Benchmark workflow initialization
        start_time = time.time()
        workflow_master = EnhancedWorkflowMaster({'autonomous_mode': True})
        
        workflows = []
        for i in range(10):
            workflow = workflow_master.initialize_workflow(f"/test/prompt_{i}.md")
            workflows.append(workflow)
        
        init_time = time.time() - start_time
        print(f"Workflow Initialization (10 workflows): {init_time:.3f}s")
        
        # Benchmark task execution
        start_time = time.time()
        for workflow in workflows[:3]:  # Test first 3 workflows
            for task in workflow.tasks[:3]:  # Test first 3 tasks
                if not task.dependencies:
                    workflow_master.execute_task(task, workflow)
        
        exec_time = time.time() - start_time
        print(f"Task Execution (9 tasks): {exec_time:.3f}s")
        
        # Benchmark state persistence
        start_time = time.time()
        for workflow in workflows:
            workflow_master.save_workflow_state(workflow)
        
        persist_time = time.time() - start_time
        print(f"State Persistence (10 workflows): {persist_time:.3f}s")
        
        # Get execution statistics
        stats = workflow_master.get_execution_statistics()
        print(f"Execution Statistics: {stats}")


if __name__ == '__main__':
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    # Run performance benchmarks
    import time
    print("\n" + "="*50)
    run_performance_benchmarks()