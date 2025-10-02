"""Item router."""

from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.item.schema import ItemResponse
from api.item.service import item_service
from exceptions import ExceptionFactory
from fastapi import APIRouter, Depends, Query
from uuid import UUID
from web import PaginatedResponse, PaginationParams, ResponseFactory, SuccessResponse, pagination_params

routes = APIRouter(
    tags=["items"],
    prefix="/items",
)


@routes.get("/", response_model=SuccessResponse[PaginatedResponse[ItemResponse]])
async def get_items(
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Get paginated list of items"""
    _, tenant, db = context
    items, total = await item_service.get_items_paginated(db, pagination.page, pagination.size, tenant)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, ItemResponse)


@routes.get("/search", response_model=SuccessResponse[PaginatedResponse[ItemResponse]])
async def search_items(
    q: str = Query(..., min_length=2, description="Search term"),
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Search items by name, code, description, barcode, or serial number"""
    _, tenant, db = context
    items, total = await item_service.search_items(db, q, pagination.page, pagination.size, tenant)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, ItemResponse)


@routes.get("/code/{code}", response_model=SuccessResponse[ItemResponse])
async def get_item_by_code(
    code: str,
    context=Depends(get_tenant_context),
):
    """Get item by code"""
    _, tenant, db = context
    item = await item_service.get_item_by_code(db, code, tenant)
    if not item:
        raise ExceptionFactory.not_found("Item", code)
    return ResponseFactory.success(item, response_model=ItemResponse)


@routes.get("/barcode/{barcode}", response_model=SuccessResponse[ItemResponse])
async def get_item_by_barcode(
    barcode: str,
    context=Depends(get_tenant_context),
):
    """Get item by barcode"""
    _, tenant, db = context
    item = await item_service.get_item_by_barcode(db, barcode, tenant)
    if not item:
        raise ExceptionFactory.not_found("Item", barcode)
    return ResponseFactory.success(item, response_model=ItemResponse)


@routes.get("/serial/{serial_number}", response_model=SuccessResponse[ItemResponse])
async def get_item_by_serial(
    serial_number: str,
    context=Depends(get_tenant_context),
):
    """Get item by serial number"""
    _, tenant, db = context
    item = await item_service.get_item_by_serial(db, serial_number, tenant)
    if not item:
        raise ExceptionFactory.not_found("Item", serial_number)
    return ResponseFactory.success(item, response_model=ItemResponse)


@routes.get("/tracking/{tracking_mode}", response_model=SuccessResponse[PaginatedResponse[ItemResponse]])
async def get_items_by_tracking_mode(
    tracking_mode: str,
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Get items filtered by tracking mode (abstract, standard, serialized)"""
    _, tenant, db = context
    items, total = await item_service.get_items_by_tracking_mode(db, tracking_mode, pagination.page, pagination.size, tenant)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, ItemResponse)


@routes.get("/active", response_model=SuccessResponse[PaginatedResponse[ItemResponse]])
async def get_active_items(
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Get active items only"""
    _, tenant, db = context
    items, total = await item_service.get_active_items(db, pagination.page, pagination.size, tenant)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, ItemResponse)


@routes.get("/{item_id}", response_model=SuccessResponse[ItemResponse])
async def get_item(
    item_id: UUID,
    context=Depends(get_tenant_context),
):
    """Get item by ID"""
    _, tenant, db = context
    item = await item_service.get_item_by_id(db, item_id, tenant)  # auto-raises if not found
    return ResponseFactory.success(item, response_model=ItemResponse)
