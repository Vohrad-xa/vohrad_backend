"""Authentication module following enterprise patterns."""

# JWT components from security
from .dependencies import (
    get_current_admin,
    get_current_tenant_and_user,
    get_current_tenant_user,
    get_current_user,
    get_optional_user,
)
from .middleware import AuthMiddleware, create_permissive_auth_middleware, create_strict_auth_middleware
from .router import router
from .schema import AdminLoginRequest, AuthStatusResponse, RefreshTokenRequest, TokenResponse, UserLoginRequest
from security.jwt import AccessToken, AuthenticatedUser, RefreshToken, TokenPair

__all__ = [
    # JWT components
    "AccessToken",
    "AdminLoginRequest",
    "AuthMiddleware",
    "AuthStatusResponse",
    "AuthenticatedUser",
    "RefreshToken",
    "RefreshTokenRequest",
    "TokenPair",
    "TokenResponse",
    # Schemas
    "UserLoginRequest",
    "create_permissive_auth_middleware",
    "create_strict_auth_middleware",
    "get_current_admin",
    "get_current_tenant_and_user",
    "get_current_tenant_user",
    # Dependencies
    "get_current_user",
    "get_optional_user",
    # Router and middleware
    "router",
]
