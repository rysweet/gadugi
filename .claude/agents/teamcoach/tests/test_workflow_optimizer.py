"""
Tests for TeamCoach Phase 3: Workflow Optimizer
"""

import unittest
from datetime import datetime
from unittest.mock import patch

from ..phase3.workflow_optimizer import (
    WorkflowOptimizer,
    WorkflowMetrics,
    Bottleneck,
    BottleneckType,
    OptimizationType,
)


class TestWorkflowOptimizer(unittest.TestCase):
    """Test cases for the WorkflowOptimizer."""

    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = WorkflowOptimizer()

        # Sample workflow data
        self.workflow_data = {
            "id": "workflow_1",
            "name": "Data Processing Pipeline",
            "stages": ["ingest", "process", "analyze", "report"],
        }

        # Sample agent states
        self.agent_states = {
            "agent_1": {
                "status": "active",
                "current_task": "task_1",
                "skills": ["python", "data_analysis"],
                "resources": ["cpu_1", "memory_pool"],
            },
            "agent_2": {
                "status": "waiting",
                "current_task": "task_2",
                "skills": ["python", "ml"],
                "resources": ["gpu_1"],
            },
            "agent_3": {
                "status": "active",
                "current_task": "task_3",
                "skills": ["java", "reporting"],
                "resources": ["cpu_2"],
            },
        }

        # Sample task history
        base_time = datetime.utcnow().timestamp()
        self.task_history = [
            {
                "task_id": "task_1",
                "agent_id": "agent_1",
                "start_time": base_time,
                "end_time": base_time + 3600,  # 1 hour
                "duration": 3600,
                "wait_time": 600,  # 10 min wait
                "resources_used": ["cpu_1", "memory_pool"],
                "required_skills": ["python"],
                "dependencies": [],
            },
            {
                "task_id": "task_2",
                "agent_id": "agent_2",
                "start_time": base_time + 1800,
                "end_time": base_time + 5400,  # 1.5 hours total
                "duration": 3600,
                "wait_time": 1800,  # 30 min wait
                "resource_wait_time": 1200,  # 20 min resource wait
                "resources_used": ["gpu_1"],
                "required_skills": ["ml"],
                "dependencies": ["task_1"],
                "blocked_time": 900,  # 15 min blocked
            },
            {
                "task_id": "task_3",
                "agent_id": "agent_3",
                "start_time": base_time + 3600,
                "end_time": base_time + 7200,
                "duration": 3600,
                "wait_time": 300,
                "resources_used": ["cpu_2"],
                "required_skills": ["reporting"],
                "dependencies": ["task_2"],
                "is_rework": True,
                "rework_reason": "Quality issue",
            },
        ]

    def test_calculate_workflow_metrics(self):
        """Test workflow metrics calculation."""
        metrics = self.optimizer._calculate_workflow_metrics(
            self.workflow_data, self.agent_states, self.task_history
        )

        # Verify metrics structure
        self.assertIsInstance(metrics, WorkflowMetrics)
        self.assertGreater(metrics.total_duration, 0)
        self.assertGreater(metrics.active_time, 0)
        self.assertGreaterEqual(metrics.wait_time, 0)
        self.assertGreater(metrics.throughput, 0)

        # Verify efficiency ratio
        self.assertGreater(metrics.efficiency_ratio, 0)
        self.assertLessEqual(metrics.efficiency_ratio, 1.0)

        # Verify bottleneck impact
        self.assertGreaterEqual(metrics.bottleneck_impact, 0)
        self.assertLessEqual(metrics.bottleneck_impact, 1.0)

    def test_detect_resource_bottlenecks(self):
        """Test detection of resource bottlenecks."""
        # Add more tasks using same resource
        for i in range(5):
            self.task_history.append(
                {
                    "task_id": f"task_gpu_{i}",
                    "agent_id": "agent_2",
                    "start_time": datetime.utcnow().timestamp() + i * 3600,
                    "end_time": datetime.utcnow().timestamp() + (i + 1) * 3600,
                    "duration": 3600,
                    "resources_used": ["gpu_1"],
                    "resource_wait_time": 2400,  # 40 min wait
                    "required_skills": ["ml"],
                }
            )

        analysis = self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        # Find resource bottlenecks
        resource_bottlenecks = [
            b
            for b in analysis.bottlenecks
            if b.type == BottleneckType.RESOURCE_CONSTRAINT
        ]

        # Should detect GPU bottleneck
        self.assertGreater(len(resource_bottlenecks), 0)

        # Verify GPU is identified
        gpu_bottlenecks = [
            b for b in resource_bottlenecks if "gpu_1" in b.evidence.get("resource", "")
        ]
        self.assertGreater(len(gpu_bottlenecks), 0)

    def test_detect_skill_bottlenecks(self):
        """Test detection of skill gap bottlenecks."""
        # Add tasks requiring rare skills
        for i in range(4):
            self.task_history.append(
                {
                    "task_id": f"task_ml_{i}",
                    "agent_id": "agent_2",
                    "start_time": datetime.utcnow().timestamp() + i * 3600,
                    "duration": 3600,
                    "required_skills": ["deep_learning", "gpu_optimization"],
                    "skill_wait_time": 7200,  # 2 hour wait for skilled agent
                }
            )

        analysis = self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        # Find skill bottlenecks
        skill_bottlenecks = [
            b for b in analysis.bottlenecks if b.type == BottleneckType.SKILL_GAP
        ]

        # Should detect skill gaps
        self.assertGreater(len(skill_bottlenecks), 0)

        # Verify specific skills identified
        dl_bottlenecks = [
            b for b in skill_bottlenecks if "deep_learning" in b.description
        ]
        self.assertGreater(len(dl_bottlenecks), 0)

    def test_detect_dependency_bottlenecks(self):
        """Test detection of dependency chain bottlenecks."""
        # Create long dependency chain
        chain_tasks = []
        for i in range(10):
            chain_tasks.append(
                {
                    "task_id": f"chain_{i}",
                    "duration": 3600,
                    "dependencies": [f"chain_{i - 1}"] if i > 0 else [],
                    "start_time": datetime.utcnow().timestamp() + i * 3600,
                    "end_time": datetime.utcnow().timestamp() + (i + 1) * 3600,
                }
            )

        self.task_history.extend(chain_tasks)

        analysis = self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        # Find dependency bottlenecks
        dep_bottlenecks = [
            b for b in analysis.bottlenecks if b.type == BottleneckType.DEPENDENCY_CHAIN
        ]

        # Should detect long chain
        self.assertGreater(len(dep_bottlenecks), 0)

        # Verify critical path identified
        for b in dep_bottlenecks:
            self.assertIn("critical_path", b.evidence)
            self.assertGreater(len(b.evidence["critical_path"]), 5)

    def test_detect_process_bottlenecks(self):
        """Test detection of process inefficiency bottlenecks."""
        # Already have rework in task history
        analysis = self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        # Find process bottlenecks
        process_bottlenecks = [
            b
            for b in analysis.bottlenecks
            if b.type == BottleneckType.PROCESS_INEFFICIENCY
        ]

        # Should detect rework issue
        rework_bottlenecks = [
            b for b in process_bottlenecks if "rework" in b.description.lower()
        ]
        self.assertGreater(len(rework_bottlenecks), 0)

    def test_generate_resource_optimization(self):
        """Test generation of resource optimization recommendations."""
        # Create resource bottleneck
        Bottleneck(
            bottleneck_id="test_resource_1",
            type=BottleneckType.RESOURCE_CONSTRAINT,
            location="Resource: gpu_1",
            impact=30.0,
            affected_agents=["agent_2"],
            affected_tasks=["task_1", "task_2"],
            description="GPU overutilized",
            evidence={"resource": "gpu_1", "utilization": 0.95},
            detected_at=datetime.utcnow(),
        )

        analysis = self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        # Should have optimization for resource issues
        resource_opts = [
            o
            for o in analysis.optimizations
            if o.type == OptimizationType.RESOURCE_REALLOCATION
        ]

        if resource_opts:
            opt = resource_opts[0]
            self.assertGreater(opt.expected_improvement, 0)
            self.assertGreater(len(opt.implementation_steps), 0)
            self.assertIn("resource", opt.description.lower())

    def test_generate_parallelization_optimization(self):
        """Test generation of parallelization optimizations."""
        # Create workflow with low parallel efficiency
        metrics = WorkflowMetrics(
            total_duration=10000,
            active_time=5000,
            wait_time=3000,
            efficiency_ratio=0.5,
            throughput=1.0,
            bottleneck_impact=0.3,
            parallel_efficiency=0.3,  # Low
        )

        with patch.object(
            self.optimizer, "_calculate_workflow_metrics", return_value=metrics
        ):
            analysis = self.optimizer.analyze_workflow(
                self.workflow_data, self.agent_states, self.task_history
            )

        # Should have parallelization optimization
        parallel_opts = [
            o
            for o in analysis.optimizations
            if o.type == OptimizationType.PARALLELIZATION
        ]
        self.assertGreater(len(parallel_opts), 0)

    def test_optimization_prioritization(self):
        """Test that optimizations are properly prioritized."""
        analysis = self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        if len(analysis.optimizations) > 1:
            # Verify optimizations are sorted by score
            for i in range(len(analysis.optimizations) - 1):
                opt1 = analysis.optimizations[i]
                opt2 = analysis.optimizations[i + 1]

                # Higher priority or higher impact should come first
                if opt1.priority == opt2.priority:
                    self.assertGreaterEqual(
                        opt1.expected_improvement, opt2.expected_improvement
                    )

    def test_projected_improvements(self):
        """Test projection of improvements after optimizations."""
        analysis = self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        # Verify projected metrics
        self.assertIsInstance(analysis.projected_metrics, WorkflowMetrics)

        if analysis.optimizations:
            # Projected should be better than current
            self.assertLessEqual(
                analysis.projected_metrics.total_duration,
                analysis.current_metrics.total_duration,
            )
            self.assertGreaterEqual(
                analysis.projected_metrics.efficiency_ratio,
                analysis.current_metrics.efficiency_ratio,
            )
            self.assertGreaterEqual(
                analysis.projected_metrics.throughput,
                analysis.current_metrics.throughput,
            )

    def test_critical_path_calculation(self):
        """Test critical path calculation."""
        # Create tasks with clear dependencies
        deps = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"], "E": ["D"]}
        durations = {"A": 100, "B": 200, "C": 50, "D": 150, "E": 100}

        critical_path = self.optimizer._find_critical_path(deps, durations)

        # Should find A->B->D->E (total: 550) as critical path
        self.assertIn("A", critical_path)
        self.assertIn("B", critical_path)
        self.assertIn("D", critical_path)
        self.assertIn("E", critical_path)

        # C should not be in critical path (shorter)
        if len(critical_path) == 4:  # If exact path found
            self.assertNotIn("C", critical_path)

    def test_communication_bottleneck_detection(self):
        """Test detection of communication lag bottlenecks."""
        # Add tasks with communication delays
        for i in range(3):
            self.task_history.append(
                {
                    "task_id": f"comm_task_{i}",
                    "duration": 3600,
                    "communication_delay": 600,  # 10 min delay
                    "communicating_agents": ["agent_1", "agent_2"],
                }
            )

        analysis = self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        # Find communication bottlenecks
        comm_bottlenecks = [
            b
            for b in analysis.bottlenecks
            if b.type == BottleneckType.COMMUNICATION_LAG
        ]

        # Should detect communication issues
        self.assertGreater(len(comm_bottlenecks), 0)

        # Verify agent pair identified
        for b in comm_bottlenecks:
            self.assertIn("agent_pair", b.evidence)
            self.assertIn("average_delay", b.evidence)

    def test_workflow_pattern_learning(self):
        """Test that workflow patterns are stored for learning."""
        # Run analysis
        self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        # Verify pattern storage
        workflow_id = self.workflow_data["id"]
        self.assertIn(workflow_id, self.optimizer.workflow_patterns)

        patterns = self.optimizer.workflow_patterns[workflow_id]
        self.assertIn("analyses", patterns)
        self.assertIn("common_bottlenecks", patterns)

        # Verify analysis was stored
        self.assertGreater(len(patterns["analyses"]), 0)

        # Run again to see pattern accumulation
        self.optimizer.analyze_workflow(
            self.workflow_data, self.agent_states, self.task_history
        )

        self.assertEqual(len(patterns["analyses"]), 2)


if __name__ == "__main__":
    unittest.main()
