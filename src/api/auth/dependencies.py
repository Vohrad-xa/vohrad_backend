"""Authentication dependencies for FastAPI integration."""

from exceptions import AuthenticationException
from exceptions import AuthorizationException
from exceptions import TokenMissingException
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from security.jwt import AuthenticatedUser
from security.jwt import get_auth_jwt_service
from typing import Any
from typing import Optional

security_scheme = HTTPBearer(auto_error=False, description="JWT Bearer token authentication")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> AuthenticatedUser:
    """Get current authenticated user from JWT token."""
    if not credentials:
        raise TokenMissingException("Authentication token required")

    try:
        auth_service = get_auth_jwt_service()
        return await auth_service.validate_access_token(credentials.credentials)
    except Exception as e:
        # Let JWT exceptions bubble up naturally, convert others to AuthenticationException
        if hasattr(e, 'error_code'):  # It's already a structured exception
            raise
        raise AuthenticationException("Authentication failed") from e


async def get_current_admin(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """Get current authenticated admin user."""
    user = await current_user
    if not user.is_admin():
        raise AuthorizationException("admin", "access")

    return user


async def get_current_tenant_user(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """Get current authenticated tenant user."""
    user = await current_user
    if not user.is_tenant_user():
        raise AuthorizationException("tenant", "access")

    return user


def require_permission(resource: str, action: str):
    """Create dependency that requires specific permission."""
    permission = f"{resource}:{action}"

    async def permission_dependency(
        current_user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        user = await current_user
        if not user.has_permission(permission):
            raise AuthorizationException(resource, action, {"required_permission": permission})
        return user

    return permission_dependency


def require_role(*roles: str):
    """Create dependency that requires specific role(s)."""
    async def role_dependency(
        current_user: AuthenticatedUser = Depends(get_current_user)
    ) -> AuthenticatedUser:
        user = await current_user
        if not any(user.has_role(role) for role in roles):
            raise AuthorizationException("roles", "access", {"required_roles": list(roles)})
        return user

    return role_dependency


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[AuthenticatedUser]:
    """Get authenticated user if present, None otherwise."""
    if not credentials:
        return None

    try:
        auth_service = get_auth_jwt_service()
        return await auth_service.validate_access_token(credentials.credentials)
    except Exception:
        return None


async def get_current_tenant_and_user(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> tuple[AuthenticatedUser, Any]:
    """Get current tenant and user objects with proper isolation."""
    if not current_user.tenant_id:
        raise AuthorizationException("tenant", "access")

    # Lazy imports to avoid circular dependencies
    from api.tenant.service import tenant_service
    from database.sessions import with_default_db

    # Get tenant from shared schema
    async with with_default_db() as shared_db:
        tenant = await tenant_service.get_tenant_by_id(shared_db, current_user.tenant_id)
        if not tenant:
            raise AuthenticationException("Tenant not found")

    return current_user, tenant
