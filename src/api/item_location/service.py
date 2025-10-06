"""ItemLocation service."""

from api.common import BaseService
from api.item_location.models import ItemLocation
from api.item_location.schema import ItemLocationCreate, ItemLocationUpdate
from exceptions import ExceptionFactory
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID


class ItemLocationService(BaseService[ItemLocation, ItemLocationCreate, ItemLocationUpdate]):
    """ItemLocation operations."""

    def __init__(self):
        super().__init__(ItemLocation)

    def get_search_fields(self) -> list[str]:
        return []


    async def get_item_locations(
        self, db: AsyncSession, page: int = 1, size: int = 20
    ) -> tuple[list[ItemLocation], int]:
        """Get paginated list of item locations."""
        return await self.get_multi(db, page, size)


    async def get_by_item_and_location(
        self, db: AsyncSession, item_id: UUID, location_id: UUID
    ) -> Optional[ItemLocation]:
        """Get item location by item_id and location_id."""
        query = select(ItemLocation).where(
            ItemLocation.item_id == item_id,
            ItemLocation.location_id == location_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


    async def update_by_item_and_location(
        self, db: AsyncSession, item_id: UUID, location_id: UUID, item_location_data: ItemLocationUpdate
    ) -> ItemLocation:
        """Update item location by item_id and location_id."""
        item_location = await self.get_by_item_and_location(db, item_id, location_id)
        if not item_location:
            raise ExceptionFactory.not_found("ItemLocation", f"item_id={item_id}, location_id={location_id}")

        updated = await self.update(db, item_location.id, item_location_data)
        return await self.reload_after_write(db, updated.id)


    async def delete_by_item_and_location(
        self, db: AsyncSession, item_id: UUID, location_id: UUID
    ) -> None:
        """Delete item from a specific location."""
        item_location = await self.get_by_item_and_location(db, item_id, location_id)
        if not item_location:
            raise ExceptionFactory.not_found("ItemLocation", f"item_id={item_id}, location_id={location_id}")

        await self.delete(db, item_location.id)


item_location_service = ItemLocationService()
