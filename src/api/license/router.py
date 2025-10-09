"""License routes for tenant users."""

from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_shared_context
from api.license.schema import LicenseResponse
from api.license.service import license_service
from fastapi import APIRouter, Depends
from web import PaginatedResponse, SuccessResponse
from web.pagination import PaginationParams, pagination_params

routes = APIRouter(
    tags   = ["licenses"],
    prefix = "/licenses",
)


@routes.get("/", response_model=SuccessResponse[PaginatedResponse[LicenseResponse]])
async def list_tenant_licenses(
    pagination: PaginationParams = Depends(pagination_params),
    context = Depends(get_shared_context),
):
    """List all licenses for the current tenant."""
    _current_user, tenant, db = context
    licenses, total = await license_service.get_multi(
        db,
        pagination.page,
        pagination.size,
        tenant_id = tenant.tenant_id
    )
    return BaseRouterMixin.create_paginated_response(
        licenses,
        total,
        pagination,
        LicenseResponse
    )
