"""Application default values and configuration constants."""

from typing import Final


class TenantDefaults:
    """Default values for tenant-related functionality."""

    DEFAULT_STATUS      : Final[str]       = "active"
    ALLOWED_STATUSES    : Final[list[str]] = ["active", "inactive", "suspended"]
    MAX_SUBDOMAIN_LENGTH: Final[int]       = 63
    MIN_SUBDOMAIN_LENGTH: Final[int]       = 2


class PaginationDefaults:
    """Default values for pagination."""

    DEFAULT_PAGE     : Final[int] = 1
    DEFAULT_PAGE_SIZE: Final[int] = 20
    MAX_PAGE_SIZE    : Final[int] = 100
    MIN_PAGE_SIZE    : Final[int] = 1


class DatabaseDefaults:
    """Database-related default values."""

    CONNECTION_TIMEOUT: Final[int] = 30
    POOL_SIZE         : Final[int] = 10
    MAX_OVERFLOW      : Final[int] = 20
    POOL_RECYCLE_TIME : Final[int] = 3600  # 1 hour
