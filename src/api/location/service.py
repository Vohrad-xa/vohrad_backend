"""Location service."""

from api.common import BaseService
from api.location.models import Location
from api.location.schema import LocationCreate, LocationUpdate
from sqlalchemy.ext.asyncio import AsyncSession


class LocationService(BaseService[Location, LocationCreate, LocationUpdate]):
    """Location operations."""

    def __init__(self):
        super().__init__(Location)

    def get_search_fields(self) -> list[str]:
        return ["name", "code", "description", "path"]

    async def get_locations_paginated(
        self, db: AsyncSession, page: int = 1, size: int = 20
    ) -> tuple[list[Location], int]:
        """Get paginated list of locations."""
        return await self.get_multi(db, page, size)

    async def create_location(self, db: AsyncSession, location_data: LocationCreate) -> Location:
        """Create a new location."""
        return await self.create(db, location_data)


location_service = LocationService()
