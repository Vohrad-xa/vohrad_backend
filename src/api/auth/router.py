"""Authentication API router following enterprise patterns."""

from .dependencies import get_current_user
from .schema import AdminLoginRequest
from .schema import AuthStatusResponse
from .schema import RefreshTokenRequest
from .schema import TokenResponse
from .schema import UserLoginRequest
from api.tenant.dependencies import get_current_tenant
from api.tenant.models import Tenant
from fastapi import APIRouter
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from security.jwt import AuthenticatedUser
from security.jwt import get_auth_jwt_service
from web import ResponseFactory
from web import SuccessResponse

router = APIRouter(
    prefix = "/auth",
    tags   = ["authentication"]
)


@router.post("/login/user", response_model=SuccessResponse[TokenResponse], summary="User Login")
async def login_user(
    login_data: UserLoginRequest,
    tenant    : Tenant = Depends(get_current_tenant),
    auth_service = Depends(get_auth_jwt_service)
):
    """Authenticate tenant user using subdomain-based tenant resolution."""
    token_pair = await auth_service.login_user(login_data, tenant)

    return ResponseFactory.success(
        data    = token_pair.to_response(),
        message = "User authentication successful"
    )


@router.post("/login/admin", response_model=SuccessResponse[TokenResponse], summary="Admin Login")
async def login_admin(
    login_data: AdminLoginRequest,
    auth_service = Depends(get_auth_jwt_service)
):
    """Authenticate global admin and return JWT tokens."""
    token_pair = await auth_service.login_admin(login_data)

    return ResponseFactory.success(
        data    = token_pair.to_response(),
        message = "Admin authentication successful"
    )


@router.post("/refresh", response_model=SuccessResponse[TokenResponse], summary="Refresh Token")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service = Depends(get_auth_jwt_service)
):
    """Refresh access token using refresh token."""
    token_pair = await auth_service.refresh_token(refresh_data.refresh_token)

    return ResponseFactory.success(
        data    = token_pair.to_response(),
        message = "Token refresh successful"
    )


bearer_scheme = HTTPBearer(auto_error=True)


@router.post("/logout", response_model=SuccessResponse[None], summary="User Logout")
async def logout(
    credentials : HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: AuthenticatedUser            = Depends(get_current_user),
                 auth_service                  = Depends(get_auth_jwt_service)
):
    """Logout current user by revoking their access token."""
    access_token = credentials.credentials

    await auth_service.logout_user(access_token)

    return ResponseFactory.success(
        data    = None,
        message = f"User {current_user.email} logged out successfully"
    )


@router.post("/logout-all", response_model=SuccessResponse[dict], summary="Logout All Devices")
async def logout_all_devices(
    current_user: AuthenticatedUser = Depends(get_current_user),
    auth_service                    = Depends(get_auth_jwt_service)
):
    """Logout user from all devices by revoking all their tokens."""
    revoked_count = await auth_service.logout_user_from_all_devices(
        current_user.user_id,
        "logout_all_devices"
    )

    return ResponseFactory.success(
        data={
            "revoked_tokens": revoked_count,
            "user_id": str(current_user.user_id)
        },
        message = f"Logged out {current_user.email} from {revoked_count} device(s)"
    )


@router.get("/status", response_model=SuccessResponse[AuthStatusResponse], summary="Service Status")
async def auth_status():
    """Authentication service health check and status information."""
    status_info = AuthStatusResponse(
        service     = "authentication",
        status      = "healthy",
        jwt_service = "operational"
    )

    return ResponseFactory.success(
        data    = status_info,
        message = "Authentication service is operational"
    )
