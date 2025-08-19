
from ..shared.state_management import StateManager
from unittest.mock import Mock, patch, MagicMock
"""
Tests for TeamCoach Task Matcher

Unit tests for the TaskAgentMatcher class and related functionality.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

# Import components to test
from ..phase2.task_matcher import (
    TaskAgentMatcher,
    TaskRequirements,
    AgentAvailability,
    MatchingScore,
    MatchingRecommendation,
    MatchingStrategy,
    TaskPriority,
    TaskUrgency,
    MatchingError,
)
from ..phase1.capability_assessment import (
    CapabilityDomain,
    ProficiencyLevel,
    AgentCapabilityProfile,
    CapabilityScore,
)
from ...shared.task_tracking import TaskMetrics
from ...shared.state_management import StateManager

class TestTaskAgentMatcher(unittest.TestCase):
    """Test cases for TaskAgentMatcher"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_capability_assessment = Mock()
        self.mock_performance_analyzer = Mock()
        self.mock_task_metrics = Mock(spec=TaskMetrics)
        self.mock_state_manager = Mock(spec=StateManager)

        self.matcher = TaskAgentMatcher(
            capability_assessment=self.mock_capability_assessment,
            performance_analyzer=self.mock_performance_analyzer,
            task_metrics=self.mock_task_metrics,
            state_manager=self.mock_state_manager,
        )

        # Sample data
        self.task_requirements = TaskRequirements(
            task_id="test_task_001",
            task_type="implementation",
            description="Test implementation task",
            required_capabilities={
                CapabilityDomain.CODE_GENERATION: ProficiencyLevel.INTERMEDIATE,
                CapabilityDomain.TESTING: ProficiencyLevel.BEGINNER,
            },
            priority=TaskPriority.HIGH,
            urgency=TaskUrgency.NORMAL,
        )

        self.available_agents = ["agent1", "agent2", "agent3"]

        # Mock capability profiles
        self.mock_capability_profile = AgentCapabilityProfile(
            agent_id="agent1",
            agent_name="Test Agent 1",
            profile_generated=datetime.now(),
            capability_scores={
                CapabilityDomain.CODE_GENERATION: CapabilityScore(
                    domain=CapabilityDomain.CODE_GENERATION,
                    proficiency_level=ProficiencyLevel.ADVANCED,
                    confidence_score=0.9,
                    evidence_count=10,
                    last_updated=datetime.now(),
                ),
                CapabilityDomain.TESTING: CapabilityScore(
                    domain=CapabilityDomain.TESTING,
                    proficiency_level=ProficiencyLevel.INTERMEDIATE,
                    confidence_score=0.8,
                    evidence_count=5,
                    last_updated=datetime.now(),
                ),
            },
            primary_strengths=[CapabilityDomain.CODE_GENERATION],
            secondary_strengths=[CapabilityDomain.TESTING],
        )

        # Mock agent availability
        self.mock_availability = AgentAvailability(
            agent_id="agent1",
            current_workload=0.3,
            scheduled_tasks=[],
            available_from=datetime.now(),
        )

    def test_initialization(self):
        """Test proper initialization of TaskAgentMatcher"""
        self.assertIsInstance(self.matcher, TaskAgentMatcher)
        self.assertIsNotNone(self.matcher.capability_assessment)
        self.assertIsNotNone(self.matcher.performance_analyzer)
        self.assertIsNotNone(self.matcher.task_metrics)
        self.assertIsInstance(self.matcher.matching_config, dict)
        self.assertIsInstance(self.matcher.agent_profiles_cache, dict)

    def test_find_optimal_agent_success(self):
        """Test successful optimal agent finding"""
        # Mock dependencies
        self.mock_capability_assessment.assess_agent_capabilities.return_value = (
            self.mock_capability_profile
        )

        mock_performance_data = Mock()
        mock_performance_data.success_rate = 0.85
        mock_performance_data.avg_execution_time = 120.0
        mock_performance_data.performance_trend = [0.7, 0.8, 0.85]
        self.mock_performance_analyzer.analyze_agent_performance.return_value = (
            mock_performance_data
        )

        # Mock task metrics for availability
        self.mock_task_metrics.get_agent_active_tasks.return_value = []

        # Execute matching
        with patch.object(
            self.matcher, "_get_agent_availability", return_value=self.mock_availability
        ):
            recommendation = self.matcher.find_optimal_agent(
                self.task_requirements, self.available_agents, MatchingStrategy.BEST_FIT
            )

        # Verify recommendation
        self.assertIsInstance(recommendation, MatchingRecommendation)
        self.assertEqual(recommendation.task_id, "test_task_001")
        self.assertGreater(len(recommendation.recommended_agents), 0)
        self.assertEqual(recommendation.assignment_strategy, MatchingStrategy.BEST_FIT)
        self.assertIsInstance(recommendation.agent_scores, dict)

    def test_find_optimal_agent_no_suitable_agents(self):
        """Test when no suitable agents are found"""
        # Mock low capability match
        weak_profile = AgentCapabilityProfile(
            agent_id="weak_agent",
            agent_name="Weak Agent",
            profile_generated=datetime.now(),
            capability_scores={
                CapabilityDomain.CODE_GENERATION: CapabilityScore(
                    domain=CapabilityDomain.CODE_GENERATION,
                    proficiency_level=ProficiencyLevel.NOVICE,
                    confidence_score=0.3,
                    evidence_count=1,
                    last_updated=datetime.now(),
                )
            },
        )

        self.mock_capability_assessment.assess_agent_capabilities.return_value = (
            weak_profile
        )
        self.mock_performance_analyzer.analyze_agent_performance.return_value = Mock(
            success_rate=0.3, avg_execution_time=500.0, performance_trend=[]
        )
        self.mock_task_metrics.get_agent_active_tasks.return_value = []

        # Should raise MatchingError for no suitable agents
        with patch.object(
            self.matcher, "_get_agent_availability", return_value=self.mock_availability
        ):
            with self.assertRaises(MatchingError):
                self.matcher.find_optimal_agent(
                    self.task_requirements,
                    self.available_agents,
                    MatchingStrategy.BEST_FIT,
                )

    def test_calculate_capability_match(self):
        """Test capability match calculation"""
        # Test perfect match
        match_score = self.matcher._calculate_capability_match(
            self.mock_capability_profile, self.task_requirements
        )

        # Should be high score since agent has advanced code generation and intermediate testing
        self.assertIsInstance(match_score, float)
        self.assertGreaterEqual(match_score, 0.8)  # Should be high match
        self.assertLessEqual(match_score, 1.0)

    def test_calculate_capability_match_missing_capabilities(self):
        """Test capability match with missing capabilities"""
        # Profile with missing required capability
        incomplete_profile = AgentCapabilityProfile(
            agent_id="incomplete_agent",
            agent_name="Incomplete Agent",
            profile_generated=datetime.now(),
            capability_scores={
                CapabilityDomain.CODE_GENERATION: CapabilityScore(
                    domain=CapabilityDomain.CODE_GENERATION,
                    proficiency_level=ProficiencyLevel.ADVANCED,
                    confidence_score=0.9,
                    evidence_count=10,
                    last_updated=datetime.now(),
                )
                # Missing TESTING capability
            },
        )

        match_score = self.matcher._calculate_capability_match(
            incomplete_profile, self.task_requirements
        )

        # Should be lower score due to missing capability
        self.assertLess(match_score, 0.8)

    def test_predict_task_performance(self):
        """Test task performance prediction"""
        # Mock performance data
        mock_performance_data = Mock()
        mock_performance_data.success_rate = 0.8
        mock_performance_data.performance_trend = [0.7, 0.75, 0.8]
        self.mock_performance_analyzer.analyze_agent_performance.return_value = (
            mock_performance_data
        )

        # Mock task results for similarity
        self.mock_task_metrics.get_agent_task_results.return_value = []

        # Execute prediction
        prediction = self.matcher._predict_task_performance(
            "agent1", self.task_requirements
        )

        # Verify prediction
        self.assertIsInstance(prediction, float)
        self.assertGreaterEqual(prediction, 0.0)
        self.assertLessEqual(prediction, 1.0)

    def test_calculate_availability_score(self):
        """Test availability score calculation"""
        # Test good availability
        good_availability = AgentAvailability(
            agent_id="agent1",
            current_workload=0.2,  # Low workload
            scheduled_tasks=[],
            available_from=datetime.now(),
        )

        score = self.matcher._calculate_availability_score(
            good_availability, self.task_requirements
        )

        self.assertIsInstance(score, float)
        self.assertGreater(score, 0.5)  # Should be good score

        # Test poor availability
        poor_availability = AgentAvailability(
            agent_id="agent1",
            current_workload=0.9,  # High workload
            scheduled_tasks=["task1", "task2", "task3"],
            available_from=datetime.now(),
        )

        score_poor = self.matcher._calculate_availability_score(
            poor_availability, self.task_requirements
        )
        self.assertLess(score_poor, score)  # Should be lower than good availability

    def test_calculate_workload_balance_score(self):
        """Test workload balance score for different strategies"""
        # Test load balanced strategy
        score_balanced = self.matcher._calculate_workload_balance_score(
            self.mock_availability, MatchingStrategy.LOAD_BALANCED
        )

        # Test best fit strategy
        score_best_fit = self.matcher._calculate_workload_balance_score(
            self.mock_availability, MatchingStrategy.BEST_FIT
        )

        self.assertIsInstance(score_balanced, float)
        self.assertIsInstance(score_best_fit, float)

        # Load balanced should consider workload more heavily
        high_workload_availability = AgentAvailability(
            agent_id="agent1",
            current_workload=0.9,
            scheduled_tasks=[],
            available_from=datetime.now(),
        )

        score_balanced_high = self.matcher._calculate_workload_balance_score(
            high_workload_availability, MatchingStrategy.LOAD_BALANCED
        )

        self.assertLess(score_balanced_high, score_balanced)

    def test_calculate_agent_task_score(self):
        """Test comprehensive agent-task scoring"""
        # Mock all dependencies
        self.mock_capability_assessment.assess_agent_capabilities.return_value = (
            self.mock_capability_profile
        )

        mock_performance_data = Mock()
        mock_performance_data.success_rate = 0.8
        mock_performance_data.avg_execution_time = 150.0
        mock_performance_data.performance_trend = [0.7, 0.8, 0.85]
        mock_performance_data.total_tasks = 10
        self.mock_performance_analyzer.analyze_agent_performance.return_value = (
            mock_performance_data
        )

        self.mock_task_metrics.get_agent_task_results.return_value = []
        self.mock_task_metrics.get_agent_active_tasks.return_value = []

        with patch.object(
            self.matcher, "_get_agent_availability", return_value=self.mock_availability
        ):
            # Execute scoring
            score = self.matcher._calculate_agent_task_score(
                "agent1", self.task_requirements, MatchingStrategy.BEST_FIT
            )

        # Verify score structure
        self.assertIsInstance(score, MatchingScore)
        self.assertEqual(score.agent_id, "agent1")
        self.assertEqual(score.task_id, "test_task_001")
        self.assertGreaterEqual(score.overall_score, 0.0)
        self.assertLessEqual(score.overall_score, 1.0)
        self.assertGreaterEqual(score.capability_match, 0.0)
        self.assertLessEqual(score.capability_match, 1.0)
        self.assertIsInstance(score.strengths, list)
        self.assertIsInstance(score.concerns, list)
        self.assertIsInstance(score.recommendations, list)

    def test_batch_match_tasks(self):
        """Test batch task matching"""
        # Create multiple task requirements
        task_list = [
            TaskRequirements(
                task_id=f"task_{i}",
                task_type="implementation",
                description=f"Test task {i}",
                required_capabilities={
                    CapabilityDomain.CODE_GENERATION: ProficiencyLevel.INTERMEDIATE
                },
            )
            for i in range(3)
        ]

        # Mock dependencies
        self.mock_capability_assessment.assess_agent_capabilities.return_value = (
            self.mock_capability_profile
        )
        self.mock_performance_analyzer.analyze_agent_performance.return_value = Mock(
            success_rate=0.8, avg_execution_time=120.0, performance_trend=[]
        )
        self.mock_task_metrics.get_agent_active_tasks.return_value = []

        with patch.object(
            self.matcher, "_get_agent_availability", return_value=self.mock_availability
        ):
            # Execute batch matching
            recommendations = self.matcher.batch_match_tasks(
                task_list, self.available_agents, MatchingStrategy.BEST_FIT
            )

        # Verify batch results
        self.assertIsInstance(recommendations, dict)
        self.assertEqual(len(recommendations), 3)

        for task_id, recommendation in recommendations.items():
            self.assertIsInstance(recommendation, MatchingRecommendation)
            self.assertEqual(recommendation.task_id, task_id)

    def test_task_type_similarity(self):
        """Test task type similarity calculation"""
        # Test identical types
        similarity_identical = self.matcher._calculate_task_type_similarity(
            "implementation", "implementation"
        )
        self.assertEqual(similarity_identical, 1.0)

        # Test similar types
        similarity_similar = self.matcher._calculate_task_type_similarity(
            "code_implementation", "implementation_task"
        )
        self.assertGreater(similarity_similar, 0.0)
        self.assertLess(similarity_similar, 1.0)

        # Test different types
        similarity_different = self.matcher._calculate_task_type_similarity(
            "implementation", "documentation"
        )
        self.assertEqual(similarity_different, 0.0)

    def test_strategy_weights(self):
        """Test different strategy weight configurations"""
        # Test all strategies
        strategies = [
            MatchingStrategy.BEST_FIT,
            MatchingStrategy.LOAD_BALANCED,
            MatchingStrategy.SKILL_DEVELOPMENT,
            MatchingStrategy.RISK_MINIMIZED,
        ]

        for strategy in strategies:
            weights = self.matcher._get_strategy_weights(strategy)

            # Verify weights structure
            self.assertIsInstance(weights, dict)
            self.assertIn("capability", weights)
            self.assertIn("performance", weights)
            self.assertIn("availability", weights)
            self.assertIn("workload", weights)

            # Verify weights sum approximately to 1.0
            total_weight = sum(weights.values())
            self.assertAlmostEqual(total_weight, 1.0, places=2)

class TestTaskRequirements(unittest.TestCase):
    """Test cases for TaskRequirements dataclass"""

    def test_initialization(self):
        """Test TaskRequirements initialization"""
        requirements = TaskRequirements(
            task_id="test_task",
            task_type="implementation",
            description="Test task description",
            required_capabilities={
                CapabilityDomain.CODE_GENERATION: ProficiencyLevel.INTERMEDIATE
            },
        )

        self.assertEqual(requirements.task_id, "test_task")
        self.assertEqual(requirements.task_type, "implementation")
        self.assertEqual(requirements.description, "Test task description")
        self.assertIsInstance(requirements.required_capabilities, dict)
        self.assertIsInstance(requirements.preferred_capabilities, dict)
        self.assertEqual(requirements.priority, TaskPriority.MEDIUM)
        self.assertEqual(requirements.urgency, TaskUrgency.NORMAL)

class TestMatchingScore(unittest.TestCase):
    """Test cases for MatchingScore dataclass"""

    def test_initialization(self):
        """Test MatchingScore initialization"""
        score = MatchingScore(
            agent_id="test_agent",
            task_id="test_task",
            capability_match=0.8,
            availability_score=0.7,
            performance_prediction=0.9,
            workload_balance=0.6,
            overall_score=0.75,
            confidence_level=0.85,
        )

        self.assertEqual(score.agent_id, "test_agent")
        self.assertEqual(score.task_id, "test_task")
        self.assertEqual(score.capability_match, 0.8)
        self.assertEqual(score.overall_score, 0.75)
        self.assertIsInstance(score.strengths, list)
        self.assertIsInstance(score.concerns, list)
        self.assertIsInstance(score.recommendations, list)

if __name__ == "__main__":
    unittest.main()
