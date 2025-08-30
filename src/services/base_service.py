"""Base service class with common CRUD operations."""

import re
from abc import ABC
from abc import abstractmethod
from exceptions import ExceptionFactory
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from typing import Generic
from typing import NoReturn
from typing import Optional
from typing import Protocol
from typing import Type
from typing import TypeVar
from uuid import UUID
from web import PaginationUtil


class DatabaseModel(Protocol):
    """Protocol for database models with common attributes."""

    __tablename__: str
    id: Any
    tenant_id: Optional[Any]


ModelType = TypeVar("ModelType", bound=DatabaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """Base service class with common CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def _count_with_filters(
        self, db: AsyncSession, tenant_id: Optional[UUID] = None, filters=None, search_conditions: Optional[list] = None
    ) -> int:
        """Count query with optional filters - DRY helper method."""
        count_query = select(func.count()).select_from(self.model)

        if tenant_id and hasattr(self.model, "tenant_id") and self.model.__tablename__ != "tenants":
            count_query = count_query.where(self.model.tenant_id == tenant_id)

        if filters is not None:
            count_query = count_query.where(filters)

        if search_conditions:
            count_query = count_query.where(or_(*search_conditions))

        result = await db.execute(count_query)
        return result.scalar()

    async def get_by_id(self, db: AsyncSession, obj_id: Any, tenant_id: Optional[UUID] = None) -> ModelType:
        """Get an object by ID with optional tenant filtering."""
        if hasattr(self.model, "tenant_id") and self.model.__tablename__ == "tenants":
            query = select(self.model).where(self.model.tenant_id == obj_id)
        else:
            query = select(self.model).where(self.model.id == obj_id)

        if tenant_id and hasattr(self.model, "tenant_id") and self.model.__tablename__ != "tenants":
            query = query.where(self.model.tenant_id == tenant_id)

        result = await db.execute(query)
        obj = result.scalar_one_or_none()
        if not obj:
            raise ExceptionFactory.not_found(self.model.__name__, obj_id)
        return obj

    async def get_multi(
        self, db: AsyncSession, page: int = 1, size: int = 20, tenant_id: Optional[UUID] = None
    ) -> tuple[list[ModelType], int]:
        """Get multiple objects with pagination and optional tenant filtering."""
        query = select(self.model)

        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        # Get total count using helper method
        total = await self._count_with_filters(db, tenant_id)

        offset = PaginationUtil.get_offset(page, size)
        query = query.offset(offset).limit(size)
        result = await db.execute(query)
        objects = result.scalars().all()

        return objects, total

    @abstractmethod
    def get_search_fields(self) -> list[str]:
        """Return the list of fields that should be searchable for this model."""
        pass

    async def search(
        self, db: AsyncSession, search_term: str, page: int = 1, size: int = 20, tenant_id: Optional[UUID] = None
    ) -> tuple[list[ModelType], int]:
        """Generic search method that all models can use."""
        query = select(self.model)

        # Add tenant filtering if applicable
        if tenant_id and hasattr(self.model, "tenant_id") and self.model.__tablename__ != "tenants":
            query = query.where(self.model.tenant_id == tenant_id)

        # Build OR conditions for all searchable fields
        search_fields = self.get_search_fields()
        search_conditions = []

        if search_fields and search_term:
            for field_name in search_fields:
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    search_conditions.append(field.ilike(f"%{search_term}%"))

            if search_conditions:
                query = query.where(or_(*search_conditions))

        # Get total count using helper method with search conditions
        total = await self._count_with_filters(db, tenant_id, search_conditions=search_conditions)

        offset = PaginationUtil.get_offset(page, size)
        query = query.offset(offset).limit(size)
        result = await db.execute(query)
        objects = result.scalars().all()

        return objects, total

    async def create(self, db: AsyncSession, obj_data: CreateSchemaType, tenant_id: Optional[UUID] = None) -> ModelType:
        """Create a new object."""
        obj_dict = obj_data.model_dump()

        if tenant_id and hasattr(self.model, "tenant_id"):
            obj_dict["tenant_id"] = tenant_id

        obj = self.model(**obj_dict)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)

        return obj

    async def update(
        self, db: AsyncSession, obj_id: Any, obj_data: UpdateSchemaType, tenant_id: Optional[UUID] = None
    ) -> ModelType:
        """Update an existing object - enterprise pattern with constraint protection."""
        obj = await self.get_by_id(db, obj_id, tenant_id)

        try:
            update_data = obj_data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(obj, field, value)

            await db.commit()
            await db.refresh(obj)

            return obj

        except IntegrityError as e:
            await db.rollback()
            await self._handle_integrity_error(
                e,
                {
                    "operation": "update",
                    "model": self.model.__name__,
                    "obj_id": obj_id,
                    "tenant_id": tenant_id,
                    **update_data,  # Include the actual field data for constraint violation handling
                },
            )

    async def delete(self, db: AsyncSession, obj_id: Any, tenant_id: Optional[UUID] = None) -> None:
        """Delete an object."""
        obj = await self.get_by_id(db, obj_id, tenant_id)

        await db.delete(obj)
        await db.commit()

    async def get_by_field(
        self, db: AsyncSession, field_name: str, field_value: Any, tenant_id: Optional[UUID] = None
    ) -> Optional[ModelType]:
        """Get object by a specific field value."""
        if not hasattr(self.model, field_name):
            raise ValueError(f"Model {self.model.__name__} does not have field {field_name}")

        query = select(self.model).where(getattr(self.model, field_name) == field_value)

        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)

        result = await db.execute(query)

        return result.scalar_one_or_none()

    async def exists(
        self,
        db: AsyncSession,
        field_name: str,
        field_value: Any,
        tenant_id: Optional[UUID] = None,
        exclude_id: Optional[Any] = None,
    ) -> bool:
        """Check if an object exists with the given field value."""
        if not hasattr(self.model, field_name):
            return False

        query = select(self.model).where(getattr(self.model, field_name) == field_value)

        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)

        if exclude_id is not None:
            # Handle different primary key field names
            if hasattr(self.model, "tenant_id") and self.model.__tablename__ == "tenants":
                query = query.where(self.model.tenant_id != exclude_id)
            else:
                query = query.where(self.model.id != exclude_id)

        result = await db.execute(query)

        return result.scalar_one_or_none() is not None

    async def get_filtered(
        self,
        db: AsyncSession,
        filters,
        page: int = 1,
        size: int = 20,
        tenant_id: Optional[UUID] = None,
    ) -> tuple[list[ModelType], int]:
        """Get filtered objects with pagination and optional tenant filtering."""
        query = select(self.model)

        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)

        if filters is not None:
            query = query.where(filters)

        # Get total count using helper method
        total = await self._count_with_filters(db, tenant_id, filters=filters)

        offset = PaginationUtil.get_offset(page, size)
        query = query.offset(offset).limit(size)
        result = await db.execute(query)
        objects = result.scalars().all()

        return objects, total

    @staticmethod
    def _extract_constraint_name(error: IntegrityError) -> Optional[str]:
        """Extract PostgreSQL constraint name from IntegrityError for professional error handling."""
        error_str = str(error.orig) if error.orig else str(error)

        # Match PostgreSQL constraint violation patterns
        patterns = [
            r"Key \([^)]+\)=\([^)]+\) already exists",
            r'duplicate key value violates unique constraint "([^"]+)"',
            r'violates unique constraint "([^"]+)"',
            r'constraint "([^"]+)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, error_str)
            if match and len(match.groups()) > 0:
                return match.group(1)

        # Fallback: extract any quoted constraint name
        match = re.search(r'"([^"]*(?:unique|idx)[^"]*)"', error_str, re.IGNORECASE)
        return match.group(1) if match else None

    async def _handle_integrity_error(self, error: IntegrityError, operation_context: dict[str, Any]) -> NoReturn:
        """Handle IntegrityError with constraint-specific exceptions - enterprise pattern."""
        # Extract constraint name for subclass use
        # Override in subclasses for model-specific constraint handling
        raise error  # Default: re-raise if not handled
