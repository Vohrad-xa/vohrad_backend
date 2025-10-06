"""Tenant router."""

from api.common.context_dependencies import get_authenticated_context, get_shared_context
from api.permission.dependencies import require_permission
from api.tenant.schema import TenantResponse, TenantSettingsUpdate, TenantUpdate
from api.tenant.service import tenant_service
from fastapi import APIRouter, Depends
from web import (
    ResponseFactory,
    SuccessResponse,
    UpdatedResponse,
)

routes = APIRouter(
    tags   = ["tenant"],
    prefix = "/tenant",
)


@routes.get("/", response_model=SuccessResponse[TenantResponse])
async def get_current_tenant_endpoint(context=Depends(get_authenticated_context)):
    """Get the current tenant"""
    _user, tenant = context
    return ResponseFactory.success(tenant, response_model=TenantResponse)


@routes.put("/settings", response_model=UpdatedResponse[TenantResponse])
async def update_tenant_settings(
    settings: TenantSettingsUpdate,
    context = Depends(get_shared_context),
    _authorized: bool = Depends(require_permission("tenant", "manage")),
):
    """Allow tenant managers to update timezone and working hours for their own tenant."""
    _current_user, tenant, db = context

    data   = settings.model_dump(exclude_unset=True)
    update = TenantUpdate(**data)

    updated = await tenant_service.update_tenant(db, tenant, update)
    return ResponseFactory.updated(updated, response_model=TenantResponse)
