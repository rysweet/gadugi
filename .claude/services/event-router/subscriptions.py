"""
Event Subscription Configuration for Gadugi v0.3
=================================================

Configures which agents subscribe to which events based on the v0.3 spec.
"""

from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EventSubscription:
    """Represents an event subscription."""
    agent_id: str
    pattern: str  # Can be wildcard pattern like "*.started"
    handler: str  # Handler function name in the agent
    priority: EventPriority = EventPriority.NORMAL
    filter: Optional[Dict[str, Any]] = None


class EventSubscriptionManager:
    """Manages event subscriptions for all agents."""

    def __init__(self):
        """Initialize subscription manager."""
        self.subscriptions: Dict[str, List[EventSubscription]] = {}
        self._pattern_cache: Dict[str, re.Pattern] = {}
        self._initialize_default_subscriptions()

    def _pattern_to_regex(self, pattern: str) -> re.Pattern:
        """Convert wildcard pattern to regex."""
        if pattern not in self._pattern_cache:
            # Convert * to .* for regex
            regex_pattern = pattern.replace(".", r"\.")
            regex_pattern = regex_pattern.replace("*", ".*")
            regex_pattern = f"^{regex_pattern}$"
            self._pattern_cache[pattern] = re.compile(regex_pattern)
        return self._pattern_cache[pattern]

    def _initialize_default_subscriptions(self):
        """Initialize default subscriptions based on v0.3 spec."""

        # Gadugi Agent subscriptions
        self.add_subscription("gadugi", "*.started", "track_agent_start")
        self.add_subscription("gadugi", "*.stopped", "track_agent_completion")
        self.add_subscription("gadugi", "system.shutdown", "graceful_shutdown")

        # Orchestration Agent subscriptions
        self.add_subscription("orchestration", "*.hasQuestion", "route_question_to_user", EventPriority.HIGH)
        self.add_subscription("orchestration", "*.needsApproval", "route_approval_to_user", EventPriority.HIGH)
        self.add_subscription("orchestration", "*.stopped", "aggregate_results")
        self.add_subscription("orchestration", "teamcoach.reflection_complete", "learn_from_session")
        self.add_subscription("orchestration", "decomposition.completed", "begin_execution_planning")

        # Team Coach subscriptions
        self.add_subscription("teamcoach", "orchestration.stopped", "trigger_reflection")
        self.add_subscription("teamcoach", "*.stopped", "collect_metrics")

        # WorkflowManager subscriptions
        self.add_subscription("workflow", "orchestration.implementation_started", "begin_workflow")
        self.add_subscription("workflow", "orchestration.tasks_distributed", "begin_assigned_workflow")
        self.add_subscription("workflow", "*.hasQuestion.response", "continue_after_answer")
        self.add_subscription("workflow", "*.needsApproval.response", "continue_after_approval")
        self.add_subscription("workflow", "codereview.completed", "proceed_to_phase_10")
        self.add_subscription("workflow", "tests.failed", "trigger_test_solver")
        self.add_subscription("workflow", "pr.conflict", "trigger_conflict_resolution")

        # CodeReviewer subscriptions
        self.add_subscription("codereview", "workflow.pr_created", "trigger_review")
        self.add_subscription("codereview", "workflow.code_changed", "re_review")
        self.add_subscription("codereview", "pr.updated", "re_review_changed_files")
        self.add_subscription("codereview", "review.response_submitted", "verify_changes_addressed")

        # MemoryManager subscriptions
        self.add_subscription("memory", "*.lessons_learned", "store_learnings")
        self.add_subscription("memory", "*.memory_updates", "update_memories")
        self.add_subscription("memory", "agent.started", "load_agent_memories")
        self.add_subscription("memory", "orchestration.pattern_learned", "store_pattern")
        self.add_subscription("memory", "workflow.pr_merged", "update_memory_md")
        self.add_subscription("memory", "agent.initialized", "load_agent_memories")
        self.add_subscription("memory", "system.shutdown", "final_memory_sync")

        # TaskDecomposer subscriptions
        self.add_subscription("taskdecomposer", "orchestration.problem_identified", "begin_decomposition")
        self.add_subscription("taskdecomposer", "orchestration.task_analyzed", "begin_decomposition")
        self.add_subscription("taskdecomposer", "workflow.blocked", "analyze_blockage")
        self.add_subscription("taskdecomposer", "decomposition.pattern_matched", "apply_learned_pattern")

        # TestSolver subscriptions
        self.add_subscription("testsolver", "workflow.tests_failed", "analyze_failures")
        self.add_subscription("testsolver", "tests.failed", "analyze_and_fix_failures")
        self.add_subscription("testsolver", "workflow.phase_started", "monitor_test_phase",
                            filter={"phase": "testing"})

        # PrBacklogManager subscriptions
        self.add_subscription("prbacklog", "workflow.pr_created", "add_to_backlog")
        self.add_subscription("prbacklog", "pr.created", "add_to_backlog_tracking")
        self.add_subscription("prbacklog", "codereview.completed", "update_readiness")
        self.add_subscription("prbacklog", "*.pr_conflict", "flag_for_resolution")
        self.add_subscription("prbacklog", "pr.review_completed", "update_readiness_status")
        self.add_subscription("prbacklog", "pr.conflict_detected", "flag_for_resolution")

        logger.info(f"Initialized {len(self.subscriptions)} default subscription patterns")

    def add_subscription(self,
                        agent_id: str,
                        pattern: str,
                        handler: str,
                        priority: EventPriority = EventPriority.NORMAL,
                        filter: Optional[Dict[str, Any]] = None):
        """Add a new event subscription."""
        subscription = EventSubscription(
            agent_id=agent_id,
            pattern=pattern,
            handler=handler,
            priority=priority,
            filter=filter
        )

        if agent_id not in self.subscriptions:
            self.subscriptions[agent_id] = []

        self.subscriptions[agent_id].append(subscription)
        logger.debug(f"Added subscription: {agent_id} -> {pattern} ({handler})")

    def get_subscribers(self, event_type: str) -> List[EventSubscription]:
        """Get all subscribers for a given event type."""
        subscribers = []

        for agent_id, agent_subs in self.subscriptions.items():
            for sub in agent_subs:
                pattern_regex = self._pattern_to_regex(sub.pattern)
                if pattern_regex.match(event_type):
                    subscribers.append(sub)

        # Sort by priority (critical first)
        priority_order = {
            EventPriority.CRITICAL: 0,
            EventPriority.HIGH: 1,
            EventPriority.NORMAL: 2,
            EventPriority.LOW: 3
        }
        subscribers.sort(key=lambda s: priority_order[s.priority])

        return subscribers

    def remove_subscription(self, agent_id: str, pattern: str) -> bool:
        """Remove a subscription."""
        if agent_id in self.subscriptions:
            original_count = len(self.subscriptions[agent_id])
            self.subscriptions[agent_id] = [
                sub for sub in self.subscriptions[agent_id]
                if sub.pattern != pattern
            ]
            removed = len(self.subscriptions[agent_id]) < original_count
            if removed:
                logger.debug(f"Removed subscription: {agent_id} -> {pattern}")
            return removed
        return False

    def get_agent_subscriptions(self, agent_id: str) -> List[EventSubscription]:
        """Get all subscriptions for a specific agent."""
        return self.subscriptions.get(agent_id, [])

    def clear_agent_subscriptions(self, agent_id: str):
        """Clear all subscriptions for an agent."""
        if agent_id in self.subscriptions:
            count = len(self.subscriptions[agent_id])
            del self.subscriptions[agent_id]
            logger.info(f"Cleared {count} subscriptions for agent {agent_id}")

    def get_subscription_stats(self) -> Dict[str, Any]:
        """Get subscription statistics."""
        total_subscriptions = sum(len(subs) for subs in self.subscriptions.values())

        # Count subscriptions by pattern type
        pattern_counts = {}
        for agent_subs in self.subscriptions.values():
            for sub in agent_subs:
                pattern_type = sub.pattern.split('.')[0]
                pattern_counts[pattern_type] = pattern_counts.get(pattern_type, 0) + 1

        return {
            "total_agents": len(self.subscriptions),
            "total_subscriptions": total_subscriptions,
            "subscriptions_per_agent": {
                agent_id: len(subs)
                for agent_id, subs in self.subscriptions.items()
            },
            "pattern_counts": pattern_counts,
            "high_priority_count": sum(
                1 for subs in self.subscriptions.values()
                for sub in subs if sub.priority in [EventPriority.HIGH, EventPriority.CRITICAL]
            )
        }


# Global subscription manager instance
subscription_manager = EventSubscriptionManager()


def get_subscription_manager() -> EventSubscriptionManager:
    """Get the global subscription manager instance."""
    return subscription_manager
