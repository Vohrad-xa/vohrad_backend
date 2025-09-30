"""Cache interface defining the contract for all cache implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class CacheInterface(ABC):
    """Abstract base class defining cache operations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache. Returns True if key existed."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all entries from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics and metrics."""
        pass
