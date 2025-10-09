"""Admin routes with tenant context switching."""

from .dependencies import get_admin_params
from .service import admin_service
from api.license import LicenseCreate, LicenseResponse, license_service
from api.permission import PermissionResponse, permission_service
from api.role import RoleResponse, role_service
from api.stripe import stripe_payment_service
from api.tenant import TenantResponse, TenantUpdate, tenant_service
from api.user.schema import UserResponse
from api.user.service import user_service
from exceptions import ExceptionFactory
from fastapi import APIRouter, Depends, Query, status
from typing import Any, Optional
from uuid import UUID
from web import (
    CreatedResponse,
    DeletedResponse,
    PaginatedResponse,
    ResponseFactory,
    SuccessResponse,
    UpdatedResponse,
)

routes = APIRouter(
    tags   = ["admin"],
    prefix = "/admin",
)


@routes.get("/tenants", response_model = SuccessResponse[PaginatedResponse[Any]])
async def list_all_tenants(params = Depends(get_admin_params)):
    """List all tenants."""
    pagination, context = params
    return await admin_service.paginated_call(
        context, tenant_service.get_multi, pagination, TenantResponse
    )


@routes.get("/users", response_model=SuccessResponse[PaginatedResponse[Any]])
async def list_users(
    params = Depends(get_admin_params),
    scope: Optional[str] = Query(None)
):
    """List global users or tenant users."""
    pagination, context = params
    return await admin_service.paginated_call(
        context,
        user_service.get_multi,
        pagination,
        UserResponse,
        tenant_id = context.tenant_id,
        scope     = scope
    )


@routes.get("/roles", response_model=SuccessResponse[PaginatedResponse[Any]])
async def list_all_roles(
    params = Depends(get_admin_params),
    scope: Optional[str] = Query(None)
):
    """List all roles."""
    pagination, context = params
    return await admin_service.paginated_call(
        context,
        role_service.get_multi,
        pagination,
        RoleResponse,
        scope=scope
    )


@routes.get("/permissions", response_model = SuccessResponse[PaginatedResponse[Any]])
async def list_all_permissions(
    params = Depends(get_admin_params),
    scope: Optional[str] = Query(None)
):
    """List all permissions."""
    pagination, context = params
    return await admin_service.paginated_call(
        context,
        permission_service.get_multi,
        pagination,
        PermissionResponse,
        scope=scope
    )


@routes.put("/tenants/{tenant_id}", response_model=UpdatedResponse[TenantResponse])
async def update_tenant(
    tenant_id  : UUID,
    tenant_data: TenantUpdate,
    params = Depends(get_admin_params)
) -> SuccessResponse[TenantResponse]:
    """Update tenant by ID (admin access only)."""
    _, context = params
    updated_tenant = await tenant_service.update_tenant_by_id(context.db_session, tenant_id, tenant_data)
    return ResponseFactory.updated(updated_tenant, response_model=TenantResponse)


@routes.delete("/tenants/{tenant_id}", response_model = DeletedResponse)
async def delete_tenant(
    tenant_id: UUID,
    params = Depends(get_admin_params)
) -> DeletedResponse:
    """Delete tenant."""
    _, context = params
    await tenant_service.delete_tenant_by_id(context.db_session, tenant_id)
    return ResponseFactory.deleted("tenant")


@routes.get("/tenant-context", response_model = SuccessResponse[dict])
async def get_current_tenant_context(params = Depends(get_admin_params)):
    """Get current tenant context."""
    _, context = params
    context_info = await admin_service.get_admin_context_info(context)
    return ResponseFactory.success(context_info)


@routes.post(
    "/licenses",
    status_code    = status.HTTP_201_CREATED,
    response_model = CreatedResponse[LicenseResponse],
)
async def create_license(
    license_data: LicenseCreate,
    params=Depends(get_admin_params),
):
    """Create new license (admin only)."""
    _, context = params
    license_obj: LicenseResponse = await license_service.create_license(context.db_session, license_data)
    return ResponseFactory.created(license_obj, response_model=LicenseResponse)


@routes.get(
    "/licenses",
    response_model = SuccessResponse[PaginatedResponse[Any]]
)
async def list_all_licenses(params=Depends(get_admin_params)):
    """List all licenses (admin only)."""
    pagination, context = params
    return await admin_service.paginated_call(context, license_service.get_multi, pagination, LicenseResponse)


@routes.put(
    "/tenants/{tenant_id}/license",
    response_model=UpdatedResponse[TenantResponse]
)
async def assign_tenant_license(
    tenant_id : UUID,
    license_id: UUID = Query(..., description="License ID to assign to tenant"),
    params = Depends(get_admin_params),
):
    """Assign/update license for a tenant (admin only)."""
    _, context = params
    await license_service.activate_license(context.db_session, license_id)
    updated_tenant = await tenant_service.get_tenant_by_id(context.db_session, tenant_id)
    return ResponseFactory.updated(updated_tenant, response_model=TenantResponse)


@routes.post(
    "/tenants/{tenant_id}/license/activate",
    response_model = UpdatedResponse[TenantResponse]
)
async def activate_tenant_license(
    tenant_id: UUID,
    params = Depends(get_admin_params),
):
    """Activate tenant's current license (admin only)."""
    _, context = params
    tenant = await tenant_service.get_tenant_by_id(context.db_session, tenant_id)
    if not tenant.license_id:
        raise ExceptionFactory.business_rule("Tenant does not have a license assigned", {"tenant_id": str(tenant_id)})
    await license_service.activate_license(context.db_session, tenant.license_id)
    updated_tenant = await tenant_service.get_tenant_by_id(context.db_session, tenant_id)
    return ResponseFactory.updated(updated_tenant, response_model=TenantResponse)


@routes.post(
    "/tenants/{tenant_id}/license/suspend",
    response_model = UpdatedResponse[TenantResponse]
)
async def suspend_tenant_license(
    tenant_id: UUID,
    params=Depends(get_admin_params),
):
    """Suspend tenant's license (admin only)."""
    _, context = params
    tenant = await tenant_service.get_tenant_by_id(context.db_session, tenant_id)
    if not tenant.license_id:
        raise ExceptionFactory.business_rule("Tenant does not have a license assigned", {"tenant_id": str(tenant_id)})
    await license_service.suspend_license(context.db_session, tenant.license_id)
    updated_tenant = await tenant_service.get_tenant_by_id(context.db_session, tenant_id)
    return ResponseFactory.updated(updated_tenant, response_model=TenantResponse)


@routes.get(
    "/tenants/{tenant_id}/license-info",
    response_model = SuccessResponse[dict]
)
async def get_tenant_license_info(
    tenant_id: UUID,
    params=Depends(get_admin_params),
):
    """Get license information for a tenant including seat usage (admin only)."""
    _, context = params
    tenant = await tenant_service.get_tenant_by_id(context.db_session, tenant_id)
    license_info: dict = await license_service.get_tenant_license_info(context.db_session, tenant)
    return ResponseFactory.success(license_info)


@routes.post(
    "/licenses/{license_id}/invoice",
    response_model = SuccessResponse[dict]
)
async def create_license_invoice(
    license_id: UUID,
    params=Depends(get_admin_params),
):
    """Create and send Stripe invoice for license (admin only)."""
    _, context = params

    result: dict = await stripe_payment_service.process_invoice_flow(context.db_session, license_id)

    if result["code"] == "already_active":
        return ResponseFactory.success(result["payload"])

    if result["code"] == "activated":
        return ResponseFactory.success(result["payload"])

    if result["code"] == "invoice_pending":
        return ResponseFactory.success(result["payload"])

    return ResponseFactory.success(result["payload"])
