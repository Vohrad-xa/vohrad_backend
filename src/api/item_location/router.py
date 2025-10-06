"""ItemLocation router."""

from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.item_location.schema import ItemLocationResponse
from api.item_location.service import item_location_service
from fastapi import APIRouter, Depends
from web import (
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
    pagination_params,
)

routes = APIRouter(
    tags   = ["item-locations"],
    prefix = "/item-locations",
)


@routes.get("/", response_model=SuccessResponse[PaginatedResponse[ItemLocationResponse]])
async def get_item_locations(
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Get paginated list of item locations"""
    _, _, db = context
    item_locations, total = await item_location_service.get_item_locations_paginated(
        db, pagination.page, pagination.size
    )
    return BaseRouterMixin.create_paginated_response(item_locations, total, pagination, ItemLocationResponse)
