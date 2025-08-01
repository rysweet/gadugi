"""
TeamCoach Phase 1: Agent Performance Analytics

This module provides comprehensive agent performance monitoring and analysis capabilities.
The AgentPerformanceAnalyzer class tracks, analyzes, and reports on individual agent and
team performance metrics to enable intelligent coaching and optimization.

Key Features:
- Comprehensive performance metric tracking
- Success rate and efficiency analysis  
- Resource utilization monitoring
- Quality assessment and trend analysis
- Collaboration effectiveness measurement
- Performance report generation
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

# Import shared modules
from ...shared.interfaces import (
    AgentMetrics, PerformanceMetrics, AgentConfig, TaskResult
)
from ...shared.task_tracking import TaskMetrics
from ...shared.utils.error_handling import ErrorHandler, CircuitBreaker
from ...shared.state_management import StateManager


class PerformanceCategory(Enum):
    """Categories for performance analysis"""
    SPEED = "speed"
    QUALITY = "quality" 
    EFFICIENCY = "efficiency"
    RELIABILITY = "reliability"
    COLLABORATION = "collaboration"


@dataclass
class AgentPerformanceData:
    """Data structure for agent performance metrics"""
    agent_id: str
    agent_name: str
    time_period: Tuple[datetime, datetime]
    
    # Core performance metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    
    # Timing metrics
    avg_execution_time: float = 0.0
    median_execution_time: float = 0.0
    min_execution_time: float = 0.0
    max_execution_time: float = 0.0
    
    # Resource metrics
    avg_memory_usage: float = 0.0
    avg_cpu_usage: float = 0.0
    resource_efficiency_score: float = 0.0
    
    # Quality metrics
    code_quality_score: float = 0.0
    test_coverage: float = 0.0
    error_rate: float = 0.0
    
    # Collaboration metrics
    collaboration_frequency: int = 0
    collaboration_success_rate: float = 0.0
    communication_score: float = 0.0
    
    # Trend data
    performance_trend: List[float] = field(default_factory=list)
    recent_improvements: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)


@dataclass
class TeamPerformanceData:
    """Data structure for team-wide performance metrics"""
    team_composition: List[str]
    time_period: Tuple[datetime, datetime]
    
    # Team metrics
    team_efficiency_score: float = 0.0
    coordination_effectiveness: float = 0.0
    conflict_frequency: int = 0
    resource_utilization: float = 0.0
    
    # Individual agent summaries
    agent_performances: Dict[str, AgentPerformanceData] = field(default_factory=dict)
    
    # Team trends
    performance_trajectory: List[float] = field(default_factory=list)
    optimization_opportunities: List[str] = field(default_factory=list)


class AgentPerformanceAnalyzer:
    """
    Comprehensive agent performance analysis system.
    
    Provides detailed performance tracking, analysis, and reporting for individual
    agents and teams. Integrates with shared modules for robust data collection
    and state management.
    """
    
    def __init__(self, 
                 state_manager: Optional[StateManager] = None,
                 task_metrics: Optional[TaskMetrics] = None,
                 error_handler: Optional[ErrorHandler] = None):
        """
        Initialize the performance analyzer.
        
        Args:
            state_manager: State management for persistent data
            task_metrics: Task tracking integration
            error_handler: Error handling for robust operation
        """
        self.logger = logging.getLogger(__name__)
        self.state_manager = state_manager or StateManager()
        self.task_metrics = task_metrics or TaskMetrics()
        self.error_handler = error_handler or ErrorHandler()
        
        # Circuit breaker for performance analysis operations
        self.analysis_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=300,
            name="performance_analysis"
        )
        
        # Performance data cache
        self.performance_cache: Dict[str, AgentPerformanceData] = {}
        self.team_performance_cache: Dict[str, TeamPerformanceData] = {}
        
        # Analysis configuration
        self.analysis_config = {
            'default_time_window': timedelta(days=7),
            'trend_analysis_periods': 5,
            'quality_weight': 0.3,
            'speed_weight': 0.3,
            'efficiency_weight': 0.2,
            'reliability_weight': 0.2
        }
        
        self.logger.info("AgentPerformanceAnalyzer initialized")
    
    @ErrorHandler.with_circuit_breaker
    def analyze_agent_performance(self, 
                                agent_id: str, 
                                time_period: Optional[Tuple[datetime, datetime]] = None,
                                force_refresh: bool = False) -> AgentPerformanceData:
        """
        Comprehensive agent performance analysis.
        
        Args:
            agent_id: Unique identifier for the agent
            time_period: Analysis time window (default: last 7 days)
            force_refresh: Force fresh analysis ignoring cache
            
        Returns:
            AgentPerformanceData: Comprehensive performance analysis
            
        Raises:
            ValueError: If agent_id is invalid
            AnalysisError: If performance analysis fails
        """
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")
        
        # Set default time period
        if time_period is None:
            end_time = datetime.now()
            start_time = end_time - self.analysis_config['default_time_window']
            time_period = (start_time, end_time)
        
        # Check cache if not forcing refresh
        cache_key = f"{agent_id}_{time_period[0].isoformat()}_{time_period[1].isoformat()}"
        if not force_refresh and cache_key in self.performance_cache:
            self.logger.debug(f"Returning cached performance data for agent {agent_id}")
            return self.performance_cache[cache_key]
        
        try:
            self.logger.info(f"Analyzing performance for agent {agent_id}")
            
            # Gather agent configuration and basic info
            agent_config = self._get_agent_config(agent_id)
            
            # Initialize performance data structure
            performance_data = AgentPerformanceData(
                agent_id=agent_id,
                agent_name=agent_config.name if agent_config else agent_id,
                time_period=time_period
            )
            
            # Analyze core performance metrics
            self._calculate_success_metrics(performance_data, time_period)
            self._analyze_execution_times(performance_data, time_period)
            self._measure_resource_usage(performance_data, time_period)
            self._assess_output_quality(performance_data, time_period)
            self._measure_collaboration_effectiveness(performance_data, time_period)
            
            # Perform trend analysis
            self._analyze_performance_trends(performance_data, time_period)
            
            # Identify improvement areas
            self._identify_improvement_areas(performance_data)
            
            # Cache the results
            self.performance_cache[cache_key] = performance_data
            
            self.logger.info(f"Performance analysis completed for agent {agent_id}")
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Failed to analyze performance for agent {agent_id}: {e}")
            raise AnalysisError(f"Performance analysis failed for agent {agent_id}: {e}")
    
    def _calculate_success_metrics(self, 
                                 performance_data: AgentPerformanceData,
                                 time_period: Tuple[datetime, datetime]) -> None:
        """Calculate success rate and task completion metrics."""
        try:
            # Get task results from task metrics
            task_results = self.task_metrics.get_agent_task_results(
                performance_data.agent_id, 
                time_period[0], 
                time_period[1]
            )
            
            if not task_results:
                self.logger.warning(f"No task results found for agent {performance_data.agent_id}")
                return
            
            performance_data.total_tasks = len(task_results)
            performance_data.completed_tasks = sum(1 for result in task_results if result.success)
            performance_data.failed_tasks = performance_data.total_tasks - performance_data.completed_tasks
            
            if performance_data.total_tasks > 0:
                performance_data.success_rate = performance_data.completed_tasks / performance_data.total_tasks
            
            self.logger.debug(f"Success metrics calculated: {performance_data.success_rate:.2%} success rate")
            
        except Exception as e:
            self.logger.error(f"Failed to calculate success metrics: {e}")
            # Set default values on error
            performance_data.success_rate = 0.0
    
    def _analyze_execution_times(self, 
                               performance_data: AgentPerformanceData,
                               time_period: Tuple[datetime, datetime]) -> None:
        """Analyze execution time metrics."""
        try:
            # Get execution times from task metrics
            execution_times = self.task_metrics.get_agent_execution_times(
                performance_data.agent_id,
                time_period[0],
                time_period[1]
            )
            
            if not execution_times:
                self.logger.warning(f"No execution times found for agent {performance_data.agent_id}")
                return
            
            performance_data.avg_execution_time = statistics.mean(execution_times)
            performance_data.median_execution_time = statistics.median(execution_times)
            performance_data.min_execution_time = min(execution_times)
            performance_data.max_execution_time = max(execution_times)
            
            self.logger.debug(f"Execution times analyzed: avg={performance_data.avg_execution_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to analyze execution times: {e}")
            # Set default values on error
            performance_data.avg_execution_time = 0.0
    
    def _measure_resource_usage(self, 
                              performance_data: AgentPerformanceData,
                              time_period: Tuple[datetime, datetime]) -> None:
        """Measure resource utilization metrics."""
        try:
            # Get resource usage data
            resource_data = self.task_metrics.get_agent_resource_usage(
                performance_data.agent_id,
                time_period[0],
                time_period[1]
            )
            
            if not resource_data:
                self.logger.warning(f"No resource data found for agent {performance_data.agent_id}")
                return
            
            # Calculate average resource usage
            memory_usage = [data.memory_usage for data in resource_data if data.memory_usage is not None]
            cpu_usage = [data.cpu_usage for data in resource_data if data.cpu_usage is not None]
            
            if memory_usage:
                performance_data.avg_memory_usage = statistics.mean(memory_usage)
            if cpu_usage:
                performance_data.avg_cpu_usage = statistics.mean(cpu_usage)
            
            # Calculate efficiency score (inverse of resource usage with quality weighting)
            if performance_data.avg_memory_usage > 0 and performance_data.avg_cpu_usage > 0:
                resource_factor = (performance_data.avg_memory_usage + performance_data.avg_cpu_usage) / 2
                performance_data.resource_efficiency_score = min(100.0, 100.0 / resource_factor)
            
            self.logger.debug(f"Resource usage measured: {performance_data.resource_efficiency_score:.2f} efficiency")
            
        except Exception as e:
            self.logger.error(f"Failed to measure resource usage: {e}")
            # Set default values on error
            performance_data.resource_efficiency_score = 50.0
    
    def _assess_output_quality(self, 
                             performance_data: AgentPerformanceData,
                             time_period: Tuple[datetime, datetime]) -> None:
        """Assess output quality metrics."""
        try:
            # Get quality metrics from task results
            quality_data = self.task_metrics.get_agent_quality_metrics(
                performance_data.agent_id,
                time_period[0],
                time_period[1]
            )
            
            if not quality_data:
                self.logger.warning(f"No quality data found for agent {performance_data.agent_id}")
                return
            
            # Calculate aggregate quality scores
            quality_scores = [data.quality_score for data in quality_data if data.quality_score is not None]
            error_rates = [data.error_rate for data in quality_data if data.error_rate is not None]
            coverage_scores = [data.test_coverage for data in quality_data if data.test_coverage is not None]
            
            if quality_scores:
                performance_data.code_quality_score = statistics.mean(quality_scores)
            if error_rates:
                performance_data.error_rate = statistics.mean(error_rates)
            if coverage_scores:
                performance_data.test_coverage = statistics.mean(coverage_scores)
            
            self.logger.debug(f"Quality assessed: {performance_data.code_quality_score:.2f} quality score")
            
        except Exception as e:
            self.logger.error(f"Failed to assess output quality: {e}")
            # Set default values on error
            performance_data.code_quality_score = 50.0
    
    def _measure_collaboration_effectiveness(self, 
                                           performance_data: AgentPerformanceData,
                                           time_period: Tuple[datetime, datetime]) -> None:
        """Measure collaboration effectiveness metrics."""
        try:
            # Get collaboration data
            collaboration_data = self.task_metrics.get_agent_collaboration_metrics(
                performance_data.agent_id,
                time_period[0],
                time_period[1]
            )
            
            if not collaboration_data:
                self.logger.warning(f"No collaboration data found for agent {performance_data.agent_id}")
                return
            
            performance_data.collaboration_frequency = len(collaboration_data)
            
            if collaboration_data:
                success_rates = [data.success_rate for data in collaboration_data if data.success_rate is not None]
                communication_scores = [data.communication_score for data in collaboration_data if data.communication_score is not None]
                
                if success_rates:
                    performance_data.collaboration_success_rate = statistics.mean(success_rates)
                if communication_scores:
                    performance_data.communication_score = statistics.mean(communication_scores)
            
            self.logger.debug(f"Collaboration measured: {performance_data.collaboration_success_rate:.2%} success rate")
            
        except Exception as e:
            self.logger.error(f"Failed to measure collaboration effectiveness: {e}")
            # Set default values on error
            performance_data.collaboration_success_rate = 0.0
    
    def _analyze_performance_trends(self, 
                                  performance_data: AgentPerformanceData,
                                  time_period: Tuple[datetime, datetime]) -> None:
        """Analyze performance trends over time."""
        try:
            # Calculate trend periods
            total_duration = time_period[1] - time_period[0]
            period_duration = total_duration / self.analysis_config['trend_analysis_periods']
            
            trend_values = []
            
            for i in range(self.analysis_config['trend_analysis_periods']):
                period_start = time_period[0] + (period_duration * i)
                period_end = period_start + period_duration
                
                # Get metrics for this period
                period_metrics = self._get_period_performance_score(
                    performance_data.agent_id,
                    (period_start, period_end)
                )
                trend_values.append(period_metrics)
            
            performance_data.performance_trend = trend_values
            
            # Identify recent improvements
            if len(trend_values) >= 2:
                recent_change = trend_values[-1] - trend_values[-2]
                if recent_change > 0.05:  # 5% improvement threshold
                    performance_data.recent_improvements.append("Overall performance trending upward")
                elif recent_change < -0.05:  # 5% decline threshold
                    performance_data.areas_for_improvement.append("Overall performance declining")
            
            self.logger.debug(f"Trend analysis completed: {len(trend_values)} periods analyzed")
            
        except Exception as e:
            self.logger.error(f"Failed to analyze performance trends: {e}")
            # Set empty trend data on error
            performance_data.performance_trend = []
    
    def _get_period_performance_score(self, 
                                    agent_id: str,
                                    period: Tuple[datetime, datetime]) -> float:
        """Calculate composite performance score for a specific period."""
        try:
            # Get basic metrics for the period
            task_results = self.task_metrics.get_agent_task_results(agent_id, period[0], period[1])
            
            if not task_results:
                return 0.0
            
            # Calculate weighted performance score
            success_rate = sum(1 for result in task_results if result.success) / len(task_results)
            
            # Additional metrics would be calculated here in a full implementation
            # For now, use success rate as the primary metric
            performance_score = success_rate
            
            return performance_score
            
        except Exception as e:
            self.logger.error(f"Failed to calculate period performance score: {e}")
            return 0.0
    
    def _identify_improvement_areas(self, performance_data: AgentPerformanceData) -> None:
        """Identify specific areas for performance improvement."""
        try:
            # Success rate improvements
            if performance_data.success_rate < 0.8:
                performance_data.areas_for_improvement.append(
                    f"Success rate below 80% ({performance_data.success_rate:.1%})"
                )
            
            # Execution time improvements
            if performance_data.avg_execution_time > 300:  # 5 minutes
                performance_data.areas_for_improvement.append(
                    f"Average execution time high ({performance_data.avg_execution_time:.1f}s)"
                )
            
            # Resource efficiency improvements
            if performance_data.resource_efficiency_score < 60:
                performance_data.areas_for_improvement.append(
                    f"Resource efficiency below target ({performance_data.resource_efficiency_score:.1f})"
                )
            
            # Quality improvements
            if performance_data.code_quality_score < 70:
                performance_data.areas_for_improvement.append(
                    f"Code quality below target ({performance_data.code_quality_score:.1f})"
                )
            
            # Collaboration improvements
            if performance_data.collaboration_success_rate < 0.7 and performance_data.collaboration_frequency > 0:
                performance_data.areas_for_improvement.append(
                    f"Collaboration success rate low ({performance_data.collaboration_success_rate:.1%})"
                )
            
            self.logger.debug(f"Identified {len(performance_data.areas_for_improvement)} improvement areas")
            
        except Exception as e:
            self.logger.error(f"Failed to identify improvement areas: {e}")
    
    def _get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration from state manager."""
        try:
            config_data = self.state_manager.get_agent_config(agent_id)
            if config_data:
                return AgentConfig(**config_data)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get agent config for {agent_id}: {e}")
            return None
    
    def generate_performance_report(self, 
                                  agent_id: str,
                                  time_period: Optional[Tuple[datetime, datetime]] = None,
                                  detailed: bool = True) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report for an agent.
        
        Args:
            agent_id: Agent to generate report for
            time_period: Time window for analysis
            detailed: Whether to include detailed metrics
            
        Returns:
            Dict containing formatted performance report data
        """
        try:
            performance_data = self.analyze_agent_performance(agent_id, time_period)
            
            report = {
                'agent_id': performance_data.agent_id,
                'agent_name': performance_data.agent_name,
                'analysis_period': {
                    'start': performance_data.time_period[0].isoformat(),
                    'end': performance_data.time_period[1].isoformat()
                },
                'summary': {
                    'overall_score': self._calculate_overall_score(performance_data),
                    'success_rate': performance_data.success_rate,
                    'total_tasks': performance_data.total_tasks,
                    'avg_execution_time': performance_data.avg_execution_time,
                    'resource_efficiency': performance_data.resource_efficiency_score
                },
                'improvements': performance_data.recent_improvements,
                'recommendations': performance_data.areas_for_improvement
            }
            
            if detailed:
                report.update({
                    'detailed_metrics': {
                        'execution_metrics': {
                            'avg_time': performance_data.avg_execution_time,
                            'median_time': performance_data.median_execution_time, 
                            'min_time': performance_data.min_execution_time,
                            'max_time': performance_data.max_execution_time
                        },
                        'resource_metrics': {
                            'avg_memory': performance_data.avg_memory_usage,
                            'avg_cpu': performance_data.avg_cpu_usage,
                            'efficiency_score': performance_data.resource_efficiency_score
                        },
                        'quality_metrics': {
                            'code_quality': performance_data.code_quality_score,
                            'test_coverage': performance_data.test_coverage,
                            'error_rate': performance_data.error_rate
                        },
                        'collaboration_metrics': {
                            'frequency': performance_data.collaboration_frequency,
                            'success_rate': performance_data.collaboration_success_rate,
                            'communication_score': performance_data.communication_score
                        }
                    },
                    'performance_trend': performance_data.performance_trend
                })
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance report for agent {agent_id}: {e}")
            raise ReportGenerationError(f"Failed to generate performance report: {e}")
    
    def _calculate_overall_score(self, performance_data: AgentPerformanceData) -> float:
        """Calculate weighted overall performance score."""
        config = self.analysis_config
        
        score = (
            performance_data.success_rate * config['reliability_weight'] +
            min(1.0, 60.0 / max(1.0, performance_data.avg_execution_time)) * config['speed_weight'] +
            (performance_data.resource_efficiency_score / 100.0) * config['efficiency_weight'] +
            (performance_data.code_quality_score / 100.0) * config['quality_weight']
        )
        
        return min(100.0, score * 100.0)


class AnalysisError(Exception):
    """Exception raised when performance analysis fails."""
    pass


class ReportGenerationError(Exception):
    """Exception raised when report generation fails."""
    pass