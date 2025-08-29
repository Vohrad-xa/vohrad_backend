"""Authentication module following enterprise patterns."""

# JWT components from security
from .dependencies import get_current_admin
from .dependencies import get_current_tenant_and_user
from .dependencies import get_current_tenant_user
from .dependencies import get_current_user
from .dependencies import get_optional_user
from .dependencies import require_permission
from .dependencies import require_role
from .middleware import AuthMiddleware
from .middleware import create_permissive_auth_middleware
from .middleware import create_strict_auth_middleware
from .router import router
from .schema import AdminLoginRequest
from .schema import AuthStatusResponse
from .schema import RefreshTokenRequest
from .schema import TokenResponse
from .schema import UserLoginRequest
from security.jwt import AccessToken
from security.jwt import AuthenticatedUser
from security.jwt import RefreshToken
from security.jwt import TokenPair

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
    "require_permission",
    "require_role",
    # Router and middleware
    "router",
]
