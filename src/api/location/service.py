"""Location service."""

from api.common import BaseService
from api.item_location import ItemLocation
from api.location.models import Location
from api.location.schema import LocationCreate, LocationUpdate
from database.constraint_handler import constraint_handler
from exceptions import ExceptionFactory
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Any, NoReturn
from uuid import UUID
from web import PaginationUtil


class LocationService(BaseService[Location, LocationCreate, LocationUpdate]):
    """Location operations."""

    def __init__(self):
        super().__init__(Location)

    def get_search_fields(self) -> list[str]:
        return ["name", "code", "description", "path"]


    async def create_location(self, db: AsyncSession, location_data: LocationCreate) -> Location:
        """Create a new location."""
        try:
            return await self.create(db, location_data)
        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e,
                {
                    "operation": "create_location",
                    "code"     : location_data.code,
                },
            )


    async def update_location(self, db: AsyncSession, location_id: UUID, location_data: LocationUpdate) -> Location:
        """Update a location."""
        try:
            return await self.update(db, location_id, location_data)
        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e,
                {
                    "operation"  : "update_location",
                    "location_id": str(location_id),
                },
            )


    async def delete_location(self, db: AsyncSession, location_id: UUID) -> None:
        """Delete a location only if it has no items and no children."""
        # Check if location exists
        location = await self.get_by_id(db, location_id)
        if not location:
            raise ExceptionFactory.not_found("Location", location_id)

        # Check if location has items
        item_count_query  = select(func.count(ItemLocation.id)).where(ItemLocation.location_id == location_id)
        item_count_result = await db.execute(item_count_query)
        item_count        = item_count_result.scalar()

        if item_count > 0:
            raise ExceptionFactory.validation_failed(
                "Cannot delete location with items",
                {"location_id": str(location_id), "item_count": item_count}
            )

        # Check if location has children
        children_count_query  = select(func.count(Location.id)).where(Location.parent_id == location_id)
        children_count_result = await db.execute(children_count_query)
        children_count        = children_count_result.scalar()

        if children_count > 0:
            raise ExceptionFactory.validation_failed(
                "Cannot delete location with child locations",
                {"location_id": str(location_id), "children_count": children_count}
            )

        # Safe to delete
        await self.delete(db, location_id)


    async def get_locations(
        self, db: AsyncSession, page: int = 1, size: int = 20
    ) -> tuple[list[Location], int]:
        """Get paginated list of locations."""
        return await self.get_multi(db, page, size)


    async def get_location_by_id(self, db: AsyncSession, location_id: UUID) -> Location:
        """Get location by ID with all items (via item_locations relationship)."""
        query = (
            select(Location)
            .where(Location.id == location_id)
            .options(
                selectinload(Location.item_locations).selectinload(ItemLocation.item)
            )
        )
        result = await db.execute(query)
        location = result.scalar_one_or_none()

        if not location:
            raise ExceptionFactory.not_found("Location", location_id)

        return location


    async def get_locations_with_filter(
        self,
        db: AsyncSession,
        filter_expression: str,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Location], int]:
        """OData filter list view."""
        query = select(Location)
        if filter_expression is not None:
            from utils.odata_parser import ODataToSQLAlchemy

            parser  = ODataToSQLAlchemy(Location)
            filters = parser.parse(filter_expression)
            query   = query.where(filters)
        else:
            filters = None

        total  = await self._count_with_filters(db, filters=filters)
        offset = PaginationUtil.get_offset(page, size)
        query  = query.offset(offset).limit(size)
        result = await db.execute(query)
        return result.scalars().all(), total


    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict[str, Any]) -> NoReturn:
        """Map database constraints to domain exceptions."""
        exception = constraint_handler.handle_violation(error, operation_context)
        raise exception


location_service = LocationService()
