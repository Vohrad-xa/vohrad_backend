"""Shared dependencies for the application."""

from api.tenant.models import Tenant
from database.sessions import get_default_db_session
from database.sessions import get_sub_domain_from_request
from exceptions import tenant_not_found
from fastapi import Depends
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_current_tenant(request: Request, db: AsyncSession = Depends(get_default_db_session)) -> Tenant:
    """Get current tenant object based on subdomain from request."""
    subdomain = get_sub_domain_from_request(request)

    result = await db.execute(select(Tenant).filter(Tenant.sub_domain == subdomain))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise tenant_not_found(subdomain)
    return tenant
