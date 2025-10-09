"""Context dependencies for authenticated requests."""

from api.auth import (
    get_admin_or_tenant_context,
    get_admin_or_tenant_context_no_license_check,
)
from database.sessions import get_default_db_session, with_tenant_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, Tuple


def get_authenticated_context(tenant_user=Depends(get_admin_or_tenant_context)):
    """Get authenticated user and tenant context with license validation."""
    return tenant_user


def get_authenticated_context_no_license_check(
    tenant_user = Depends(get_admin_or_tenant_context_no_license_check)
):
    """Get authenticated user and tenant context without license validation."""
    return tenant_user


async def get_tenant_context(
    auth_context=Depends(get_authenticated_context),
) -> AsyncGenerator[Tuple, None]:
    """Get authenticated user, tenant, and tenant database session.

    Admin-aware: if called by admins, uses the resolved tenant context; otherwise uses tenant user's tenant.
    """
    current_user, tenant = auth_context
    async with with_tenant_db(tenant.tenant_schema_name) as db:
        yield current_user, tenant, db


async def get_tenant_context_no_license_check(
    auth_context = Depends(get_authenticated_context_no_license_check),
) -> AsyncGenerator[Tuple, None]:
    """Get authenticated user, tenant, and tenant database session without license validation.

    Admin-aware: if called by admins, uses the resolved tenant context; otherwise uses tenant user's tenant.
    """
    current_user, tenant = auth_context
    async with with_tenant_db(tenant.tenant_schema_name) as db:
        yield current_user, tenant, db


def get_shared_context(
    auth_context = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_default_db_session)
) -> Tuple:
    """Get authenticated user, tenant, and shared database session."""
    current_user, tenant = auth_context
    return current_user, tenant, db


def get_shared_context_no_license_check(
    auth_context = Depends(get_authenticated_context_no_license_check),
    db: AsyncSession = Depends(get_default_db_session)
) -> Tuple:
    """Get authenticated user, tenant, and shared database session without license validation."""
    current_user, tenant = auth_context
    return current_user, tenant, db
