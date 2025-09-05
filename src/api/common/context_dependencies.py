"""Context dependencies for authenticated requests."""

from api.auth import get_current_tenant_and_user
from database.sessions import get_default_db_session, get_tenant_db_session
from fastapi import Depends
from security.jwt import AuthenticatedUser
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple


def get_authenticated_context(
    tenant_user=Depends(get_current_tenant_and_user),
) -> Tuple[AuthenticatedUser, object]:
    """Get authenticated user and tenant context."""
    current_user, tenant = tenant_user
    return current_user, tenant


def get_tenant_context(
    auth_context=Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_tenant_db_session)
) -> Tuple[AuthenticatedUser, object, AsyncSession]:
    """Get authenticated user, tenant, and tenant database session."""
    current_user, tenant = auth_context
    return current_user, tenant, db


def get_shared_context(
    auth_context=Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_default_db_session)
) -> Tuple[AuthenticatedUser, object, AsyncSession]:
    """Get authenticated user, tenant, and shared database session."""
    current_user, tenant = auth_context
    return current_user, tenant, db
