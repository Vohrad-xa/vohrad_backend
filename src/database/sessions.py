from contextlib import asynccontextmanager
from typing import Optional
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from domain.subdomain import SubdomainExtractor
from .engine import async_engine

__all__ = ["get_default_db_session", "get_tenant_db_session", "with_default_db", "with_tenant_db"]

def get_sub_domain_from_request(req: Request) -> str:
    """Get the subdomain from the request"""
    subdomain = SubdomainExtractor.from_request(req)
    if not subdomain:
        return req.headers.get("host", "localhost").split(":", 1)[0]
    return subdomain

@asynccontextmanager
async def with_default_db():
    """Get a database connection using the schemas defined in each model"""
    connectable = async_engine.execution_options()
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

async def get_tenant_db_session(tenant_schema_name=Depends(get_sub_domain_from_request)):
    """FastAPI dependency for tenant-specific database session.
    Uses modular tenant service for clean schema resolution.
    """
    from services.tenant_service import get_tenant_schema_service

    # Resolve tenant schema using service layer
    tenant_service = get_tenant_schema_service()
    tenant_schema = await tenant_service.resolve_tenant_schema(tenant_schema_name)

    # Single session with proper schema translation
    async with with_tenant_db(tenant_schema=tenant_schema) as session:
        yield session
