"""Item service."""

from api.common import BaseService
from api.item.models import Item
from api.item.schema import ItemCreate, ItemUpdate
from database.constraint_handler import constraint_handler
from security.jwt import AuthenticatedUser
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


    async def create_item(self, db: AsyncSession, item_data: ItemCreate, current_user: AuthenticatedUser) -> Item:
        """Create a new item."""
        try:
            item_dict            = item_data.model_dump()
            item_dict["user_id"] = current_user.user_id
            item                 = Item(**item_dict)
            db.add(item)
            await db.commit()
            await db.refresh(item)
            return item

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e, {
                    "operation"    : "create_item",
                    "code"         : item_data.code,
                    "serial_number": item_data.serial_number
                   }
            )


    async def get_item_by_id(self, db: AsyncSession, item_id: UUID) -> Item:
        """Get item by ID."""
        return await self.get_by_id(db, item_id)


    async def get_item_by_code(self, db: AsyncSession, code: str) -> Optional[Item]:
        """Get item by code."""
        return await self.get_by_field(db, "code", code)


    async def get_item_by_barcode(self, db: AsyncSession, barcode: str) -> Optional[Item]:
        """Get item by barcode."""
        return await self.get_by_field(db, "barcode", barcode)


    async def get_item_by_serial(self, db: AsyncSession, serial_number: str) -> Optional[Item]:
        """Get item by serial number."""
        return await self.get_by_field(db, "serial_number", serial_number)


    async def get_items_paginated(self, db: AsyncSession, page: int = 1, size: int = 20) -> tuple[list[Item], int]:
        """Get paginated list of items."""
        return await self.get_multi(db, page, size)


    async def search_items(
        self, db: AsyncSession, search_term: str, page: int = 1, size: int = 20
    ) -> tuple[list[Item], int]:
        """Search items by name, code, description, barcode, or serial number."""
        return await self.search(db, search_term, page, size)


    async def get_items_by_tracking_mode(
        self, db: AsyncSession, tracking_mode: str, page: int = 1, size: int = 20
    ) -> tuple[list[Item], int]:
        """Get items filtered by tracking mode."""
        filters = Item.tracking_mode == tracking_mode
        return await self.get_filtered(db, filters, page, size)


    async def get_active_items(self, db: AsyncSession, page: int = 1, size: int = 20) -> tuple[list[Item], int]:
        """Get active items only."""
        filters = Item.is_active == True  # noqa: E712
        return await self.get_filtered(db, filters, page, size)


    async def update_item(self, db: AsyncSession, item_id: UUID, item_data: ItemUpdate) -> Item:
        """Update an item."""
        try:
            return await self.update(db, item_id, item_data)
        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e, {
                    "operation": "update_item",
                    "item_id": str(item_id)
                }
            )


    async def _handle_integrity_error(
        self, error: IntegrityError, operation_context: dict[str, Any]
    ) -> NoReturn:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


item_service = ItemService()
