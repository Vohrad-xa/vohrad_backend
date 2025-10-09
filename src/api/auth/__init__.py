"""Authentication module following enterprise patterns."""

from .dependencies import (
    get_admin_or_tenant_context,
    get_admin_or_tenant_context_no_license_check,
    get_current_admin,
    get_current_tenant_user,
    get_current_user,
    get_optional_user,
)
from .middleware import AuthMiddleware, create_permissive_auth_middleware, create_strict_auth_middleware
from .router import router
from .schema import AdminLoginRequest, AuthStatusResponse, RefreshTokenRequest, TokenResponse, UserLoginRequest
from security.jwt import AccessToken, AuthenticatedUser, RefreshToken, TokenPair

__all__ = [
    "AccessToken",
    "AdminLoginRequest",
    "AuthMiddleware",
    "AuthStatusResponse",
    "AuthenticatedUser",
    "RefreshToken",
    "RefreshTokenRequest",
    "TokenPair",
    "TokenResponse",
    "UserLoginRequest",
    "create_permissive_auth_middleware",
    "create_strict_auth_middleware",
    "get_admin_or_tenant_context",
    "get_admin_or_tenant_context_no_license_check",
    "get_current_admin",
    "get_current_tenant_user",
    "get_current_user",
    "get_optional_user",
    "router",
]
