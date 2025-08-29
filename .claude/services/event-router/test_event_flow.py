#!/usr/bin/env python3
"""
Test script to demonstrate event flow between agents in Gadugi v0.3
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directories to path
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from models import AgentEvent, EventType, EventPriority
from subscriptions import get_subscription_manager


async def simulate_agent_lifecycle():
    """Simulate a complete agent lifecycle with events."""

    print("\n" + "="*60)
    print("🚀 GADUGI V0.3 EVENT FLOW DEMONSTRATION")
    print("="*60 + "\n")

    # Get subscription manager
    sub_manager = get_subscription_manager()

    # 1. Orchestration starts (user request)
    print("📋 PHASE 1: User Request → Orchestration")
    print("-" * 40)

    orchestration_started = {
        "event_type": "orchestration.started",
        "agent_id": "orchestration-001",
        "data": {
            "input": "Implement user authentication with JWT",
            "task_id": "task-auth-123",
            "timestamp": datetime.now().isoformat()
        }
    }

    print(f"✉️  Event: orchestration.started")
    subscribers = sub_manager.get_subscribers("orchestration.started")
    print(f"   Subscribers: {[s.agent_id for s in subscribers]}")

    # 2. Problem identification triggers decomposition
    print("\n📋 PHASE 2: Problem Identified → Task Decomposition")
    print("-" * 40)

    problem_identified = {
        "event_type": "orchestration.problem_identified",
        "agent_id": "orchestration-001",
        "data": {
            "problem": "User authentication system needed",
            "complexity": "medium",
            "timestamp": datetime.now().isoformat()
        }
    }

    print(f"✉️  Event: orchestration.problem_identified")
    subscribers = sub_manager.get_subscribers("orchestration.problem_identified")
    for sub in subscribers:
        print(f"   → {sub.agent_id}.{sub.handler}")

    # 3. Decomposition completes
    print("\n📋 PHASE 3: Decomposition Complete → Orchestration")
    print("-" * 40)

    decomposition_complete = {
        "event_type": "decomposition.completed",
        "agent_id": "taskdecomposer-001",
        "data": {
            "subtasks": ["Design auth schema", "Implement JWT", "Add endpoints", "Write tests"],
            "dependencies": {"Implement JWT": ["Design auth schema"]},
            "timestamp": datetime.now().isoformat()
        }
    }

    print(f"✉️  Event: decomposition.completed")
    subscribers = sub_manager.get_subscribers("decomposition.completed")
    for sub in subscribers:
        print(f"   → {sub.agent_id}.{sub.handler}")

    # 4. Tasks distributed to WorkflowManagers
    print("\n📋 PHASE 4: Tasks Distributed → Multiple WorkflowManagers")
    print("-" * 40)

    tasks_distributed = {
        "event_type": "orchestration.tasks_distributed",
        "agent_id": "orchestration-001",
        "data": {
            "tasks": [
                {"id": "wf-001", "task": "Design auth schema"},
                {"id": "wf-002", "task": "Implement JWT"},
                {"id": "wf-003", "task": "Add endpoints"}
            ],
            "timestamp": datetime.now().isoformat()
        }
    }

    print(f"✉️  Event: orchestration.tasks_distributed")
    subscribers = sub_manager.get_subscribers("orchestration.tasks_distributed")
    for sub in subscribers:
        print(f"   → {sub.agent_id}.{sub.handler}")

    # 5. Workflow creates PR
    print("\n📋 PHASE 5: PR Created → Code Review")
    print("-" * 40)

    pr_created = {
        "event_type": "workflow.pr_created",
        "agent_id": "workflow-001",
        "data": {
            "pr_number": 420,
            "title": "feat: Add JWT authentication",
            "branch": "feature/jwt-auth",
            "timestamp": datetime.now().isoformat()
        }
    }

    print(f"✉️  Event: workflow.pr_created")
    subscribers = sub_manager.get_subscribers("workflow.pr_created")
    for sub in subscribers:
        print(f"   → {sub.agent_id}.{sub.handler}")

    # 6. Agent needs approval
    print("\n📋 PHASE 6: Agent Needs Approval → Orchestration → User")
    print("-" * 40)

    needs_approval = {
        "event_type": "workflow.needsApproval",
        "agent_id": "workflow-001",
        "data": {
            "command": "npm install jsonwebtoken bcrypt",
            "description": "Install JWT and bcrypt packages",
            "risk_level": "low",
            "timestamp": datetime.now().isoformat()
        }
    }

    print(f"✉️  Event: workflow.needsApproval")
    subscribers = sub_manager.get_subscribers("workflow.needsApproval")
    for sub in subscribers:
        print(f"   → {sub.agent_id}.{sub.handler} (priority: {sub.priority.value})")

    # 7. Tests fail
    print("\n📋 PHASE 7: Tests Failed → TestSolver")
    print("-" * 40)

    tests_failed = {
        "event_type": "workflow.tests_failed",
        "agent_id": "workflow-001",
        "data": {
            "failed_tests": ["test_jwt_validation", "test_token_expiry"],
            "error": "JWT signature verification failed",
            "timestamp": datetime.now().isoformat()
        }
    }

    print(f"✉️  Event: workflow.tests_failed")
    subscribers = sub_manager.get_subscribers("workflow.tests_failed")
    for sub in subscribers:
        print(f"   → {sub.agent_id}.{sub.handler}")

    # 8. All workflows complete
    print("\n📋 PHASE 8: All Tasks Complete → Orchestration")
    print("-" * 40)

    for i in range(3):
        workflow_stopped = {
            "event_type": f"workflow.stopped",
            "agent_id": f"workflow-00{i+1}",
            "data": {
                "output": f"Task {i+1} completed successfully",
                "task_id": f"task-{i+1}",
                "success": True,
                "duration_seconds": 120.5 + i*10,
                "timestamp": datetime.now().isoformat()
            }
        }

        print(f"✉️  Event: workflow.stopped (from workflow-00{i+1})")

    subscribers = sub_manager.get_subscribers("workflow.stopped")
    for sub in subscribers:
        print(f"   → {sub.agent_id}.{sub.handler}")

    # 9. Orchestration completes, triggers reflection
    print("\n📋 PHASE 9: Orchestration Complete → Team Coach Reflection")
    print("-" * 40)

    orchestration_stopped = {
        "event_type": "orchestration.stopped",
        "agent_id": "orchestration-001",
        "data": {
            "output": "Authentication system implemented successfully",
            "task_id": "task-auth-123",
            "success": True,
            "duration_seconds": 450.3,
            "timestamp": datetime.now().isoformat()
        }
    }

    print(f"✉️  Event: orchestration.stopped")
    subscribers = sub_manager.get_subscribers("orchestration.stopped")
    for sub in subscribers:
        print(f"   → {sub.agent_id}.{sub.handler}")

    # 10. Team Coach learns and stores memories
    print("\n📋 PHASE 10: Lessons Learned → Memory Storage")
    print("-" * 40)

    lessons_learned = {
        "event_type": "teamcoach.lessons_learned",
        "agent_id": "teamcoach-001",
        "data": {
            "lessons": [
                "JWT implementation pattern successful",
                "Parallel testing saved 60% time",
                "Need better error messages in auth endpoints"
            ],
            "improvements": ["Add rate limiting", "Implement refresh tokens"],
            "timestamp": datetime.now().isoformat()
        }
    }

    print(f"✉️  Event: teamcoach.lessons_learned")
    subscribers = sub_manager.get_subscribers("teamcoach.lessons_learned")
    for sub in subscribers:
        print(f"   → {sub.agent_id}.{sub.handler}")

    # Show subscription statistics
    print("\n" + "="*60)
    print("📊 SUBSCRIPTION STATISTICS")
    print("="*60)

    stats = sub_manager.get_subscription_stats()
    print(f"Total Agents: {stats['total_agents']}")
    print(f"Total Subscriptions: {stats['total_subscriptions']}")
    print(f"High Priority Subscriptions: {stats['high_priority_count']}")
    print("\nSubscriptions per Agent:")
    for agent, count in stats['subscriptions_per_agent'].items():
        print(f"  - {agent}: {count} subscriptions")

    print("\nPattern Distribution:")
    for pattern, count in stats['pattern_counts'].items():
        print(f"  - {pattern}.*: {count} subscriptions")


async def test_wildcard_patterns():
    """Test wildcard pattern matching."""
    print("\n" + "="*60)
    print("🔍 TESTING WILDCARD PATTERNS")
    print("="*60 + "\n")

    sub_manager = get_subscription_manager()

    # Test various event types against wildcard patterns
    test_events = [
        "workflow.started",
        "workflow.stopped",
        "orchestration.started",
        "random.hasQuestion",
        "testsolver.needsApproval",
        "memory.stored"
    ]

    for event_type in test_events:
        print(f"\n🔸 Event: {event_type}")
        subscribers = sub_manager.get_subscribers(event_type)
        if subscribers:
            for sub in subscribers:
                print(f"   Matched: {sub.pattern} → {sub.agent_id}.{sub.handler}")
        else:
            print("   No subscribers")


async def main():
    """Run all tests."""
    await simulate_agent_lifecycle()
    await test_wildcard_patterns()

    print("\n" + "="*60)
    print("✅ EVENT FLOW DEMONSTRATION COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
