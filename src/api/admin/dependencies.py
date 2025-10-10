"""Admin dependencies."""

from api.auth import get_current_admin
from database.sessions import get_admin_db_session
from fastapi import Depends
from security.jwt import AuthenticatedUser
from sqlalchemy.ext.asyncio import AsyncSession
from web import PaginationParams


def get_admin_params(
    pagination  : PaginationParams = Depends(),
    current_user: AuthenticatedUser = Depends(get_current_admin),
    db          : AsyncSession = Depends(get_admin_db_session)
) -> tuple[PaginationParams, AuthenticatedUser, AsyncSession]:
    """Get pagination, authenticated admin user, and database session."""
    return pagination, current_user, db
