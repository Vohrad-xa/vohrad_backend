"""User-specific cache implementation for authentication performance."""

from .lru_cache import LRUCache
from constants.defaults import CacheDefaults
from typing import Any, Optional
from uuid import UUID


class UserCache:
    """High-level user cache for authentication and frequent lookups."""

    def __init__(
        self,
        max_users: int = CacheDefaults.USER_CACHE_MAX_SIZE,
        ttl_seconds: int = CacheDefaults.USER_CACHE_TTL_SECONDS,
    ):
        """Initialize user cache.

        Args:
            max_users: Maximum number of users to cache (10k users)
            ttl_seconds: How long to cache user data (15 minutes)
        """
        self._cache = LRUCache(max_size=max_users, default_ttl_seconds=ttl_seconds)

    async def get_user_by_id(self, user_id: UUID, tenant_id: UUID) -> Optional[Any]:
        """Get user from cache by ID (tenant-scoped)."""
        return await self._cache.get(f"user_id:{tenant_id}:{user_id}")

    async def get_user_by_email(self, email: str, tenant_id: UUID) -> Optional[Any]:
        """Get user from cache by email (tenant-scoped)."""
        return await self._cache.get(f"user_email:{tenant_id}:{email}")

    async def cache_user(self, user: Any, tenant_id: UUID) -> None:
        """Cache user data with both ID and email keys."""
        await self._cache.set(f"user_id:{tenant_id}:{user.id}", user)
        await self._cache.set(f"user_email:{tenant_id}:{user.email}", user)

    async def invalidate_user(self, user_id: UUID, tenant_id: UUID, email: str | None = None) -> bool:
        """Remove user from cache (useful for user updates)."""
        id_deleted = await self._cache.delete(f"user_id:{tenant_id}:{user_id}")
        email_deleted = True
        if email:
            email_deleted = await self._cache.delete(f"user_email:{tenant_id}:{email}")
        return id_deleted and email_deleted

    async def clear_tenant_users(self, tenant_id: UUID) -> None:
        """Clear all users for a specific tenant."""
        # Note: LRU cache doesn't support pattern deletion, but we can enhance this later
        await self._cache.clear()

    async def user_exists_in_cache(self, user_id: UUID, tenant_id: UUID) -> bool:
        """Check if user is cached."""
        return await self._cache.exists(f"user_id:{tenant_id}:{user_id}")

    async def get_cache_stats(self) -> dict:
        """Get user cache performance metrics."""
        stats = await self._cache.get_stats()
        stats["cache_purpose"] = "user_authentication_lookup"
        return stats
