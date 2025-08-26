"""LRU Cache implementation with TTL support."""

import asyncio
import time
from .interface import CacheInterface
from collections import OrderedDict
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

class LRUCache(CacheInterface):
    """In-memory LRU cache with TTL support and size limits."""

    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 3600):
        """Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
            default_ttl_seconds: Default TTL for entries
        """
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = asyncio.Lock()
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with TTL validation."""
        async with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, timestamp = self._cache[key]
            current_time = time.time()

            # Check if expired
            if current_time - timestamp > self.default_ttl:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache with LRU eviction."""
        async with self._lock:
            current_time = time.time()

            # Store value with timestamp
            self._cache[key] = (value, current_time)
            self._cache.move_to_end(key)

            # Evict oldest entries if over size limit
            while len(self._cache) > self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return await self.get(key) is not None

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "type": "LRU",
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "ttl_seconds": self.default_ttl,
            }
