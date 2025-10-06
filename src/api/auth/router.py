"""Authentication API router following enterprise patterns."""

from .dependencies import get_current_user
from .schema import (
    AdminLoginRequest,
    AuthStatusResponse,
    RefreshTokenRequest,
    SecurityStatusResponse,
    TokenResponse,
    UserLoginRequest,
)
from api.tenant.dependencies import get_current_tenant
from api.tenant.models import Tenant
from config.keys import get_key_manager
from config.settings import get_settings
from exceptions import AuthenticationException
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from security.jwt import AuthenticatedUser, get_auth_jwt_service
from security.jwt.tokens import TokenPair
from web import ResponseFactory, SuccessResponse

settings = get_settings()
REFRESH_COOKIE_NAME = settings.WEB_REFRESH_COOKIE_NAME


def _is_web_client(request: Request) -> bool:
    client_platform = request.headers.get("x-client-platform")
    return isinstance(client_platform, str) and client_platform.lower() == "web"


def _set_refresh_cookie(response: Response, token_pair: TokenPair) -> None:
    refresh_token = token_pair.refresh_token
    # Clamp cookie lifetime to configured web maximum (default 12h) even if token lives longer.
    max_age = min(refresh_token.expires_in_seconds, settings.WEB_COOKIE_MAX_AGE_SECONDS)
    cookie_kwargs = {
        "httponly": True,
        "secure": bool(settings.WEB_COOKIE_SECURE),
        "samesite": settings.WEB_COOKIE_SAMESITE.lower(),
        "path": settings.WEB_COOKIE_PATH or "/",
    }
    if settings.WEB_COOKIE_DOMAIN:
        cookie_kwargs["domain"] = settings.WEB_COOKIE_DOMAIN

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token.token,
        max_age=max_age,
        expires=max_age,
        **cookie_kwargs,
    )


def _clear_refresh_cookie(response: Response) -> None:
    delete_kwargs = {
        "path": settings.WEB_COOKIE_PATH or "/",
    }
    if settings.WEB_COOKIE_DOMAIN:
        delete_kwargs["domain"] = settings.WEB_COOKIE_DOMAIN

    response.delete_cookie(REFRESH_COOKIE_NAME, **delete_kwargs)


router = APIRouter(
    prefix = "/auth",
    tags   = ["authentication"]
)


@router.post("/login/user", response_model=SuccessResponse[TokenResponse], summary="User Login")
async def login_user(
    login_data: UserLoginRequest,
    request   : Request,
    response  : Response,
    tenant    : Tenant = Depends(get_current_tenant),
    auth_service = Depends(get_auth_jwt_service)
):
    """Authenticate tenant user using subdomain-based tenant resolution."""
    token_pair = await auth_service.login_user(login_data, tenant)

    if _is_web_client(request):
        _set_refresh_cookie(response, token_pair)

    return ResponseFactory.success(
        data    = token_pair.to_response(),
        message = "User authentication successful"
    )


@router.post("/login/admin", response_model=SuccessResponse[TokenResponse], summary="Admin Login")
async def login_admin(
    login_data: AdminLoginRequest,
    request   : Request,
    response  : Response,
    auth_service = Depends(get_auth_jwt_service)
):
    """Authenticate global admin and return JWT tokens."""
    token_pair = await auth_service.login_admin(login_data)

    if _is_web_client(request):
        _set_refresh_cookie(response, token_pair)

    return ResponseFactory.success(
        data    = token_pair.to_response(),
        message = "Admin authentication successful"
    )


@router.post("/refresh", response_model=SuccessResponse[TokenResponse], summary="Refresh Token")
async def refresh_token(
    request      : Request,
    response     : Response,
    refresh_data : RefreshTokenRequest | None = None,
    auth_service = Depends(get_auth_jwt_service)
):
    """Refresh access token using refresh token."""
    provided_refresh = refresh_data.refresh_token if refresh_data else None

    refresh_token_value = provided_refresh
    if not refresh_token_value and _is_web_client(request):
        refresh_token_value = request.cookies.get(REFRESH_COOKIE_NAME)

    if not refresh_token_value:
        raise AuthenticationException("Refresh token required")

    token_pair = await auth_service.refresh_token(refresh_token_value)

    if _is_web_client(request):
        _set_refresh_cookie(response, token_pair)

    return ResponseFactory.success(
        data    = token_pair.to_response(),
        message = "Token refresh successful"
    )


bearer_scheme = HTTPBearer(auto_error=True)


@router.post("/logout", response_model=SuccessResponse[None], summary="User Logout")
async def logout(
    request     : Request,
    response    : Response,
    credentials : HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: AuthenticatedUser            = Depends(get_current_user),
                 auth_service                  = Depends(get_auth_jwt_service)
):
    """Logout current user by revoking their access token."""
    access_token = credentials.credentials

    await auth_service.logout_user(access_token)

    if _is_web_client(request):
        _clear_refresh_cookie(response)

    return ResponseFactory.success(
        data    = None,
        message = f"User {current_user.email} logged out successfully"
    )


@router.post("/logout-all", response_model=SuccessResponse[dict], summary="Logout All Devices")
async def logout_all_devices(
    request     : Request,
    response    : Response,
    current_user: AuthenticatedUser = Depends(get_current_user),
    auth_service                    = Depends(get_auth_jwt_service)
):
    """Logout user from all devices by revoking all their tokens."""
    revoked_count = await auth_service.logout_user_from_all_devices(
        current_user.user_id,
        "logout_all_devices"
    )

    if _is_web_client(request):
        _clear_refresh_cookie(response)

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


@router.get(
    "/security-status",
    response_model = SuccessResponse[SecurityStatusResponse],
    summary        = "Security Configuration Status"
)
async def security_status():
    """Get security configuration status and key validation information."""
    key_manager = get_key_manager()
    validation_result = key_manager.validate_keys()

    security_info = SecurityStatusResponse(
        service                   = validation_result.get("service", "security"),
        secret_key_configured     = validation_result["secret_key_configured"],
        secret_key_length         = validation_result["secret_key_length"],
        secret_key_strength       = validation_result["secret_key_strength"],
        encryption_key_configured = validation_result["encryption_key_configured"],
        jwt_algorithm             = validation_result["jwt_algorithm"],
        environment               = validation_result["environment"],
        warnings                  = validation_result["warnings"]
    )

    return ResponseFactory.success(
        data    = security_info,
        message = "Security configuration validated successfully"
    )
