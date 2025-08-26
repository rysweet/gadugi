"""
Tests for TeamCoach Performance Analytics

Unit tests for the AgentPerformanceAnalyzer class and related functionality.
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Import components to test
from ..phase1.performance_analytics import (
    AgentPerformanceAnalyzer,
    AgentPerformanceData,
    TeamPerformanceData,
    AnalysisError,
)
from ....shared.task_tracking import TaskMetrics
from ....shared.state_management import StateManager
try:
    from ....shared.utils.error_handling import ErrorHandler
except ImportError:
    # Fallback stub for ErrorHandler
    class ErrorHandler:
        def __init__(self, config=None):
            pass


class TestAgentPerformanceAnalyzer(unittest.TestCase):
    """Test cases for AgentPerformanceAnalyzer"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_state_manager = Mock(spec=StateManager)
        self.mock_task_metrics = Mock(spec=TaskMetrics)
        self.mock_error_handler = Mock(spec=ErrorHandler)

        self.analyzer = AgentPerformanceAnalyzer(
            state_manager=self.mock_state_manager,
            task_metrics=self.mock_task_metrics,
            error_handler=self.mock_error_handler,
        )

        # Sample data
        self.agent_id = "test_agent_001"
        self.time_period = (datetime.now() - timedelta(days=7), datetime.now())

        # Mock task results
        self.mock_task_results = [
            Mock(success=True, execution_time=120.0, quality_score=85.0),
            Mock(success=True, execution_time=150.0, quality_score=90.0),
            Mock(success=False, execution_time=200.0, quality_score=70.0),
            Mock(success=True, execution_time=100.0, quality_score=95.0),
        ]

    def test_initialization(self):
        """Test proper initialization of AgentPerformanceAnalyzer"""
        self.assertIsInstance(self.analyzer, AgentPerformanceAnalyzer)
        self.assertIsNotNone(self.analyzer.state_manager)
        self.assertIsNotNone(self.analyzer.task_metrics)
        self.assertIsNotNone(self.analyzer.error_handler)
        self.assertIsInstance(self.analyzer.performance_cache, dict)
        self.assertIsInstance(self.analyzer.analysis_config, dict)

    def test_analyze_agent_performance_success(self):
        """Test successful agent performance analysis"""
        # Mock dependencies
        self.mock_task_metrics.get_agent_task_results.return_value = (
            self.mock_task_results
        )
        self.mock_task_metrics.get_agent_execution_times.return_value = [
            120.0,
            150.0,
            200.0,
            100.0,
        ]
        self.mock_task_metrics.get_agent_resource_usage.return_value = []
        self.mock_task_metrics.get_agent_quality_metrics.return_value = []
        self.mock_task_metrics.get_agent_collaboration_metrics.return_value = []

        # Mock agent config
        mock_config = Mock()
        mock_config.name = "Test Agent"
        self.mock_state_manager.get_agent_config.return_value = {"name": "Test Agent"}

        # Execute analysis
        result = self.analyzer.analyze_agent_performance(
            self.agent_id, self.time_period
        )

        # Verify result
        self.assertIsInstance(result, AgentPerformanceData)
        self.assertEqual(result.agent_id, self.agent_id)
        self.assertEqual(result.agent_name, "Test Agent")
        self.assertEqual(result.total_tasks, 4)
        self.assertEqual(result.completed_tasks, 3)
        self.assertEqual(result.failed_tasks, 1)
        self.assertEqual(result.success_rate, 0.75)  # 3/4
        self.assertGreater(result.avg_execution_time, 0)

    def test_analyze_agent_performance_invalid_agent_id(self):
        """Test analysis with invalid agent ID"""
        with self.assertRaises(ValueError):
            self.analyzer.analyze_agent_performance("", self.time_period)

    def test_analyze_agent_performance_no_data(self):
        """Test analysis when no task data is available"""
        # Mock no task results
        self.mock_task_metrics.get_agent_task_results.return_value = []
        self.mock_task_metrics.get_agent_execution_times.return_value = []
        self.mock_task_metrics.get_agent_resource_usage.return_value = []
        self.mock_task_metrics.get_agent_quality_metrics.return_value = []
        self.mock_task_metrics.get_agent_collaboration_metrics.return_value = []

        self.mock_state_manager.get_agent_config.return_value = {"name": "Test Agent"}

        # Execute analysis
        result = self.analyzer.analyze_agent_performance(
            self.agent_id, self.time_period
        )

        # Verify result with no data
        self.assertEqual(result.total_tasks, 0)
        self.assertEqual(result.success_rate, 0.0)
        self.assertEqual(result.avg_execution_time, 0.0)

    def test_calculate_success_metrics(self):
        """Test success metrics calculation"""
        # Create performance data
        performance_data = AgentPerformanceData(
            agent_id=self.agent_id,
            agent_name="Test Agent",
            time_period=self.time_period,
        )

        # Mock task results
        self.mock_task_metrics.get_agent_task_results.return_value = (
            self.mock_task_results
        )

        # Execute calculation
        self.analyzer._calculate_success_metrics(performance_data, self.time_period)

        # Verify calculations
        self.assertEqual(performance_data.total_tasks, 4)
        self.assertEqual(performance_data.completed_tasks, 3)
        self.assertEqual(performance_data.failed_tasks, 1)
        self.assertEqual(performance_data.success_rate, 0.75)

    def test_analyze_execution_times(self):
        """Test execution time analysis"""
        performance_data = AgentPerformanceData(
            agent_id=self.agent_id,
            agent_name="Test Agent",
            time_period=self.time_period,
        )

        execution_times = [120.0, 150.0, 200.0, 100.0]
        self.mock_task_metrics.get_agent_execution_times.return_value = execution_times

        # Execute analysis
        self.analyzer._analyze_execution_times(performance_data, self.time_period)

        # Verify calculations
        self.assertEqual(
            performance_data.avg_execution_time, 142.5
        )  # (120+150+200+100)/4
        self.assertEqual(
            performance_data.median_execution_time, 135.0
        )  # median of sorted list
        self.assertEqual(performance_data.min_execution_time, 100.0)
        self.assertEqual(performance_data.max_execution_time, 200.0)

    def test_generate_performance_report(self):
        """Test performance report generation"""
        # Mock successful analysis
        mock_performance_data = AgentPerformanceData(
            agent_id=self.agent_id,
            agent_name="Test Agent",
            time_period=self.time_period,
            total_tasks=10,
            success_rate=0.8,
            avg_execution_time=150.0,
            resource_efficiency_score=75.0,
        )

        with patch.object(
            self.analyzer,
            "analyze_agent_performance",
            return_value=mock_performance_data,
        ):
            # Generate report
            report = self.analyzer.generate_performance_report(
                self.agent_id, self.time_period, detailed=True
            )

            # Verify report structure
            self.assertIsInstance(report, dict)
            self.assertIn("agent_id", report)
            self.assertIn("summary", report)
            self.assertIn("detailed_metrics", report)
            self.assertEqual(report["agent_id"], self.agent_id)
            self.assertIn("overall_score", report["summary"])

    def test_calculate_overall_score(self):
        """Test overall performance score calculation"""
        performance_data = AgentPerformanceData(
            agent_id=self.agent_id,
            agent_name="Test Agent",
            time_period=self.time_period,
            success_rate=0.8,
            avg_execution_time=120.0,
            resource_efficiency_score=75.0,
            code_quality_score=85.0,
        )

        # Calculate overall score
        score = self.analyzer._calculate_overall_score(performance_data)

        # Verify score is reasonable
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_caching_behavior(self):
        """Test performance data caching"""
        # Mock dependencies
        self.mock_task_metrics.get_agent_task_results.return_value = (
            self.mock_task_results
        )
        self.mock_task_metrics.get_agent_execution_times.return_value = [120.0, 150.0]
        self.mock_task_metrics.get_agent_resource_usage.return_value = []
        self.mock_task_metrics.get_agent_quality_metrics.return_value = []
        self.mock_task_metrics.get_agent_collaboration_metrics.return_value = []
        self.mock_state_manager.get_agent_config.return_value = {"name": "Test Agent"}

        # First call - should analyze
        self.analyzer.analyze_agent_performance(self.agent_id, self.time_period)

        # Second call - should use cache
        self.analyzer.analyze_agent_performance(self.agent_id, self.time_period)

        # Verify cache was used (same object)
        cache_key = f"{self.agent_id}_{self.time_period[0].isoformat()}_{self.time_period[1].isoformat()}"
        self.assertIn(cache_key, self.analyzer.performance_cache)

        # Verify get_agent_task_results was called only once (due to caching)
        self.assertEqual(self.mock_task_metrics.get_agent_task_results.call_count, 1)

    def test_error_handling(self):
        """Test error handling in analysis"""
        # Mock exception in task metrics
        self.mock_task_metrics.get_agent_task_results.side_effect = Exception(
            "Mock error"
        )

        # Should raise AnalysisError
        with self.assertRaises(AnalysisError):
            self.analyzer.analyze_agent_performance(self.agent_id, self.time_period)

    def test_trend_analysis(self):
        """Test performance trend analysis"""
        performance_data = AgentPerformanceData(
            agent_id=self.agent_id,
            agent_name="Test Agent",
            time_period=self.time_period,
        )

        # Mock trend data
        with patch.object(
            self.analyzer,
            "_get_period_performance_score",
            side_effect=[0.6, 0.7, 0.8, 0.75, 0.85],
        ):
            self.analyzer._analyze_performance_trends(
                performance_data, self.time_period
            )

            # Verify trend data
            self.assertEqual(len(performance_data.performance_trend), 5)
            self.assertIsInstance(performance_data.performance_trend, list)

    def test_improvement_area_identification(self):
        """Test identification of improvement areas"""
        performance_data = AgentPerformanceData(
            agent_id=self.agent_id,
            agent_name="Test Agent",
            time_period=self.time_period,
            success_rate=0.7,  # Below 80% threshold
            avg_execution_time=400.0,  # Above 300s threshold
            resource_efficiency_score=50.0,  # Below 60 threshold
            code_quality_score=65.0,  # Below 70 threshold
            collaboration_success_rate=0.6,  # Below 70% threshold
            collaboration_frequency=5,  # Has collaboration
        )

        # Execute identification
        self.analyzer._identify_improvement_areas(performance_data)

        # Verify improvement areas were identified
        self.assertGreater(len(performance_data.areas_for_improvement), 0)

        # Check specific improvements
        improvement_text = " ".join(performance_data.areas_for_improvement)
        self.assertIn("Success rate", improvement_text)
        self.assertIn("execution time", improvement_text)
        self.assertIn("Resource efficiency", improvement_text)
        self.assertIn("Code quality", improvement_text)


class TestAgentPerformanceData(unittest.TestCase):
    """Test cases for AgentPerformanceData dataclass"""

    def test_initialization(self):
        """Test AgentPerformanceData initialization"""
        time_period = (datetime.now() - timedelta(days=1), datetime.now())

        data = AgentPerformanceData(
            agent_id="test_agent", agent_name="Test Agent", time_period=time_period
        )

        self.assertEqual(data.agent_id, "test_agent")
        self.assertEqual(data.agent_name, "Test Agent")
        self.assertEqual(data.time_period, time_period)
        self.assertEqual(data.total_tasks, 0)
        self.assertEqual(data.success_rate, 0.0)
        self.assertIsInstance(data.performance_trend, list)
        self.assertIsInstance(data.recent_improvements, list)
        self.assertIsInstance(data.areas_for_improvement, list)


class TestTeamPerformanceData(unittest.TestCase):
    """Test cases for TeamPerformanceData dataclass"""

    def test_initialization(self):
        """Test TeamPerformanceData initialization"""
        time_period = (datetime.now() - timedelta(days=1), datetime.now())
        team_composition = ["agent1", "agent2", "agent3"]

        data = TeamPerformanceData(
            team_composition=team_composition, time_period=time_period
        )

        self.assertEqual(data.team_composition, team_composition)
        self.assertEqual(data.time_period, time_period)
        self.assertEqual(data.team_efficiency_score, 0.0)
        self.assertIsInstance(data.agent_performances, dict)
        self.assertIsInstance(data.performance_trajectory, list)
        self.assertIsInstance(data.optimization_opportunities, list)


if __name__ == "__main__":
    unittest.main()
