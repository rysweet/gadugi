"""
Tests for TeamCoach Phase 3: Strategic Planner
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

from ..phase3.strategic_planner import (
    StrategicPlanner,
    TeamEvolutionPlan,
    StrategicGoal,
    StrategicInitiative,
    CapacityPlan,
    SkillDevelopmentPlan,
    PlanningHorizon,
    StrategyType,
    StrategyPriority,
)
from ..phase1.performance_analytics import PerformanceMetrics


class TestStrategicPlanner(unittest.TestCase):
    """Test cases for the StrategicPlanner."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_performance_analyzer = Mock()
        self.mock_capability_assessment = Mock()

        # Create planner
        self.planner = StrategicPlanner(
            self.mock_performance_analyzer, self.mock_capability_assessment
        )

        # Sample business objectives
        self.business_objectives = [
            {
                "title": "Improve Operational Efficiency",
                "description": "Achieve 25% improvement in team efficiency",
                "metric": "efficiency_ratio",
                "target": 0.85,
                "timeline_days": 90,
                "priority": "high",
            },
            {
                "title": "Scale Operations",
                "description": "Build capacity to handle 3x current workload",
                "metric": "capacity_multiplier",
                "target": 3.0,
                "timeline_days": 180,
                "priority": "medium",
            },
        ]

        # Mock performance data
        self.mock_performance = PerformanceMetrics(
            agent_id="agent_1",
            success_rate=0.75,
            average_execution_time=120,
            total_tasks=100,
            successful_tasks=75,
            failed_tasks=25,
            error_count=25,
            error_types={},
            metrics={"efficiency_ratio": 0.65, "capacity_multiplier": 1.0},
        )

        # Mock capability data
        self.mock_capability = Mock()
        self.mock_capability.domain_scores = {
            "python": 0.8,
            "java": 0.6,
            "ml": 0.4,  # Gap
            "devops": 0.3,  # Gap
            "testing": 0.7,
        }

    def test_create_team_evolution_plan(self):
        """Test creation of comprehensive team evolution plan."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Create plan
        plan = self.planner.create_team_evolution_plan(
            "team_1", ["agent_1", "agent_2"], self.business_objectives
        )

        # Verify plan structure
        self.assertIsInstance(plan, TeamEvolutionPlan)
        self.assertIsNotNone(plan.vision)
        self.assertGreater(len(plan.strategic_goals), 0)
        self.assertGreater(len(plan.initiatives), 0)
        self.assertIsInstance(plan.capacity_plan, CapacityPlan)
        self.assertIsInstance(plan.skill_plan, SkillDevelopmentPlan)
        self.assertIsInstance(plan.roadmap, dict)
        self.assertIsInstance(plan.success_metrics, dict)
        self.assertGreater(len(plan.review_schedule), 0)

    def test_define_team_vision(self):
        """Test team vision creation from objectives."""
        vision = self.planner._define_team_vision(self.business_objectives)

        # Should include efficiency theme
        self.assertIn("efficiency", vision.lower())

        # Test with innovation objective
        innovation_objectives = [
            {"description": "Foster innovation and continuous improvement"}
        ]
        vision = self.planner._define_team_vision(innovation_objectives)
        self.assertIn("innovation", vision.lower())

    def test_create_strategic_goals(self):
        """Test strategic goal creation from business objectives."""
        # Configure mock
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )

        goals = self.planner._create_strategic_goals(
            self.business_objectives, ["agent_1", "agent_2"]
        )

        # Verify goals created
        self.assertEqual(len(goals), len(self.business_objectives))

        # Check goal properties
        for goal in goals:
            self.assertIsInstance(goal, StrategicGoal)
            self.assertIsNotNone(goal.goal_id)
            self.assertIsNotNone(goal.title)
            self.assertIsNotNone(goal.target_metric)
            self.assertGreater(goal.target_value, goal.current_value)
            self.assertIsInstance(goal.deadline, datetime)
            self.assertIsInstance(goal.priority, StrategyPriority)

    def test_create_default_strategic_goals(self):
        """Test creation of default goals when none provided."""
        # Configure mock
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )

        goals = self.planner._create_strategic_goals([], ["agent_1"])

        # Should have default goals
        self.assertGreater(len(goals), 0)

        # Check for standard goals
        goal_titles = [g.title for g in goals]
        efficiency_goals = [t for t in goal_titles if "efficiency" in t.lower()]
        quality_goals = [t for t in goal_titles if "quality" in t.lower()]

        self.assertGreater(len(efficiency_goals), 0)
        self.assertGreater(len(quality_goals), 0)

    def test_analyze_current_state(self):
        """Test current state analysis."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        state = self.planner._analyze_current_state(["agent_1", "agent_2"])

        # Verify state structure
        self.assertIn("performance_metrics", state)
        self.assertIn("capability_coverage", state)
        self.assertIn("skill_distribution", state)

        # Check capability coverage calculation
        self.assertIn("python", state["capability_coverage"])
        self.assertIn("ml", state["capability_coverage"])

        # Weak skills should have low coverage
        self.assertLess(state["capability_coverage"]["ml"], 0.5)

    def test_create_capacity_plan(self):
        """Test capacity planning."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Create goals and state
        goals = self.planner._create_strategic_goals(
            self.business_objectives, ["agent_1", "agent_2"]
        )
        state = self.planner._analyze_current_state(["agent_1", "agent_2"])

        # Create capacity plan
        capacity_plan = self.planner._create_capacity_plan(
            ["agent_1", "agent_2"], goals, state
        )

        # Verify plan structure
        self.assertIsInstance(capacity_plan, CapacityPlan)
        self.assertIsInstance(capacity_plan.current_capacity, dict)
        self.assertIsInstance(capacity_plan.projected_demand, dict)
        self.assertIsInstance(capacity_plan.gaps, dict)
        self.assertGreater(len(capacity_plan.recommendations), 0)

        # Check for capacity gaps
        if capacity_plan is not None and capacity_plan.gaps:
            for _, gaps in capacity_plan.gaps.items():
                self.assertIsInstance(gaps, dict)

    def test_create_skill_development_plan(self):
        """Test skill development planning."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Create goals and state
        goals = self.planner._create_strategic_goals(
            self.business_objectives, ["agent_1"]
        )
        state = self.planner._analyze_current_state(["agent_1"])

        # Create skill plan
        skill_plan = self.planner._create_skill_development_plan(
            ["agent_1"], goals, state
        )

        # Verify plan structure
        self.assertIsInstance(skill_plan, SkillDevelopmentPlan)
        self.assertIsInstance(skill_plan.skill_gaps, dict)
        self.assertIsInstance(skill_plan.development_paths, dict)
        self.assertIsInstance(skill_plan.training_calendar, dict)
        self.assertIsInstance(skill_plan.investment_required, dict)

        # Should identify ML and DevOps gaps
        self.assertGreater(skill_plan.skill_gaps.get("ml", 0), 0)
        self.assertGreater(skill_plan.skill_gaps.get("devops", 0), 0)

    def test_generate_strategic_initiatives(self):
        """Test generation of strategic initiatives."""
        # Configure mocks
        self.mock_performance_analyzer.get_agent_performance.return_value = (
            self.mock_performance
        )
        self.mock_capability_assessment.get_agent_capabilities.return_value = (
            self.mock_capability
        )

        # Create prerequisites
        goals = self.planner._create_strategic_goals(
            self.business_objectives, ["agent_1", "agent_2"]
        )
        state = self.planner._analyze_current_state(["agent_1", "agent_2"])
        capacity_plan = self.planner._create_capacity_plan(
            ["agent_1", "agent_2"], goals, state
        )
        skill_plan = self.planner._create_skill_development_plan(
            ["agent_1", "agent_2"], goals, state
        )

        # Generate initiatives
        initiatives = self.planner._generate_strategic_initiatives(
            goals, capacity_plan, skill_plan, None
        )

        # Verify initiatives
        self.assertGreater(len(initiatives), 0)

        for initiative in initiatives:
            self.assertIsInstance(initiative, StrategicInitiative)
            self.assertIsNotNone(initiative.initiative_id)
            self.assertIsInstance(initiative.type, StrategyType)
            self.assertGreater(len(initiative.implementation_steps), 0)
            self.assertIsInstance(initiative.timeline, dict)
            self.assertGreater(len(initiative.success_criteria), 0)

    def test_strategic_roadmap_creation(self):
        """Test creation of strategic roadmap."""
        # Create sample initiatives
        now = datetime.utcnow()
        initiatives = [
            StrategicInitiative(
                initiative_id="init_1",
                type=StrategyType.PROCESS_IMPROVEMENT,
                title="Quick Win",
                description="Fast improvement",
                goals_addressed=["goal_1"],
                impact_estimate={"efficiency": 0.1},
                resource_requirements={},
                timeline={"completion": now + timedelta(weeks=2)},
                risks=[],
                success_criteria=["Done in 2 weeks"],
                owner=None,
            ),
            StrategicInitiative(
                initiative_id="init_2",
                type=StrategyType.CAPACITY_EXPANSION,
                title="Medium Term",
                description="Capacity growth",
                goals_addressed=["goal_2"],
                impact_estimate={"capacity": 1.0},
                resource_requirements={},
                timeline={"completion": now + timedelta(weeks=8)},
                risks=[],
                success_criteria=["Capacity doubled"],
                owner=None,
            ),
            StrategicInitiative(
                initiative_id="init_3",
                type=StrategyType.SKILL_DEVELOPMENT,
                title="Long Term",
                description="Skill building",
                goals_addressed=["goal_3"],
                impact_estimate={"skills": 0.5},
                resource_requirements={},
                timeline={"completion": now + timedelta(weeks=20)},
                risks=[],
                success_criteria=["Skills improved"],
                owner=None,
            ),
        ]

        # Create roadmap
        roadmap = self.planner._create_strategic_roadmap(initiatives, [])

        # Verify roadmap structure
        self.assertIn(PlanningHorizon.SHORT_TERM, roadmap)
        self.assertIn(PlanningHorizon.MEDIUM_TERM, roadmap)
        self.assertIn(PlanningHorizon.LONG_TERM, roadmap)

        # Check initiative placement
        self.assertIn("init_1", roadmap[PlanningHorizon.SHORT_TERM])
        self.assertIn("init_2", roadmap[PlanningHorizon.MEDIUM_TERM])
        self.assertIn("init_3", roadmap[PlanningHorizon.LONG_TERM])

    def test_success_metrics_definition(self):
        """Test definition of success metrics."""
        # Create sample goals
        goals = [
            StrategicGoal(
                goal_id="goal_1",
                title="Efficiency Goal",
                description="Improve efficiency",
                target_metric="efficiency_ratio",
                current_value=0.6,
                target_value=0.85,
                deadline=datetime.utcnow() + timedelta(days=90),
                priority=StrategyPriority.HIGH,
                dependencies=[],
            )
        ]

        metrics = self.planner._define_success_metrics(goals)

        # Verify metrics
        self.assertIn("efficiency_ratio", metrics)
        self.assertEqual(metrics["efficiency_ratio"], 0.85)

        # Should include default metrics
        self.assertIn("team_satisfaction", metrics)
        self.assertIn("innovation_index", metrics)

    def test_review_schedule_creation(self):
        """Test creation of review schedule."""
        # Create roadmap
        roadmap = {
            PlanningHorizon.SHORT_TERM: ["init_1", "init_2"],
            PlanningHorizon.MEDIUM_TERM: ["init_3"],
            PlanningHorizon.LONG_TERM: ["init_4"],
        }

        schedule = self.planner._create_review_schedule(roadmap)

        # Verify schedule
        self.assertIsInstance(schedule, list)
        self.assertGreater(len(schedule), 0)

        # All dates should be in the future
        now = datetime.utcnow()
        for review_date in schedule:
            self.assertGreater(review_date, now)

        # Should be sorted
        for i in range(len(schedule) - 1):
            self.assertLess(schedule[i], schedule[i + 1])

    def test_capacity_gap_calculation(self):
        """Test capacity gap calculation."""
        current = {"python": 2.0, "java": 1.5, "ml": 0.5}

        demand = {
            "short_term": {"python": 2.5, "java": 1.5, "ml": 2.0},
            "medium_term": {"python": 3.0, "java": 2.0, "ml": 3.0},
            "long_term": {"python": 4.0, "java": 3.0, "ml": 4.0},
        }

        gaps = self.planner._calculate_capacity_gaps(current, demand)

        # Verify gaps
        self.assertIn("short_term", gaps)
        self.assertIn("ml", gaps["short_term"])
        self.assertGreater(gaps["short_term"]["ml"], 0)

        # Python gap should appear in later timeframes
        self.assertIn("python", gaps["long_term"])
        self.assertGreater(gaps["long_term"]["python"], 0)

    def test_training_investment_calculation(self):
        """Test calculation of training investment."""
        # Create development paths
        development_paths = {
            "agent_1": [
                {"skill": "ml", "duration_weeks": 4, "training_type": "intensive"}
            ],
            "agent_2": [
                {"skill": "devops", "duration_weeks": 2, "training_type": "moderate"}
            ],
        }

        # Create training calendar
        training_calendar = {
            datetime.utcnow(): ["ML training session"],
            datetime.utcnow() + timedelta(weeks=1): ["DevOps workshop"],
        }

        investment = self.planner._calculate_training_investment(
            development_paths, training_calendar
        )

        # Verify investment calculation
        self.assertIn("training_hours", investment)
        self.assertIn("external_training", investment)
        self.assertIn("lost_productivity", investment)
        self.assertIn("materials", investment)

        # Should have calculated hours (4 weeks * 10 + 2 weeks * 10 = 60)
        self.assertEqual(investment["training_hours"], 60)

        # External training cost should be based on calendar
        self.assertEqual(investment["external_training"], len(training_calendar) * 2000)


if __name__ == "__main__":
    unittest.main()
