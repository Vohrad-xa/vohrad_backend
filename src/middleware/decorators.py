"""Utility decorators for common patterns."""

from database.sessions import get_default_db_session, get_tenant_db_session
from exceptions import tenant_not_found, user_not_found
from functools import wraps
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


def with_database_session(session_type: str = "tenant"):
    """Async decorator to automatically manage database sessions."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if "db_context" in kwargs:
                db_context = kwargs.pop("db_context")
                async for db in db_context:
                    result = await func(db, *args, **kwargs)
                    break
                return result
            else:
                session_func = get_tenant_db_session if session_type == "tenant" else get_default_db_session
                async for db in session_func():
                    result = await func(db, *args, **kwargs)
                    break
                return result

        return wrapper

    return decorator


def handle_service_exceptions(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Decorator to handle common service exceptions consistently."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if hasattr(e, "status_code"):
                raise

            error_msg = str(e).lower()
            if "not found" in error_msg:
                if "user" in func.__name__.lower():
                    raise user_not_found() from e
                elif "tenant" in func.__name__.lower():
                    raise tenant_not_found() from e
            raise

    return wrapper
