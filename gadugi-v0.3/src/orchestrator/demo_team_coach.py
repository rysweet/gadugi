#!/usr/bin/env python3
"""Demo script for Team Coach Engine.

Shows the team coach capabilities including:
- Performance analysis of workflows
- Pattern recognition across multiple workflows
- Learning insights extraction
- Optimization recommendations
- Trend analysis
"""

from datetime import datetime, timedelta

from team_coach_engine import run_team_coach


def demo_team_coach():
    """Demonstrate team coach capabilities."""
    # Create sample workflow data for analysis

    sample_workflow = {
        "workflow_id": "demo_workflow_001",
        "agents_used": [
            "orchestrator",
            "task-decomposer",
            "code-writer",
            "test-writer",
        ],
        "task_sequence": [
            {
                "agent": "orchestrator",
                "action": "coordinate_tasks",
                "duration_seconds": 12,
                "success": True,
                "metadata": {"tasks_created": 4, "parallel_execution": True},
            },
            {
                "agent": "task-decomposer",
                "action": "decompose_requirements",
                "duration_seconds": 28,
                "success": True,
                "metadata": {"subtasks_created": 6, "complexity_score": 7.5},
            },
            {
                "agent": "code-writer",
                "action": "generate_code",
                "duration_seconds": 95,
                "success": True,
                "metadata": {
                    "files_created": 3,
                    "lines_written": 250,
                    "language": "python",
                },
            },
            {
                "agent": "test-writer",
                "action": "generate_tests",
                "duration_seconds": 65,
                "success": True,
                "metadata": {
                    "test_files_created": 2,
                    "tests_written": 18,
                    "coverage_target": 85,
                },
            },
        ],
        "resource_usage": {
            "peak_memory_mb": 384,
            "cpu_time_seconds": 200,
            "disk_io_mb": 22,
            "network_io_mb": 1.5,
        },
        "outcomes": {
            "files_created": 5,
            "tests_written": 18,
            "lines_of_code": 250,
            "success_rate": 1.0,
            "user_satisfaction": "high",
            "errors_encountered": 0,
            "warnings_generated": 2,
        },
        "project_context": "gadugi_v0.3_development",
    }

    # Analyze performance
    performance_request = {
        "analysis_type": "performance",
        "workflow_data": sample_workflow,
        "historical_context": {},
        "reflection_scope": "session",
    }

    performance_result = run_team_coach(performance_request)

    analysis = performance_result["analysis_results"]
    for _metric, _value in analysis["efficiency_metrics"].items():
        pass

    for i, _rec in enumerate(performance_result["recommendations"][:3], 1):
        pass

    # Simulate historical workflows for pattern analysis
    historical_workflows = []
    datetime.now() - timedelta(hours=2)

    # Create varied workflows to demonstrate patterns
    workflow_scenarios = [
        {
            "name": "fast_simple_workflow",
            "agents": ["orchestrator", "code-writer"],
            "durations": [10, 25],
            "success_rate": 1.0,
            "memory": 128,
            "satisfaction": "high",
        },
        {
            "name": "complex_workflow",
            "agents": ["orchestrator", "task-decomposer", "code-writer", "test-writer"],
            "durations": [15, 35, 80, 45],
            "success_rate": 0.95,
            "memory": 512,
            "satisfaction": "high",
        },
        {
            "name": "problematic_workflow",
            "agents": ["orchestrator", "code-writer", "test-writer"],
            "durations": [20, 120, 90],  # Slow code generation
            "success_rate": 0.7,
            "memory": 256,
            "satisfaction": "medium",
        },
    ]

    for i, scenario in enumerate(workflow_scenarios * 2):  # Duplicate for patterns
        workflow_data = {
            "workflow_id": f"{scenario['name']}_{i}",
            "agents_used": scenario["agents"],
            "task_sequence": [
                {
                    "agent": agent,
                    "action": f"perform_{agent.replace('-', '_')}_task",
                    "duration_seconds": duration,
                    "success": True if scenario["success_rate"] > 0.8 else (i % 2 == 0),
                    "metadata": {},
                }
                for agent, duration in zip(scenario["agents"], scenario["durations"])
            ],
            "resource_usage": {
                "peak_memory_mb": scenario["memory"],
                "cpu_time_seconds": sum(scenario["durations"]),
                "disk_io_mb": 15,
            },
            "outcomes": {
                "files_created": len(scenario["agents"]),
                "tests_written": 8 if "test-writer" in scenario["agents"] else 0,
                "lines_of_code": sum(scenario["durations"]),
                "success_rate": scenario["success_rate"],
                "user_satisfaction": scenario["satisfaction"],
            },
            "project_context": "gadugi_v0.3_development",
        }
        historical_workflows.append(workflow_data)

    # Analyze patterns with historical context
    pattern_request = {
        "analysis_type": "learning",
        "workflow_data": sample_workflow,
        "historical_context": {"previous_workflows": historical_workflows},
        "reflection_scope": "project",
    }

    pattern_result = run_team_coach(pattern_request)

    patterns = pattern_result["patterns_identified"]

    for _pattern in patterns[:4]:  # Show first 4 patterns
        pass

    for _insight in pattern_result["learning_insights"][:3]:
        pass

    # Analyze trends with system-wide scope
    trend_request = {
        "analysis_type": "optimization",
        "workflow_data": sample_workflow,
        "historical_context": {"previous_workflows": historical_workflows},
        "reflection_scope": "system",
    }

    trend_result = run_team_coach(trend_request)

    trends = trend_result["performance_trends"]
    if "insufficient_data" not in trends:
        pass
    else:
        pass

    # Generate comprehensive optimization report
    all_recommendations = []
    all_insights = []

    for result in [performance_result, pattern_result, trend_result]:
        all_recommendations.extend(result["recommendations"])
        all_insights.extend(result["learning_insights"])

    # Prioritize recommendations
    high_priority = [r for r in all_recommendations if r["priority"] == "high"]
    [r for r in all_recommendations if r["priority"] == "medium"]

    for i, _rec in enumerate(high_priority[:3], 1):
        pass

    best_practices = [i for i in all_insights if i["insight_type"] == "best_practice"]
    for _insight in best_practices[:2]:
        pass

    optimization_opportunities = [
        i for i in all_insights if i["insight_type"] == "optimization_opportunity"
    ]
    for _insight in optimization_opportunities[:2]:
        pass

    # Return comprehensive results for further analysis
    return {
        "performance_analysis": performance_result,
        "pattern_analysis": pattern_result,
        "trend_analysis": trend_result,
        "total_recommendations": len(all_recommendations),
        "total_insights": len(all_insights),
        "high_priority_actions": len(high_priority),
    }


def demonstrate_advanced_features() -> None:
    """Demonstrate advanced team coach features."""
    # Example of analyzing a failed workflow
    failed_workflow = {
        "workflow_id": "failed_demo_workflow",
        "agents_used": ["orchestrator", "code-writer"],
        "task_sequence": [
            {
                "agent": "orchestrator",
                "action": "coordinate_tasks",
                "duration_seconds": 15,
                "success": True,
                "metadata": {},
            },
            {
                "agent": "code-writer",
                "action": "generate_code",
                "duration_seconds": 180,  # Very slow
                "success": False,  # Failed
                "metadata": {"error": "compilation_failed", "attempts": 3},
            },
        ],
        "resource_usage": {
            "peak_memory_mb": 1024,  # High memory usage
            "cpu_time_seconds": 195,
            "disk_io_mb": 5,
        },
        "outcomes": {
            "files_created": 0,  # No output
            "tests_written": 0,
            "lines_of_code": 0,
            "success_rate": 0.5,  # Partial success
            "user_satisfaction": "low",
            "errors_encountered": 3,
            "warnings_generated": 8,
        },
        "project_context": "problematic_scenario",
    }

    failed_analysis = run_team_coach(
        {
            "analysis_type": "performance",
            "workflow_data": failed_workflow,
            "historical_context": {},
            "reflection_scope": "session",
        },
    )

    failed_analysis["analysis_results"]

    for rec in failed_analysis["recommendations"][:3]:
        pass

    # Simulate real-time monitoring scenario
    realtime_workflow = {
        "workflow_id": "realtime_monitoring",
        "agents_used": ["orchestrator", "code-writer", "test-writer"],
        "task_sequence": [
            {
                "agent": "orchestrator",
                "action": "coordinate_tasks",
                "duration_seconds": 8,  # Very fast
                "success": True,
                "metadata": {"optimization_applied": True},
            },
            {
                "agent": "code-writer",
                "action": "generate_optimized_code",
                "duration_seconds": 35,  # Optimized speed
                "success": True,
                "metadata": {"cache_hit": True, "templates_used": 3},
            },
            {
                "agent": "test-writer",
                "action": "generate_comprehensive_tests",
                "duration_seconds": 25,  # Efficient testing
                "success": True,
                "metadata": {"parallel_generation": True, "coverage": 95},
            },
        ],
        "resource_usage": {
            "peak_memory_mb": 192,  # Optimized memory usage
            "cpu_time_seconds": 68,
            "disk_io_mb": 12,
        },
        "outcomes": {
            "files_created": 4,
            "tests_written": 22,
            "lines_of_code": 180,
            "success_rate": 1.0,
            "user_satisfaction": "high",
            "errors_encountered": 0,
            "warnings_generated": 0,
        },
        "project_context": "optimized_workflow",
    }

    optimized_analysis = run_team_coach(
        {
            "analysis_type": "performance",
            "workflow_data": realtime_workflow,
            "historical_context": {},
            "reflection_scope": "session",
        },
    )

    optimized_analysis["analysis_results"]

    if optimized_analysis["recommendations"]:
        for rec in optimized_analysis["recommendations"]:
            if "maintain" in rec["description"].lower():
                pass
    else:
        pass


if __name__ == "__main__":
    try:
        # Run main demo
        results = demo_team_coach()

        # Run advanced features demo
        demonstrate_advanced_features()

    except Exception:
        import traceback

        traceback.print_exc()
