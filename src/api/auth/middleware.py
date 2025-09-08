"""Authentication middleware for enterprise security."""

from exceptions.jwt_exceptions import JWTException, TokenExpiredException, TokenInvalidException
from fastapi import Request, Response
import re
from security.jwt import get_auth_jwt_service
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from typing import List, Optional, Set


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware following enterprise security patterns."""

    def __init__(
        self,
        app,
        excluded_paths   : Optional[Set[str]] = None,
        excluded_patterns: Optional[List[str]] = None,
        auto_error       : bool = False,
    ):
        super().__init__(app)
        self.auth_service = get_auth_jwt_service()

        # Default excluded paths
        if excluded_paths is None:
            self.excluded_paths = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}
        else:
            self.excluded_paths = excluded_paths

        # Excluded routes
        if excluded_patterns is None:
            default_patterns = [
                r"^/v1/auth/login/.*",
                r"^/v1/auth/refresh$",
                r"^/v1/auth/status$",
                r"^/static/.*",
                r"^/assets/.*",
                r"^/public/.*",
            ]
        else:
            default_patterns = excluded_patterns

        self.excluded_patterns = [re.compile(pattern) for pattern in default_patterns]

        self.auto_error = auto_error

    def _is_path_excluded(self, path: str) -> bool:
        """Check if path should skip authentication."""
        # Check exact path matches
        if path in self.excluded_paths:
            return True

        # Check regex patterns
        for pattern in self.excluded_patterns:
            if pattern.match(path):
                return True

        return False

    def _extract_bearer_token(self, request: Request) -> Optional[str]:
        """Extract Bearer token from Authorization header."""
        authorization = request.headers.get("authorization")
        if not authorization:
            return None

        # Support both "Bearer " and "bearer " prefixes
        if authorization.lower().startswith("bearer "):
            return authorization[7:]

        return None

    def _create_error_response(self, exception: JWTException) -> JSONResponse:
        """Create standardized error response."""
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code"   : getattr(exception, "error_code", "AUTH_ERROR"),
                    "message": str(exception),
                    "type"   : "authentication_error",
                }
            },
            headers={
                "WWW-Authenticate": "Bearer",
                "X-Content-Type-Options": "nosniff"
            },
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with authentication context injection."""
        path = request.url.path

        # Skip authentication for excluded paths
        if self._is_path_excluded(path):
            response = await call_next(request)
            return self._add_security_headers(response)

        token = self._extract_bearer_token(request)

        # Initialize request state
        request.state.authenticated      = False
        request.state.authenticated_user = None
        request.state.auth_context       = None

        if token:
            try:
                authenticated_user = await self.auth_service.validate_access_token(token)

                # Set request state for downstream usage
                request.state.authenticated = True
                request.state.authenticated_user = authenticated_user
                request.state.auth_context = {
                    "user_id"  : str(authenticated_user.user_id),
                    "email"    : authenticated_user.email,
                    "tenant_id": str(authenticated_user.tenant_id) if authenticated_user.tenant_id else None,
                    "user_type": authenticated_user.user_type,
                }

            except (TokenInvalidException, TokenExpiredException) as e:
                if self.auto_error:
                    return self._create_error_response(e)
                # Continue without authentication if auto_error is False

            except Exception:
                # Log unexpected errors (add proper logging here)
                if self.auto_error:
                    return self._create_error_response(TokenInvalidException("Authentication service error"))

        response = await call_next(request)

        # Add security headers
        return self._add_security_headers(response)

    def _add_security_headers(self, response: Response) -> Response:
        """Add enterprise security headers to response."""
        security_headers = {
            "X-Content-Type-Options"           : "nosniff",
            "X-Frame-Options"                  : "DENY",
            "X-XSS-Protection"                 : "1; mode=block",
            "Strict-Transport-Security"        : "max-age=31536000; includeSubDomains",
            "Referrer-Policy"                  : "strict-origin-when-cross-origin",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cache-Control"                    : "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma"                           : "no-cache",
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


# Convenience factory functions for different configurations


def create_strict_auth_middleware(app) -> AuthMiddleware:
    """Create strict auth middleware that requires authentication for most routes."""
    return AuthMiddleware(
        app=app,
        auto_error=True,
        excluded_paths={
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        },
        excluded_patterns=[
            r"^/v1/auth/login/.*",
            r"^/v1/auth/refresh$",
            r"^/v1/auth/status$",
            r"^/static/.*",
            r"^/public/.*"
        ],
    )


def create_permissive_auth_middleware(app) -> AuthMiddleware:
    """Create permissive auth middleware that injects context when available."""
    return AuthMiddleware(
        app=app,
        auto_error=False,          # Don't automatically error on missing/invalid tokens
        excluded_paths    = set(),  # Process all paths for context injection
        excluded_patterns = [],    # No excluded patterns
    )
