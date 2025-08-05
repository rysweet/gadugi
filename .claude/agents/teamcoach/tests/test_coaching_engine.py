"""
Tests for TeamCoach Phase 3: Coaching Engine
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from ..phase3.coaching_engine import (
    CoachingEngine,
    CoachingRecommendation,
    TeamCoachingPlan,
    CoachingPriority,
    CoachingCategory,
)
from ..phase1.performance_analytics import PerformanceMetrics


class TestCoachingEngine(unittest.TestCase):
    """Test cases for the CoachingEngine."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_performance_analyzer = Mock()
        self.mock_capability_assessment = Mock()
        self.mock_task_matcher = Mock()

        # Create coaching engine
        self.engine = CoachingEngine(
            self.mock_performance_analyzer,
            self.mock_capability_assessment,
            self.mock_task_matcher,
        )

        # Set up mock performance data
        self.mock_performance = PerformanceMetrics(
            agent_id="agent_1",
            success_rate=0.65,  # Below target
            average_execution_time=150,  # Slow
            total_tasks=100,
            successful_tasks=65,
            failed_tasks=35,
            error_count=35,
            error_types={"timeout": 20, "validation": 15},
            metrics={
                "collaboration_score": 0.5,
                "workload_score": 0.9,  # Overloaded
                "task_variety_score": 0.2,  # Low variety
                "interaction_count": 10,
            },
        )

        # Set up mock capability data
        self.mock_capability = Mock()
        self.mock_capability.domain_scores = {
            "python": 0.9,  # Strong
            "database": 0.4,  # Weak
            "testing": 0.5,  # Weak
            "deployment": 0.8,  # Good
        }

    def test_generate_agent_coaching_performance_issues(self):
        """Test coaching generation for performance issues."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Generate coaching
        recommendations = self.engine.generate_agent_coaching("agent_1")

        # Verify recommendations generated
        self.assertGreater(len(recommendations), 0)

        # Check for performance recommendations
        perf_recs = [
            r for r in recommendations if r.category == CoachingCategory.PERFORMANCE
        ]
        self.assertGreater(len(perf_recs), 0)

        # Verify critical performance issue detected
        critical_recs = [r for r in perf_recs if r.priority == CoachingPriority.HIGH]
        self.assertGreater(len(critical_recs), 0)

        # Check specific recommendations
        for rec in critical_recs:
            self.assertIn("success rate", rec.description.lower())
            self.assertGreater(len(rec.specific_actions), 0)
            self.assertIsNotNone(rec.expected_impact)
            self.assertIsNotNone(rec.timeframe)

    def test_generate_agent_coaching_efficiency_issues(self):
        """Test coaching generation for efficiency issues."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Generate coaching
        recommendations = self.engine.generate_agent_coaching("agent_1")

        # Check for efficiency recommendations
        eff_recs = [
            r for r in recommendations if r.category == CoachingCategory.EFFICIENCY
        ]
        self.assertGreater(len(eff_recs), 0)

        # Verify efficiency issues detected
        for rec in eff_recs:
            self.assertIn("execution time", rec.description.lower())
            self.assertIn("optimization", " ".join(rec.specific_actions).lower())

    def test_generate_agent_coaching_capability_gaps(self):
        """Test coaching generation for capability gaps."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Mock capability utilization
        with patch.object(
            self.engine, "_calculate_capability_utilization", return_value=0.2
        ):
            recommendations = self.engine.generate_agent_coaching("agent_1")

        # Check for skill development recommendations
        skill_recs = [
            r
            for r in recommendations
            if r.category == CoachingCategory.SKILL_DEVELOPMENT
        ]
        self.assertGreater(len(skill_recs), 0)

        # Verify weak skills identified
        weak_skills = ["database", "testing"]
        rec_skills = []
        for rec in skill_recs:
            for skill in weak_skills:
                if skill in rec.title.lower():
                    rec_skills.append(skill)

        self.assertGreater(len(rec_skills), 0)

    def test_generate_agent_coaching_workload_issues(self):
        """Test coaching generation for workload issues."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Generate coaching
        recommendations = self.engine.generate_agent_coaching("agent_1")

        # Check for workload recommendations
        workload_recs = [
            r for r in recommendations if r.category == CoachingCategory.WORKLOAD
        ]
        self.assertGreater(len(workload_recs), 0)

        # Verify overload detected
        overload_recs = [r for r in workload_recs if "optimization" in r.title.lower()]
        self.assertGreater(len(overload_recs), 0)

        for rec in overload_recs:
            self.assertIn("workload", rec.description.lower())
            self.assertEqual(rec.priority, CoachingPriority.HIGH)

    def test_generate_team_coaching_plan(self):
        """Test team coaching plan generation."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Mock team analysis methods
        with patch.object(
            self.engine,
            "_analyze_team_capability_balance",
            return_value={"gaps": ["ai", "ml"], "total_domains": 10},
        ):
            with patch.object(
                self.engine, "_calculate_team_collaboration_score", return_value=0.6
            ):
                # Generate team plan
                plan = self.engine.generate_team_coaching_plan(
                    "team_1",
                    ["agent_1", "agent_2"],
                    ["Improve efficiency", "Enhance quality"],
                )

        # Verify plan structure
        self.assertIsInstance(plan, TeamCoachingPlan)
        self.assertEqual(plan.team_id, "team_1")
        self.assertGreater(len(plan.recommendations), 0)
        self.assertGreater(len(plan.team_goals), 0)
        self.assertIsNotNone(plan.timeline)
        self.assertIsInstance(plan.success_metrics, dict)

        # Check for team-level recommendations
        team_recs = [r for r in plan.recommendations if r.agent_id.startswith("team_")]
        self.assertGreater(len(team_recs), 0)

    def test_coaching_priority_ranking(self):
        """Test that recommendations are properly prioritized."""
        # Create recommendations with different priorities
        recs = [
            CoachingRecommendation(
                agent_id="agent_1",
                category=CoachingCategory.PERFORMANCE,
                priority=CoachingPriority.LOW,
                title="Low priority",
                description="Low priority issue",
                specific_actions=["Action 1"],
                expected_impact="Minor improvement",
                metrics_to_track=["metric1"],
                resources=[],
                timeframe="4 weeks",
                created_at=datetime.utcnow(),
                evidence={},
            ),
            CoachingRecommendation(
                agent_id="agent_1",
                category=CoachingCategory.PERFORMANCE,
                priority=CoachingPriority.CRITICAL,
                title="Critical issue",
                description="Critical performance issue",
                specific_actions=["Urgent action"],
                expected_impact="Major improvement",
                metrics_to_track=["metric2"],
                resources=[],
                timeframe="1 week",
                created_at=datetime.utcnow(),
                evidence={},
            ),
        ]

        # Sort using engine's method
        sorted_recs = sorted(
            recs, key=lambda r: self.engine._get_priority_rank(r.priority), reverse=True
        )

        # Verify critical comes first
        self.assertEqual(sorted_recs[0].priority, CoachingPriority.CRITICAL)
        self.assertEqual(sorted_recs[1].priority, CoachingPriority.LOW)

    def test_collaboration_pattern_analysis(self):
        """Test collaboration pattern analysis."""
        # Set up performance with low collaboration score
        self.mock_performance.metrics["collaboration_score"] = 0.4
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Generate coaching
        recommendations = self.engine.generate_agent_coaching("agent_1")

        # Check for collaboration recommendations
        collab_recs = [
            r for r in recommendations if r.category == CoachingCategory.COLLABORATION
        ]
        self.assertGreater(len(collab_recs), 0)

        # Verify collaboration improvement suggested
        for rec in collab_recs:
            self.assertIn("collaboration", rec.description.lower())
            self.assertIn("communication", " ".join(rec.specific_actions).lower())

    def test_task_variety_analysis(self):
        """Test task variety analysis and recommendations."""
        # Performance already has low task variety (0.2)
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Generate coaching
        recommendations = self.engine.generate_agent_coaching("agent_1")

        # Check for skill development recommendations related to variety
        variety_recs = [r for r in recommendations if "diversify" in r.title.lower()]
        self.assertGreater(len(variety_recs), 0)

        for rec in variety_recs:
            self.assertIn("variety", rec.description.lower())
            self.assertEqual(rec.category, CoachingCategory.SKILL_DEVELOPMENT)

    def test_underutilized_strengths_detection(self):
        """Test detection of underutilized strengths."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Mock low utilization for strong skills
        with patch.object(
            self.engine, "_calculate_capability_utilization", return_value=0.1
        ):
            recommendations = self.engine.generate_agent_coaching("agent_1")

        # Check for underutilization recommendations
        underutil_recs = [
            r for r in recommendations if "underutilized" in r.title.lower()
        ]
        self.assertGreater(len(underutil_recs), 0)

        # Verify it's about strong skills
        for rec in underutil_recs:
            self.assertIn("python", rec.title.lower())  # Python is a strong skill (0.9)
            self.assertEqual(rec.priority, CoachingPriority.LOW)  # Not critical

    def test_success_metrics_definition(self):
        """Test success metrics are properly defined."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Generate team plan
        plan = self.engine.generate_team_coaching_plan("team_1", ["agent_1", "agent_2"])

        # Verify success metrics
        self.assertIn("team_success_rate", plan.success_metrics)
        self.assertIn("collaboration_score", plan.success_metrics)
        self.assertIn("recommendation_completion", plan.success_metrics)

        # Check metric values are reasonable
        self.assertGreater(plan.success_metrics["team_success_rate"], 0.5)
        self.assertLessEqual(plan.success_metrics["team_success_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
