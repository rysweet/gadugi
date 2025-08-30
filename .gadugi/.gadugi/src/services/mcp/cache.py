"""LRU Cache implementation for MCP Service."""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, Optional, Tuple


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    size: int
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None  # Time-to-live in seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl is None:
            return False
        return (time.time() - self.created_at) > self.ttl

    def update_access(self) -> None:
        """Update access metadata."""
        self.last_accessed = time.time()
        self.access_count += 1


class LRUCache:
    """Thread-safe LRU cache with size and TTL support."""

    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: int = 100,
        default_ttl: Optional[float] = 3600,  # 1 hour default
    ):
        """Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
            default_ttl: Default time-to-live for entries in seconds
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._total_memory = 0

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.expirations = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired():
                self._remove_entry(key)
                self.expirations += 1
                self.misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.update_access()

            self.hits += 1
            return entry.value

    def put(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        size: Optional[int] = None,
    ) -> None:
        """Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (overrides default)
            size: Size of value in bytes (estimated if not provided)
        """
        with self._lock:
            # Estimate size if not provided
            if size is None:
                size = self._estimate_size(value)

            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)

            # Check if we need to evict entries
            self._evict_if_needed(size)

            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                size=size,
                created_at=time.time(),
                last_accessed=time.time(),
                ttl=ttl if ttl is not None else self.default_ttl,
            )

            # Add to cache
            self._cache[key] = entry
            self._total_memory += size

    def remove(self, key: str) -> bool:
        """Remove entry from cache.

        Args:
            key: Cache key

        Returns:
            True if entry was removed, False if not found
        """
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            self._total_memory = 0
            self.evictions = 0
            self.expirations = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "memory_bytes": self._total_memory,
                "max_memory_bytes": self.max_memory_bytes,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "evictions": self.evictions,
                "expirations": self.expirations,
            }

    def get_entries(self, limit: int = 10) -> list[Tuple[str, Any]]:
        """Get most recently used entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of (key, value) tuples
        """
        with self._lock:
            entries = []
            for key, entry in reversed(self._cache.items()):
                if len(entries) >= limit:
                    break
                if not entry.is_expired():
                    entries.append((key, entry.value))
            return entries

    def _remove_entry(self, key: str) -> None:
        """Remove entry from cache (internal, not thread-safe)."""
        if key in self._cache:
            entry = self._cache[key]
            self._total_memory -= entry.size
            del self._cache[key]

    def _evict_if_needed(self, new_size: int) -> None:
        """Evict entries if cache is full (internal, not thread-safe)."""
        # Evict based on size limit
        while len(self._cache) >= self.max_size:
            # Remove least recently used (first item)
            key = next(iter(self._cache))
            self._remove_entry(key)
            self.evictions += 1

        # Evict based on memory limit
        while self._total_memory + new_size > self.max_memory_bytes:
            if not self._cache:
                break
            # Remove least recently used (first item)
            key = next(iter(self._cache))
            self._remove_entry(key)
            self.evictions += 1

        # Clean up expired entries
        expired_keys = []
        for key, entry in self._cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            self._remove_entry(key)
            self.expirations += 1

    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes."""
        # Simple estimation based on type
        if isinstance(value, str):
            return len(value.encode("utf-8"))
        elif isinstance(value, bytes):
            return len(value)
        elif isinstance(value, (int, float)):
            return 8
        elif isinstance(value, bool):
            return 1
        elif isinstance(value, dict):
            # Rough estimation for dictionaries
            size = 0
            for k, v in value.items():
                size += self._estimate_size(k) + self._estimate_size(v)
            return size
        elif isinstance(value, (list, tuple)):
            # Rough estimation for sequences
            return sum(self._estimate_size(item) for item in value)
        else:
            # Default estimation for complex objects
            return 1024  # 1KB default


class MultiLevelCache:
    """Multi-level cache with L1 (in-memory) and L2 (distributed) layers."""

    def __init__(
        self,
        l1_max_size: int = 100,
        l1_max_memory_mb: int = 10,
        l2_client: Optional[Any] = None,  # Redis or similar client
    ):
        """Initialize multi-level cache.

        Args:
            l1_max_size: Maximum L1 cache entries
            l1_max_memory_mb: Maximum L1 memory in MB
            l2_client: Optional L2 cache client (e.g., Redis)
        """
        self.l1_cache = LRUCache(
            max_size=l1_max_size,
            max_memory_mb=l1_max_memory_mb,
            default_ttl=300,  # 5 minutes for L1
        )
        self.l2_client = l2_client

        # Statistics
        self.l1_hits = 0
        self.l2_hits = 0
        self.total_misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (checks L1, then L2).

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        # Check L1 cache
        value = self.l1_cache.get(key)
        if value is not None:
            self.l1_hits += 1
            return value

        # Check L2 cache if available
        if self.l2_client:
            try:
                value = await self._get_from_l2(key)
                if value is not None:
                    self.l2_hits += 1
                    # Promote to L1
                    self.l1_cache.put(key, value)
                    return value
            except Exception:
                pass  # Fall through to miss

        self.total_misses += 1
        return None

    async def put(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """Put value in cache (writes to both L1 and L2).

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        # Write to L1
        self.l1_cache.put(key, value, ttl=ttl)

        # Write to L2 if available
        if self.l2_client:
            try:
                await self._put_to_l2(key, value, ttl)
            except Exception:
                pass  # L2 write failures don't fail the operation

    async def remove(self, key: str) -> bool:
        """Remove entry from all cache levels.

        Args:
            key: Cache key

        Returns:
            True if entry was removed from any level
        """
        removed_l1 = self.l1_cache.remove(key)
        removed_l2 = False

        if self.l2_client:
            try:
                removed_l2 = await self._remove_from_l2(key)
            except Exception:
                pass

        return removed_l1 or removed_l2

    async def _get_from_l2(self, key: str) -> Optional[Any]:
        """Get value from L2 cache (implementation depends on client)."""
        # This would be implemented based on the specific L2 client
        # For example, with Redis:
        # return await self.l2_client.get(key)
        return None

    async def _put_to_l2(self, key: str, value: Any, ttl: Optional[float]) -> None:
        """Put value in L2 cache (implementation depends on client)."""
        # This would be implemented based on the specific L2 client
        # For example, with Redis:
        # await self.l2_client.set(key, value, ex=ttl)
        pass

    async def _remove_from_l2(self, key: str) -> bool:
        """Remove value from L2 cache (implementation depends on client)."""
        # This would be implemented based on the specific L2 client
        # For example, with Redis:
        # return await self.l2_client.delete(key) > 0
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        l1_stats = self.l1_cache.get_stats()
        total_hits = self.l1_hits + self.l2_hits
        total_requests = total_hits + self.total_misses

        return {
            "l1_stats": l1_stats,
            "l1_hits": self.l1_hits,
            "l2_hits": self.l2_hits,
            "total_misses": self.total_misses,
            "total_hit_rate": total_hits / total_requests if total_requests > 0 else 0,
            "l2_enabled": self.l2_client is not None,
        }
