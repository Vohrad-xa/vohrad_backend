"""Item router."""

from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.item.schema import ItemCreate, ItemDetailResponse, ItemResponse, ItemUpdate
from api.item.service import item_service
from api.item_location.schema import ItemLocationResponse, ItemLocationUpdate
from api.item_location.service import item_location_service
from exceptions import ExceptionFactory
from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from web import (
    CreatedResponse,
    DeletedResponse,
    PaginatedResponse,
    PaginationParams,
    ResponseFactory,
    SuccessResponse,
    UpdatedResponse,
    pagination_params,
)

routes = APIRouter(
    tags   = ["items"],
    prefix = "/items",
)


@routes.post(
    "/",
    status_code    = status.HTTP_201_CREATED,
    response_model = CreatedResponse[ItemResponse],
)
async def create_item(
    item_data: ItemCreate,
    context=Depends(get_tenant_context),
):
    """Create new item"""
    current_user, _, db = context
    item = await item_service.create_item(db, item_data, current_user)
    return ResponseFactory.created(item, response_model=ItemResponse)


@routes.get("/", response_model=SuccessResponse[PaginatedResponse[ItemResponse]])
async def get_items(
    pagination: PaginationParams = Depends(pagination_params),
    odata_filter: str | None = Query(None, description="OData filter expression"),
    context=Depends(get_tenant_context),
):
    """Get paginated list of items with optional OData filtering"""
    _, _, db = context

    if odata_filter:
        items, total = await item_service.get_items_with_filter(db, odata_filter, pagination.page, pagination.size)
    else:
        items, total = await item_service.get_items_for_list(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, ItemResponse)


@routes.get("/search", response_model=SuccessResponse[PaginatedResponse[ItemResponse]])
async def search_items(
    q: str = Query(..., min_length=2, description="Search term"),
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Search items by name, code, description, barcode, or serial number"""
    _, _, db = context
    items, total = await item_service.search_items(db, q, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, ItemResponse)


@routes.get("/code/{code}", response_model=SuccessResponse[ItemDetailResponse])
async def get_item_by_code(
    code: str,
    context=Depends(get_tenant_context),
):
    """Get item by code"""
    _, _, db = context
    item = await item_service.get_item_by_code(db, code)
    if not item:
        raise ExceptionFactory.not_found("Item", code)
    return ResponseFactory.success(item, response_model=ItemDetailResponse)


@routes.get("/barcode/{barcode}", response_model=SuccessResponse[ItemDetailResponse])
async def get_item_by_barcode(
    barcode: str,
    context=Depends(get_tenant_context),
):
    """Get item by barcode"""
    _, _, db = context
    item = await item_service.get_item_by_barcode(db, barcode)
    if not item:
        raise ExceptionFactory.not_found("Item", barcode)
    return ResponseFactory.success(item, response_model=ItemDetailResponse)


@routes.get("/serial/{serial_number}", response_model=SuccessResponse[ItemDetailResponse])
async def get_item_by_serial(
    serial_number: str,
    context=Depends(get_tenant_context),
):
    """Get item by serial number"""
    _, _, db = context
    item = await item_service.get_item_by_serial(db, serial_number)
    if not item:
        raise ExceptionFactory.not_found("Item", serial_number)
    return ResponseFactory.success(item, response_model=ItemDetailResponse)


@routes.get("/tracking/{tracking_mode}", response_model=SuccessResponse[PaginatedResponse[ItemResponse]])
async def get_items_by_tracking_mode(
    tracking_mode: str,
    pagination   : PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Get items filtered by tracking mode (abstract, standard, serialized)"""
    _, _, db = context
    items, total = await item_service.get_items_by_tracking_mode(db, tracking_mode, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, ItemResponse)


@routes.get("/active", response_model=SuccessResponse[PaginatedResponse[ItemResponse]])
async def get_active_items(
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Get active items only"""
    _, _, db = context
    items, total = await item_service.get_active_items(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, ItemResponse)


@routes.get("/{item_id}", response_model=SuccessResponse[ItemDetailResponse])
async def get_item(
    item_id: UUID,
    context=Depends(get_tenant_context),
):
    """Get item by ID"""
    _, _, db = context
    item = await item_service.get_item_for_detail(db, item_id)
    return ResponseFactory.success(item, response_model=ItemDetailResponse)


@routes.put("/{item_id}", response_model=UpdatedResponse[ItemResponse])
async def update_item(
    item_id  : UUID,
    item_data: ItemUpdate,
    context=Depends(get_tenant_context),
):
    """Update item"""
    _, _, db = context
    item = await item_service.update_item(db, item_id, item_data)
    return ResponseFactory.updated(item, response_model=ItemResponse)


@routes.delete("/{item_id}", response_model=DeletedResponse)
async def delete_item(
    item_id: UUID,
    context=Depends(get_tenant_context),
):
    """Delete item"""
    _, _, db = context
    await item_service.delete_item(db, item_id)
    return ResponseFactory.deleted("item")


@routes.put("/{item_id}/locations/{location_id}", response_model=UpdatedResponse[ItemLocationResponse])
async def update_item_location(
    item_id           : UUID,
    location_id       : UUID,
    item_location_data: ItemLocationUpdate,
    context=Depends(get_tenant_context),
):
    """Update item quantity at a specific location"""
    _, _, db = context
    item_location = await item_location_service.update_by_item_and_location(
        db, item_id, location_id, item_location_data
    )
    return ResponseFactory.updated(item_location, response_model=ItemLocationResponse)


@routes.delete("/{item_id}/locations/{location_id}", response_model=DeletedResponse)
async def delete_item_from_location(
    item_id    : UUID,
    location_id: UUID,
    context=Depends(get_tenant_context),
):
    """Remove item from a specific location"""
    _, _, db = context
    await item_location_service.delete_by_item_and_location(db, item_id, location_id)
    return ResponseFactory.deleted("item from location")
