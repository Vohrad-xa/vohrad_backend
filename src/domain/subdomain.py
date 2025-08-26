"""Centralized subdomain extraction utilities."""

from typing import Optional
from fastapi import Request

class SubdomainExtractor:
    """Utility class for extracting subdomain from various sources."""

    @staticmethod
    def from_request(request: Request) -> Optional[str]:
        """Extract subdomain from FastAPI request.

        Args:
            request: FastAPI Request object

        Returns:
            Subdomain string or None if extraction fails

        Examples:
            - "company1.example.com" -> "company1"
            - "api.example.com:8000" -> "api"
            - "localhost:8000" -> None (no subdomain)
        """
        try:
            host = request.headers.get("host", "")
            if not host:
                return None

            host_without_port = host.split(":", 1)[0]

            parts = host_without_port.split(".")

            if len(parts) < 3:
                return None

            return parts[0]

        except (ValueError, AttributeError, IndexError):
            return None

    @staticmethod
    def from_host_string(host: str) -> Optional[str]:
        """Extract subdomain from host string.

        Args:
            host: Host string (e.g., "company1.example.com:8000")

        Returns:
            Subdomain string or None if extraction fails
        """
        try:
            if not host:
                return None

            host_without_port = host.split(":", 1)[0]

            parts = host_without_port.split(".")

            if len(parts) < 3:
                return None

            return parts[0]

        except (ValueError, AttributeError, IndexError):
            return None

    @staticmethod
    def is_valid_subdomain(subdomain: str) -> bool:
        """Validate if subdomain is valid according to RFC standards.

        Args:
            subdomain: Subdomain string to validate

        Returns:
            True if valid, False otherwise
        """
        if not subdomain:
            return False

        if not subdomain.replace("-", "").replace("_", "").isalnum():
            return False

        if subdomain.startswith("-") or subdomain.endswith("-"):
            return False

        if len(subdomain) > 63 or len(subdomain) < 1:
            return False

        return True

def get_subdomain_from_request(request: Request) -> Optional[str]:
    """Backward compatible function for subdomain extraction."""
    return SubdomainExtractor.from_request(request)
