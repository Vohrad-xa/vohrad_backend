"""ItemLocation router."""

from .schema import ItemLocationCreate, ItemLocationResponse
from .service import item_location_service
from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.permission.dependencies import RequireItemCreate
from fastapi import APIRouter, Depends, status
from web import (
    CreatedResponse,
    PaginatedResponse,
    PaginationParams,
    ResponseFactory,
    SuccessResponse,
    pagination_params,
)

routes = APIRouter(
    tags   = ["item-locations"],
    prefix = "/item-locations",
)


@routes.post(
    "/",
    status_code    = status.HTTP_201_CREATED,
    response_model = CreatedResponse[ItemLocationResponse],
)
async def create_item_location(
    item_location_data: ItemLocationCreate,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireItemCreate),
):
    """Add item to a location"""
    _, _, db = context
    item_location = await item_location_service.create_item_location(db, item_location_data)
    return ResponseFactory.created(item_location, response_model=ItemLocationResponse)


@routes.get("/", response_model=SuccessResponse[PaginatedResponse[ItemLocationResponse]])
async def get_item_locations(
    pagination: PaginationParams = Depends(pagination_params),
    context = Depends(get_tenant_context),
):
    """Get list of item locations"""
    _, _, db = context
    item_locations, total = await item_location_service.get_item_locations(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(item_locations, total, pagination, ItemLocationResponse)
