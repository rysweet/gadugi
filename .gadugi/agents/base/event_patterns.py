"""
Common Event Reaction Patterns and Examples
===========================================

This module provides example implementations of common event reaction patterns
that can be used with the EventSubscriber mixin. These patterns demonstrate
how to create sophisticated agent behaviors through event-driven programming.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

from .event_subscriber import (
    EventSubscriberMixin,
    EventPattern,
    ReactionType,
    CustomFilter,
    FilterOperator,
    AgentEvent,
)

# Type alias for EventSubscriber
EventSubscriber = EventSubscriberMixin


class CollaborationPatterns:
    """Event patterns for agent collaboration."""

    @staticmethod
    def create_help_request_pattern() -> EventPattern:
        """Pattern to match help requests from other agents."""
        return EventPattern(
            event_types={"collaboration.message"},
            custom_filters=[
                CustomFilter(
                    field="data.message_type",
                    operator=FilterOperator.EQUALS,
                    value="help_request",
                )
            ],
        )

    @staticmethod
    def create_task_completion_notification_pattern() -> EventPattern:
        """Pattern to match task completion notifications."""
        return EventPattern(
            event_types={"task.completed"}, priorities={"normal", "high"}
        )

    @staticmethod
    def create_error_escalation_pattern() -> EventPattern:
        """Pattern to match errors that need escalation."""
        return EventPattern(
            event_types={"error.occurred"},
            priorities={"high", "critical"},
            custom_filters=[
                CustomFilter(
                    field="data.error_type",
                    operator=FilterOperator.IN,
                    value=["timeout", "resource_exhausted", "system_failure"],
                )
            ],
        )


class WorkflowPatterns:
    """Event patterns for workflow management."""

    @staticmethod
    def create_dependency_completion_pattern(
        dependency_task_ids: List[str],
    ) -> EventPattern:
        """Pattern to match completion of dependency tasks."""
        return EventPattern(
            event_types={"task.completed"},
            custom_filters=[
                CustomFilter(
                    field="data.task_id",
                    operator=FilterOperator.IN,
                    value=dependency_task_ids,
                )
            ],
        )

    @staticmethod
    def create_pipeline_trigger_pattern() -> EventPattern:
        """Pattern to match events that should trigger a pipeline."""
        return EventPattern(
            event_types={"task.completed", "knowledge.learned"},
            tag_patterns=[re.compile(r"pipeline_trigger|workflow_ready")],
        )

    @staticmethod
    def create_rollback_pattern() -> EventPattern:
        """Pattern to match events that require rollback."""
        return EventPattern(
            event_types={"task.failed", "error.occurred"},
            priorities={"high", "critical"},
            tag_patterns=[re.compile(r"rollback_trigger")],
        )


class LearningPatterns:
    """Event patterns for learning and adaptation."""

    @staticmethod
    def create_knowledge_sharing_pattern() -> EventPattern:
        """Pattern to match knowledge sharing events."""
        return EventPattern(
            event_types={"knowledge.learned"},
            custom_filters=[
                CustomFilter(
                    field="data.confidence",
                    operator=FilterOperator.GREATER_THAN,
                    value=0.8,
                )
            ],
        )

    @staticmethod
    def create_pattern_recognition_pattern() -> EventPattern:
        """Pattern to match events for pattern recognition."""
        return EventPattern(
            event_types={"task.completed", "task.failed"}
            # Note: aggregate_window functionality would need to be implemented separately
        )

    @staticmethod
    def create_feedback_pattern() -> EventPattern:
        """Pattern to match feedback events."""
        return EventPattern(
            event_types={"collaboration.message"},
            custom_filters=[
                CustomFilter(
                    field="data.message_type",
                    operator=FilterOperator.EQUALS,
                    value="feedback",
                )
            ],
        )


class MonitoringPatterns:
    """Event patterns for system monitoring and health."""

    @staticmethod
    def create_health_check_pattern() -> EventPattern:
        """Pattern to match health check events."""
        return EventPattern(event_types={"system.health_check", "agent.heartbeat"})

    @staticmethod
    def create_performance_anomaly_pattern() -> EventPattern:
        """Pattern to detect performance anomalies."""
        return EventPattern(
            event_types={"task.completed"},
            custom_filters=[
                CustomFilter(
                    field="data.duration",
                    operator=FilterOperator.GREATER_THAN,
                    value=300,  # Tasks taking more than 5 minutes
                )
            ],
        )

    @staticmethod
    def create_resource_alert_pattern() -> EventPattern:
        """Pattern to match resource alerts."""
        return EventPattern(
            event_types={"error.occurred"},
            custom_filters=[
                CustomFilter(
                    field="data.error_type",
                    operator=FilterOperator.CONTAINS,
                    value="resource",
                )
            ],
        )


@dataclass
class ReactionChain:
    """Defines a chain of event reactions."""

    name: str
    description: str
    initial_pattern: EventPattern
    chain_steps: List[Dict[str, Any]]


class ExampleEventReactionAgent(EventSubscriber):
    """
    Example agent demonstrating various event reaction patterns.

    This agent shows how to implement complex event-driven behaviors
    using the EventSubscriber mixin.
    """

    def __init__(self, agent_id: str, agent_type: str = "event_demo"):
        # Store agent attributes
        self.agent_id = agent_id
        self.agent_type = agent_type
        # Initialize parent class
        super().__init__()

        # State for pattern tracking
        self.task_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.performance_metrics: List[Dict[str, Any]] = []
        self.collaboration_history: List[Dict[str, Any]] = []
        self.learned_patterns: Dict[str, List[Dict]] = defaultdict(list)

        # Mock memory attribute for demonstration
        self.memory: Dict[str, Any] = {}

    async def setup_event_patterns(self):
        """Set up all event reaction patterns."""
        await self.setup_collaboration_patterns()
        await self.setup_workflow_patterns()
        await self.setup_learning_patterns()
        await self.setup_monitoring_patterns()
        await self.setup_chain_reactions()
        await self.setup_aggregated_reactions()

    # ========== Collaboration Patterns ==========

    async def setup_collaboration_patterns(self):
        """Set up collaboration event patterns."""

        # Handle help requests
        help_pattern = CollaborationPatterns.create_help_request_pattern()
        self.subscribe_to_events(
            pattern=help_pattern,
            handler=self.handle_help_request,
            reaction_type=ReactionType.IMMEDIATE,
        )

        # Celebrate task completions
        completion_pattern = (
            CollaborationPatterns.create_task_completion_notification_pattern()
        )
        self.subscribe_to_events(
            pattern=completion_pattern,
            handler=self.handle_task_completion_celebration,
            reaction_type=ReactionType.DEBOUNCED,
            delay_seconds=2.0,  # Brief delay for celebration
        )

        # Escalate critical errors
        error_pattern = CollaborationPatterns.create_error_escalation_pattern()
        self.subscribe_to_events(
            pattern=error_pattern,
            handler=self.handle_error_escalation,
            reaction_type=ReactionType.IMMEDIATE,
        )

    async def handle_help_request(self, event: AgentEvent):
        """Handle help requests from other agents."""
        try:
            requesting_agent = event.agent_id
            help_topic = event.data.get("topic", "general")

            # Check if we have expertise in the requested area
            my_expertise = getattr(self, "capabilities", {}).get("expertise_areas", [])

            if help_topic in my_expertise or "general" in my_expertise:
                # Offer help
                await self.emit_collaboration(
                    message=f"I can help with {help_topic}! Available for assistance.",
                    recipient_id=requesting_agent,
                    message_type="help_offer",
                    requires_response=True,
                )

                # Store collaboration history
                self.collaboration_history.append(
                    {
                        "timestamp": datetime.now(),
                        "type": "help_offered",
                        "to_agent": requesting_agent,
                        "topic": help_topic,
                    }
                )
            else:
                # Suggest alternative
                await self.emit_collaboration(
                    message=f"I don't specialize in {help_topic}, but you might try asking a specialist.",
                    recipient_id=requesting_agent,
                    message_type="suggestion",
                )

        except Exception as e:
            await self.emit_error(
                "collaboration_error", f"Failed to handle help request: {e}"
            )

    async def handle_task_completion_celebration(self, event: AgentEvent):
        """Celebrate task completions from team members."""
        try:
            completing_agent = event.agent_id
            task_type = event.data.get("task_type", "task")

            # Don't celebrate our own completions
            if completing_agent == self.agent_id:
                return

            celebration_messages = [
                f"Great work on completing that {task_type}! 🎉",
                f"Excellent job with the {task_type}! 👏",
                f"Way to go on finishing that {task_type}! ⭐",
            ]

            import random

            message = random.choice(celebration_messages)

            await self.emit_collaboration(
                message=message,
                recipient_id=completing_agent,
                message_type="celebration",
            )

        except Exception:
            # Don't emit error for celebration failures - they're non-critical
            pass

    async def handle_error_escalation(self, event: AgentEvent):
        """Handle critical error escalation."""
        try:
            error_agent = event.agent_id
            error_type = event.data.get("error_type", "unknown")
            error_message = event.data.get("error_message", "No details")

            # Escalate to workflow manager or orchestrator
            await self.emit_collaboration(
                message=f"CRITICAL ERROR ALERT: Agent {error_agent} encountered {error_type}: {error_message}",
                message_type="error_escalation",
                requires_response=True,
            )

            # If we're a workflow manager, take action
            if "workflow" in self.agent_type.lower():
                await self.handle_workflow_error_recovery(event)

        except Exception as e:
            await self.emit_error("escalation_error", f"Failed to escalate error: {e}")

    # ========== Workflow Patterns ==========

    async def setup_workflow_patterns(self):
        """Set up workflow management patterns."""

        # Track dependency completion
        dependency_pattern = EventPattern(
            event_types={"task.completed"}, tag_patterns=[re.compile(r"dependency")]
        )
        self.subscribe_to_events(
            pattern=dependency_pattern,
            handler=self.handle_dependency_completion,
            reaction_type=ReactionType.IMMEDIATE,
        )

        # Pipeline triggers
        pipeline_pattern = WorkflowPatterns.create_pipeline_trigger_pattern()
        self.subscribe_to_events(
            pattern=pipeline_pattern,
            handler=self.handle_pipeline_trigger,
            reaction_type=ReactionType.DEBOUNCED,
            delay_seconds=1.0,  # Brief delay to collect any additional triggers
        )

        # Rollback handling
        rollback_pattern = WorkflowPatterns.create_rollback_pattern()
        self.subscribe_to_events(
            pattern=rollback_pattern,
            handler=self.handle_rollback_request,
            reaction_type=ReactionType.IMMEDIATE,
        )

    async def handle_dependency_completion(self, event: AgentEvent):
        """Handle completion of task dependencies."""
        try:
            completed_task = event.data.get("task_id")
            dependent_tasks = event.data.get("dependent_tasks", [])

            # Update dependency tracking
            for task_id in dependent_tasks:
                if task_id in self.task_dependencies and completed_task is not None:
                    self.task_dependencies[task_id].discard(completed_task)

                    # Check if all dependencies are complete
                    if not self.task_dependencies[task_id]:
                        await self.emit_collaboration(
                            message=f"All dependencies complete for task {task_id}. Ready to proceed!",
                            message_type="dependency_ready",
                            tags=["workflow", "ready"],
                        )

                        # Clean up
                        del self.task_dependencies[task_id]

        except Exception as e:
            await self.emit_error(
                "dependency_error", f"Failed to handle dependency completion: {e}"
            )

    async def handle_pipeline_trigger(self, event: AgentEvent):
        """Handle events that trigger workflow pipelines."""
        try:
            trigger_type = event.event_type
            agent_id = event.agent_id

            # Determine appropriate pipeline
            if trigger_type == "task.completed" and "test" in event.data.get(
                "task_type", ""
            ):
                # Tests completed - trigger deployment pipeline
                await self.emit_collaboration(
                    message="Tests completed successfully. Initiating deployment pipeline.",
                    message_type="pipeline_trigger",
                    tags=["deployment", "pipeline"],
                )
            elif trigger_type == "knowledge.learned":
                # New knowledge - trigger knowledge sharing
                await self.emit_collaboration(
                    message=f"New knowledge learned by {agent_id}. Initiating knowledge sharing.",
                    message_type="pipeline_trigger",
                    tags=["knowledge_sharing", "pipeline"],
                )

        except Exception as e:
            await self.emit_error(
                "pipeline_error", f"Failed to handle pipeline trigger: {e}"
            )

    async def handle_rollback_request(self, event: AgentEvent):
        """Handle rollback requests."""
        try:
            failed_task = event.data.get("task_id")
            error_details = event.data.get("error_message", "Unknown error")

            # Initiate rollback process
            await self.emit_collaboration(
                message=f"Initiating rollback for failed task {failed_task}: {error_details}",
                message_type="rollback_initiated",
                tags=["rollback", "recovery"],
            )

            # If we're a worktree manager, handle the rollback
            if "worktree" in self.agent_type.lower() and failed_task is not None:
                await self.handle_worktree_rollback(failed_task)

        except Exception as e:
            await self.emit_error("rollback_error", f"Failed to handle rollback: {e}")

    # ========== Learning Patterns ==========

    async def setup_learning_patterns(self):
        """Set up learning and adaptation patterns."""

        # Knowledge sharing
        knowledge_pattern = LearningPatterns.create_knowledge_sharing_pattern()
        self.subscribe_to_events(
            pattern=knowledge_pattern,
            handler=self.handle_knowledge_sharing,
            reaction_type=ReactionType.IMMEDIATE,
        )

        # Pattern recognition (aggregated)
        pattern_pattern = LearningPatterns.create_pattern_recognition_pattern()
        self.subscribe_to_events(
            pattern=pattern_pattern,
            handler=self.handle_pattern_recognition,
            reaction_type=ReactionType.AGGREGATED,
            aggregate_window=timedelta(hours=1),
            aggregate_count=3,  # Look for patterns in 3+ events
            aggregate_handler=self.analyze_task_patterns,
        )

        # Feedback processing
        feedback_pattern = LearningPatterns.create_feedback_pattern()
        self.subscribe_to_events(
            pattern=feedback_pattern,
            handler=self.handle_feedback,
            reaction_type=ReactionType.IMMEDIATE,
        )

    async def handle_knowledge_sharing(self, event: AgentEvent):
        """Share high-confidence knowledge with the team."""
        try:
            knowledge_type = event.data.get("knowledge_type", "general")
            content = event.data.get("content", "")
            confidence = event.data.get("confidence", 0.0)
            learning_agent = event.agent_id

            # Share knowledge if confidence is high enough
            if confidence > 0.8:
                await self.emit_collaboration(
                    message=f"📚 Knowledge Update: {learning_agent} learned about {knowledge_type} "
                    f"(confidence: {confidence:.1%}): {content[:100]}...",
                    message_type="knowledge_broadcast",
                    tags=["knowledge", "learning"],
                )

                # Store for our own learning
                self.learned_patterns[knowledge_type].append(
                    {
                        "content": content,
                        "confidence": confidence,
                        "source_agent": learning_agent,
                        "timestamp": datetime.now(),
                    }
                )

        except Exception as e:
            await self.emit_error(
                "knowledge_error", f"Failed to handle knowledge sharing: {e}"
            )

    async def handle_pattern_recognition(self, event: AgentEvent):
        """Handle individual events for pattern recognition."""
        # This is called for individual events, the aggregated handler analyzes patterns
        pass

    async def analyze_task_patterns(self, events: List[AgentEvent]):
        """Analyze patterns in multiple task events."""
        try:
            # Analyze completion times
            completion_times = []
            failure_types = []
            success_factors = []

            for event in events:
                if event.event_type == "task.completed":
                    duration = event.data.get("duration", 0)
                    completion_times.append(duration)

                    success_factors.extend(event.data.get("success_factors", []))
                elif event.event_type == "task.failed":
                    failure_types.append(event.data.get("error_type", "unknown"))

            # Look for patterns
            patterns = []

            if completion_times:
                avg_time = sum(completion_times) / len(completion_times)
                patterns.append(f"Average task completion: {avg_time:.1f}s")

                # Detect time anomalies
                long_tasks = [t for t in completion_times if t > avg_time * 2]
                if long_tasks:
                    patterns.append(f"Detected {len(long_tasks)} unusually long tasks")

            if failure_types:
                common_failures: Dict[str, int] = {}
                for failure in failure_types:
                    common_failures[failure] = common_failures.get(failure, 0) + 1

                most_common = max(common_failures, key=lambda k: common_failures[k])
                patterns.append(
                    f"Most common failure: {most_common} ({common_failures[most_common]} times)"
                )

            # Share insights if patterns found
            if patterns:
                await self.emit_knowledge_learned(
                    knowledge_type="task_patterns",
                    content=f"Pattern analysis: {'; '.join(patterns)}",
                    confidence=0.7,
                )

        except Exception as e:
            await self.emit_error(
                "pattern_error", f"Failed to analyze task patterns: {e}"
            )

    async def handle_feedback(self, event: AgentEvent):
        """Handle feedback from other agents."""
        try:
            feedback = event.data.get("content", "")
            feedback_type = event.data.get("feedback_type", "general")
            from_agent = event.agent_id

            # Store feedback for learning
            feedback_record = {
                "feedback": feedback,
                "type": feedback_type,
                "from_agent": from_agent,
                "timestamp": datetime.now(),
            }

            # Store in memory if available
            if hasattr(self, "memory") and self.memory:
                # In a real implementation, this would call memory.remember_long_term
                # For now, just store in the mock memory dict
                self.memory[f"feedback_{from_agent}"] = {
                    "content": f"Feedback from {from_agent}: {feedback}",
                    "type": feedback_type,
                    "timestamp": datetime.now(),
                }

            # Acknowledge feedback
            await self.emit_collaboration(
                message=f"Thank you for the {feedback_type} feedback! I'll incorporate it into my learning.",
                recipient_id=from_agent,
                message_type="feedback_acknowledgment",
            )

        except Exception as e:
            await self.emit_error("feedback_error", f"Failed to handle feedback: {e}")

    # ========== Monitoring Patterns ==========

    async def setup_monitoring_patterns(self):
        """Set up system monitoring patterns."""

        # Health checks
        health_pattern = MonitoringPatterns.create_health_check_pattern()
        self.subscribe_to_events(
            pattern=health_pattern,
            handler=self.handle_health_check,
            reaction_type=ReactionType.THROTTLED,
            throttle_seconds=30.0,  # Don't spam health responses
        )

        # Performance anomalies
        perf_pattern = MonitoringPatterns.create_performance_anomaly_pattern()
        self.subscribe_to_events(
            pattern=perf_pattern,
            handler=self.handle_performance_anomaly,
            reaction_type=ReactionType.IMMEDIATE,
        )

        # Resource alerts
        resource_pattern = MonitoringPatterns.create_resource_alert_pattern()
        self.subscribe_to_events(
            pattern=resource_pattern,
            handler=self.handle_resource_alert,
            reaction_type=ReactionType.IMMEDIATE,
        )

    async def handle_health_check(self, event: AgentEvent):
        """Respond to health check events."""
        try:
            # Report our health status
            health_info = {
                "agent_id": self.agent_id,
                "status": "healthy",
                "uptime": (
                    datetime.now() - getattr(self, "start_time", datetime.now())
                ).total_seconds(),
                "tasks_completed": getattr(self, "tasks_completed", 0),
                "success_rate": getattr(self, "success_rate", 1.0),
                "subscriptions": len(self._subscriptions),
                "memory_available": hasattr(self, "memory") and self.memory is not None,
            }

            await self.emit_collaboration(
                message=f"Health check response: {json.dumps(health_info)}",
                message_type="health_response",
                tags=["health", "monitoring"],
            )

        except Exception as e:
            await self.emit_error(
                "health_check_error", f"Failed to respond to health check: {e}"
            )

    async def handle_performance_anomaly(self, event: AgentEvent):
        """Handle performance anomaly detection."""
        try:
            duration = event.data.get("duration", 0)
            task_type = event.data.get("task_type", "unknown")
            agent_id = event.agent_id

            # Store performance data
            self.performance_metrics.append(
                {
                    "agent_id": agent_id,
                    "task_type": task_type,
                    "duration": duration,
                    "timestamp": datetime.now(),
                    "anomaly": True,
                }
            )

            # Alert team about performance issue
            await self.emit_collaboration(
                message=f"⚠️ Performance Alert: {agent_id} took {duration}s for {task_type} (unusually long)",
                message_type="performance_alert",
                tags=["performance", "alert"],
            )

        except Exception as e:
            await self.emit_error(
                "performance_error", f"Failed to handle performance anomaly: {e}"
            )

    async def handle_resource_alert(self, event: AgentEvent):
        """Handle resource-related alerts."""
        try:
            error_type = event.data.get("error_type", "unknown")
            error_message = event.data.get("error_message", "")
            agent_id = event.agent_id

            # Escalate resource issues
            await self.emit_collaboration(
                message=f"🚨 Resource Alert: {agent_id} - {error_type}: {error_message}",
                message_type="resource_alert",
                requires_response=True,
                tags=["resource", "critical"],
            )

            # If we're a resource manager, take action
            if "resource" in self.agent_type.lower():
                await self.handle_resource_management(event)

        except Exception as e:
            await self.emit_error(
                "resource_alert_error", f"Failed to handle resource alert: {e}"
            )

    # ========== Chain Reactions ==========

    async def setup_chain_reactions(self):
        """Set up chain reaction patterns."""

        # Test completion triggers deployment
        test_completion_pattern = EventPattern(
            event_types={"task.completed"},
            # Note: tags not supported, using tag_patterns instead
            tag_patterns=[re.compile(r"test"), re.compile(r"success")],
        )
        self.subscribe_to_events(
            pattern=test_completion_pattern,
            handler=self.handle_test_completion,
            reaction_type=ReactionType.CHAINED,
            chain_to=["deployment.ready"],
        )

        # Error triggers investigation
        error_investigation_pattern = EventPattern(
            event_types={"error.occurred"}, priorities={"high", "critical"}
        )
        self.subscribe_to_events(
            pattern=error_investigation_pattern,
            handler=self.handle_error_investigation,
            reaction_type=ReactionType.CHAINED,
            chain_to=["investigation.started"],
        )

    async def handle_test_completion(self, event: AgentEvent):
        """Handle test completion and prepare for deployment."""
        try:
            test_results = event.data.get("test_results", {})
            all_passed = test_results.get("all_passed", False)

            if all_passed:
                await self.emit_collaboration(
                    message="All tests passed! Deployment pipeline is ready to proceed.",
                    message_type="deployment_ready",
                    tags=["deployment", "ready"],
                )
            else:
                failed_tests = test_results.get("failed_count", 0)
                await self.emit_collaboration(
                    message=f"Tests completed with {failed_tests} failures. Deployment blocked.",
                    message_type="deployment_blocked",
                    tags=["deployment", "blocked"],
                )

        except Exception as e:
            await self.emit_error(
                "test_completion_error", f"Failed to handle test completion: {e}"
            )

    async def handle_error_investigation(self, event: AgentEvent):
        """Handle error investigation initiation."""
        try:
            error_type = event.data.get("error_type", "unknown")
            error_agent = event.agent_id

            await self.emit_collaboration(
                message=f"Initiating investigation for {error_type} error from {error_agent}",
                message_type="investigation_started",
                tags=["investigation", "error"],
            )

            # If we're a debugging agent, start analysis
            if (
                "debug" in self.agent_type.lower()
                or "investigator" in self.agent_type.lower()
            ):
                await self.start_error_analysis(event)

        except Exception as e:
            await self.emit_error(
                "investigation_error", f"Failed to handle error investigation: {e}"
            )

    # ========== Aggregated Reactions ==========

    async def setup_aggregated_reactions(self):
        """Set up aggregated reaction patterns."""

        # Multiple failures trigger system check
        failure_pattern = EventPattern(
            event_types={"task.failed", "error.occurred"},
            priorities={"high", "critical"},
        )
        self.subscribe_to_events(
            pattern=failure_pattern,
            handler=self.handle_individual_failure,
            reaction_type=ReactionType.AGGREGATED,
            aggregate_window=timedelta(minutes=10),
            aggregate_count=3,  # 3 failures in 10 minutes
            aggregate_handler=self.handle_system_instability,
        )

        # Multiple knowledge events trigger sharing session
        knowledge_pattern = EventPattern(event_types={"knowledge.learned"})
        self.subscribe_to_events(
            pattern=knowledge_pattern,
            handler=self.handle_individual_knowledge,
            reaction_type=ReactionType.AGGREGATED,
            aggregate_window=timedelta(hours=2),
            aggregate_count=5,  # 5 knowledge events in 2 hours
            aggregate_handler=self.trigger_knowledge_sharing_session,
        )

    async def handle_individual_failure(self, event: AgentEvent):
        """Handle individual failure events (part of aggregation)."""
        # Individual failures are just counted, action taken on aggregation
        pass

    async def handle_system_instability(self, events: List[AgentEvent]):
        """Handle system instability detected through multiple failures."""
        try:
            failure_count = len(events)
            affected_agents = set(event.agent_id for event in events)
            error_types = [event.data.get("error_type", "unknown") for event in events]

            await self.emit_collaboration(
                message=f"🚨 SYSTEM INSTABILITY DETECTED: {failure_count} failures affecting "
                f"{len(affected_agents)} agents. Error types: {', '.join(set(error_types))}",
                message_type="system_alert",
                requires_response=True,
                tags=["system", "instability", "critical"],
            )

            # Initiate system recovery procedures
            await self.emit_collaboration(
                message="Initiating system stability analysis and recovery procedures.",
                message_type="recovery_initiated",
                tags=["recovery", "system"],
            )

        except Exception as e:
            await self.emit_error(
                "instability_error", f"Failed to handle system instability: {e}"
            )

    async def handle_individual_knowledge(self, event: AgentEvent):
        """Handle individual knowledge events (part of aggregation)."""
        # Individual knowledge events are just counted
        pass

    async def trigger_knowledge_sharing_session(self, events: List[AgentEvent]):
        """Trigger knowledge sharing session after multiple learning events."""
        try:
            learning_agents = set(event.agent_id for event in events)
            knowledge_types = [
                event.data.get("knowledge_type", "general") for event in events
            ]

            await self.emit_collaboration(
                message=f"📚 KNOWLEDGE SHARING SESSION: {len(events)} new learnings from "
                f"{len(learning_agents)} agents. Topics: {', '.join(set(knowledge_types))}",
                message_type="knowledge_session",
                tags=["knowledge", "sharing", "session"],
            )

            # Schedule knowledge sharing meeting
            await self.emit_collaboration(
                message="Scheduling team knowledge sharing session to discuss recent learnings.",
                message_type="meeting_scheduled",
                tags=["meeting", "knowledge"],
            )

        except Exception as e:
            await self.emit_error(
                "knowledge_session_error", f"Failed to trigger knowledge sharing: {e}"
            )

    # ========== Helper Methods ==========

    async def emit_collaboration(
        self,
        message: str,
        message_type: str,
        tags: Optional[List[str]] = None,
        recipient_id: Optional[str] = None,
        requires_response: bool = False,
    ) -> bool:
        """Emit a collaboration message (stub method for demonstration)."""
        # In a real implementation, this would emit an event
        print(f"[{self.agent_id}] Collaboration: {message_type} - {message}")
        return True

    async def emit_error(self, error_type: str, error_message: str) -> bool:
        """Emit an error event (stub method for demonstration)."""
        # In a real implementation, this would emit an error event
        print(f"[{self.agent_id}] Error: {error_type} - {error_message}")
        return True

    async def emit_knowledge_learned(
        self, knowledge_type: str, content: str, confidence: float = 0.8
    ) -> bool:
        """Emit a knowledge learned event (stub method for demonstration)."""
        # In a real implementation, this would emit a knowledge event
        print(
            f"[{self.agent_id}] Knowledge: {knowledge_type} - {content} (confidence: {confidence})"
        )
        return True

    def subscribe_to_events(
        self,
        pattern: Optional[EventPattern] = None,
        handler: Optional[Any] = None,
        reaction_type: Optional[ReactionType] = None,
        **kwargs,
    ) -> str:
        """Subscribe to events (stub method for demonstration)."""
        # In a real implementation, this would set up event subscriptions
        # For now, just return a dummy subscription ID
        return f"sub_{id(pattern)}"

    async def handle_workflow_error_recovery(self, event: AgentEvent):
        """Handle workflow error recovery (placeholder for workflow manager logic)."""
        # This would contain workflow-specific recovery logic
        pass

    async def handle_worktree_rollback(self, failed_task: str):
        """Handle worktree rollback (placeholder for worktree manager logic)."""
        # This would contain worktree-specific rollback logic
        pass

    async def handle_resource_management(self, event: AgentEvent):
        """Handle resource management (placeholder for resource manager logic)."""
        # This would contain resource management logic
        pass

    async def start_error_analysis(self, event: AgentEvent):
        """Start error analysis (placeholder for debugging agent logic)."""
        # This would contain error analysis logic
        pass


# ========== Factory Functions for Common Patterns ==========


def create_collaboration_agent(agent_id: str) -> ExampleEventReactionAgent:
    """Create an agent focused on collaboration patterns."""
    agent = ExampleEventReactionAgent(agent_id, "collaboration_manager")
    return agent


def create_workflow_manager(agent_id: str) -> ExampleEventReactionAgent:
    """Create an agent focused on workflow management patterns."""
    agent = ExampleEventReactionAgent(agent_id, "workflow_manager")
    return agent


def create_learning_agent(agent_id: str) -> ExampleEventReactionAgent:
    """Create an agent focused on learning and knowledge sharing."""
    agent = ExampleEventReactionAgent(agent_id, "learning_agent")
    return agent


def create_monitoring_agent(agent_id: str) -> ExampleEventReactionAgent:
    """Create an agent focused on system monitoring."""
    agent = ExampleEventReactionAgent(agent_id, "monitoring_agent")
    return agent


# ========== Quick Pattern Builders ==========


class PatternBuilder:
    """Builder class for creating common event patterns quickly."""

    @staticmethod
    def task_events(task_types: Optional[List[str]] = None) -> EventPattern:
        """Build pattern for task events."""
        custom_filters = []
        if task_types:
            custom_filters.append(
                CustomFilter(
                    field="data.task_type", operator=FilterOperator.IN, value=task_types
                )
            )

        return EventPattern(
            event_types={"task.started", "task.completed", "task.failed"},
            custom_filters=custom_filters,
        )

    @staticmethod
    def agent_communication(agent_ids: List[str]) -> EventPattern:
        """Build pattern for communication with specific agents."""
        return EventPattern(
            event_types={"collaboration.message"},
            agent_sources=set(agent_ids),  # Using agent_sources instead of agent_ids
        )

    @staticmethod
    def high_priority_alerts() -> EventPattern:
        """Build pattern for high priority alerts."""
        return EventPattern(
            priorities={"high", "critical"},
            # Note: tags_any not supported, using tag_patterns instead
            tag_patterns=[
                re.compile(r"alert"),
                re.compile(r"error"),
                re.compile(r"failure"),
            ],
        )

    @staticmethod
    def learning_opportunities(confidence_threshold: float = 0.7) -> EventPattern:
        """Build pattern for learning opportunities."""
        return EventPattern(
            event_types={"knowledge.learned", "task.completed"},
            custom_filters=[
                CustomFilter(
                    field="data.confidence",
                    operator=FilterOperator.GREATER_THAN,
                    value=confidence_threshold,
                )
            ],
        )
