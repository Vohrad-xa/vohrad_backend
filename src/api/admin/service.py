"""Admin service for summaries and paginated calls."""

from .models import Admin
from api.common.base_router import BaseRouterMixin
from api.common.base_service import BaseService
from database.sessions import with_default_db, with_tenant_db
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Any
from web import ResponseFactory


class AdminService(BaseService[Admin, Any, Any]):
    """Admin operations."""

    def __init__(self):
        super().__init__(Admin)


    def get_search_fields(self) -> list[str]:
        """Return searchable fields."""
        return ["email", "first_name", "last_name", "role"]


    async def handle_global_request(self, service_method, pagination, **kwargs):
        """Handle global admin requests (list or summary)."""
        if kwargs.get("scope") == "global":
            async with with_default_db() as shared_db:
                service_class_name = service_method.__self__.__class__.__name__
                if service_class_name == "UserService":
                    return await self.get_multi(shared_db, pagination.page, pagination.size)
                else:
                    return await service_method(shared_db, pagination.page, pagination.size)
        else:
            return await self.get_tenant_summary(service_method, **kwargs)


    async def get_tenant_summary(self, service_method, **kwargs):
        """Get per-tenant count summary for a service."""
        from api.tenant.service import tenant_service

        # Filter out admin-specific params
        service_kwargs = {k: v for k, v in kwargs.items() if k not in ["scope"]}

        # TenantService lives in shared schema; return filtered results
        service_class_name = service_method.__self__.__class__.__name__
        if service_class_name == "TenantService":
            async with with_default_db() as shared_db:
                return await service_method(shared_db, **service_kwargs)

        async with with_default_db() as shared_db:
            if service_class_name == "UserService":
                _, global_count = await self.get_multi(shared_db)
            else:
                global_kwargs = {k: v for k, v in service_kwargs.items() if k != "tenant_id"}
                _, global_count = await service_method(shared_db, **global_kwargs)

            tenants, _ = await tenant_service.get_multi(shared_db)

        tenant_summary = []
        total_tenant_items = 0

        for tenant in tenants:
            try:
                async with with_tenant_db(tenant.tenant_schema_name) as tenant_db:
                    _, tenant_count = await service_method(tenant_db, **service_kwargs)
                    tenant_summary.append(
                        {"tenant_id": str(tenant.tenant_id), "tenant_name": tenant.tenant_schema_name, "count": tenant_count}
                    )
                    total_tenant_items += tenant_count
            except (ProgrammingError, OperationalError, Exception):

                tenant_summary.append(
                    {
                        "tenant_id"  : str(tenant.tenant_id),
                        "tenant_name": tenant.tenant_schema_name,
                        "count"      : 0,
                        "error"      : "schema_or_table_missing",
                    }  # Ignore errors for missing schemas/tables
                )

        return {
            "global_count"  : global_count,
            "tenant_summary": tenant_summary,
            "total_tenants" : len(tenants),
            "total_items"   : global_count + total_tenant_items,
        }


    async def get_admin_context_info(self, context):
        """Get admin context information with role checks."""
        from security.authorization.service import AuthorizationService

        authorization_service = AuthorizationService()

        has_super_admin = await authorization_service.user_has_role(context.user_id, "super_admin")
        has_admin = await authorization_service.user_has_role(context.user_id, "admin")

        admin_roles = []
        if has_super_admin:
            admin_roles.append("super_admin")
        if has_admin:
            admin_roles.append("admin")

        return {
            "admin_user_id"        : str(context.user_id),
            "current_tenant_id"    : str(context.tenant_id) if context.tenant_id else None,
            "current_tenant_schema": context.tenant_schema,
            "is_tenant_context"    : context.is_tenant_context,
            "admin_roles"          : admin_roles,
        }


    async def paginated_call(
        self,
        context,
        service_method,
        pagination,
        response_class,
        **kwargs
    ):
        """Execute paginated service call with admin context."""
        if context.is_global_context:
            result = await self.handle_global_request(service_method, pagination, **kwargs)
            if isinstance(result, tuple):
                items, total = result
                return BaseRouterMixin.create_paginated_response(items, total, pagination, response_class)
            else:
                from web import PaginationUtil

                paginated_result = PaginationUtil.paginate_query_result([result], 1, pagination.page, pagination.size)
                return ResponseFactory.paginated(paginated_result)

        # When in tenant context (with ?tenant_id=xyz), return normal paginated results
        service_kwargs = {k: v for k, v in kwargs.items() if k not in ["scope"]}
        items, total = await service_method(context.db_session, pagination.page, pagination.size, **service_kwargs)
        return BaseRouterMixin.create_paginated_response(items, total, pagination, response_class)


admin_service = AdminService()
