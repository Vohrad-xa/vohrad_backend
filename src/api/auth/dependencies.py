"""Authentication dependencies for FastAPI integration."""

from domain.subdomain import SubdomainExtractor
from exceptions import AuthenticationException, ExceptionFactory, TokenMissingException
from fastapi import Depends, Header, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from security.jwt import AuthenticatedUser, get_auth_jwt_service
from typing import Optional
from uuid import UUID

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


async def _get_tenant_and_user(current_user: AuthenticatedUser, validate_license: bool = True):
    """Internal helper to get tenant and user with optional license validation."""
    if not current_user.tenant_id:
        raise ExceptionFactory.authorization_failed("tenant", "access")

    from api.tenant.models import Tenant
    from api.tenant.service import tenant_service
    from database.sessions import with_default_db

    async with with_default_db() as shared_db:
        tenant: Tenant = await tenant_service.get_tenant_by_id(shared_db, current_user.tenant_id)
        if not tenant:
            raise AuthenticationException("Tenant not found")

        if validate_license:
            from api.license.service import license_service

            if not tenant.license_id:
                raise ExceptionFactory.business_rule(
                    "Tenant does not have an active license", {"tenant_id": str(tenant.tenant_id)}
                )

            license_obj = await license_service.get_by_id(shared_db, tenant.license_id)
            if not license_service._is_license_active(license_obj):
                raise ExceptionFactory.business_rule(
                    f"Tenant license is {license_obj.status}",
                    {"tenant_id": str(tenant.tenant_id), "license_status": license_obj.status},
                )

    return current_user, tenant


# Deprecated: replaced by admin-aware context helpers
# async def get_current_tenant_and_user(current_user: AuthenticatedUser = Depends(get_current_user)):
#     """With license validation."""
#     return await _get_tenant_and_user(current_user, validate_license=True)


# Deprecated: replaced by admin-aware context helpers
# async def get_current_tenant_and_user_no_license_check(current_user: AuthenticatedUser = Depends(get_current_user)):
#     """Without license validation (for license info endpoints)."""
#     return await _get_tenant_and_user(current_user, validate_license=False)


# ===== Admin-aware helpers =====
async def _resolve_admin_target_tenant(
    request: Request,
    tenant_context_id: Optional[str],
    x_tenant_id      : Optional[str],
):
    """Resolve tenant for admin using tenant_id (query/header) or subdomain fallback."""
    # Prefer explicit tenant_id in query/header
    target_tenant_id: Optional[UUID] = None
    if tenant_context_id:
        try:
            target_tenant_id = UUID(tenant_context_id)
        except ValueError as err:
            raise ExceptionFactory.validation_failed("tenant_id", "Invalid UUID format") from err
    elif x_tenant_id:
        try:
            target_tenant_id = UUID(x_tenant_id)
        except ValueError as err:
            raise ExceptionFactory.validation_failed("x_tenant_id", "Invalid UUID format") from err

    from api.tenant.service import tenant_service
    from database.sessions import with_default_db

    async with with_default_db() as shared_db:
        if target_tenant_id:
            return await tenant_service.get_tenant_by_id(shared_db, target_tenant_id)

        # Fallback: try subdomain header/host if present
        subdomain = SubdomainExtractor.from_request(request)
        if not subdomain:
            raise ExceptionFactory.authorization_failed("tenant", "access")
        return await tenant_service.get_tenant_by_subdomain(shared_db, subdomain)


async def get_admin_or_tenant_context(
    request          : Request,
    current_user     : AuthenticatedUser = Depends(get_current_user),
    tenant_context_id: Optional[str]     = Query(None, alias="tenant_id"),
    x_tenant_id      : Optional[str]     = Header(None),
):
    """Return (current_user, tenant) for either tenant users or admins.

    - Tenant users: identical behavior to get_current_tenant_and_user (with license validation).
    - Admins      : resolve tenant by explicit tenant_id (query/header) or by subdomain; skip license checks.
    """
    if current_user.is_tenant_user():
        return await _get_tenant_and_user(current_user, validate_license=True)

    if current_user.is_admin():
        tenant = await _resolve_admin_target_tenant(request, tenant_context_id, x_tenant_id)
        return current_user, tenant

    # Shouldn't happen, but keep explicit
    raise ExceptionFactory.authorization_failed("tenant", "access")


async def get_admin_or_tenant_context_no_license_check(
    request          : Request,
    current_user     : AuthenticatedUser = Depends(get_current_user),
    tenant_context_id: Optional[str]     = Query(None, alias="tenant_id"),
    x_tenant_id      : Optional[str]     = Header(None),
):
    """Like get_admin_or_tenant_context but without tenant license validation for tenant users."""
    if current_user.is_tenant_user():
        return await _get_tenant_and_user(current_user, validate_license=False)

    if current_user.is_admin():
        tenant = await _resolve_admin_target_tenant(request, tenant_context_id, x_tenant_id)
        return current_user, tenant

    raise ExceptionFactory.authorization_failed("tenant", "access")
