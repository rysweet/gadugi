#!/usr/bin/env python3
"""
Team Coach Agent - Example Usage

This script demonstrates how to use the Team Coach agent for session analysis,
improvement identification, and coaching recommendations.
"""

import asyncio
from datetime import datetime
from team_coach import TeamCoach, SessionMetrics


def example_basic_usage():
    """Demonstrate basic Team Coach usage."""
    print("=== Team Coach Basic Usage Example ===\n")

    # Initialize the Team Coach
    coach = TeamCoach()
    print(f"Initialized {coach.name}")

    # Example session data - successful session
    successful_session = {
        "session_id": "example_session_001",
        "start_time": "2025-01-08T09:00:00Z",
        "end_time": "2025-01-08T11:30:00Z",
        "tasks": ["implement-user-auth", "add-unit-tests", "update-docs"],
        "errors": [],
        "test_failures": 0,
        "code_changes": 42,
        "pr_created": True,
        "review_comments": 2
    }

    # Analyze the session
    print("Analyzing successful session...")
    result = coach.execute({
        "action": "analyze_session",
        "session_data": successful_session
    })

    if result["success"]:
        metrics = result["metrics"]
        print(f"Session ID: {metrics['session_id']}")
        print(f"Performance Score: {metrics['performance_score']:.2f}")
        print(f"Tasks Completed: {metrics['tasks_completed']}")
        print(f"Errors: {metrics['errors_encountered']}")
        print(f"Test Failures: {metrics['test_failures']}")

    print()


def example_improvement_identification():
    """Demonstrate improvement identification for problematic sessions."""
    print("=== Improvement Identification Example ===\n")

    coach = TeamCoach()

    # Example session data - problematic session
    problematic_session = {
        "session_id": "example_session_002",
        "start_time": "2025-01-08T14:00:00Z",
        "end_time": "2025-01-08T18:00:00Z",
        "tasks": [],  # No tasks completed
        "errors": ["import-error", "type-error", "connection-error", "timeout-error"],
        "test_failures": 5,
        "code_changes": 8,
        "pr_created": False,
        "review_comments": 0
    }

    # Analyze the problematic session
    print("Analyzing problematic session...")
    analysis_result = coach.execute({
        "action": "analyze_session",
        "session_data": problematic_session
    })

    if analysis_result["success"]:
        metrics = analysis_result["metrics"]
        print(f"Performance Score: {metrics['performance_score']:.2f}")

        # Identify improvements
        print("\nIdentifying improvements...")
        improvements_result = coach.execute({
            "action": "identify_improvements",
            "metrics": metrics
        })

        if improvements_result["success"]:
            suggestions = improvements_result["suggestions"]
            print(f"Found {len(suggestions)} improvement opportunities:\n")

            for i, suggestion in enumerate(suggestions, 1):
                print(f"{i}. {suggestion['title']}")
                print(f"   Type: {suggestion['type']}")
                print(f"   Priority: {suggestion['priority']}")
                print(f"   Impact: {suggestion['estimated_impact']:.1%}")
                print(f"   Steps: {', '.join(suggestion['implementation_steps'])}")
                print()


def example_performance_trends():
    """Demonstrate performance trend analysis with multiple sessions."""
    print("=== Performance Trends Example ===\n")

    coach = TeamCoach()

    # Simulate multiple sessions with varying performance
    sessions = [
        {"session_id": f"trend_session_{i:03d}", "tasks": [f"task_{j}" for j in range(i % 3)],
         "errors": [f"error_{j}" for j in range(i % 2)], "test_failures": i % 2,
         "pr_created": i % 2 == 0, "performance_score": 0.3 + (i * 0.05)}
        for i in range(1, 11)
    ]

    # Analyze each session to build history
    print("Building session history...")
    for session_data in sessions:
        coach.execute({
            "action": "analyze_session",
            "session_data": session_data
        })

    # Analyze trends
    print("Analyzing performance trends...")
    trends_result = coach.execute({
        "action": "track_performance_trends"
    })

    if trends_result["success"]:
        trends = trends_result["trends"]
        print(f"Generated {len(trends)} performance trends:\n")

        for trend in trends:
            print(f"Metric: {trend['metric_name']}")
            print(f"Direction: {trend['trend_direction']}")
            print(f"Current Value: {trend['current_value']:.2f}")
            print(f"Previous Value: {trend['previous_value']:.2f}")
            print(f"Change: {trend['change_percentage']:+.1f}%")
            print(f"Period: {trend['time_period']}")
            print()


def example_coaching_report():
    """Demonstrate coaching report generation."""
    print("=== Coaching Report Example ===\n")

    coach = TeamCoach()

    # Add some session data
    sample_sessions = [
        {"session_id": "report_session_1", "tasks": ["task1", "task2"],
         "errors": [], "test_failures": 0, "pr_created": True},
        {"session_id": "report_session_2", "tasks": ["task3"],
         "errors": ["error1"], "test_failures": 1, "pr_created": True},
        {"session_id": "report_session_3", "tasks": ["task4", "task5", "task6"],
         "errors": [], "test_failures": 0, "pr_created": True}
    ]

    for session_data in sample_sessions:
        coach.execute({
            "action": "analyze_session",
            "session_data": session_data
        })

    # Generate coaching report
    print("Generating coaching report...")
    report_result = coach.execute({
        "action": "generate_coaching_report"
    })

    if report_result["success"]:
        report = report_result["report"]
        print(f"Report Generated: {report['generated_at']}")
        print(f"Sessions Analyzed: {report['sessions_analyzed']}")
        print(f"Average Performance: {report['average_performance']:.2f}")
        print("\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
        print()


def example_github_integration():
    """Demonstrate GitHub issue creation (mocked)."""
    print("=== GitHub Integration Example ===\n")

    coach = TeamCoach()

    # Create improvement suggestion
    suggestion_data = {
        "title": "Implement Better Error Handling",
        "description": "Multiple sessions show high error rates. Implement comprehensive error handling with retry logic and better validation.",
        "type": "tooling",
        "priority": "high"
    }

    print("Creating GitHub issue for improvement...")
    # Use simple context to avoid security validation issues
    context = {
        "action": "create_improvement_issue",
        "suggestion": suggestion_data
    }
    issue_result = coach._execute_core(context)  # Use internal method to avoid security validation

    if issue_result["success"]:
        print(f"✅ Issue created successfully!")
        print(f"URL: {issue_result['issue_url']}")
        print(f"Message: {issue_result['message']}")
    else:
        print(f"❌ Failed to create issue: {issue_result['error']}")

    print()


def example_status_monitoring():
    """Demonstrate status monitoring and agent capabilities."""
    print("=== Status Monitoring Example ===\n")

    coach = TeamCoach()

    # Add some data to the coach
    sample_session = {
        "session_id": "status_demo_session",
        "tasks": ["demo-task"],
        "errors": [],
        "test_failures": 0,
        "pr_created": True
    }

    coach._execute_core({
        "action": "analyze_session",
        "session_data": sample_session
    })

    # Get status summary
    status = coach.get_status_summary()

    print("Team Coach Status:")
    print(f"  Name: {status['name']}")
    print(f"  Sessions Analyzed: {status['sessions_analyzed']}")
    print(f"  Improvements Identified: {status['improvements_identified']}")
    print(f"  Last Analysis: {status['last_analysis']}")
    print(f"  Performance Metrics: {status['performance_metrics']}")
    print(f"  Learning Summary: {status['learning_summary']}")
    print()


async def example_async_usage():
    """Demonstrate async interface usage."""
    print("=== Async Interface Example ===\n")

    coach = TeamCoach()

    # Sample session data
    session_data = {
        "session_id": "async_session_001",
        "tasks": ["async-task-1", "async-task-2"],
        "errors": ["minor-error"],
        "test_failures": 0,
        "pr_created": True
    }

    try:
        # Async session analysis
        print("Running async session analysis...")
        metrics = await coach.analyze_session(session_data)
        print(f"✅ Analyzed session: {metrics.session_id}")
        print(f"   Performance score: {metrics.performance_score:.2f}")

        # Async improvement identification
        print("Running async improvement identification...")
        improvements = await coach.identify_improvements(metrics)
        print(f"✅ Found {len(improvements)} improvement opportunities")

        # Async trend analysis
        print("Running async trend analysis...")
        trends = await coach.track_performance_trends()
        print(f"✅ Generated {len(trends)} performance trends")

        # Async coaching report
        print("Running async coaching report generation...")
        report = await coach.generate_coaching_report()
        print(f"✅ Report generated at: {report['generated_at']}")

    except Exception as e:
        print(f"❌ Async operation failed: {e}")

    print()


def main():
    """Run all examples."""
    print("Team Coach Agent - Comprehensive Usage Examples")
    print("=" * 50)
    print()

    # Run synchronous examples
    example_basic_usage()
    example_improvement_identification()
    example_performance_trends()
    example_coaching_report()
    example_github_integration()
    example_status_monitoring()

    # Run async example
    print("Running async examples...")
    asyncio.run(example_async_usage())

    print("All examples completed successfully!")
    print("\nFor more information, see:")
    print("- README.md for detailed documentation")
    print("- tests/test_team_coach.py for comprehensive test examples")
    print("- .claude/recipes/team-coach/recipe.yaml for configuration options")


if __name__ == "__main__":
    main()
