"""Tenant-specific dependencies."""

from api.tenant.models import Tenant
from api.tenant.service import tenant_service
from database.sessions import get_default_db_session
from domain.subdomain import SubdomainExtractor
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_current_tenant(
    request: Request,
    db     : AsyncSession = Depends(get_default_db_session)
) -> Tenant:
    """Get current tenant object based on subdomain from request."""
    subdomain = SubdomainExtractor.from_request(request)
    return await tenant_service.get_tenant_by_subdomain(db, subdomain)
