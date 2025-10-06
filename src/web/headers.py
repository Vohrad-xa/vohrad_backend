"""Header helpers for declarative routers."""

from fastapi import Header
from typing import Optional


def get_if_match_header(if_match: Optional[str] = Header(None, alias="If-Match")) -> Optional[str]:
    """Return If-Match header for optimistic concurrency."""
    return if_match
