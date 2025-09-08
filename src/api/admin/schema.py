"""Admin API response schemas."""

from api.tenant.schema import TenantResponse
from api.user.schema import UserResponse
from pydantic import BaseModel
from typing import List
from web import PaginatedResponse


class AdminTenantListResponse(PaginatedResponse[TenantResponse]):
    """Paginated response for admin tenant list."""

    pass


class AdminUserListResponse(PaginatedResponse[UserResponse]):
    """Paginated response for admin user list."""

    pass


class TenantContextResponse(BaseModel):
    """Current tenant context for admin dashboard."""

    admin_user_id: str
    current_tenant_id: str | None
    admin_roles: List[str]
