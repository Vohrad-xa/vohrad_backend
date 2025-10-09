"""Admin service for paginated calls with admin context."""

from .models import Admin
from api.common import BaseRouterMixin, BaseService
from database import with_default_db
from typing import Any


class AdminService(BaseService[Admin, Any, Any]):
    """Admin operations."""

    def __init__(self):
        super().__init__(Admin)


    def get_search_fields(self) -> list[str]:
        """Return searchable fields."""
        return ["email", "first_name", "last_name", "role"]


    async def paginated_call(
        self,
        db_session,
        service_method,
        pagination,
        response_class,
        **kwargs
    ):
        """Execute paginated service call with admin database session."""
        # LicenseService always uses shared schema (licenses are global)
        service_class_name = service_method.__self__.__class__.__name__

        if service_class_name == "LicenseService":
            async with with_default_db() as shared_db:
                items, total = await service_method(shared_db, pagination.page, pagination.size, **kwargs)
                return BaseRouterMixin.create_paginated_response(items, total, pagination, response_class)

        # All other services use provided db_session (tenant-aware via get_admin_db_session)
        items, total = await service_method(db_session, pagination.page, pagination.size, **kwargs)
        return BaseRouterMixin.create_paginated_response(items, total, pagination, response_class)


admin_service = AdminService()
