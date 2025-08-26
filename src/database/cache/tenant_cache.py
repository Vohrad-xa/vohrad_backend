"""Tenant-specific cache implementation for schema lookups."""

from typing import Optional
from .lru_cache import LRUCache

class TenantCache:
    """High-level tenant schema cache with business logic."""

    def __init__(self, max_tenants: int = 1000, ttl_seconds: int = 3600):
        """Initialize tenant cache.

        Args:
            max_tenants: Maximum number of tenant schemas to cache
            ttl_seconds: How long to cache tenant schemas
        """
        self._cache = LRUCache(max_size=max_tenants, default_ttl_seconds=ttl_seconds)

    async def get_tenant_schema(self, subdomain: str) -> Optional[str]:
        """Get tenant schema name by subdomain."""
        return await self._cache.get(f"tenant:{subdomain}")

    async def cache_tenant_schema(self, subdomain: str, schema_name: str) -> None:
        """Cache tenant schema mapping."""
        await self._cache.set(f"tenant:{subdomain}", schema_name)

    async def invalidate_tenant(self, subdomain: str) -> bool:
        """Remove tenant from cache (useful for tenant updates)."""
        return await self._cache.delete(f"tenant:{subdomain}")

    async def clear_all_tenants(self) -> None:
        """Clear all tenant cache entries."""
        await self._cache.clear()

    async def tenant_exists_in_cache(self, subdomain: str) -> bool:
        """Check if tenant is cached."""
        return await self._cache.exists(f"tenant:{subdomain}")

    async def get_cache_stats(self) -> dict:
        """Get tenant cache performance metrics."""
        stats = await self._cache.get_stats()
        stats["cache_purpose"] = "tenant_schema_lookup"
        return stats
