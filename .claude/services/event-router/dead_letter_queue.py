"""Dead Letter Queue implementation for failed event deliveries."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import Event, Subscription


@dataclass
class DeadLetterEntry:
    """Entry in the dead letter queue."""
    
    event: Event
    subscription: Optional[Subscription] = None
    error_message: str = ""
    error_type: str = ""
    failed_at: datetime = field(default_factory=datetime.now)
    retry_after: Optional[datetime] = None
    permanent_failure: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "event": self.event.to_dict(),
            "subscription_id": self.subscription.id if self.subscription else None,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "failed_at": self.failed_at.isoformat(),
            "retry_after": self.retry_after.isoformat() if self.retry_after else None,
            "permanent_failure": self.permanent_failure,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DeadLetterEntry:
        """Create from dictionary."""
        return cls(
            event=Event.from_dict(data["event"]),
            subscription=None,  # Will need to be resolved separately
            error_message=data.get("error_message", ""),
            error_type=data.get("error_type", ""),
            failed_at=datetime.fromisoformat(data.get("failed_at", datetime.now().isoformat())),
            retry_after=datetime.fromisoformat(data["retry_after"]) if data.get("retry_after") else None,
            permanent_failure=data.get("permanent_failure", False),
        )


class DeadLetterQueue:
    """Dead Letter Queue for handling failed event deliveries."""
    
    def __init__(
        self,
        max_size: int = 10000,
        retention_days: int = 30,
        persistence_path: Optional[Path] = None,
        auto_retry: bool = True,
        retry_interval: int = 300,  # 5 minutes
    ):
        """Initialize the Dead Letter Queue.
        
        Args:
            max_size: Maximum number of entries to keep in memory
            retention_days: Days to retain dead letter entries
            persistence_path: Path for persistent storage
            auto_retry: Whether to automatically retry failed events
            retry_interval: Seconds between retry attempts
        """
        self.max_size = max_size
        self.retention_days = retention_days
        self.persistence_path = persistence_path
        self.auto_retry = auto_retry
        self.retry_interval = retry_interval
        
        self.logger = logging.getLogger(__name__)
        
        # In-memory storage
        self.entries: List[DeadLetterEntry] = []
        self._lock = asyncio.Lock()
        
        # Retry management
        self.retry_task: Optional[asyncio.Task] = None
        self.retry_callbacks: Dict[str, Any] = {}
        
        # Statistics
        self.total_entries = 0
        self.retry_successes = 0
        self.retry_failures = 0
        
        # Load persisted entries if path provided
        if self.persistence_path:
            self._load_persisted_entries()
    
    async def add(
        self,
        event: Event,
        error: Exception,
        subscription: Optional[Subscription] = None,
        permanent_failure: bool = False,
    ) -> None:
        """Add a failed event to the dead letter queue.
        
        Args:
            event: The failed event
            error: The exception that caused the failure
            subscription: The subscription that failed (if applicable)
            permanent_failure: Whether this is a permanent failure (no retry)
        """
        async with self._lock:
            # Calculate retry time with exponential backoff
            retry_after = None
            if not permanent_failure and event.should_retry():
                backoff_seconds = min(
                    self.retry_interval * (2 ** event.retry_count),
                    3600  # Max 1 hour backoff
                )
                retry_after = datetime.now() + timedelta(seconds=backoff_seconds)
            
            # Create dead letter entry
            entry = DeadLetterEntry(
                event=event,
                subscription=subscription,
                error_message=str(error),
                error_type=type(error).__name__,
                failed_at=datetime.now(),
                retry_after=retry_after,
                permanent_failure=permanent_failure,
            )
            
            # Add to queue
            self.entries.append(entry)
            self.total_entries += 1
            
            # Enforce max size
            if len(self.entries) > self.max_size:
                self.entries = self.entries[-self.max_size:]
            
            # Persist if configured
            if self.persistence_path:
                await self._persist_entry(entry)
            
            self.logger.warning(
                f"Added event {event.id} to dead letter queue: {error_message}",
                extra={"event_id": event.id, "error_type": type(error).__name__}
            )
    
    async def get_retriable_events(self, limit: int = 100) -> List[DeadLetterEntry]:
        """Get events that are ready for retry.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of dead letter entries ready for retry
        """
        async with self._lock:
            now = datetime.now()
            retriable = []
            
            for entry in self.entries:
                if len(retriable) >= limit:
                    break
                    
                if (
                    not entry.permanent_failure
                    and entry.retry_after
                    and entry.retry_after <= now
                    and entry.event.should_retry()
                ):
                    retriable.append(entry)
            
            return retriable
    
    async def remove(self, entry: DeadLetterEntry) -> None:
        """Remove an entry from the dead letter queue.
        
        Args:
            entry: The entry to remove
        """
        async with self._lock:
            if entry in self.entries:
                self.entries.remove(entry)
                
                # Remove from persistence if configured
                if self.persistence_path:
                    await self._remove_persisted_entry(entry)
    
    async def mark_retry_success(self, entry: DeadLetterEntry) -> None:
        """Mark an entry as successfully retried.
        
        Args:
            entry: The entry that was successfully retried
        """
        await self.remove(entry)
        self.retry_successes += 1
        self.logger.info(
            f"Event {entry.event.id} successfully retried and removed from DLQ",
            extra={"event_id": entry.event.id}
        )
    
    async def mark_retry_failure(self, entry: DeadLetterEntry, error: Exception) -> None:
        """Mark an entry as failed retry.
        
        Args:
            entry: The entry that failed retry
            error: The new error from retry attempt
        """
        entry.event.increment_retry()
        entry.error_message = str(error)
        entry.error_type = type(error).__name__
        entry.failed_at = datetime.now()
        
        # Check if we've exhausted retries
        if not entry.event.should_retry():
            entry.permanent_failure = True
            entry.retry_after = None
            self.logger.error(
                f"Event {entry.event.id} exhausted all retries, marked as permanent failure",
                extra={"event_id": entry.event.id}
            )
        else:
            # Calculate next retry time with exponential backoff
            backoff_seconds = min(
                self.retry_interval * (2 ** entry.event.retry_count),
                3600  # Max 1 hour backoff
            )
            entry.retry_after = datetime.now() + timedelta(seconds=backoff_seconds)
        
        self.retry_failures += 1
        
        # Persist updated entry if configured
        if self.persistence_path:
            await self._persist_entry(entry)
    
    async def cleanup_old_entries(self) -> int:
        """Remove entries older than retention period.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            original_count = len(self.entries)
            
            self.entries = [
                entry for entry in self.entries
                if entry.failed_at > cutoff_date
            ]
            
            removed_count = original_count - len(self.entries)
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old dead letter entries")
                
                # Update persistence if configured
                if self.persistence_path:
                    await self._persist_all_entries()
            
            return removed_count
    
    async def start_retry_loop(self, retry_callback) -> None:
        """Start automatic retry loop.
        
        Args:
            retry_callback: Async function to call for retry attempts
        """
        if not self.auto_retry:
            return
        
        if self.retry_task and not self.retry_task.done():
            self.logger.warning("Retry loop already running")
            return
        
        self.retry_task = asyncio.create_task(self._retry_loop(retry_callback))
        self.logger.info("Started dead letter queue retry loop")
    
    async def stop_retry_loop(self) -> None:
        """Stop the automatic retry loop."""
        if self.retry_task:
            self.retry_task.cancel()
            try:
                await self.retry_task
            except asyncio.CancelledError:
                pass
            self.retry_task = None
            self.logger.info("Stopped dead letter queue retry loop")
    
    async def _retry_loop(self, retry_callback) -> None:
        """Internal retry loop."""
        while True:
            try:
                # Wait for retry interval
                await asyncio.sleep(self.retry_interval)
                
                # Get retriable events
                retriable = await self.get_retriable_events()
                
                if retriable:
                    self.logger.info(f"Retrying {len(retriable)} events from dead letter queue")
                    
                    for entry in retriable:
                        try:
                            # Attempt retry
                            await retry_callback(entry.event, entry.subscription)
                            await self.mark_retry_success(entry)
                        except Exception as e:
                            await self.mark_retry_failure(entry, e)
                
                # Periodic cleanup
                await self.cleanup_old_entries()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.exception(f"Error in dead letter retry loop: {e}")
    
    def _load_persisted_entries(self) -> None:
        """Load persisted entries from disk."""
        if not self.persistence_path or not self.persistence_path.exists():
            return
        
        try:
            dlq_file = self.persistence_path / "dead_letter_queue.json"
            if dlq_file.exists():
                with open(dlq_file, "r") as f:
                    data = json.load(f)
                    self.entries = [
                        DeadLetterEntry.from_dict(entry_data)
                        for entry_data in data.get("entries", [])
                    ]
                    self.total_entries = data.get("total_entries", 0)
                    self.retry_successes = data.get("retry_successes", 0)
                    self.retry_failures = data.get("retry_failures", 0)
                    
                self.logger.info(f"Loaded {len(self.entries)} entries from dead letter queue")
        except Exception as e:
            self.logger.exception(f"Error loading persisted dead letter entries: {e}")
    
    async def _persist_entry(self, entry: DeadLetterEntry) -> None:
        """Persist a single entry to disk."""
        if not self.persistence_path:
            return
        
        try:
            await self._persist_all_entries()
        except Exception as e:
            self.logger.exception(f"Error persisting dead letter entry: {e}")
    
    async def _persist_all_entries(self) -> None:
        """Persist all entries to disk."""
        if not self.persistence_path:
            return
        
        try:
            self.persistence_path.mkdir(parents=True, exist_ok=True)
            dlq_file = self.persistence_path / "dead_letter_queue.json"
            
            data = {
                "entries": [entry.to_dict() for entry in self.entries],
                "total_entries": self.total_entries,
                "retry_successes": self.retry_successes,
                "retry_failures": self.retry_failures,
                "last_updated": datetime.now().isoformat(),
            }
            
            with open(dlq_file, "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.exception(f"Error persisting dead letter queue: {e}")
    
    async def _remove_persisted_entry(self, entry: DeadLetterEntry) -> None:
        """Remove a persisted entry from disk."""
        # For simplicity, we just rewrite the entire file
        await self._persist_all_entries()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dead letter queue statistics."""
        permanent_failures = sum(1 for e in self.entries if e.permanent_failure)
        retriable = sum(1 for e in self.entries if not e.permanent_failure and e.event.should_retry())
        
        return {
            "current_size": len(self.entries),
            "total_entries": self.total_entries,
            "permanent_failures": permanent_failures,
            "retriable_events": retriable,
            "retry_successes": self.retry_successes,
            "retry_failures": self.retry_failures,
            "success_rate": (
                self.retry_successes / (self.retry_successes + self.retry_failures)
                if (self.retry_successes + self.retry_failures) > 0
                else 0
            ),
        }