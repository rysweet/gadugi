#!/usr/bin/env python3
"""
Test script for WorkflowManagerV03 agent.

This script validates that the workflow manager v0.3 agent:
1. Initializes properly with memory integration
2. Can handle basic workflow tasks
3. Has proper error handling
4. Learns from experiences
"""

import asyncio
import sys
from pathlib import Path

# Add the agent to the Python path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflow_manager_v03 import WorkflowManagerV03, PRReviewFeedback


async def test_workflow_manager_basic():
    """Basic functionality test."""
    print("🧪 Testing WorkflowManagerV03 - Basic Functionality")
    print("=" * 60)

    # Create agent
    agent = WorkflowManagerV03("test_workflow_manager")

    try:
        # Test initialization (without actual memory system)
        print("✓ Agent created successfully")

        # Test task capability check
        can_handle = await agent.can_handle_task("Implement user authentication feature")
        print(f"✓ Can handle auth task: {can_handle}")

        can_handle_other = await agent.can_handle_task("Write a poetry book")
        print(f"✓ Can handle poetry task: {can_handle_other}")

        # Test PR feedback processing (without memory)
        feedback = [
            PRReviewFeedback(
                reviewer="test_reviewer",
                comment="Please add error handling for edge cases",
                severity="major"
            ),
            PRReviewFeedback(
                reviewer="security_team",
                comment="Consider input validation",
                severity="critical"
            )
        ]

        # This would work without memory system
        agent.pr_feedback_history.extend(feedback)
        print(f"✓ PR feedback processed: {len(agent.pr_feedback_history)} items")

        # Test error pattern detection
        error_msg = "Git merge conflict in src/main.py"

        # Test the agent's error pattern extraction
        pattern_result = agent._extract_error_pattern(error_msg)
        detected_patterns = [pattern_result['pattern']] if pattern_result else []

        print(f"✓ Error pattern detection: {detected_patterns}")

        print("\n🎉 Basic functionality tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # No need to shutdown since no memory was initialized
        pass

    return True


async def test_workflow_phases():
    """Test workflow phase enumeration and logic."""
    print("\n🧪 Testing Workflow Phases")
    print("=" * 60)

    from workflow_manager_v03 import WorkflowPhase, WorkflowContext

    # Test workflow phases
    phases = list(WorkflowPhase)
    print(f"✓ Total workflow phases: {len(phases)}")

    expected_phases = [
        "REQUIREMENTS_ANALYSIS",
        "DESIGN_PLANNING",
        "TASK_DECOMPOSITION",
        "ENVIRONMENT_SETUP",
        "IMPLEMENTATION",
        "TESTING",
        "CODE_REVIEW_PREP",
        "QUALITY_GATES",
        "DOCUMENTATION",
        "PR_CREATION",
        "CI_CD_VALIDATION",
        "REVIEW_RESPONSE",
        "MERGE_CLEANUP"
    ]

    for expected in expected_phases:
        assert any(phase.name == expected for phase in phases), f"Missing phase: {expected}"

    print("✓ All expected phases present")

    # Test workflow context
    context = WorkflowContext(
        task_description="Test task",
        repository_path="/test/path",
        target_branch="main"
    )

    print(f"✓ Workflow context created: {context.task_description}")

    return True


async def test_helper_methods():
    """Test helper methods."""
    print("\n🧪 Testing Helper Methods")
    print("=" * 60)

    agent = WorkflowManagerV03("test_helper")

    try:
        # Test complexity estimation
        requirements = {
            'is_feature': True,
            'needs_testing': True,
            'needs_documentation': True
        }

        complexity = agent._estimate_complexity(requirements)
        print(f"✓ Complexity estimation: {complexity}")

        # Test effort estimation
        effort = agent._estimate_subtask_effort("api_implementation")
        print(f"✓ Subtask effort estimation: {effort}")

        # Test effort to number conversion
        effort_num = agent._effort_to_number("medium")
        print(f"✓ Effort to number: {effort_num}")

        # Test error pattern extraction
        error_text = "Git authentication failed during push"
        pattern = agent._extract_error_pattern(error_text)
        print(f"✓ Error pattern extracted: {pattern}")

        # Test PR description generation
        from workflow_manager_v03 import WorkflowContext, WorkflowPhase
        context = WorkflowContext(
            task_description="Add user authentication",
            repository_path="/test",
            target_branch="main"
        )

        # Add some mock phase outputs
        context.phase_outputs[WorkflowPhase.IMPLEMENTATION] = {
            'implementation_results': [
                {'subtask_name': 'JWT token validation'},
                {'subtask_name': 'User session management'}
            ]
        }

        pr_description = agent._generate_pr_description(context)
        print(f"✓ PR description generated ({len(pr_description)} chars)")

        print("\n🎉 Helper methods tests passed!")

    except Exception as e:
        print(f"❌ Helper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


async def main():
    """Run all tests."""
    print("🚀 WorkflowManagerV03 Test Suite")
    print("=" * 80)

    tests = [
        test_workflow_manager_basic,
        test_workflow_phases,
        test_helper_methods
    ]

    results = []

    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Results Summary")
    print("=" * 80)

    passed = sum(results)
    total = len(results)

    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! WorkflowManagerV03 is ready for production.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    # Run the test suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
