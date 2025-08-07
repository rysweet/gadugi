#!/usr/bin/env python3
"""
Demo script for Team Coach Engine

Shows the team coach capabilities including:
- Performance analysis of workflows
- Pattern recognition across multiple workflows
- Learning insights extraction
- Optimization recommendations
- Trend analysis
"""

import json
from datetime import datetime, timedelta
from team_coach_engine import run_team_coach


def demo_team_coach():
    """Demonstrate team coach capabilities"""
    
    print("🏆 Team Coach Engine Demo")
    print("=" * 50)
    
    # Create sample workflow data for analysis
    print("\n1. 📊 Analyzing Single Workflow Performance")
    print("-" * 40)
    
    sample_workflow = {
        'workflow_id': 'demo_workflow_001',
        'agents_used': ['orchestrator', 'task-decomposer', 'code-writer', 'test-writer'],
        'task_sequence': [
            {
                'agent': 'orchestrator',
                'action': 'coordinate_tasks',
                'duration_seconds': 12,
                'success': True,
                'metadata': {'tasks_created': 4, 'parallel_execution': True}
            },
            {
                'agent': 'task-decomposer',
                'action': 'decompose_requirements',
                'duration_seconds': 28,
                'success': True,
                'metadata': {'subtasks_created': 6, 'complexity_score': 7.5}
            },
            {
                'agent': 'code-writer',
                'action': 'generate_code',
                'duration_seconds': 95,
                'success': True,
                'metadata': {'files_created': 3, 'lines_written': 250, 'language': 'python'}
            },
            {
                'agent': 'test-writer',
                'action': 'generate_tests',
                'duration_seconds': 65,
                'success': True,
                'metadata': {'test_files_created': 2, 'tests_written': 18, 'coverage_target': 85}
            }
        ],
        'resource_usage': {
            'peak_memory_mb': 384,
            'cpu_time_seconds': 200,
            'disk_io_mb': 22,
            'network_io_mb': 1.5
        },
        'outcomes': {
            'files_created': 5,
            'tests_written': 18,
            'lines_of_code': 250,
            'success_rate': 1.0,
            'user_satisfaction': 'high',
            'errors_encountered': 0,
            'warnings_generated': 2
        },
        'project_context': 'gadugi_v0.3_development'
    }
    
    # Analyze performance
    performance_request = {
        'analysis_type': 'performance',
        'workflow_data': sample_workflow,
        'historical_context': {},
        'reflection_scope': 'session'
    }
    
    performance_result = run_team_coach(performance_request)
    
    print(f"✅ Performance Analysis Complete:")
    analysis = performance_result['analysis_results']
    print(f"   • Overall Performance Score: {analysis['performance_score']:.1f}/10.0")
    print(f"   • Workflow Duration: {analysis['workflow_duration']:.1f} seconds")
    print(f"   • Agents Utilized: {analysis['agents_utilized']}")
    print(f"   • Success Rate: {analysis['success_rate'] * 100:.0f}%")
    print(f"   • Efficiency Metrics:")
    for metric, value in analysis['efficiency_metrics'].items():
        print(f"     - {metric.replace('_', ' ').title()}: {value}")
    
    print(f"\n📋 Recommendations Generated: {len(performance_result['recommendations'])}")
    for i, rec in enumerate(performance_result['recommendations'][:3], 1):
        print(f"   {i}. [{rec['priority'].upper()}] {rec['description']}")
        print(f"      Expected: {rec['expected_improvement']}")
        print(f"      Effort: {rec['implementation_effort']}, Risk: {rec['risk_level']}")
    
    print("\n2. 🔍 Pattern Recognition Analysis")
    print("-" * 40)
    
    # Simulate historical workflows for pattern analysis
    historical_workflows = []
    base_time = datetime.now() - timedelta(hours=2)
    
    # Create varied workflows to demonstrate patterns
    workflow_scenarios = [
        {
            'name': 'fast_simple_workflow',
            'agents': ['orchestrator', 'code-writer'],
            'durations': [10, 25],
            'success_rate': 1.0,
            'memory': 128,
            'satisfaction': 'high'
        },
        {
            'name': 'complex_workflow',
            'agents': ['orchestrator', 'task-decomposer', 'code-writer', 'test-writer'],
            'durations': [15, 35, 80, 45],
            'success_rate': 0.95,
            'memory': 512,
            'satisfaction': 'high'
        },
        {
            'name': 'problematic_workflow',
            'agents': ['orchestrator', 'code-writer', 'test-writer'],
            'durations': [20, 120, 90],  # Slow code generation
            'success_rate': 0.7,
            'memory': 256,
            'satisfaction': 'medium'
        }
    ]
    
    for i, scenario in enumerate(workflow_scenarios * 2):  # Duplicate for patterns
        workflow_data = {
            'workflow_id': f'{scenario["name"]}_{i}',
            'agents_used': scenario['agents'],
            'task_sequence': [
                {
                    'agent': agent,
                    'action': f'perform_{agent.replace("-", "_")}_task',
                    'duration_seconds': duration,
                    'success': True if scenario['success_rate'] > 0.8 else (i % 2 == 0),
                    'metadata': {}
                }
                for agent, duration in zip(scenario['agents'], scenario['durations'])
            ],
            'resource_usage': {
                'peak_memory_mb': scenario['memory'],
                'cpu_time_seconds': sum(scenario['durations']),
                'disk_io_mb': 15
            },
            'outcomes': {
                'files_created': len(scenario['agents']),
                'tests_written': 8 if 'test-writer' in scenario['agents'] else 0,
                'lines_of_code': sum(scenario['durations']),
                'success_rate': scenario['success_rate'],
                'user_satisfaction': scenario['satisfaction']
            },
            'project_context': 'gadugi_v0.3_development'
        }
        historical_workflows.append(workflow_data)
    
    # Analyze patterns with historical context
    pattern_request = {
        'analysis_type': 'learning',
        'workflow_data': sample_workflow,
        'historical_context': {'previous_workflows': historical_workflows},
        'reflection_scope': 'project'
    }
    
    pattern_result = run_team_coach(pattern_request)
    
    print(f"✅ Pattern Analysis Complete:")
    patterns = pattern_result['patterns_identified']
    print(f"   • Patterns Identified: {len(patterns)}")
    
    for pattern in patterns[:4]:  # Show first 4 patterns
        print(f"     - {pattern['pattern_type'].title()}: {pattern['description']}")
        print(f"       Frequency: {pattern['frequency']:.0%}, Impact: {pattern['impact']}, Confidence: {pattern['confidence']:.0%}")
    
    print(f"\n🧠 Learning Insights Generated: {len(pattern_result['learning_insights'])}")
    for insight in pattern_result['learning_insights'][:3]:
        print(f"   • [{insight['insight_type'].replace('_', ' ').title()}] {insight['description']}")
        print(f"     Confidence: {insight['confidence']:.0%}")
    
    print("\n3. 📈 Performance Trend Analysis")
    print("-" * 40)
    
    # Analyze trends with system-wide scope
    trend_request = {
        'analysis_type': 'optimization',
        'workflow_data': sample_workflow,
        'historical_context': {'previous_workflows': historical_workflows},
        'reflection_scope': 'system'
    }
    
    trend_result = run_team_coach(trend_request)
    
    trends = trend_result['performance_trends']
    if 'insufficient_data' not in trends:
        print(f"✅ Trend Analysis Complete:")
        print(f"   • Overall Improvement Rate: {trends.get('improvement_rate', 0) * 100:.1f}%")
        print(f"   • Success Trend: {trends.get('success_trend', 0) * 100:+.1f}%")
        print(f"   • Speed Trend: {trends.get('speed_trend', 0) * 100:+.1f}%")
        print(f"   • Workflows Analyzed: {trends.get('total_workflows_analyzed', 0)}")
    else:
        print("   • Insufficient historical data for trend analysis")
    
    print("\n4. 🎯 Comprehensive Optimization Report")
    print("-" * 40)
    
    # Generate comprehensive optimization report
    all_recommendations = []
    all_insights = []
    
    for result in [performance_result, pattern_result, trend_result]:
        all_recommendations.extend(result['recommendations'])
        all_insights.extend(result['learning_insights'])
    
    # Prioritize recommendations
    high_priority = [r for r in all_recommendations if r['priority'] == 'high']
    medium_priority = [r for r in all_recommendations if r['priority'] == 'medium']
    
    print(f"📊 Optimization Summary:")
    print(f"   • Total Recommendations: {len(all_recommendations)}")
    print(f"     - High Priority: {len(high_priority)}")
    print(f"     - Medium Priority: {len(medium_priority)}")
    print(f"   • Learning Insights: {len(all_insights)}")
    
    print(f"\n🚀 Top Priority Actions:")
    for i, rec in enumerate(high_priority[:3], 1):
        print(f"   {i}. {rec['description']}")
        print(f"      → {rec['expected_improvement']}")
        print(f"      Implementation: {rec['implementation_effort']} effort, {rec['risk_level']} risk")
    
    print(f"\n💡 Key Learning Insights:")
    best_practices = [i for i in all_insights if i['insight_type'] == 'best_practice']
    for insight in best_practices[:2]:
        print(f"   • {insight['description']}")
    
    optimization_opportunities = [i for i in all_insights if i['insight_type'] == 'optimization_opportunity']
    for insight in optimization_opportunities[:2]:
        print(f"   • {insight['description']}")
    
    print(f"\n📈 Team Coach Demo Summary")
    print("=" * 50)
    print("✅ Successfully demonstrated:")
    print("   • Comprehensive workflow performance analysis")
    print("   • Multi-dimensional scoring (speed, quality, resource, coordination)")
    print("   • Pattern recognition across workflow histories")
    print("   • Learning insights extraction from success and failure patterns")
    print("   • Prioritized optimization recommendations")
    print("   • Performance trend analysis and forecasting")
    print()
    print("🎯 Team Coach is ready for:")
    print("   • Real-time workflow optimization")
    print("   • Historical pattern analysis for continuous improvement")
    print("   • Intelligent recommendation generation")
    print("   • Multi-agent coordination enhancement")
    print("   • Performance trend monitoring and forecasting")
    
    # Return comprehensive results for further analysis
    return {
        'performance_analysis': performance_result,
        'pattern_analysis': pattern_result,
        'trend_analysis': trend_result,
        'total_recommendations': len(all_recommendations),
        'total_insights': len(all_insights),
        'high_priority_actions': len(high_priority)
    }


def demonstrate_advanced_features():
    """Demonstrate advanced team coach features"""
    
    print("\n\n🔬 Advanced Team Coach Features Demo")
    print("=" * 50)
    
    print("\n1. 🎨 Custom Workflow Analysis")
    print("-" * 30)
    
    # Example of analyzing a failed workflow
    failed_workflow = {
        'workflow_id': 'failed_demo_workflow',
        'agents_used': ['orchestrator', 'code-writer'],
        'task_sequence': [
            {
                'agent': 'orchestrator',
                'action': 'coordinate_tasks',
                'duration_seconds': 15,
                'success': True,
                'metadata': {}
            },
            {
                'agent': 'code-writer',
                'action': 'generate_code',
                'duration_seconds': 180,  # Very slow
                'success': False,  # Failed
                'metadata': {'error': 'compilation_failed', 'attempts': 3}
            }
        ],
        'resource_usage': {
            'peak_memory_mb': 1024,  # High memory usage
            'cpu_time_seconds': 195,
            'disk_io_mb': 5
        },
        'outcomes': {
            'files_created': 0,  # No output
            'tests_written': 0,
            'lines_of_code': 0,
            'success_rate': 0.5,  # Partial success
            'user_satisfaction': 'low',
            'errors_encountered': 3,
            'warnings_generated': 8
        },
        'project_context': 'problematic_scenario'
    }
    
    failed_analysis = run_team_coach({
        'analysis_type': 'performance',
        'workflow_data': failed_workflow,
        'historical_context': {},
        'reflection_scope': 'session'
    })
    
    print(f"❌ Failed Workflow Analysis:")
    analysis = failed_analysis['analysis_results']
    print(f"   • Performance Score: {analysis['performance_score']:.1f}/10.0 (Poor)")
    print(f"   • Success Rate: {analysis['success_rate'] * 100:.0f}%")
    print(f"   • Resource Efficiency: {analysis['efficiency_metrics']['resource_efficiency']}")
    
    print(f"\n🔧 Recovery Recommendations:")
    for rec in failed_analysis['recommendations'][:3]:
        print(f"   • {rec['description']} (Priority: {rec['priority']})")
    
    print("\n2. ⚡ Real-time Performance Monitoring")
    print("-" * 30)
    
    # Simulate real-time monitoring scenario
    realtime_workflow = {
        'workflow_id': 'realtime_monitoring',
        'agents_used': ['orchestrator', 'code-writer', 'test-writer'],
        'task_sequence': [
            {
                'agent': 'orchestrator',
                'action': 'coordinate_tasks',
                'duration_seconds': 8,  # Very fast
                'success': True,
                'metadata': {'optimization_applied': True}
            },
            {
                'agent': 'code-writer',
                'action': 'generate_optimized_code',
                'duration_seconds': 35,  # Optimized speed
                'success': True,
                'metadata': {'cache_hit': True, 'templates_used': 3}
            },
            {
                'agent': 'test-writer',
                'action': 'generate_comprehensive_tests',
                'duration_seconds': 25,  # Efficient testing
                'success': True,
                'metadata': {'parallel_generation': True, 'coverage': 95}
            }
        ],
        'resource_usage': {
            'peak_memory_mb': 192,  # Optimized memory usage
            'cpu_time_seconds': 68,
            'disk_io_mb': 12
        },
        'outcomes': {
            'files_created': 4,
            'tests_written': 22,
            'lines_of_code': 180,
            'success_rate': 1.0,
            'user_satisfaction': 'high',
            'errors_encountered': 0,
            'warnings_generated': 0
        },
        'project_context': 'optimized_workflow'
    }
    
    optimized_analysis = run_team_coach({
        'analysis_type': 'performance',
        'workflow_data': realtime_workflow,
        'historical_context': {},
        'reflection_scope': 'session'
    })
    
    print(f"🚀 Optimized Workflow Results:")
    analysis = optimized_analysis['analysis_results']
    print(f"   • Performance Score: {analysis['performance_score']:.1f}/10.0 (Excellent)")
    print(f"   • Duration: {analysis['workflow_duration']:.0f}s (Fast)")
    print(f"   • All Efficiency Metrics: Excellent")
    
    print(f"\n✨ Performance Improvements Detected:")
    if optimized_analysis['recommendations']:
        for rec in optimized_analysis['recommendations']:
            if 'maintain' in rec['description'].lower():
                print(f"   • {rec['description']}")
    else:
        print("   • No recommendations needed - workflow is performing optimally!")
    
    print("\n🎓 Advanced Demo Complete")
    print("Team Coach successfully analyzed diverse workflow scenarios:")
    print("• High-performing workflows with detailed metrics")
    print("• Failed workflows with targeted recovery recommendations")  
    print("• Optimized workflows with maintenance suggestions")
    print("• Real-time performance monitoring capabilities")


if __name__ == '__main__':
    try:
        print("🚀 Starting Team Coach Engine Demonstration...")
        
        # Run main demo
        results = demo_team_coach()
        
        # Run advanced features demo
        demonstrate_advanced_features()
        
        print(f"\n🎉 Team Coach Demo Completed Successfully!")
        print(f"   • Generated {results['total_recommendations']} optimization recommendations")
        print(f"   • Extracted {results['total_insights']} learning insights")
        print(f"   • Identified {results['high_priority_actions']} high-priority actions")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()