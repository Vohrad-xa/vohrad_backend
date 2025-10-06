"""Admin dependencies with tenant context switching."""

from .context import AdminContext
from api.auth import get_current_admin
from database.sessions import get_admin_db_session
from exceptions import ExceptionFactory
from fastapi import Depends
from security.authorization.service import AuthorizationService
from security.jwt import AuthenticatedUser
from sqlalchemy.ext.asyncio import AsyncSession
from web import PaginationParams


async def get_admin_context(
    current_user: AuthenticatedUser = Depends(get_current_admin),
    db          : AsyncSession = Depends(get_admin_db_session)
) -> AdminContext:
    """Create admin context with authentication and tenant switching capability."""
    tenant_id = getattr(db, "_tenant_id", None)
    tenant_schema = getattr(db, "_tenant_schema", None)

    # Validate admin tenant permissions
    authorization_service = AuthorizationService()
    has_tenant_permission = await authorization_service.user_has_permission(current_user.user_id, "tenant", "*")

    if not has_tenant_permission:
        raise ExceptionFactory.authorization_failed("tenant", "access")

    return AdminContext(
        user          = current_user,
        db_session    = db,
        tenant_id     = tenant_id,
        tenant_schema = tenant_schema
    )


def get_admin_params(
    pagination: PaginationParams = Depends(), context: AdminContext = Depends(get_admin_context)
) -> tuple[PaginationParams, AdminContext]:
    """Get pagination and admin context in single dependency."""
    return pagination, context
