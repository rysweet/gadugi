#!/usr/bin/env python3
"""Tests for Team Coach Engine."""

import os

# Add src to path for imports
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "orchestrator"))

from team_coach_engine import (
    LearningEngine,
    LearningInsight,
    Pattern,
    PatternRecognizer,
    PerformanceAnalyzer,
    PerformanceMetrics,
    Recommendation,
    RecommendationEngine,
    ResourceUsage,
    TeamCoachEngine,
    WorkflowData,
    WorkflowOutcomes,
    WorkflowStep,
    _parse_workflow_data,
    run_team_coach,
)


class TestWorkflowData:
    """Test workflow data structures."""

    def test_workflow_step_creation(self) -> None:
        """Test WorkflowStep creation."""
        step = WorkflowStep(
            agent="test-agent",
            action="test-action",
            duration_seconds=30.5,
            success=True,
            metadata={"key": "value"},
            timestamp=datetime.now(),
        )

        assert step.agent == "test-agent"
        assert step.action == "test-action"
        assert step.duration_seconds == 30.5
        assert step.success is True
        assert step.metadata == {"key": "value"}

    def test_resource_usage_creation(self) -> None:
        """Test ResourceUsage creation."""
        resource_usage = ResourceUsage(
            peak_memory_mb=512.0, cpu_time_seconds=120.0, disk_io_mb=25.5,
        )

        assert resource_usage.peak_memory_mb == 512.0
        assert resource_usage.cpu_time_seconds == 120.0
        assert resource_usage.disk_io_mb == 25.5
        assert resource_usage.network_io_mb == 0.0  # Default value

    def test_workflow_outcomes_creation(self) -> None:
        """Test WorkflowOutcomes creation."""
        outcomes = WorkflowOutcomes(
            files_created=3,
            tests_written=15,
            lines_of_code=250,
            success_rate=0.95,
            user_satisfaction="high",
        )

        assert outcomes.files_created == 3
        assert outcomes.tests_written == 15
        assert outcomes.lines_of_code == 250
        assert outcomes.success_rate == 0.95
        assert outcomes.user_satisfaction == "high"
        assert outcomes.errors_encountered == 0  # Default value


class TestPerformanceAnalyzer:
    """Test the PerformanceAnalyzer class."""

    def setup_method(self) -> None:
        self.analyzer = PerformanceAnalyzer()
        self.sample_workflow = self._create_sample_workflow()

    def _create_sample_workflow(self):
        """Create a sample workflow for testing."""
        start_time = datetime.now() - timedelta(minutes=2)
        end_time = datetime.now()

        return WorkflowData(
            workflow_id="test_workflow_001",
            agents_used=["orchestrator", "code-writer"],
            task_sequence=[
                WorkflowStep("orchestrator", "coordinate", 15, True, {}, start_time),
                WorkflowStep(
                    "code-writer",
                    "generate",
                    45,
                    True,
                    {},
                    start_time + timedelta(seconds=15),
                ),
            ],
            resource_usage=ResourceUsage(256, 60, 10),
            outcomes=WorkflowOutcomes(2, 8, 150, 1.0, "high"),
            start_time=start_time,
            end_time=end_time,
            project_context="test_project",
        )

    def test_analyze_workflow_performance(self) -> None:
        """Test workflow performance analysis."""
        metrics = self.analyzer.analyze_workflow_performance(self.sample_workflow)

        assert isinstance(metrics, PerformanceMetrics)
        assert 0.0 <= metrics.overall_score <= 10.0
        assert 0.0 <= metrics.speed_score <= 10.0
        assert 0.0 <= metrics.quality_score <= 10.0
        assert 0.0 <= metrics.resource_efficiency_score <= 10.0
        assert 0.0 <= metrics.coordination_score <= 10.0

    def test_calculate_speed_score(self) -> None:
        """Test speed score calculation."""
        score = self.analyzer._calculate_speed_score(self.sample_workflow)

        assert isinstance(score, float)
        assert 2.0 <= score <= 10.0  # Should be in valid range

    def test_calculate_quality_score(self) -> None:
        """Test quality score calculation."""
        score = self.analyzer._calculate_quality_score(self.sample_workflow)

        assert isinstance(score, float)
        assert 0.0 <= score <= 10.0

        # High success rate and satisfaction should yield good score
        assert score >= 8.0  # Sample workflow has high quality

    def test_calculate_resource_efficiency_score(self) -> None:
        """Test resource efficiency score calculation."""
        score = self.analyzer._calculate_resource_efficiency_score(self.sample_workflow)

        assert isinstance(score, float)
        assert 2.0 <= score <= 10.0

    def test_calculate_coordination_score(self) -> None:
        """Test coordination score calculation."""
        score = self.analyzer._calculate_coordination_score(self.sample_workflow)

        assert isinstance(score, float)
        assert 5.0 <= score <= 10.0  # Sample workflow has good coordination

    def test_single_step_coordination_score(self) -> None:
        """Test coordination score for single-step workflow."""
        single_step_workflow = WorkflowData(
            workflow_id="single_step",
            agents_used=["code-writer"],
            task_sequence=[
                WorkflowStep("code-writer", "generate", 30, True, {}, datetime.now()),
            ],
            resource_usage=ResourceUsage(256, 30, 5),
            outcomes=WorkflowOutcomes(1, 0, 50, 1.0, "high"),
            start_time=datetime.now() - timedelta(seconds=30),
            end_time=datetime.now(),
            project_context="test",
        )

        score = self.analyzer._calculate_coordination_score(single_step_workflow)
        assert score == 10.0  # Single step should have perfect coordination


class TestPatternRecognizer:
    """Test the PatternRecognizer class."""

    def setup_method(self) -> None:
        self.recognizer = PatternRecognizer()
        self.sample_workflows = self._create_sample_workflows()

    def _create_sample_workflows(self):
        """Create sample workflows for pattern testing."""
        workflows = []
        base_time = datetime.now() - timedelta(hours=1)

        # Create successful workflows with similar patterns
        for i in range(5):
            workflows.append(
                WorkflowData(
                    workflow_id=f"successful_{i}",
                    agents_used=["orchestrator", "code-writer", "test-writer"],
                    task_sequence=[
                        WorkflowStep(
                            "orchestrator", "coordinate", 15, True, {}, base_time,
                        ),
                        WorkflowStep(
                            "code-writer",
                            "generate",
                            30,
                            True,
                            {},
                            base_time + timedelta(seconds=15),
                        ),
                        WorkflowStep(
                            "test-writer",
                            "generate_tests",
                            20,
                            True,
                            {},
                            base_time + timedelta(seconds=45),
                        ),
                    ],
                    resource_usage=ResourceUsage(256, 65, 12),
                    outcomes=WorkflowOutcomes(2, 10, 120, 0.95, "high"),
                    start_time=base_time,
                    end_time=base_time + timedelta(seconds=65),
                    project_context="test_project",
                ),
            )

        # Create some failed workflows
        for i in range(2):
            workflows.append(
                WorkflowData(
                    workflow_id=f"failed_{i}",
                    agents_used=["orchestrator", "code-writer"],
                    task_sequence=[
                        WorkflowStep(
                            "orchestrator", "coordinate", 15, True, {}, base_time,
                        ),
                        WorkflowStep(
                            "code-writer",
                            "generate",
                            30,
                            False,
                            {},
                            base_time + timedelta(seconds=15),
                        ),
                    ],
                    resource_usage=ResourceUsage(512, 45, 8),
                    outcomes=WorkflowOutcomes(0, 0, 0, 0.2, "low"),
                    start_time=base_time,
                    end_time=base_time + timedelta(seconds=45),
                    project_context="test_project",
                ),
            )

        return workflows

    def test_identify_patterns(self) -> None:
        """Test pattern identification."""
        patterns = self.recognizer.identify_patterns(self.sample_workflows)

        assert isinstance(patterns, list)
        assert len(patterns) > 0

        # Should find success patterns
        success_patterns = [p for p in patterns if p.pattern_type == "success"]
        assert len(success_patterns) > 0

    def test_identify_success_patterns(self) -> None:
        """Test identification of success patterns."""
        patterns = self.recognizer._identify_success_patterns(self.sample_workflows)

        assert isinstance(patterns, list)

        for pattern in patterns:
            assert pattern.pattern_type == "success"
            assert 0.0 <= pattern.frequency <= 1.0
            assert pattern.impact in ["low", "medium", "high"]
            assert 0.0 <= pattern.confidence <= 1.0

    def test_identify_failure_patterns(self) -> None:
        """Test identification of failure patterns."""
        patterns = self.recognizer._identify_failure_patterns(self.sample_workflows)

        assert isinstance(patterns, list)

        for pattern in patterns:
            assert pattern.pattern_type == "failure"
            assert 0.0 <= pattern.frequency <= 1.0
            assert pattern.impact in ["low", "medium", "high"]

    def test_identify_optimization_patterns(self) -> None:
        """Test identification of optimization patterns."""
        patterns = self.recognizer._identify_optimization_patterns(
            self.sample_workflows,
        )

        assert isinstance(patterns, list)

        for pattern in patterns:
            assert pattern.pattern_type == "optimization"
            assert 0.0 <= pattern.frequency <= 1.0

    def test_identify_bottleneck_patterns(self) -> None:
        """Test identification of bottleneck patterns."""
        patterns = self.recognizer._identify_bottleneck_patterns(self.sample_workflows)

        assert isinstance(patterns, list)

        for pattern in patterns:
            assert pattern.pattern_type == "bottleneck"
            assert pattern.impact in ["low", "medium", "high"]

    def test_empty_workflows_list(self) -> None:
        """Test pattern recognition with empty workflows list."""
        patterns = self.recognizer.identify_patterns([])

        assert patterns == []

    def test_single_workflow(self) -> None:
        """Test pattern recognition with single workflow."""
        patterns = self.recognizer.identify_patterns([self.sample_workflows[0]])

        # Should handle single workflow gracefully
        assert isinstance(patterns, list)


class TestLearningEngine:
    """Test the LearningEngine class."""

    def setup_method(self) -> None:
        self.learning_engine = LearningEngine()
        self.sample_patterns = [
            Pattern(
                "success",
                "Test success pattern",
                0.8,
                "high",
                0.9,
                ["workflow1", "workflow2"],
            ),
            Pattern(
                "failure", "Test failure pattern", 0.3, "medium", 0.7, ["workflow3"],
            ),
            Pattern(
                "optimization",
                "Test optimization pattern",
                0.5,
                "medium",
                0.6,
                ["workflow1"],
            ),
        ]
        self.sample_workflows = self._create_sample_workflows()

    def _create_sample_workflows(self):
        """Create sample workflows for testing."""
        return [
            WorkflowData(
                workflow_id="test1",
                agents_used=["orchestrator"],
                task_sequence=[],
                resource_usage=ResourceUsage(128, 30, 5),
                outcomes=WorkflowOutcomes(1, 5, 50, 1.0, "high"),
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(seconds=30),
                project_context="test",
            ),
        ]

    def test_extract_learning_insights(self) -> None:
        """Test extraction of learning insights."""
        insights = self.learning_engine.extract_learning_insights(
            self.sample_workflows, self.sample_patterns,
        )

        assert isinstance(insights, list)

        for insight in insights:
            assert isinstance(insight, LearningInsight)
            assert insight.insight_type in [
                "best_practice",
                "anti_pattern",
                "optimization_opportunity",
            ]
            assert 0.0 <= insight.confidence <= 1.0
            assert isinstance(insight.supporting_evidence, list)
            assert isinstance(insight.applicable_contexts, list)

    def test_extract_resource_insights(self) -> None:
        """Test extraction of resource-related insights."""
        insights = self.learning_engine._extract_resource_insights(
            self.sample_workflows,
        )

        assert isinstance(insights, list)
        # Low resource usage shouldn't generate insights
        assert len(insights) == 0

    def test_extract_coordination_insights(self) -> None:
        """Test extraction of coordination-related insights."""
        insights = self.learning_engine._extract_coordination_insights(
            self.sample_workflows,
        )

        assert isinstance(insights, list)

    def test_high_resource_insight_generation(self) -> None:
        """Test insight generation for high resource usage."""
        high_resource_workflows = [
            WorkflowData(
                workflow_id="high_resource",
                agents_used=["orchestrator"],
                task_sequence=[],
                resource_usage=ResourceUsage(1024, 180, 50),  # High resource usage
                outcomes=WorkflowOutcomes(1, 0, 100, 1.0, "high"),
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(seconds=180),
                project_context="test",
            ),
        ]

        insights = self.learning_engine._extract_resource_insights(
            high_resource_workflows,
        )

        # Should generate insights for high resource usage
        memory_insights = [i for i in insights if "memory" in i.description.lower()]
        cpu_insights = [i for i in insights if "cpu" in i.description.lower()]

        assert len(memory_insights) > 0 or len(cpu_insights) > 0


class TestRecommendationEngine:
    """Test the RecommendationEngine class."""

    def setup_method(self) -> None:
        self.recommendation_engine = RecommendationEngine()
        self.sample_metrics = PerformanceMetrics(
            efficiency_score=7.5,
            speed_score=6.0,
            quality_score=8.0,
            resource_efficiency_score=5.0,
            coordination_score=7.0,
            overall_score=6.5,
        )
        self.sample_patterns = [
            Pattern("bottleneck", "Slow code generation", 0.8, "high", 0.9, []),
            Pattern("optimization", "High memory usage", 0.6, "medium", 0.7, []),
        ]
        self.sample_insights = [
            LearningInsight(
                "optimization_opportunity",
                "Parallel processing opportunity",
                0.8,
                [],
                [],
            ),
        ]

    def test_generate_recommendations(self) -> None:
        """Test recommendation generation."""
        recommendations = self.recommendation_engine.generate_recommendations(
            self.sample_metrics, self.sample_patterns, self.sample_insights,
        )

        assert isinstance(recommendations, list)

        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.type in [
                "workflow_optimization",
                "agent_coordination",
                "resource_management",
            ]
            assert rec.priority in ["high", "medium", "low"]
            assert rec.implementation_effort in ["low", "medium", "high"]
            assert rec.risk_level in ["low", "medium", "high"]

    def test_generate_performance_recommendations(self) -> None:
        """Test performance-based recommendations."""
        recommendations = (
            self.recommendation_engine._generate_performance_recommendations(
                self.sample_metrics,
            )
        )

        assert isinstance(recommendations, list)
        assert (
            len(recommendations) > 0
        )  # Should generate recommendations for low scores

        # Should recommend resource optimization (score is 5.0, below threshold)
        resource_recs = [
            r for r in recommendations if "resource" in r.description.lower()
        ]
        assert len(resource_recs) > 0

    def test_generate_pattern_recommendations(self) -> None:
        """Test pattern-based recommendations."""
        recommendations = self.recommendation_engine._generate_pattern_recommendations(
            self.sample_patterns,
        )

        assert isinstance(recommendations, list)

        # Should recommend bottleneck resolution
        bottleneck_recs = [
            r for r in recommendations if "bottleneck" in r.description.lower()
        ]
        assert len(bottleneck_recs) > 0

    def test_generate_insight_recommendations(self) -> None:
        """Test insight-based recommendations."""
        recommendations = self.recommendation_engine._generate_insight_recommendations(
            self.sample_insights,
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0  # Should generate recommendation from insight

    def test_recommendation_sorting(self) -> None:
        """Test that recommendations are properly sorted."""
        recommendations = self.recommendation_engine.generate_recommendations(
            self.sample_metrics, self.sample_patterns, self.sample_insights,
        )

        if len(recommendations) > 1:
            # Should be sorted by priority (high first)
            priorities = [r.priority for r in recommendations]
            priorities.count("high")
            priorities.count("medium")
            priorities.count("low")

            # High priority should come first
            assert recommendations[0].priority in ["high", "medium"]


class TestTeamCoachEngine:
    """Test the main TeamCoachEngine."""

    def setup_method(self) -> None:
        self.engine = TeamCoachEngine()
        self.sample_request = self._create_sample_request()

    def _create_sample_request(self):
        """Create a sample team coach request."""
        from team_coach_engine import TeamCoachRequest

        workflow_data = WorkflowData(
            workflow_id="test_workflow",
            agents_used=["orchestrator", "code-writer"],
            task_sequence=[
                WorkflowStep(
                    "orchestrator", "coordinate", 15, True, {}, datetime.now(),
                ),
                WorkflowStep(
                    "code-writer",
                    "generate",
                    30,
                    True,
                    {},
                    datetime.now() + timedelta(seconds=15),
                ),
            ],
            resource_usage=ResourceUsage(256, 45, 10),
            outcomes=WorkflowOutcomes(2, 5, 100, 1.0, "high"),
            start_time=datetime.now() - timedelta(seconds=45),
            end_time=datetime.now(),
            project_context="test_project",
        )

        return TeamCoachRequest(
            analysis_type="performance",
            workflow_data=workflow_data,
            historical_context={},
            reflection_scope="session",
        )

    def test_process_request(self) -> None:
        """Test processing a team coach request."""
        response = self.engine.process_request(self.sample_request)

        assert response.success is True
        assert "performance_score" in response.analysis_results
        assert "efficiency_metrics" in response.analysis_results
        assert isinstance(response.recommendations, list)
        assert isinstance(response.learning_insights, list)
        assert isinstance(response.patterns_identified, list)
        assert len(response.errors) == 0

    def test_get_relevant_historical_workflows(self) -> None:
        """Test getting relevant historical workflows."""
        # Add some historical workflows
        self.engine.historical_workflows = [
            self.sample_request.workflow_data,  # Same project context
        ]

        relevant = self.engine._get_relevant_historical_workflows(self.sample_request)

        assert len(relevant) >= 1  # Should include current workflow
        assert self.sample_request.workflow_data in relevant

    def test_calculate_performance_trends(self) -> None:
        """Test performance trend calculation."""
        workflows = [self.sample_request.workflow_data]
        trends = self.engine._calculate_performance_trends(workflows)

        assert isinstance(trends, dict)
        assert (
            "insufficient_data" in trends
        )  # Single workflow should indicate insufficient data

    def test_score_to_label(self) -> None:
        """Test score to label conversion."""
        assert self.engine._score_to_label(9.0) == "excellent"
        assert self.engine._score_to_label(7.0) == "good"
        assert self.engine._score_to_label(5.0) == "fair"
        assert self.engine._score_to_label(3.0) == "poor"

    def test_exception_handling(self) -> None:
        """Test exception handling in engine."""
        # Create invalid request to trigger exception
        invalid_request = self.sample_request
        invalid_request.workflow_data = None  # This should cause issues

        response = self.engine.process_request(invalid_request)

        # Should handle gracefully
        assert response.success is False
        assert len(response.errors) > 0


class TestRunTeamCoach:
    """Test the run_team_coach entry point."""

    def test_successful_request(self) -> None:
        """Test successful team coach request."""
        request_data = {
            "analysis_type": "performance",
            "workflow_data": {
                "workflow_id": "test_workflow",
                "agents_used": ["orchestrator", "code-writer"],
                "task_sequence": [
                    {
                        "agent": "orchestrator",
                        "action": "coordinate",
                        "duration_seconds": 15,
                        "success": True,
                        "metadata": {},
                    },
                    {
                        "agent": "code-writer",
                        "action": "generate",
                        "duration_seconds": 30,
                        "success": True,
                        "metadata": {},
                    },
                ],
                "resource_usage": {
                    "peak_memory_mb": 256,
                    "cpu_time_seconds": 45,
                    "disk_io_mb": 10,
                },
                "outcomes": {
                    "files_created": 2,
                    "tests_written": 5,
                    "lines_of_code": 100,
                    "success_rate": 1.0,
                    "user_satisfaction": "high",
                },
                "project_context": "test_project",
            },
            "historical_context": {},
            "reflection_scope": "session",
        }

        result = run_team_coach(request_data)

        assert result["success"] is True
        assert "analysis_results" in result
        assert "recommendations" in result
        assert "learning_insights" in result
        assert "performance_trends" in result
        assert "patterns_identified" in result
        assert len(result["errors"]) == 0

    def test_parse_workflow_data(self) -> None:
        """Test parsing workflow data from dictionary."""
        data = {
            "workflow_id": "test_workflow",
            "agents_used": ["orchestrator"],
            "task_sequence": [
                {
                    "agent": "orchestrator",
                    "action": "test_action",
                    "duration_seconds": 30,
                    "success": True,
                    "metadata": {"key": "value"},
                },
            ],
            "resource_usage": {
                "peak_memory_mb": 256,
                "cpu_time_seconds": 30,
                "disk_io_mb": 5,
            },
            "outcomes": {
                "files_created": 1,
                "tests_written": 3,
                "lines_of_code": 50,
                "success_rate": 1.0,
                "user_satisfaction": "high",
            },
            "project_context": "test",
        }

        workflow_data = _parse_workflow_data(data)

        assert workflow_data.workflow_id == "test_workflow"
        assert workflow_data.agents_used == ["orchestrator"]
        assert len(workflow_data.task_sequence) == 1
        assert workflow_data.task_sequence[0].agent == "orchestrator"
        assert workflow_data.resource_usage.peak_memory_mb == 256
        assert workflow_data.outcomes.files_created == 1

    def test_invalid_request_handling(self) -> None:
        """Test handling of invalid requests."""
        invalid_request = {"invalid": "data"}

        result = run_team_coach(invalid_request)

        # Should handle gracefully
        assert "success" in result
        assert "errors" in result

    def test_exception_handling(self) -> None:
        """Test exception handling in entry point."""
        # Pass None to trigger exception
        result = run_team_coach(None)

        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "Team coach error" in result["errors"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
