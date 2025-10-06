"""ItemLocation service."""

from api.common import BaseService
from api.item_location.models import ItemLocation
from api.item_location.schema import ItemLocationCreate, ItemLocationUpdate
from sqlalchemy.ext.asyncio import AsyncSession


class ItemLocationService(BaseService[ItemLocation, ItemLocationCreate, ItemLocationUpdate]):
    """ItemLocation operations."""

    def __init__(self):
        super().__init__(ItemLocation)

    def get_search_fields(self) -> list[str]:
        return []


    async def get_item_locations_paginated(
        self, db: AsyncSession, page: int = 1, size: int = 20
    ) -> tuple[list[ItemLocation], int]:
        """Get paginated list of item locations."""
        return await self.get_multi(db, page, size)


item_location_service = ItemLocationService()
