"""Centralized subdomain extraction utilities."""

from constants import TenantDefaults, ValidationConstraints
from fastapi import Request
from typing import Optional


class SubdomainExtractor:
    """Utility class for extracting subdomain from various sources."""

    @staticmethod
    def from_request(request: Request) -> Optional[str]:
        """Extract subdomain from FastAPI request."""
        # header added for development and testing purposes
        subdomain = request.headers.get("x-tenant-subdomain")
        if subdomain:
            return subdomain
        try:
            host = request.headers.get("host", "")
            if not host:
                return None

            host_without_port = host.split(":", 1)[0]

            parts = host_without_port.split(".")

            # Development: allow subdomain.localhost (e.g., amine2.localhost)
            if len(parts) == 2 and parts[1] == "localhost":
                return parts[0]

            # Production: require subdomain.domain.tld (e.g., amine2.example.com)
            if len(parts) < 3:
                return None

            return parts[0]

        except (ValueError, AttributeError, IndexError):
            return None

    @staticmethod
    def from_host_string(host: str) -> Optional[str]:
        """Extract subdomain from the host string."""
        try:
            if not host:
                return None

            host_without_port = host.split(":", 1)[0]

            parts = host_without_port.split(".")

            # Development: allow subdomain.localhost
            if len(parts) == 2 and parts[1] == "localhost":
                return parts[0]

            # Production: require subdomain.domain.tld
            if len(parts) < 3:
                return None

            return parts[0]

        except (ValueError, AttributeError, IndexError):
            return None

    @staticmethod
    def is_valid_subdomain(subdomain: str) -> bool:
        """Validate if the subdomain is valid, according to RFC standards."""
        if not subdomain:
            return False

        if not subdomain.replace("-", "").replace("_", "").isalnum():
            return False

        if subdomain.startswith("-") or subdomain.endswith("-"):
            return False

        if len(subdomain) > TenantDefaults.MAX_SUBDOMAIN_LENGTH or len(subdomain) < ValidationConstraints.MIN_SUBDOMAIN_LENGTH:
            return False

        return True


def get_subdomain_from_request(request: Request) -> Optional[str]:
    """Backward compatible function for subdomain extraction."""
    return SubdomainExtractor.from_request(request)
