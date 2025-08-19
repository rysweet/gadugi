from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import logging
import json
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# Import shared modules and Phase 1 components
from ...shared.utils.error_handling import ErrorHandler, CircuitBreaker
from ...shared.state_management import StateManager
from .performance_analytics import AgentPerformanceAnalyzer, AgentPerformanceData
from .capability_assessment import CapabilityAssessment, AgentCapabilityProfile
from .metrics_collector import MetricsCollector
from ..shared.state_management import StateManager
from ..shared.error_handling import ErrorHandler

"""
TeamCoach Phase 1: Performance Reporting System

This module provides comprehensive performance reporting and visualization capabilities.
The ReportingSystem class generates detailed reports, dashboards, and insights from
collected performance metrics and capability assessments.

Key Features:
- Comprehensive performance reports
- Interactive dashboards
- Trend analysis and visualization
- Comparative performance analysis
- Automated report generation
- Multiple output formats (JSON, HTML, PDF)
"""

# Import shared modules and Phase 1 components

class ReportType(Enum):
    """Types of reports available"""

    AGENT_PERFORMANCE = "agent_performance"
    TEAM_OVERVIEW = "team_overview"
    CAPABILITY_ANALYSIS = "capability_analysis"
    TREND_ANALYSIS = "trend_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    EXECUTIVE_SUMMARY = "executive_summary"

class ReportFormat(Enum):
    """Output formats for reports"""

    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"

@dataclass
class ReportConfig:
    """Configuration for report generation"""

    report_type: ReportType
    format: ReportFormat
    time_period: Tuple[datetime, datetime]
    agents: List[str] = field(default_factory=list)
    include_charts: bool = True
    include_recommendations: bool = True
    detailed_metrics: bool = True
    comparison_baseline: Optional[str] = None

@dataclass
class ReportSection:
    """Individual section of a report"""

    title: str
    content: str
    charts: List[str] = field(default_factory=list)  # Base64 encoded chart images
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GeneratedReport:
    """Complete generated report"""

    report_id: str
    report_type: ReportType
    format: ReportFormat
    generated_at: datetime
    time_period: Tuple[datetime, datetime]

    # Report structure
    title: str
    executive_summary: str
    sections: List[ReportSection] = field(default_factory=list)

    # Output content
    content: str  # type: ignore
    attachments: Dict[str, bytes] = field(default_factory=dict)

    # Metadata
    agents_included: List[str] = field(default_factory=list)
    metrics_included: List[str] = field(default_factory=list)
    generation_time: float = 0.0

class ReportingSystem:
    """
    Comprehensive performance reporting and visualization system.

    Generates detailed reports, dashboards, and insights from performance metrics
    and capability assessments. Supports multiple output formats and automated
    report generation.
    """

    def __init__(
        self,
        performance_analyzer: Optional[AgentPerformanceAnalyzer] = None,
        capability_assessment: Optional[CapabilityAssessment] = None,
        metrics_collector: Optional[MetricsCollector] = None,
        state_manager: Optional[StateManager] = None,
        error_handler: Optional[ErrorHandler] = None,
    ):
        """
        Initialize the reporting system.

        Args:
            performance_analyzer: Performance analysis component
            capability_assessment: Capability assessment component
            metrics_collector: Metrics collection component
            state_manager: State management for report storage
            error_handler: Error handling for robust operation
        """
        self.logger = logging.getLogger(__name__)
        self.performance_analyzer = performance_analyzer or AgentPerformanceAnalyzer()
        self.capability_assessment = capability_assessment or CapabilityAssessment()
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.state_manager = state_manager or StateManager()
        self.error_handler = error_handler or ErrorHandler()

        # Circuit breaker for report generation
        self.reporting_circuit_breaker = CircuitBreaker(
            failure_threshold=3, timeout=600, name="report_generation"
        )

        # Report cache
        self.report_cache: Dict[str, GeneratedReport] = {}

        # Report templates
        self.report_templates = self._initialize_report_templates()

        # Visualization settings
        plt.style.use("seaborn-v0_8")
        sns.set_palette("husl")

        self.logger.info("ReportingSystem initialized")

    @ErrorHandler.with_circuit_breaker
    def generate_report(self, config: ReportConfig) -> GeneratedReport:
        """
        Generate a comprehensive report based on configuration.

        Args:
            config: Report generation configuration

        Returns:
            GeneratedReport: Complete generated report

        Raises:
            ReportGenerationError: If report generation fails
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"Generating {config.report_type.value} report")

            # Generate unique report ID
            report_id = (
                f"{config.report_type.value}_{start_time.strftime('%Y%m%d_%H%M%S')}"
            )

            # Initialize report structure
            report = GeneratedReport(  # type: ignore
                report_id=report_id,
                report_type=config.report_type,
                format=config.format,
                generated_at=start_time,
                time_period=config.time_period,
                title=self._generate_report_title(config),
                executive_summary="",
                agents_included=config.agents.copy(),
            )

            # Generate report content based on type
            if config.report_type == ReportType.AGENT_PERFORMANCE:
                self._generate_agent_performance_report(report, config)
            elif config.report_type == ReportType.TEAM_OVERVIEW:
                self._generate_team_overview_report(report, config)
            elif config.report_type == ReportType.CAPABILITY_ANALYSIS:
                self._generate_capability_analysis_report(report, config)
            elif config.report_type == ReportType.TREND_ANALYSIS:
                self._generate_trend_analysis_report(report, config)
            elif config.report_type == ReportType.COMPARATIVE_ANALYSIS:
                self._generate_comparative_analysis_report(report, config)
            elif config.report_type == ReportType.EXECUTIVE_SUMMARY:
                self._generate_executive_summary_report(report, config)

            # Generate executive summary
            report.executive_summary = self._generate_executive_summary(report, config)

            # Format report content
            report.content = self._format_report_content(report, config)

            # Calculate generation time
            report.generation_time = (datetime.now() - start_time).total_seconds()

            # Cache the report
            self.report_cache[report_id] = report

            self.logger.info(
                f"Report {report_id} generated in {report.generation_time:.2f}s"
            )
            return report

        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            raise ReportGenerationError(f"Report generation failed: {e}")

    def _generate_agent_performance_report(
        self, report: GeneratedReport, config: ReportConfig
    ) -> None:
        """Generate agent performance analysis report."""
        try:
            for agent_id in config.agents:
                # Get performance data
                performance_data = self.performance_analyzer.analyze_agent_performance(
                    agent_id, config.time_period
                )

                # Create performance section
                section = ReportSection(
                    title=f"Agent Performance: {performance_data.agent_name}",
                    content=self._format_performance_analysis(performance_data),
                    data={"agent_id": agent_id, "performance_data": performance_data},
                )

                # Add performance charts if requested
                if config.include_charts:
                    charts = self._generate_performance_charts(performance_data)
                    section.charts.extend(charts)

                report.sections.append(section)
                report.metrics_included.extend(
                    [
                        "success_rate",
                        "execution_time",
                        "resource_efficiency",
                        "quality_score",
                    ]
                )

        except Exception as e:
            self.logger.error(f"Failed to generate agent performance report: {e}")

    def _generate_team_overview_report(
        self, report: GeneratedReport, config: ReportConfig
    ) -> None:
        """Generate team overview report."""
        try:
            # Collect team-wide metrics
            team_metrics = {}
            agent_summaries = []

            for agent_id in config.agents:
                # Get agent performance summary
                summary = self.metrics_collector.get_agent_metrics_summary(
                    agent_id, config.time_period
                )
                agent_summaries.append(summary)

                # Aggregate team metrics
                for metric_name, metric_data in summary.get("metrics", {}).items():
                    if metric_name not in team_metrics:
                        team_metrics[metric_name] = []
                    team_metrics[metric_name].append(metric_data["value"])

            # Calculate team aggregates
            team_aggregates = {}
            for metric_name, values in team_metrics.items():
                if values:
                    team_aggregates[metric_name] = {
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values),
                    }

            # Create team overview section
            section = ReportSection(
                title="Team Performance Overview",
                content=self._format_team_overview(team_aggregates, agent_summaries),
                data={
                    "team_aggregates": team_aggregates,
                    "agent_summaries": agent_summaries,
                },
            )

            # Add team charts if requested
            if config.include_charts:
                charts = self._generate_team_charts(team_aggregates, agent_summaries)
                section.charts.extend(charts)

            report.sections.append(section)
            report.metrics_included.extend(list(team_metrics.keys()))

        except Exception as e:
            self.logger.error(f"Failed to generate team overview report: {e}")

    def _generate_capability_analysis_report(
        self, report: GeneratedReport, config: ReportConfig
    ) -> None:
        """Generate capability analysis report."""
        try:
            for agent_id in config.agents:
                # Get capability profile
                capability_profile = (
                    self.capability_assessment.assess_agent_capabilities(agent_id)
                )

                # Create capability section
                section = ReportSection(
                    title=f"Capability Analysis: {capability_profile.agent_name}",
                    content=self._format_capability_analysis(capability_profile),
                    data={
                        "agent_id": agent_id,
                        "capability_profile": capability_profile,
                    },
                )

                # Add capability charts if requested
                if config.include_charts:
                    charts = self._generate_capability_charts(capability_profile)
                    section.charts.extend(charts)

                report.sections.append(section)

        except Exception as e:
            self.logger.error(f"Failed to generate capability analysis report: {e}")

    def _generate_trend_analysis_report(
        self, report: GeneratedReport, config: ReportConfig
    ) -> None:
        """Generate trend analysis report."""
        try:
            # Analyze trends for each agent
            for agent_id in config.agents:
                performance_data = self.performance_analyzer.analyze_agent_performance(
                    agent_id, config.time_period
                )

                # Create trend section
                section = ReportSection(
                    title=f"Performance Trends: {performance_data.agent_name}",
                    content=self._format_trend_analysis(performance_data),
                    data={
                        "agent_id": agent_id,
                        "trend_data": performance_data.performance_trend,
                    },
                )

                # Add trend charts if requested
                if config.include_charts:
                    charts = self._generate_trend_charts(performance_data)
                    section.charts.extend(charts)

                report.sections.append(section)

        except Exception as e:
            self.logger.error(f"Failed to generate trend analysis report: {e}")

    def _generate_comparative_analysis_report(
        self, report: GeneratedReport, config: ReportConfig
    ) -> None:
        """Generate comparative analysis report."""
        try:
            # Collect performance data for all agents
            agent_performances = {}
            for agent_id in config.agents:
                performance_data = self.performance_analyzer.analyze_agent_performance(
                    agent_id, config.time_period
                )
                agent_performances[agent_id] = performance_data

            # Create comparative analysis section
            section = ReportSection(
                title="Comparative Performance Analysis",
                content=self._format_comparative_analysis(agent_performances),
                data={"agent_performances": agent_performances},
            )

            # Add comparison charts if requested
            if config.include_charts:
                charts = self._generate_comparison_charts(agent_performances)
                section.charts.extend(charts)

            report.sections.append(section)

        except Exception as e:
            self.logger.error(f"Failed to generate comparative analysis report: {e}")

    def _generate_executive_summary_report(
        self, report: GeneratedReport, config: ReportConfig
    ) -> None:
        """Generate executive summary report."""
        try:
            # Collect high-level metrics
            summary_data = {
                "total_agents": len(config.agents),
                "time_period": config.time_period,
                "key_metrics": {},
                "recommendations": [],
            }

            # Aggregate key metrics across all agents
            all_success_rates = []
            all_execution_times = []
            all_quality_scores = []

            for agent_id in config.agents:
                performance_data = self.performance_analyzer.analyze_agent_performance(
                    agent_id, config.time_period
                )

                all_success_rates.append(performance_data.success_rate)
                all_execution_times.append(performance_data.avg_execution_time)
                all_quality_scores.append(performance_data.code_quality_score)

                # Collect recommendations
                summary_data["recommendations"].extend(
                    performance_data.areas_for_improvement
                )

            # Calculate summary metrics
            if all_success_rates:
                summary_data["key_metrics"]["avg_success_rate"] = sum(
                    all_success_rates
                ) / len(all_success_rates)
            if all_execution_times:
                summary_data["key_metrics"]["avg_execution_time"] = sum(
                    all_execution_times
                ) / len(all_execution_times)
            if all_quality_scores:
                summary_data["key_metrics"]["avg_quality_score"] = sum(
                    all_quality_scores
                ) / len(all_quality_scores)

            # Create executive summary section
            section = ReportSection(
                title="Executive Summary",
                content=self._format_executive_summary_content(summary_data),
                data=summary_data,
            )

            # Add summary charts if requested
            if config.include_charts:
                charts = self._generate_summary_charts(summary_data)
                section.charts.extend(charts)

            report.sections.append(section)

        except Exception as e:
            self.logger.error(f"Failed to generate executive summary report: {e}")

    def _format_performance_analysis(
        self, performance_data: AgentPerformanceData
    ) -> str:
        """Format performance analysis content."""
        content = f"""
## Performance Summary

**Agent**: {performance_data.agent_name}
**Analysis Period**: {performance_data.time_period[0].strftime("%Y-%m-%d")} to {performance_data.time_period[1].strftime("%Y-%m-%d")}

### Key Metrics
- **Success Rate**: {performance_data.success_rate:.1%}
- **Total Tasks**: {performance_data.total_tasks}
- **Average Execution Time**: {performance_data.avg_execution_time:.1f} seconds
- **Resource Efficiency Score**: {performance_data.resource_efficiency_score:.1f}
- **Code Quality Score**: {performance_data.code_quality_score:.1f}

### Recent Improvements
"""
        for improvement in performance_data.recent_improvements:
            content += f"- {improvement}\n"

        content += "\n### Areas for Improvement\n"
        for area in performance_data.areas_for_improvement:
            content += f"- {area}\n"

        return content

    def _format_team_overview(
        self, team_aggregates: Dict[str, Any], agent_summaries: List[Dict[str, Any]]
    ) -> str:
        """Format team overview content."""
        content = "## Team Performance Overview\n\n"

        content += "### Team Aggregates\n"
        for metric_name, aggregates in team_aggregates.items():
            content += f"- **{metric_name}**: Avg {aggregates['average']:.2f}, Range {aggregates['min']:.2f}-{aggregates['max']:.2f}\n"

        content += f"\n### Agent Summary ({len(agent_summaries)} agents)\n"
        for summary in agent_summaries:
            agent_id = summary.get("agent_id", "Unknown")
            content += f"- **{agent_id}**: "

            metrics = summary.get("metrics", {})
            if "task_success_rate" in metrics:
                content += (
                    f"Success Rate: {metrics['task_success_rate']['value']:.1%}, "
                )
            if "task_execution_time" in metrics:
                content += f"Avg Time: {metrics['task_execution_time']['value']:.1f}s"
            content += "\n"

        return content

    def _format_capability_analysis(
        self, capability_profile: AgentCapabilityProfile
    ) -> str:
        """Format capability analysis content."""
        content = f"""
## Capability Analysis

**Agent**: {capability_profile.agent_name}
**Profile Generated**: {capability_profile.profile_generated.strftime("%Y-%m-%d %H:%M")}
**Versatility Score**: {capability_profile.versatility_score:.2f}

### Primary Strengths
"""
        for strength in capability_profile.primary_strengths:
            content += f"- {strength.value}\n"

        content += "\n### Secondary Strengths\n"
        for strength in capability_profile.secondary_strengths:
            content += f"- {strength.value}\n"

        content += "\n### Improvement Areas\n"
        for area in capability_profile.improvement_areas:
            content += f"- {area.value}\n"

        content += "\n### Optimal Task Types\n"
        for task_type in capability_profile.optimal_task_types:
            content += f"- {task_type}\n"

        content += "\n### Development Recommendations\n"
        for recommendation in capability_profile.skill_development_recommendations:
            content += f"- {recommendation}\n"

        return content

    def _format_trend_analysis(self, performance_data: AgentPerformanceData) -> str:
        """Format trend analysis content."""
        content = f"""
## Performance Trends

**Agent**: {performance_data.agent_name}

### Trend Analysis
"""
        if performance_data.performance_trend:
            trend_direction = (
                "improving"
                if performance_data.performance_trend[-1]
                > performance_data.performance_trend[0]
                else "declining"
            )
            content += f"- Overall trend: {trend_direction}\n"
            content += f"- Current performance level: {performance_data.performance_trend[-1]:.2f}\n"
            content += (
                f"- Trend data points: {len(performance_data.performance_trend)}\n"
            )
        else:
            content += "- Insufficient data for trend analysis\n"

        return content

    def _format_comparative_analysis(
        self, agent_performances: Dict[str, AgentPerformanceData]
    ) -> str:
        """Format comparative analysis content."""
        content = "## Comparative Performance Analysis\n\n"

        # Rank agents by success rate
        sorted_agents = sorted(
            agent_performances.items(), key=lambda x: x[1].success_rate, reverse=True
        )

        content += "### Success Rate Ranking\n"
        for i, (_agent_id, performance) in enumerate(sorted_agents, 1):
            content += (
                f"{i}. **{performance.agent_name}**: {performance.success_rate:.1%}\n"
            )

        # Rank by execution time (lower is better)
        sorted_by_time = sorted(
            agent_performances.items(), key=lambda x: x[1].avg_execution_time
        )

        content += "\n### Execution Time Ranking (Fastest First)\n"
        for i, (_agent_id, performance) in enumerate(sorted_by_time, 1):
            content += f"{i}. **{performance.agent_name}**: {performance.avg_execution_time:.1f}s\n"

        return content

    def _format_executive_summary_content(self, summary_data: Dict[str, Any]) -> str:
        """Format executive summary content."""
        content = "## Executive Summary\n\n"

        period_start = summary_data["time_period"][0].strftime("%Y-%m-%d")
        period_end = summary_data["time_period"][1].strftime("%Y-%m-%d")

        content += f"**Analysis Period**: {period_start} to {period_end}\n"
        content += f"**Agents Analyzed**: {summary_data['total_agents']}\n\n"

        content += "### Key Performance Indicators\n"
        key_metrics = summary_data["key_metrics"]
        if "avg_success_rate" in key_metrics:
            content += (
                f"- **Team Success Rate**: {key_metrics['avg_success_rate']:.1%}\n"
            )
        if "avg_execution_time" in key_metrics:
            content += f"- **Average Execution Time**: {key_metrics['avg_execution_time']:.1f} seconds\n"
        if "avg_quality_score" in key_metrics:
            content += (
                f"- **Average Quality Score**: {key_metrics['avg_quality_score']:.1f}\n"
            )

        content += "\n### Key Recommendations\n"
        unique_recommendations = list(set(summary_data["recommendations"]))[
            :5
        ]  # Top 5 unique recommendations
        for recommendation in unique_recommendations:
            content += f"- {recommendation}\n"

        return content

    def _generate_performance_charts(
        self, performance_data: AgentPerformanceData
    ) -> List[str]:
        """Generate performance charts."""
        charts = []

        try:
            # Performance metrics bar chart
            if performance_data.total_tasks > 0:
                _fig, ax = plt.subplots(figsize=(10, 6))

                metrics = ["Success Rate", "Quality Score", "Resource Efficiency"]
                values = [
                    performance_data.success_rate * 100,
                    performance_data.code_quality_score,
                    performance_data.resource_efficiency_score,
                ]

                bars = ax.bar(metrics, values, color=["#2E8B57", "#4169E1", "#FF6347"])
                ax.set_ylabel("Score")
                ax.set_title(f"Performance Metrics - {performance_data.agent_name}")
                ax.set_ylim(0, 100)

                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height + 1,
                        f"{height:.1f}",
                        ha="center",
                        va="bottom",
                    )

                plt.tight_layout()

                # Convert to base64
                buffer = BytesIO()
                plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                charts.append(chart_data)
                plt.close()

            # Trend chart if available
            if (
                performance_data.performance_trend
                and len(performance_data.performance_trend) > 1
            ):
                _fig, ax = plt.subplots(figsize=(10, 6))

                x = range(len(performance_data.performance_trend))
                ax.plot(
                    x,
                    performance_data.performance_trend,
                    marker="o",
                    linewidth=2,
                    markersize=6,
                )
                ax.set_xlabel("Time Period")
                ax.set_ylabel("Performance Score")
                ax.set_title(f"Performance Trend - {performance_data.agent_name}")
                ax.grid(True, alpha=0.3)

                plt.tight_layout()

                buffer = BytesIO()
                plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                charts.append(chart_data)
                plt.close()

        except Exception as e:
            self.logger.error(f"Failed to generate performance charts: {e}")

        return charts

    def _generate_team_charts(
        self, team_aggregates: Dict[str, Any], agent_summaries: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate team overview charts."""
        charts = []

        try:
            # Team metrics comparison chart
            if team_aggregates:
                _fig, ax = plt.subplots(figsize=(12, 8))

                metrics = list(team_aggregates.keys())[:5]  # Limit to 5 metrics
                averages = [team_aggregates[metric]["average"] for metric in metrics]
                mins = [team_aggregates[metric]["min"] for metric in metrics]
                maxs = [team_aggregates[metric]["max"] for metric in metrics]

                x = range(len(metrics))
                width = 0.3

                ax.bar([i - width for i in x], mins, width, label="Min", alpha=0.7)
                ax.bar(x, averages, width, label="Average", alpha=0.7)
                ax.bar([i + width for i in x], maxs, width, label="Max", alpha=0.7)

                ax.set_xlabel("Metrics")
                ax.set_ylabel("Value")
                ax.set_title("Team Performance Metrics Distribution")
                ax.set_xticks(x)
                ax.set_xticklabels(metrics, rotation=45, ha="right")
                ax.legend()

                plt.tight_layout()

                buffer = BytesIO()
                plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                charts.append(chart_data)
                plt.close()

        except Exception as e:
            self.logger.error(f"Failed to generate team charts: {e}")

        return charts

    def _generate_capability_charts(
        self, capability_profile: AgentCapabilityProfile
    ) -> List[str]:
        """Generate capability analysis charts."""
        charts = []

        try:
            # Capability radar chart
            if capability_profile.capability_scores:
                _fig, ax = plt.subplots(
                    figsize=(10, 10), subplot_kw=dict(projection="polar")
                )

                capabilities = list(capability_profile.capability_scores.keys())[
                    :8
                ]  # Limit to 8 for readability
                proficiency_values = [
                    capability_profile.capability_scores[cap].proficiency_level.value
                    for cap in capabilities
                ]
                confidence_values = [
                    capability_profile.capability_scores[cap].confidence_score
                    * 5  # Scale to 0-5
                    for cap in capabilities
                ]

                # Calculate angles for each capability
                angles = [
                    i * 2 * 3.14159 / len(capabilities)
                    for i in range(len(capabilities))
                ]
                angles += angles[:1]  # Complete the circle
                proficiency_values += proficiency_values[:1]
                confidence_values += confidence_values[:1]

                # Plot proficiency and confidence
                ax.plot(
                    angles,
                    proficiency_values,
                    "o-",
                    linewidth=2,
                    label="Proficiency",
                    color="blue",
                )
                ax.fill(angles, proficiency_values, alpha=0.25, color="blue")
                ax.plot(
                    angles,
                    confidence_values,
                    "o-",
                    linewidth=2,
                    label="Confidence",
                    color="red",
                )

                # Customize the chart
                ax.set_ylim(0, 5)
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(
                    [cap.value.replace("_", " ").title() for cap in capabilities]
                )
                ax.set_title(
                    f"Capability Profile - {capability_profile.agent_name}", y=1.08
                )
                ax.legend()

                plt.tight_layout()

                buffer = BytesIO()
                plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                charts.append(chart_data)
                plt.close()

        except Exception as e:
            self.logger.error(f"Failed to generate capability charts: {e}")

        return charts

    def _generate_trend_charts(
        self, performance_data: AgentPerformanceData
    ) -> List[str]:
        """Generate trend analysis charts."""
        charts = []

        try:
            if (
                performance_data.performance_trend
                and len(performance_data.performance_trend) > 1
            ):
                _fig, ax = plt.subplots(figsize=(12, 6))

                x = range(len(performance_data.performance_trend))
                y = performance_data.performance_trend

                # Plot trend line
                ax.plot(x, y, marker="o", linewidth=3, markersize=8, color="#2E8B57")

                # Add trend line
                if len(x) > 2:
                    z = np.polyfit(x, y, 1)
                    p = np.poly1d(z)
                    ax.plot(
                        x,
                        p(x),
                        "--",
                        alpha=0.8,
                        color="red",
                        linewidth=2,
                        label="Trend Line",
                    )

                ax.set_xlabel("Time Period")
                ax.set_ylabel("Performance Score")
                ax.set_title(
                    f"Performance Trend Analysis - {performance_data.agent_name}"
                )
                ax.grid(True, alpha=0.3)
                ax.legend()

                # Add annotations for significant points
                if len(y) > 0:
                    max_idx = y.index(max(y))
                    min_idx = y.index(min(y))

                    ax.annotate(
                        f"Peak: {max(y):.2f}",
                        xy=(max_idx, max(y)),
                        xytext=(max_idx, max(y) + 0.1),
                        arrowprops=dict(arrowstyle="->", color="green"),
                        ha="center",
                    )

                    ax.annotate(
                        f"Low: {min(y):.2f}",
                        xy=(min_idx, min(y)),
                        xytext=(min_idx, min(y) - 0.1),
                        arrowprops=dict(arrowstyle="->", color="red"),
                        ha="center",
                    )

                plt.tight_layout()

                buffer = BytesIO()
                plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                charts.append(chart_data)
                plt.close()

        except Exception as e:
            self.logger.error(f"Failed to generate trend charts: {e}")

        return charts

    def _generate_comparison_charts(
        self, agent_performances: Dict[str, AgentPerformanceData]
    ) -> List[str]:
        """Generate comparative analysis charts."""
        charts = []

        try:
            # Comparative performance bar chart
            if agent_performances:
                _fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

                list(agent_performances.keys())
                agent_names = [perf.agent_name for perf in agent_performances.values()]
                success_rates = [
                    perf.success_rate * 100 for perf in agent_performances.values()
                ]
                quality_scores = [
                    perf.code_quality_score for perf in agent_performances.values()
                ]

                # Success rate comparison
                bars1 = ax1.bar(agent_names, success_rates, color="#4169E1")
                ax1.set_ylabel("Success Rate (%)")
                ax1.set_title("Agent Success Rate Comparison")
                ax1.set_ylim(0, 100)

                for bar in bars1:
                    height = bar.get_height()
                    ax1.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height + 1,
                        f"{height:.1f}%",
                        ha="center",
                        va="bottom",
                    )

                # Quality score comparison
                bars2 = ax2.bar(agent_names, quality_scores, color="#FF6347")
                ax2.set_ylabel("Quality Score")
                ax2.set_title("Agent Quality Score Comparison")
                ax2.set_ylim(0, 100)

                for bar in bars2:
                    height = bar.get_height()
                    ax2.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height + 1,
                        f"{height:.1f}",
                        ha="center",
                        va="bottom",
                    )

                # Rotate x-axis labels if needed
                for ax in [ax1, ax2]:
                    ax.tick_params(axis="x", rotation=45)

                plt.tight_layout()

                buffer = BytesIO()
                plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                buffer.seek(0)
                chart_data = base64.b64encode(buffer.getvalue()).decode()
                charts.append(chart_data)
                plt.close()

        except Exception as e:
            self.logger.error(f"Failed to generate comparison charts: {e}")

        return charts

    def _generate_summary_charts(self, summary_data: Dict[str, Any]) -> List[str]:
        """Generate executive summary charts."""
        charts = []

        try:
            # KPI dashboard chart
            key_metrics = summary_data.get("key_metrics", {})
            if key_metrics:
                _fig, ax = plt.subplots(figsize=(10, 6))

                # Create a simple KPI dashboard
                metrics = []
                values = []
                colors = []

                if "avg_success_rate" in key_metrics:
                    metrics.append("Success Rate")
                    values.append(key_metrics["avg_success_rate"] * 100)
                    colors.append("#2E8B57")

                if "avg_quality_score" in key_metrics:
                    metrics.append("Quality Score")
                    values.append(key_metrics["avg_quality_score"])
                    colors.append("#4169E1")

                if metrics:
                    bars = ax.bar(metrics, values, color=colors)
                    ax.set_ylabel("Score")
                    ax.set_title("Team Key Performance Indicators")
                    ax.set_ylim(0, 100)

                    # Add value labels
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            height + 1,
                            f"{height:.1f}",
                            ha="center",
                            va="bottom",
                            fontweight="bold",
                        )

                    plt.tight_layout()

                    buffer = BytesIO()
                    plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                    buffer.seek(0)
                    chart_data = base64.b64encode(buffer.getvalue()).decode()
                    charts.append(chart_data)
                    plt.close()

        except Exception as e:
            self.logger.error(f"Failed to generate summary charts: {e}")

        return charts

    def _generate_report_title(self, config: ReportConfig) -> str:
        """Generate appropriate report title."""
        period_str = f"{config.time_period[0].strftime('%Y-%m-%d')} to {config.time_period[1].strftime('%Y-%m-%d')}"

        title_map = {
            ReportType.AGENT_PERFORMANCE: f"Agent Performance Report ({period_str})",
            ReportType.TEAM_OVERVIEW: f"Team Performance Overview ({period_str})",
            ReportType.CAPABILITY_ANALYSIS: f"Capability Analysis Report ({period_str})",
            ReportType.TREND_ANALYSIS: f"Performance Trend Analysis ({period_str})",
            ReportType.COMPARATIVE_ANALYSIS: f"Comparative Performance Analysis ({period_str})",
            ReportType.EXECUTIVE_SUMMARY: f"Executive Summary ({period_str})",
        }

        return title_map.get(config.report_type, f"Performance Report ({period_str})")

    def _generate_executive_summary(
        self, report: GeneratedReport, config: ReportConfig
    ) -> str:
        """Generate executive summary for the report."""
        summary = f"This {config.report_type.value} report analyzes performance data for {len(config.agents)} agent(s) "
        summary += f"from {config.time_period[0].strftime('%Y-%m-%d')} to {config.time_period[1].strftime('%Y-%m-%d')}. "

        if report.sections:
            summary += f"The report contains {len(report.sections)} detailed sections covering "
            summary += (
                "performance metrics, trends, and recommendations for optimization."
            )

        return summary

    def _format_report_content(
        self, report: GeneratedReport, config: ReportConfig
    ) -> str:
        """Format the complete report content based on output format."""
        if config.format == ReportFormat.JSON:
            return self._format_json_report(report)
        elif config.format == ReportFormat.HTML:
            return self._format_html_report(report)
        elif config.format == ReportFormat.MARKDOWN:
            return self._format_markdown_report(report)
        else:
            return self._format_markdown_report(report)  # Default to markdown

    def _format_json_report(self, report: GeneratedReport) -> str:
        """Format report as JSON."""
        report_dict = {
            "report_id": report.report_id,
            "title": report.title,
            "generated_at": report.generated_at.isoformat(),
            "time_period": {
                "start": report.time_period[0].isoformat(),
                "end": report.time_period[1].isoformat(),
            },
            "executive_summary": report.executive_summary,
            "sections": [],
            "agents_included": report.agents_included,
            "metrics_included": report.metrics_included,
            "generation_time": report.generation_time,
        }

        for section in report.sections:
            section_dict = {
                "title": section.title,
                "content": section.content,
                "charts_count": len(section.charts),
                "data": section.data,
                "metadata": section.metadata,
            }
            report_dict["sections"].append(section_dict)

        return json.dumps(report_dict, indent=2, default=str)

    def _format_html_report(self, report: GeneratedReport) -> str:
        """Format report as HTML."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2E8B57; }}
        h2 {{ color: #4169E1; }}
        .chart {{ text-align: center; margin: 20px 0; }}
        .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .metadata {{ font-size: 0.9em; color: #666; }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>

    <div class="metadata">
        <p><strong>Generated:</strong> {report.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>Period:</strong> {report.time_period[0].strftime("%Y-%m-%d")} to {report.time_period[1].strftime("%Y-%m-%d")}</p>
        <p><strong>Generation Time:</strong> {report.generation_time:.2f} seconds</p>
    </div>

    <div class="summary">
        <h2>Executive Summary</h2>
        <p>{report.executive_summary}</p>
    </div>
"""

        for section in report.sections:
            html += "\n    <div class='section'>\n"
            html += f"        <h2>{section.title}</h2>\n"
            html += f"        <div>{section.content.replace(chr(10), '<br>')}</div>\n"

            # Add charts
            for i, chart in enumerate(section.charts):
                html += "        <div class='chart'>\n"
                html += f"            <img src='data:image/png;base64,{chart}' alt='Chart {i + 1}' style='max-width: 100%;'>\n"
                html += "        </div>\n"

            html += "    </div>\n"

        html += """
</body>
</html>
"""
        return html

    def _format_markdown_report(self, report: GeneratedReport) -> str:
        """Format report as Markdown."""
        content = f"# {report.title}\n\n"

        content += (
            f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  \n"
        )
        content += f"**Period:** {report.time_period[0].strftime('%Y-%m-%d')} to {report.time_period[1].strftime('%Y-%m-%d')}  \n"
        content += f"**Generation Time:** {report.generation_time:.2f} seconds  \n\n"

        content += f"## Executive Summary\n\n{report.executive_summary}\n\n"

        for section in report.sections:
            content += f"{section.content}\n\n"

            # Note about charts (can't embed in markdown easily)
            if section.charts:
                content += f"*{len(section.charts)} chart(s) available in HTML/PDF version*\n\n"

        return content

    def _initialize_report_templates(self) -> Dict[str, str]:
        """Initialize report templates."""
        return {
            "header": "# {title}\n\n**Generated:** {timestamp}\n\n",
            "section": "## {section_title}\n\n{content}\n\n",
            "footer": "\n---\n*Report generated by TeamCoach ReportingSystem*\n",
        }

    def get_report(self, report_id: str) -> Optional[GeneratedReport]:
        """Retrieve a previously generated report."""
        return self.report_cache.get(report_id)

    def list_reports(self) -> List[str]:
        """List all available report IDs."""
        return list(self.report_cache.keys())

    def export_report(self, report_id: str, file_path: str) -> bool:
        """Export a report to file."""
        try:
            report = self.get_report(report_id)
            if not report:
                return False

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report.content)

            self.logger.info(f"Report {report_id} exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export report {report_id}: {e}")
            return False

class ReportGenerationError(Exception):
    """Exception raised when report generation fails."""

    pass
