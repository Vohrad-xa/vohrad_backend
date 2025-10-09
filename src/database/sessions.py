"""Database session helpers and dependencies."""

from .engine import async_engine
from contextlib import asynccontextmanager

# from domain.subdomain import SubdomainExtractor  # Deprecated helper only
from exceptions import ExceptionFactory, tenant_not_found
from fastapi import Header, Query  # Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

# === Deprecated: unused after admin-aware tenant context ===
# def get_sub_domain_from_request(req: Request) -> str:
#     """Get the subdomain from the request"""
#     subdomain = SubdomainExtractor.from_request(req)
#     if not subdomain:
#         return req.headers.get("host", "localhost").split(":", 1)[0]
#     return subdomain


@asynccontextmanager
async def with_default_db():
    """Get a database connection for shared schema operations"""
    connectable = async_engine.execution_options(schema_translate_map={"tenant_default": "shared"})
    try:
        db = AsyncSession(autocommit=False, autoflush=False, bind=connectable)
        yield db
    finally:
        await db.close()


@asynccontextmanager
async def with_tenant_db(tenant_schema: Optional[str]):
    """Get a database connection for the given tenant schema"""
    connectable = async_engine.execution_options(schema_translate_map={"tenant_default": tenant_schema})
    try:
        db = AsyncSession(autocommit=False, autoflush=False, bind=connectable)
        yield db
    finally:
        await db.close()


async def get_default_db_session():
    """Dependency for default database session."""
    async with with_default_db() as session:
        yield session


# === Deprecated: unused after admin-aware tenant context ===
# async def get_tenant_db_session(tenant_schema_name=Depends(get_sub_domain_from_request)):
#     """FastAPI dependency for tenant-specific database session."""
#     from api.tenant import get_tenant_schema_resolver
#
#     tenant_service = get_tenant_schema_resolver()
#     tenant_schema = await tenant_service.resolve_tenant_schema(tenant_schema_name)
#
#     async with with_tenant_db(tenant_schema=tenant_schema) as session:
#         yield session


async def get_admin_db_session(
    tenant_context_id: Optional[UUID] = Query(
        None, alias="tenant_id", description="Tenant ID to manage (for admin context switching)"
    ),
    x_tenant_id: Optional[str] = Header(None, description="Alternative tenant ID via header"),
):
    """Admin database session with tenant context switching."""
    # Parse tenant ID from query param or header
    target_tenant_id = tenant_context_id
    if not target_tenant_id and x_tenant_id:
        try:
            target_tenant_id = UUID(x_tenant_id)
        except ValueError as err:
            raise ExceptionFactory.validation_failed("x_tenant_id", "Invalid UUID format") from err

    if target_tenant_id:
        from api.tenant.service import tenant_service

        async with with_default_db() as shared_db:
            try:
                tenant = await tenant_service.get_tenant_by_id(shared_db, target_tenant_id)
            except Exception as err:
                raise tenant_not_found(target_tenant_id) from err

        async with with_tenant_db(tenant.tenant_schema_name) as session:
            session._admin_context = True
            session._tenant_id = target_tenant_id
            session._tenant_schema = tenant.tenant_schema_name
            yield session
    else:
        async with with_default_db() as session:
            session._admin_context = True
            yield session
