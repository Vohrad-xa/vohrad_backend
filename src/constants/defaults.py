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


class SecurityDefaults:
    """Security-related default values."""

    BCRYPT_MIN_ROUNDS       : Final[int] = 12
    BUSINESS_HOUR_START     : Final[int] = 9
    BUSINESS_HOUR_END       : Final[int] = 17
    HSTS_MAX_AGE_SECONDS    : Final[int] = 31536000  # 1 year


class CacheDefaults:
    """Cache-related default values."""

    LRU_MAX_SIZE            : Final[int] = 1000
    LRU_TTL_SECONDS         : Final[int] = 3600
    USER_CACHE_MAX_SIZE     : Final[int] = 10000
    USER_CACHE_TTL_SECONDS  : Final[int] = 900


class LicenseDefaults:
    """License-related default values."""

    LICENSE_KEY_PREFIX      : Final[str] = "VRDX"
    LICENSE_KEY_SEGMENT_SIZE: Final[int] = 4
    LICENSE_KEY_SEGMENTS    : Final[int] = 6
    LICENSE_KEY_MAX_ATTEMPTS: Final[int] = 10
