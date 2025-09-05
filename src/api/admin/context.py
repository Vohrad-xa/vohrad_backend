"""Admin context management for tenant switching and access control."""

from dataclasses import dataclass
from security.jwt import AuthenticatedUser
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID


@dataclass
class AdminContext:
    """Admin context with tenant switching capabilities."""

    user: AuthenticatedUser
    db_session: AsyncSession
    tenant_id: Optional[UUID] = None
    tenant_schema: Optional[str] = None

    @property
    def is_tenant_context(self) -> bool:
        """True if operating in tenant context."""
        return self.tenant_id is not None

    @property
    def is_global_context(self) -> bool:
        """True if operating in global context."""
        return self.tenant_id is None

    @property
    def user_id(self) -> UUID:
        """Admin user ID."""
        return self.user.user_id

    def __post_init__(self):
        """Initialize session context markers."""
        self.db_session._admin_context = True
        self.db_session._admin_user_id = self.user.user_id
        if self.tenant_id:
            self.db_session._tenant_id = self.tenant_id
            self.db_session._tenant_schema = self.tenant_schema
