"""Rate limiting configuration."""

from .settings import get_settings
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address


def get_limiter() -> Limiter:
    """Create rate limiter instance."""
    settings = get_settings()

    # Use environment-based limits
    default_limit = "100/minute" if settings.is_production else "1000/minute"

    return Limiter(
        key_func=get_remote_address,
        default_limits=[default_limit],
        storage_uri="memory://",
    )


def install_rate_limiting(app: FastAPI) -> None:
    """Install rate limiting middleware."""
    limiter = get_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


limiter = get_limiter()
