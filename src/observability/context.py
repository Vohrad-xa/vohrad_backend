"""Context management for correlation tracking and performance monitoring."""

from contextvars import ContextVar
import time
from typing import Optional
from uuid import uuid4

"""Context variables for request correlation and tracking"""
correlation_id_var    : ContextVar[Optional[str]]   = ContextVar("correlation_id", default=None)
request_start_time_var: ContextVar[Optional[float]] = ContextVar("request_start_time", default=None)
user_id_var           : ContextVar[Optional[str]]   = ContextVar("user_id", default=None)
tenant_id_var         : ContextVar[Optional[str]]   = ContextVar("tenant_id", default=None)


class PerformanceTracker:
    """Simple and effective performance tracking for requests and operations."""

    @staticmethod
    def start_request(
        correlation_id: Optional[str] = None,
        user_id       : Optional[str] = None,
        tenant_id     : Optional[str] = None
    ) -> str:
        """Start request timing and set correlation context."""
        if not correlation_id:
            correlation_id = str(uuid4())

        correlation_id_var.set(correlation_id)
        request_start_time_var.set(time.time())

        if user_id:
            user_id_var.set(user_id)
        if tenant_id:
            tenant_id_var.set(tenant_id)

        return correlation_id

    @staticmethod
    def end_request():
        """Clear all request context variables."""
        correlation_id_var.set(None)
        request_start_time_var.set(None)
        user_id_var.set(None)
        tenant_id_var.set(None)

    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get current correlation ID."""
        return correlation_id_var.get()

    @staticmethod
    def get_request_duration() -> Optional[float]:
        """Get current request duration in milliseconds."""
        start_time = request_start_time_var.get()
        if start_time:
            return round((time.time() - start_time) * 1000, 2)
        return None

    @staticmethod
    def get_context_info() -> dict:
        """Get all current context information as a dictionary."""
        context = {}

        if correlation_id := correlation_id_var.get():
            context["correlation_id"] = correlation_id

        if user_id := user_id_var.get():
            context["user_id"] = user_id

        if tenant_id := tenant_id_var.get():
            context["tenant_id"] = tenant_id

        if duration := PerformanceTracker.get_request_duration():
            context["request_duration_ms"] = str(duration)

        return context
