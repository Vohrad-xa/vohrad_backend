"""Item service."""

from api.common import BaseService
from api.item.models import Item
from api.item.schema import ItemCreate, ItemUpdate
from api.item_location.models import ItemLocation
from database.constraint_handler import constraint_handler
from exceptions import ExceptionFactory
from security.jwt import AuthenticatedUser
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Any, NoReturn, Optional
from uuid import UUID
from web import PaginationUtil


class ItemService(BaseService[Item, ItemCreate, ItemUpdate]):
    """Item operations with use-case-specific loading."""

    def __init__(self):
        super().__init__(Item)


    def get_search_fields(self) -> list[str]:
        return ["name", "code", "description", "barcode", "serial_number"]


    async def get_items_for_list(self, db: AsyncSession, page: int, size: int) -> tuple[list[Item], int]:
        """List view: minimal loading (only item_locations for total_quantity)."""
        query  = select(Item).options(selectinload(Item.item_locations))
        total  = await self._count_with_filters(db)
        offset = PaginationUtil.get_offset(page, size)
        query  = query.offset(offset).limit(size)
        result = await db.execute(query)
        return result.scalars().all(), total


    async def get_item_for_detail(self, db: AsyncSession, item_id: UUID) -> Item:
        """Detail view: full graph (locations + junctions)."""
        query = (
            select(Item)
            .where(Item.id == item_id)
            .options(selectinload(Item.item_locations).selectinload(ItemLocation.location))
        )
        result = await db.execute(query)
        item   = result.scalar_one_or_none()
        if not item:
            raise ExceptionFactory.not_found("Item", item_id)
        return item


    async def reload_after_write(self, db: AsyncSession, obj_id: Any, tenant_id: Optional[UUID] = None) -> Item:
        """Reload item after write operations."""
        return await self.get_item_for_detail(db, obj_id)


    async def create_item(self, db: AsyncSession, item_data: ItemCreate, current_user: AuthenticatedUser) -> Item:
        """Create a new item."""
        try:
            item_dict = item_data.model_dump()
            item_dict["user_id"] = current_user.user_id
            item = Item(**item_dict)
            db.add(item)
            await db.commit()
            await db.refresh(item)
            return await self.reload_after_write(db, item.id)

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e,
                {
                    "operation"    : "create_item",
                    "code"         : item_data.code,
                    "serial_number": item_data.serial_number,
                },
            )


    async def update_item(self, db: AsyncSession, item_id: UUID, item_data: ItemUpdate) -> Item:
        """Update an item and return the fully loaded entity."""
        try:
            updated = await self.update(db, item_id, item_data)
            return await self.reload_after_write(db, updated.id)
        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e,
                {
                    "operation": "update_item",
                    "item_id"  : str(item_id),
                },
            )


    async def delete_item(self, db: AsyncSession, item_id: UUID) -> None:
        """Delete an item."""
        await self.delete(db, item_id)


    async def _get_detail_by_field(self, db: AsyncSession, field_name: str, value: Any) -> Optional[Item]:
        """Get item by field value."""
        field = getattr(Item, field_name)
        query = (
            select(Item)
            .where(field == value)
            .options(selectinload(Item.item_locations).selectinload(ItemLocation.location))
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


    async def get_item_by_id(self, db: AsyncSession, item_id: UUID) -> Item:
        """Get item by ID with full graph."""
        item = await self._get_detail_by_field(db, "id", item_id)
        if not item:
            raise ExceptionFactory.not_found("Item", item_id)
        return item


    async def get_item_by_code(self, db: AsyncSession, code: str) -> Optional[Item]:
        """Get item by code."""
        return await self._get_detail_by_field(db, "code", code)


    async def get_item_by_barcode(self, db: AsyncSession, barcode: str) -> Optional[Item]:
        """Get item by barcode."""
        return await self._get_detail_by_field(db, "barcode", barcode)


    async def get_item_by_serial(self, db: AsyncSession, serial_number: str) -> Optional[Item]:
        """Get item by serial."""
        return await self._get_detail_by_field(db, "serial_number", serial_number)


    async def search_items(self, db: AsyncSession, search_term: str, page: int = 1, size: int = 20) -> tuple[list[Item], int]:
        """Search list view with minimal loading (item_locations only)."""
        query = select(Item).options(selectinload(Item.item_locations))

        search_fields = self.get_search_fields()
        search_conditions = []
        if search_fields and search_term:
            for field_name in search_fields:
                if hasattr(Item, field_name):
                    field = getattr(Item, field_name)
                    search_conditions.append(field.ilike(f"%{search_term}%"))
            if search_conditions:
                query = query.where(or_(*search_conditions))

        total  = await self._count_with_filters(db, search_conditions=search_conditions)
        offset = PaginationUtil.get_offset(page, size)
        query  = query.offset(offset).limit(size)
        result = await db.execute(query)
        return result.scalars().all(), total


    async def get_items_with_filter(
        self,
        db: AsyncSession,
        filter_expression: str,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Item], int]:
        """OData filter list view with minimal loading (item_locations only)."""
        query = select(Item).options(selectinload(Item.item_locations))
        if filter_expression is not None:
            from utils.odata_parser import ODataToSQLAlchemy

            parser  = ODataToSQLAlchemy(Item, jsonb_fields={"specifications": "specifications"})
            filters = parser.parse(filter_expression)
            query   = query.where(filters)
        else:
            filters = None

        total  = await self._count_with_filters(db, filters=filters)
        offset = PaginationUtil.get_offset(page, size)
        query  = query.offset(offset).limit(size)
        result = await db.execute(query)
        return result.scalars().all(), total


    async def get_items_by_tracking_mode(
        self,
        db: AsyncSession,
        tracking_mode: str,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Item], int]:
        """Get items by tracking mode."""
        query  = select(Item).where(Item.tracking_mode == tracking_mode).options(selectinload(Item.item_locations))
        total  = await self._count_with_filters(db, filters=(Item.tracking_mode == tracking_mode))
        offset = PaginationUtil.get_offset(page, size)
        query  = query.offset(offset).limit(size)
        result = await db.execute(query)
        return result.scalars().all(), total


    async def get_active_items(self, db: AsyncSession, page: int = 1, size: int = 20) -> tuple[list[Item], int]:
        """Get active items."""
        query  = select(Item).where(Item.is_active == True).options(selectinload(Item.item_locations))  # noqa: E712
        total  = await self._count_with_filters(db, filters=(Item.is_active == True))  # noqa: E712
        offset = PaginationUtil.get_offset(page, size)
        query  = query.offset(offset).limit(size)
        result = await db.execute(query)
        return result.scalars().all(), total


    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict[str, Any]) -> NoReturn:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


item_service = ItemService()
