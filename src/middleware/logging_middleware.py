"""Request logging middleware with correlation ID tracking and performance monitoring."""

import time
from fastapi import Request
from fastapi import Response
from observability import PerformanceTracker
from observability import get_logger
from observability import get_security_logger
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from uuid import uuid4

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging, correlation tracking, and performance monitoring."""

    def __init__(self, app, exclude_paths: set | None = None):
        super().__init__(app)
        self.logger = get_logger("vohrad.requests")
        self.security_logger = get_security_logger()
        self.exclude_paths = exclude_paths or {
            "/health",
            "/metrics",
            "/status",
            "/ping",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/favicon.ico",
            "/robots.txt",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Skip logging for excluded paths"""
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        start_time = time.time()
        correlation_id = self._get_or_create_correlation_id(request)
        user_id = self._extract_user_id(request)
        tenant_id = self._extract_tenant_id(request)
        PerformanceTracker.start_request(correlation_id, user_id, tenant_id)
        self._log_request_start(request, correlation_id, user_id, tenant_id)

        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            self._log_request_completion(request, response, correlation_id, duration_ms, user_id, tenant_id)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            self._log_request_error(request, exc, correlation_id, duration_ms, user_id, tenant_id)
            raise
        finally:
            PerformanceTracker.end_request()

    def _get_or_create_correlation_id(self, request: Request) -> str:
        """Get correlation ID from headers or create new one."""
        return request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID") or str(uuid4())

    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request context (JWT, session, etc.)."""
        # TODO: Implement based on authentication system
        return request.headers.get("X-User-ID")

    def _extract_tenant_id(self, request: Request) -> str:
        """Extract tenant ID from request (subdomain, header, etc.)."""
        host = request.headers.get("host", "")
        if "." in host:
            return host.split(".")[0]
        return request.headers.get("X-Tenant-ID")

    def _log_request_start(self, request: Request, correlation_id: str, user_id: str, tenant_id: str):
        """Log request start."""
        self.logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get("user-agent"),
                "client_ip": self._get_client_ip(request),
                "user_id": user_id,
                "tenant_id": tenant_id,
                "content_type": request.headers.get("content-type"),
                "event_type": "request_start",
            },
        )

    def _log_request_completion(
        self,
        request: Request,
        response: Response,
        correlation_id: str,
        duration_ms: float,
        user_id: str,
        tenant_id: str,
    ):
        """Log successful request completion."""
        log_level = "info"
        if response.status_code >= 400:
            log_level = "warning" if response.status_code < 500 else "error"

        getattr(self.logger, log_level)(
            "Request completed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "client_ip": self._get_client_ip(request),
                "response_size": response.headers.get("content-length"),
                "event_type": "request_completed",
            },
        )

        """Log security events for sensitive operations"""
        if self._is_sensitive_endpoint(request.url.path):
            self.security_logger.info(
                "Sensitive operation accessed",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "client_ip": self._get_client_ip(request),
                    "event_type": "sensitive_access",
                },
            )

    def _log_request_error(
        self, request: Request, exc: Exception, correlation_id: str, duration_ms: float, user_id: str, tenant_id: str
    ):
        """Log request error."""
        self.logger.error(
            "Request failed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "client_ip": self._get_client_ip(request),
                "exception_type": exc.__class__.__name__,
                "exception_message": str(exc),
                "event_type": "request_error",
            },
            exc_info=True,
        )

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address with proxy support."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        forwarded = request.headers.get("X-Forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint involves sensitive operations."""
        sensitive_patterns = ["/login", "/logout", "/password", "/reset", "/admin/", "/users/", "/tenants/"]
        return any(pattern in path.lower() for pattern in sensitive_patterns)
