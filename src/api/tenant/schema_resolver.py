"""Tenant schema resolution service with caching."""

from database.cache import TenantCache
from exceptions import tenant_not_found
from typing import Optional
from uuid import UUID


class TenantSchemaResolver:
    """Service for tenant schema resolution with caching."""

    def __init__(self, cache: Optional[TenantCache] = None):
        """Initialize tenant schema resolver."""
        self._cache = cache or TenantCache()

    async def resolve_tenant_schema(self, subdomain: str) -> str:
        """Resolve the tenant schema name with a cache-first strategy."""
        # Try cache first
        cached_schema = await self._cache.get_tenant_schema(subdomain)
        if cached_schema:
            return cached_schema

        # Cache miss - query database
        schema_name = await self._query_tenant_from_database(subdomain)

        # Cache the result for future requests
        await self._cache.cache_tenant_schema(subdomain, schema_name)

        return schema_name

    async def resolve_tenant_schema_by_id(self, tenant_id: UUID) -> str:
        """Resolve tenant schema by tenant_id with cache-first strategy."""
        # Try cache by ID first
        cached_schema = await self._cache.get_tenant_schema_by_id(tenant_id)
        if cached_schema:
            return cached_schema

        # Cache miss - query database by ID
        schema_name = await self._query_tenant_schema_by_id(tenant_id)

        # Cache both id and, if needed, subdomain mapping can be added by caller
        await self._cache.cache_tenant_schema_by_id(tenant_id, schema_name)
        return schema_name

    async def _query_tenant_from_database(self, subdomain: str) -> str:
        """Query tenant schema from a database."""
        from api.tenant.models import Tenant
        from database.sessions import with_default_db
        from sqlalchemy import select

        async with with_default_db() as db:
            result = await db.execute(select(Tenant.tenant_schema_name).filter(Tenant.sub_domain == subdomain))
            schema_name = result.scalar_one_or_none()

        if schema_name is None:
            raise tenant_not_found(subdomain)

        return schema_name

    async def _query_tenant_schema_by_id(self, tenant_id: UUID) -> str:
        """Query tenant schema by tenant_id from the database."""
        from api.tenant.models import Tenant
        from database.sessions import with_default_db
        from sqlalchemy import select

        async with with_default_db() as db:
            result = await db.execute(select(Tenant.tenant_schema_name).filter(Tenant.tenant_id == tenant_id))
            schema_name = result.scalar_one_or_none()

        if schema_name is None:
            raise tenant_not_found(tenant_id)

        return schema_name

    async def invalidate_tenant_cache(self, subdomain: str) -> bool:
        """Invalidate cached tenant (useful after tenant updates)."""
        return await self._cache.invalidate_tenant(subdomain)

    async def get_cache_performance(self) -> dict:
        """Get cache performance metrics."""
        return await self._cache.get_cache_stats()

    async def clear_cache(self) -> None:
        """Clear all tenant cache entries."""
        await self._cache.clear_all_tenants()


_tenant_schema_resolver = TenantSchemaResolver()


def get_tenant_schema_resolver() -> TenantSchemaResolver:
    """Get global tenant schema resolver instance."""
    return _tenant_schema_resolver
