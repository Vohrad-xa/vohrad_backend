"""Item service."""

from api.common import BaseService
from api.item.models import Item
from api.item.schema import ItemCreate, ItemUpdate
from api.tenant.models import Tenant
from database.constraint_handler import constraint_handler
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, NoReturn, Optional
from uuid import UUID


class ItemService(BaseService[Item, ItemCreate, ItemUpdate]):
    """Item operations."""

    def __init__(self):
        super().__init__(Item)


    def get_search_fields(self) -> list[str]:
        return ["name", "code", "description", "barcode", "serial_number"]


    async def get_item_by_id(self, db: AsyncSession, item_id: UUID, tenant: Tenant) -> Item:
        """Get item by ID."""
        return await self.get_by_id(db, item_id, tenant.tenant_id)


    async def get_item_by_code(self, db: AsyncSession, code: str, tenant: Tenant) -> Optional[Item]:
        """Get item by code."""
        return await self.get_by_field(db, "code", code, tenant.tenant_id)


    async def get_item_by_barcode(self, db: AsyncSession, barcode: str, tenant: Tenant) -> Optional[Item]:
        """Get item by barcode."""
        return await self.get_by_field(db, "barcode", barcode, tenant.tenant_id)


    async def get_item_by_serial(self, db: AsyncSession, serial_number: str, tenant: Tenant) -> Optional[Item]:
        """Get item by serial number."""
        return await self.get_by_field(db, "serial_number", serial_number, tenant.tenant_id)


    async def get_items_paginated(
        self, db: AsyncSession, page: int = 1, size: int = 20, tenant: Tenant = None
    ) -> tuple[list[Item], int]:
        """Get paginated list of items."""
        tenant_id = tenant.tenant_id if tenant else None
        return await self.get_multi(db, page, size, tenant_id)


    async def search_items(
        self, db: AsyncSession, search_term: str, page: int = 1, size: int = 20, tenant: Tenant = None
    ) -> tuple[list[Item], int]:
        """Search items by name, code, description, barcode, or serial number."""
        tenant_id = tenant.tenant_id if tenant else None
        return await self.search(db, search_term, page, size, tenant_id)


    async def get_items_by_tracking_mode(
        self, db: AsyncSession, tracking_mode: str, page: int = 1, size: int = 20, tenant: Tenant = None
    ) -> tuple[list[Item], int]:
        """Get items filtered by tracking mode."""
        tenant_id = tenant.tenant_id if tenant else None
        filters = Item.tracking_mode == tracking_mode
        return await self.get_filtered(db, filters, page, size, tenant_id)


    async def get_active_items(
        self, db: AsyncSession, page: int = 1, size: int = 20, tenant: Tenant = None
    ) -> tuple[list[Item], int]:
        """Get active items only."""
        tenant_id = tenant.tenant_id if tenant else None
        filters = Item.is_active == True  # noqa: E712
        return await self.get_filtered(db, filters, page, size, tenant_id)


    async def _handle_integrity_error(
        self, error: IntegrityError, operation_context: dict[str, Any]
    ) -> NoReturn:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


item_service = ItemService()
