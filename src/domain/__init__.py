"""Domain utilities for tenant/subdomain handling and business logic."""

from .subdomain import SubdomainExtractor
from .subdomain import get_subdomain_from_request

__all__ = ["SubdomainExtractor", "get_subdomain_from_request"]
