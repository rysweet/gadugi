"""
TeamCoach Phase 2: Real-time Task Assignment

This module provides real-time task assignment optimization and monitoring.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import threading
from queue import Queue

from ...shared.utils.error_handling import ErrorHandler  # type: ignore
from .task_matcher import TaskAgentMatcher, TaskRequirements, MatchingStrategy


@dataclass
class AssignmentRequest:
    """Real-time assignment request"""

    request_id: str
    task_requirements: TaskRequirements
    available_agents: List[str]
    strategy: MatchingStrategy = MatchingStrategy.BEST_FIT
    priority: int = 1
    submitted_at: datetime = datetime.now()


class RealtimeAssignment:
    """
    Real-time task assignment system.

    Provides immediate task assignment optimization with continuous
    monitoring and dynamic rebalancing capabilities.
    """

    def __init__(
        self,
        task_matcher: Optional[TaskAgentMatcher] = None,
        error_handler: Optional[ErrorHandler] = None,
    ):
        """Initialize the real-time assignment system."""
        self.logger = logging.getLogger(__name__)
        self.task_matcher = task_matcher or TaskAgentMatcher()
        self.error_handler = error_handler or ErrorHandler()

        # Assignment queue and processing
        self.assignment_queue = Queue()
        self.active_assignments: Dict[str, Any] = {}
        self.processing_thread = None
        self.stop_processing = threading.Event()

        # Performance tracking
        self.assignment_stats = {
            "total_requests": 0,
            "successful_assignments": 0,
            "average_response_time": 0.0,
            "queue_size": 0,
        }

        self.logger.info("RealtimeAssignment initialized")

    def start_processing(self):
        """Start the real-time assignment processing."""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.stop_processing.clear()
            self.processing_thread = threading.Thread(
                target=self._process_assignment_queue,
                name="RealtimeAssignmentProcessor",
                daemon=True,
            )
            self.processing_thread.start()
            self.logger.info("Started real-time assignment processing")

    def stop_processing(self):
        """Stop the real-time assignment processing."""
        self.stop_processing.set()
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        self.logger.info("Stopped real-time assignment processing")

    def request_assignment(
        self,
        task_requirements: TaskRequirements,
        available_agents: List[str],
        strategy: MatchingStrategy = MatchingStrategy.BEST_FIT,
        priority: int = 1,
    ) -> str:
        """
        Request real-time task assignment.

        Args:
            task_requirements: Task requirements
            available_agents: Available agents
            strategy: Assignment strategy
            priority: Request priority (higher = more urgent)

        Returns:
            str: Request ID for tracking
        """
        try:
            request_id = (
                f"rt_assign_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{priority}"
            )

            request = AssignmentRequest(
                request_id=request_id,
                task_requirements=task_requirements,
                available_agents=available_agents,
                strategy=strategy,
                priority=priority,
            )

            self.assignment_queue.put(request)
            self.assignment_stats["total_requests"] += 1
            self.assignment_stats["queue_size"] = self.assignment_queue.qsize()

            self.logger.info(f"Queued assignment request {request_id}")
            return request_id

        except Exception as e:
            self.logger.error(f"Failed to queue assignment request: {e}")
            raise

    def _process_assignment_queue(self):
        """Process assignment requests from the queue."""
        try:
            while not self.stop_processing.is_set():
                try:
                    # Get request with timeout
                    if not self.assignment_queue.empty():
                        request = self.assignment_queue.get(timeout=1.0)
                        self._process_assignment_request(request)
                        self.assignment_queue.task_done()
                    else:
                        # No requests, sleep briefly
                        self.stop_processing.wait(0.1)

                except Exception as e:
                    self.logger.error(f"Error processing assignment request: {e}")

        except Exception as e:
            self.logger.error(f"Assignment queue processing failed: {e}")

    def _process_assignment_request(self, request: AssignmentRequest):
        """Process a single assignment request."""
        try:
            start_time = datetime.now()

            # Perform task matching
            recommendation = self.task_matcher.find_optimal_agent(
                request.task_requirements, request.available_agents, request.strategy
            )

            # Store active assignment
            self.active_assignments[request.request_id] = {
                "request": request,
                "recommendation": recommendation,
                "processed_at": datetime.now(),
                "status": "completed",
            }

            # Update statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.assignment_stats["successful_assignments"] += 1

            # Update average response time
            current_avg = self.assignment_stats["average_response_time"]
            total_successful = self.assignment_stats["successful_assignments"]
            new_avg = (
                (current_avg * (total_successful - 1)) + processing_time
            ) / total_successful
            self.assignment_stats["average_response_time"] = new_avg

            self.logger.info(
                f"Processed assignment request {request.request_id} in {processing_time:.3f}s"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to process assignment request {request.request_id}: {e}"
            )
            self.active_assignments[request.request_id] = {
                "request": request,
                "error": str(e),
                "processed_at": datetime.now(),
                "status": "failed",
            }

    def get_assignment_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of an assignment request."""
        return self.active_assignments.get(request_id)

    def get_assignment_stats(self) -> Dict[str, Any]:
        """Get real-time assignment statistics."""
        stats = self.assignment_stats.copy()
        stats["queue_size"] = self.assignment_queue.qsize()
        stats["active_assignments"] = len(self.active_assignments)
        return stats
