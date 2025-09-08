"""Authentication dependencies for FastAPI integration."""

from domain.subdomain import SubdomainExtractor
from exceptions import AuthenticationException, ExceptionFactory, TokenMissingException
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from security.jwt import AuthenticatedUser, get_auth_jwt_service
from typing import Any, Optional

security_scheme = HTTPBearer(auto_error=False, description="JWT Bearer token authentication")


async def _validate_token_with_subdomain(token: str, request: Request) -> AuthenticatedUser:
    """Extract subdomain and validate token - DRY utility."""
    auth_service = get_auth_jwt_service()

    subdomain = SubdomainExtractor.from_request(request)

    return await auth_service.validate_access_token(token, subdomain)


async def get_current_user(
    request    : Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> AuthenticatedUser:
    """Get current authenticated user from JWT token with tenant-subdomain validation."""
    if not credentials:
        raise TokenMissingException("Authentication token required")

    try:
        return await _validate_token_with_subdomain(credentials.credentials, request)
    except Exception as e:
        # Let JWT exceptions bubble up naturally, convert others to AuthenticationException
        if hasattr(e, "error_code"):  # It's already a structured exception
            raise
        raise AuthenticationException("Authentication failed") from e


def get_current_admin(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    """Get current authenticated admin user."""
    if not current_user.is_admin():
        raise ExceptionFactory.authorization_failed("admin", "access")

    return current_user


def get_current_tenant_user(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    """Get current authenticated tenant user."""
    if not current_user.is_tenant_user():
        raise ExceptionFactory.authorization_failed("tenant", "access")

    return current_user


async def get_optional_user(
    request    : Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> Optional[AuthenticatedUser]:
    """Get authenticated user if present, None otherwise."""
    if not credentials:
        return None

    try:
        return await _validate_token_with_subdomain(credentials.credentials, request)
    except Exception:
        return None


async def get_current_tenant_and_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> tuple[AuthenticatedUser, Any]:
    """Get current tenant and user objects with proper isolation."""
    if not current_user.tenant_id:
        raise ExceptionFactory.authorization_failed("tenant", "access")

    # Lazy imports to avoid circular dependencies
    from api.tenant.service import tenant_service
    from database.sessions import with_default_db

    # Get tenant from shared schema
    async with with_default_db() as shared_db:
        tenant = await tenant_service.get_tenant_by_id(shared_db, current_user.tenant_id)
        if not tenant:
            raise AuthenticationException("Tenant not found")

    return current_user, tenant
