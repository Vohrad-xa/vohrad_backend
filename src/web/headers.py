"""Small header dependencies to keep routers declarative and logic-free."""

from fastapi import Header
from typing import Optional


def get_if_match_header(if_match: Optional[str] = Header(None, alias="If-Match")) -> Optional[str]:
    """Expose the If-Match header value for optimistic concurrency when present.

    Explanation: Routers can depend on this to retrieve the header without embedding
    conditional logic. Services remain the place where ETag checks are enforced.
    """
    return if_match
