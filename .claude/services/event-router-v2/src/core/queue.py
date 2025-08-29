#!/usr/bin/env python3
"""Priority-based event queue implementation."""

import asyncio
import heapq
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging

from .models import Event, EventPriority

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PrioritizedEvent:
    """Event wrapper for priority queue."""
    priority: int = field(compare=True)
    timestamp: float = field(compare=True)
    event: Event = field(compare=False)

    @classmethod
    def from_event(cls, event: Event) -> 'PrioritizedEvent':
        """Create from event with inverted priority for max-heap behavior."""
        # Invert priority so higher priority events come first
        priority = -int(event.priority)
        timestamp = time.time()
        return cls(priority=priority, timestamp=timestamp, event=event)


class EventQueue:
    """Thread-safe priority-based event queue."""

    def __init__(self, max_size: int = 10000):
        """Initialize event queue.

        Args:
            max_size: Maximum queue size
        """
        self.max_size = max_size
        self._queue: List[PrioritizedEvent] = []
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition()
        self._size = 0

        # Statistics
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.total_dropped = 0

        # Priority statistics
        self.priority_counts: Dict[EventPriority, int] = defaultdict(int)

    async def put(self, event: Event, wait: bool = True) -> bool:
        """Add event to queue.

        Args:
            event: Event to add
            wait: Whether to wait if queue is full

        Returns:
            True if event was added, False otherwise
        """
        async with self._lock:
            # Check if queue is full
            if self._size >= self.max_size:
                if not wait:
                    self.total_dropped += 1
                    logger.warning(f"Queue full, dropping event {event.id}")
                    return False

                # Drop lowest priority event to make room
                if self._queue:
                    # Find the lowest priority event (highest priority value due to inversion)
                    lowest_idx = max(range(len(self._queue)),
                                   key=lambda i: (self._queue[i].priority, self._queue[i].timestamp))

                    # Only drop if new event has higher priority
                    if -event.priority < self._queue[lowest_idx].priority:
                        dropped = self._queue.pop(lowest_idx)
                        heapq.heapify(self._queue)
                        self._size -= 1
                        self.total_dropped += 1
                        logger.warning(f"Dropped lower priority event {dropped.event.id} for {event.id}")
                    else:
                        self.total_dropped += 1
                        logger.warning(f"Event {event.id} priority too low, dropped")
                        return False

            # Add event to queue
            prioritized = PrioritizedEvent.from_event(event)
            heapq.heappush(self._queue, prioritized)
            self._size += 1
            self.total_enqueued += 1
            self.priority_counts[event.priority] += 1

            # Notify waiters
            async with self._not_empty:
                self._not_empty.notify()

            return True

    async def get(self, timeout: Optional[float] = None) -> Optional[Event]:
        """Get next event from queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            Next event or None if timeout
        """
        async with self._not_empty:
            # Wait for event if queue is empty
            if not self._queue:
                try:
                    await asyncio.wait_for(
                        self._not_empty.wait(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    return None

            async with self._lock:
                if self._queue:
                    prioritized = heapq.heappop(self._queue)
                    self._size -= 1
                    self.total_dequeued += 1
                    return prioritized.event

                return None

    async def peek(self) -> Optional[Event]:
        """Peek at next event without removing it."""
        async with self._lock:
            if self._queue:
                return self._queue[0].event
            return None

    async def get_batch(self, max_items: int = 10, timeout: Optional[float] = None) -> List[Event]:
        """Get batch of events.

        Args:
            max_items: Maximum items to return
            timeout: Timeout for first item

        Returns:
            List of events
        """
        events = []

        # Wait for first event with timeout
        first_event = await self.get(timeout=timeout)
        if first_event:
            events.append(first_event)

            # Get remaining events without waiting
            for _ in range(max_items - 1):
                event = await self.get(timeout=0)
                if event:
                    events.append(event)
                else:
                    break

        return events

    async def size(self) -> int:
        """Get current queue size."""
        async with self._lock:
            return self._size

    async def is_empty(self) -> bool:
        """Check if queue is empty."""
        async with self._lock:
            return self._size == 0

    async def is_full(self) -> bool:
        """Check if queue is full."""
        async with self._lock:
            return self._size >= self.max_size

    async def clear(self) -> List[Event]:
        """Clear queue and return all events."""
        async with self._lock:
            events = [p.event for p in self._queue]
            self._queue.clear()
            self._size = 0
            self.priority_counts.clear()
            return events

    async def get_stats(self) -> Dict:
        """Get queue statistics."""
        async with self._lock:
            return {
                "size": self._size,
                "max_size": self.max_size,
                "total_enqueued": self.total_enqueued,
                "total_dequeued": self.total_dequeued,
                "total_dropped": self.total_dropped,
                "priority_distribution": dict(self.priority_counts),
                "utilization": self._size / self.max_size if self.max_size > 0 else 0
            }

    async def get_events_by_priority(self, priority: EventPriority, limit: int = 10) -> List[Event]:
        """Get events with specific priority.

        Args:
            priority: Priority to filter by
            limit: Maximum events to return

        Returns:
            List of events with specified priority
        """
        async with self._lock:
            events = []
            for p_event in self._queue:
                if p_event.event.priority == priority:
                    events.append(p_event.event)
                    if len(events) >= limit:
                        break
            return events

    async def remove_event(self, event_id: str) -> bool:
        """Remove specific event from queue.

        Args:
            event_id: Event ID to remove

        Returns:
            True if event was removed
        """
        async with self._lock:
            for i, p_event in enumerate(self._queue):
                if p_event.event.id == event_id:
                    self._queue.pop(i)
                    heapq.heapify(self._queue)
                    self._size -= 1
                    return True
            return False


class MultiQueue:
    """Multiple queues for different event categories."""

    def __init__(self, queue_configs: Optional[Dict[str, int]] = None):
        """Initialize multi-queue system.

        Args:
            queue_configs: Dict of queue_name -> max_size
        """
        self.queues: Dict[str, EventQueue] = {}

        # Default queue configuration
        default_configs = {
            "system": 1000,   # System events
            "high": 5000,     # High priority events
            "normal": 10000,  # Normal priority events
            "low": 5000,      # Low priority events
        }

        configs = queue_configs or default_configs
        for name, size in configs.items():
            self.queues[name] = EventQueue(max_size=size)

    def get_queue_for_event(self, event: Event) -> str:
        """Determine which queue an event belongs to.

        Args:
            event: Event to categorize

        Returns:
            Queue name
        """
        if event.priority == EventPriority.SYSTEM:
            return "system"
        elif event.priority >= EventPriority.HIGH:
            return "high"
        elif event.priority >= EventPriority.NORMAL:
            return "normal"
        else:
            return "low"

    async def put(self, event: Event) -> bool:
        """Add event to appropriate queue.

        Args:
            event: Event to add

        Returns:
            True if added successfully
        """
        queue_name = self.get_queue_for_event(event)
        queue = self.queues.get(queue_name)
        if queue:
            return await queue.put(event)
        return False

    async def get_next(self, timeout: Optional[float] = None) -> Optional[Event]:
        """Get next event from highest priority queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            Next event or None
        """
        # Check queues in priority order
        priority_order = ["system", "high", "normal", "low"]

        for queue_name in priority_order:
            queue = self.queues.get(queue_name)
            if queue:
                event = await queue.get(timeout=0)  # Non-blocking check
                if event:
                    return event

        # If no events found, wait on highest priority queue
        if timeout and timeout > 0:
            for queue_name in priority_order:
                queue = self.queues.get(queue_name)
                if queue:
                    event = await queue.get(timeout=timeout)
                    if event:
                        return event

        return None

    async def get_stats(self) -> Dict[str, Dict]:
        """Get statistics for all queues."""
        stats = {}
        for name, queue in self.queues.items():
            stats[name] = await queue.get_stats()
        return stats
