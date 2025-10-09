"""Admin dependencies with tenant context switching."""

from api.auth import get_current_admin
from database.sessions import get_admin_db_session
from exceptions import ExceptionFactory
from fastapi import Depends
from security.authorization.service import AuthorizationService
from security.jwt import AuthenticatedUser
from sqlalchemy.ext.asyncio import AsyncSession
from web import PaginationParams


async def get_admin_session(
    current_user: AuthenticatedUser = Depends(get_current_admin),
    db          : AsyncSession = Depends(get_admin_db_session)
) -> tuple[AuthenticatedUser, AsyncSession]:
    """Get authenticated admin user and database session."""
    # Validate admin tenant permissions
    authorization_service = AuthorizationService()
    has_tenant_permission = await authorization_service.user_has_permission(current_user.user_id, "tenant", "*")

    if not has_tenant_permission:
        raise ExceptionFactory.authorization_failed("tenant", "access")

    return current_user, db


def get_admin_params(
    pagination: PaginationParams = Depends(),
    admin_session = Depends(get_admin_session)
) -> tuple[PaginationParams, AuthenticatedUser, AsyncSession]:
    """Get pagination, authenticated admin, and database session."""
    current_user, db = admin_session
    return pagination, current_user, db
