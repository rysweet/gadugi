
"""
Tests for TeamCoach Phase 3: Conflict Resolver
"""

import unittest
from datetime import datetime
from ..phase3.conflict_resolver import (
    ConflictResolver,
    AgentConflict,
    ConflictResolution,
    ConflictType,
    ConflictSeverity,
    ResolutionStrategy,
)

class TestConflictResolver(unittest.TestCase):
    """Test cases for the ConflictResolver."""

    def setUp(self):
        """Set up test fixtures."""
        self.resolver = ConflictResolver()

        # Sample agent states
        self.agent_states = {
            "agent_1": {
                "resources": ["database", "api_server"],
                "assigned_tasks": ["task_1", "task_2"],
                "capabilities": ["python", "testing"],
                "waiting_for": [
                    {"provider": "agent_2", "wait_time": 7200}  # 2 hours
                ],
            },
            "agent_2": {
                "resources": ["database", "compute_cluster"],
                "assigned_tasks": ["task_1", "task_3"],
                "capabilities": ["java", "deployment"],
                "waiting_for": [],
            },
            "agent_3": {
                "resources": ["api_server"],
                "assigned_tasks": ["task_4"],
                "capabilities": ["python", "ml"],
                "waiting_for": [
                    {"provider": "agent_1", "wait_time": 3600}  # 1 hour
                ],
            },
        }

        # Sample team context
        self.team_context = {
            "resources": {
                "database": {"max_concurrent": 1},
                "api_server": {"max_concurrent": 2},
                "compute_cluster": {"max_concurrent": 4},
            },
            "tasks": {
                "task_1": {
                    "collaborative": False,
                    "required_capabilities": ["python", "testing"],
                },
                "task_2": {"collaborative": True, "required_capabilities": ["python"]},
                "task_3": {
                    "collaborative": False,
                    "required_capabilities": ["java", "ml"],
                },
                "task_4": {
                    "collaborative": True,
                    "required_capabilities": ["python", "ml"],
                },
            },
        }

    def test_detect_resource_contention(self):
        """Test detection of resource contention conflicts."""
        conflicts = self.resolver.detect_conflicts(self.agent_states, self.team_context)

        # Find resource conflicts
        resource_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.RESOURCE_CONTENTION
        ]

        # Should detect database contention (2 agents, max 1)
        self.assertGreater(len(resource_conflicts), 0)

        # Verify database conflict
        db_conflicts = [
            c for c in resource_conflicts if c.evidence.get("resource") == "database"
        ]
        self.assertEqual(len(db_conflicts), 1)

        conflict = db_conflicts[0]
        self.assertEqual(len(conflict.agents_involved), 2)
        self.assertIn("agent_1", conflict.agents_involved)
        self.assertIn("agent_2", conflict.agents_involved)

    def test_detect_task_overlap(self):
        """Test detection of task overlap conflicts."""
        conflicts = self.resolver.detect_conflicts(self.agent_states, self.team_context)

        # Find task overlap conflicts
        task_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.TASK_OVERLAP
        ]

        # Should detect task_1 overlap (non-collaborative, 2 agents)
        self.assertGreater(len(task_conflicts), 0)

        # Verify task_1 conflict
        task1_conflicts = [
            c for c in task_conflicts if c.evidence.get("task_id") == "task_1"
        ]
        self.assertEqual(len(task1_conflicts), 1)

        conflict = task1_conflicts[0]
        self.assertEqual(conflict.severity, ConflictSeverity.HIGH)
        self.assertIn("agent_1", conflict.agents_involved)
        self.assertIn("agent_2", conflict.agents_involved)

    def test_detect_coordination_failures(self):
        """Test detection of coordination failure conflicts."""
        conflicts = self.resolver.detect_conflicts(self.agent_states, self.team_context)

        # Find coordination conflicts
        coord_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.COORDINATION_FAILURE
        ]

        # Should detect agent_1 waiting for agent_2 (2 hours)
        self.assertGreater(len(coord_conflicts), 0)

        # Verify specific coordination failure
        long_wait = [
            c for c in coord_conflicts if c.evidence.get("wait_time", 0) >= 7200
        ]
        self.assertGreater(len(long_wait), 0)

        conflict = long_wait[0]
        self.assertEqual(conflict.severity, ConflictSeverity.HIGH)
        self.assertIn("agent_1", conflict.agents_involved)

    def test_detect_capability_mismatches(self):
        """Test detection of capability mismatch conflicts."""
        conflicts = self.resolver.detect_conflicts(self.agent_states, self.team_context)

        # Find capability conflicts
        cap_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.CAPABILITY_MISMATCH
        ]

        # agent_2 lacks 'ml' for task_3
        self.assertGreater(len(cap_conflicts), 0)

        # Verify specific mismatch
        ml_conflicts = [
            c
            for c in cap_conflicts
            if "ml" in c.evidence.get("missing_capabilities", [])
        ]
        self.assertGreater(len(ml_conflicts), 0)

        conflict = ml_conflicts[0]
        self.assertEqual(conflict.severity, ConflictSeverity.HIGH)
        self.assertIn("agent_2", conflict.agents_involved)

    def test_detect_dependency_deadlock(self):
        """Test detection of circular dependency deadlocks."""
        # Create circular dependency
        circular_states = {
            "agent_1": {"waiting_for": [{"provider": "agent_2", "wait_time": 1000}]},
            "agent_2": {"waiting_for": [{"provider": "agent_3", "wait_time": 1000}]},
            "agent_3": {"waiting_for": [{"provider": "agent_1", "wait_time": 1000}]},
        }

        conflicts = self.resolver.detect_conflicts(circular_states, self.team_context)

        # Find deadlock conflicts
        deadlock_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.DEPENDENCY_DEADLOCK
        ]

        # Should detect the circular dependency
        self.assertGreater(len(deadlock_conflicts), 0)

        conflict = deadlock_conflicts[0]
        self.assertEqual(conflict.severity, ConflictSeverity.CRITICAL)
        self.assertEqual(len(conflict.agents_involved), 3)

        # Verify cycle detection
        cycle = conflict.evidence.get("cycle", [])
        self.assertEqual(len(cycle), 3)

    def test_resolve_conflict_resource_contention(self):
        """Test resolution of resource contention conflicts."""
        # Create a resource conflict
        conflict = AgentConflict(
            conflict_id="test_resource_1",
            conflict_type=ConflictType.RESOURCE_CONTENTION,
            severity=ConflictSeverity.HIGH,
            agents_involved=["agent_1", "agent_2"],
            description="Database contention",
            impact="50% wait time",
            detected_at=datetime.utcnow(),
            evidence={"resource": "database"},
        )

        # Generate resolution
        resolution = self.resolver.resolve_conflict(conflict)

        # Verify resolution
        self.assertIsInstance(resolution, ConflictResolution)
        self.assertEqual(resolution.conflict_id, conflict.conflict_id)
        self.assertIn(
            resolution.strategy,
            [
                ResolutionStrategy.IMMEDIATE_REALLOCATION,
                ResolutionStrategy.SCHEDULED_ADJUSTMENT,
            ],
        )
        self.assertGreater(len(resolution.actions), 0)
        self.assertGreater(len(resolution.implementation_steps), 0)
        self.assertIsNotNone(resolution.timeline)

    def test_resolve_conflict_task_overlap(self):
        """Test resolution of task overlap conflicts."""
        # Create a task overlap conflict
        conflict = AgentConflict(
            conflict_id="test_task_1",
            conflict_type=ConflictType.TASK_OVERLAP,
            severity=ConflictSeverity.HIGH,
            agents_involved=["agent_1", "agent_2"],
            description="Multiple agents on task_1",
            impact="Duplicated effort",
            detected_at=datetime.utcnow(),
            evidence={"task_id": "task_1"},
        )

        # Generate resolution
        resolution = self.resolver.resolve_conflict(conflict)

        # Verify resolution
        self.assertEqual(resolution.strategy, ResolutionStrategy.IMMEDIATE_REALLOCATION)

        # Should have remove task actions
        remove_actions = [a for a in resolution.actions if a["type"] == "remove_task"]
        self.assertGreater(len(remove_actions), 0)

    def test_implement_resolution(self):
        """Test implementation of conflict resolution."""
        # Create conflict and resolution
        conflict = AgentConflict(
            conflict_id="test_impl_1",
            conflict_type=ConflictType.TASK_OVERLAP,
            severity=ConflictSeverity.HIGH,
            agents_involved=["agent_1", "agent_2"],
            description="Task overlap",
            impact="Duplicated effort",
            detected_at=datetime.utcnow(),
            evidence={"task_id": "task_1"},
        )

        resolution = ConflictResolution(
            conflict_id=conflict.conflict_id,
            strategy=ResolutionStrategy.IMMEDIATE_REALLOCATION,
            actions=[
                {"type": "remove_task", "agent_id": "agent_2", "task_id": "task_1"}
            ],
            expected_outcome="Task assigned to single agent",
            implementation_steps=["Remove task from agent_2"],
            timeline="Immediate",
            created_at=datetime.utcnow(),
        )

        # Copy agent states for modification
        test_states = self.agent_states.copy()

        # Implement resolution
        result = self.resolver.implement_resolution(conflict, resolution, test_states)

        # Verify implementation
        self.assertTrue(result["success"])
        self.assertIn("agent_2", result["updated_states"])

        # Verify task was removed
        updated_tasks = result["updated_states"]["agent_2"].get("assigned_tasks", [])
        self.assertNotIn("task_1", updated_tasks)

    def test_conflict_report_generation(self):
        """Test conflict report generation."""
        # Detect some conflicts first
        self.resolver.detect_conflicts(self.agent_states, self.team_context)

        # Generate report
        report = self.resolver.generate_conflict_report()

        # Verify report structure
        self.assertGreater(len(report.active_conflicts), 0)
        self.assertIsInstance(report.conflict_patterns, dict)
        self.assertIsInstance(report.prevention_recommendations, list)
        self.assertGreater(len(report.prevention_recommendations), 0)

        # Verify patterns analysis
        if report.conflict_patterns.get("total_conflicts", 0) > 0:
            self.assertIn("by_type", report.conflict_patterns)
            self.assertIn("by_severity", report.conflict_patterns)

    def test_resolution_strategy_selection(self):
        """Test appropriate strategy selection for different conflict types."""
        # Test critical deadlock
        deadlock = AgentConflict(
            conflict_id="test_deadlock",
            conflict_type=ConflictType.DEPENDENCY_DEADLOCK,
            severity=ConflictSeverity.CRITICAL,
            agents_involved=["agent_1", "agent_2"],
            description="Deadlock",
            impact="Complete blockage",
            detected_at=datetime.utcnow(),
            evidence={},
        )

        strategy = self.resolver._select_resolution_strategy(deadlock)
        self.assertEqual(strategy, ResolutionStrategy.IMMEDIATE_REALLOCATION)

        # Test coordination failure
        coord_fail = AgentConflict(
            conflict_id="test_coord",
            conflict_type=ConflictType.COORDINATION_FAILURE,
            severity=ConflictSeverity.MEDIUM,
            agents_involved=["agent_1", "agent_2"],
            description="Coordination issue",
            impact="Delays",
            detected_at=datetime.utcnow(),
            evidence={},
        )

        strategy = self.resolver._select_resolution_strategy(coord_fail)
        self.assertEqual(strategy, ResolutionStrategy.NEGOTIATION)

    def test_prevention_recommendations(self):
        """Test generation of prevention recommendations."""
        # Simulate multiple resource conflicts
        for i in range(10):
            self.resolver.conflict_patterns["resource_contention_high"] = 10

        patterns = self.resolver._analyze_conflict_patterns()
        recommendations = self.resolver._generate_prevention_recommendations(patterns)

        # Should recommend resource improvements
        resource_recs = [r for r in recommendations if "resource" in r.lower()]
        self.assertGreater(len(resource_recs), 0)

        # Should include general recommendations
        self.assertGreater(len(recommendations), 2)

if __name__ == "__main__":
    unittest.main()
