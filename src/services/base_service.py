"""Base service class with common CRUD operations."""

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Protocol, Type, TypeVar
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from exceptions import ExceptionFactory
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

    async def get_by_id(self, db: AsyncSession, obj_id: Any, tenant_id: Optional[UUID] = None) -> ModelType:
        """Get object by ID with optional tenant filtering."""
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
    ) -> tuple[List[ModelType], int]:
        """Get multiple objects with pagination and optional tenant filtering."""
        query = select(self.model)

        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)
        # Get total count
        count_query = select(self.model)
        if tenant_id and hasattr(self.model, "tenant_id"):
            count_query = count_query.where(self.model.tenant_id == tenant_id)
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())

        offset = PaginationUtil.get_offset(page, size)
        query = query.offset(offset).limit(size)
        result = await db.execute(query)
        objects = result.scalars().all()

        return objects, total

    @abstractmethod
    def get_search_fields(self) -> List[str]:
        """Return list of fields that should be searchable for this model."""
        pass

    async def search(
        self, db: AsyncSession, search_term: str, page: int = 1, size: int = 20, tenant_id: Optional[UUID] = None
    ) -> tuple[List[ModelType], int]:
        """Generic search method that all models can use."""
        query = select(self.model)

        # Add tenant filtering if applicable
        if tenant_id and hasattr(self.model, "tenant_id") and self.model.__tablename__ != "tenants":
            query = query.where(self.model.tenant_id == tenant_id)

        # Build OR conditions for all searchable fields
        search_fields = self.get_search_fields()
        if search_fields and search_term:
            search_conditions = []
            for field_name in search_fields:
                if hasattr(self.model, field_name):
                    field = getattr(self.model, field_name)
                    search_conditions.append(field.ilike(f"%{search_term}%"))

            if search_conditions:
                query = query.where(or_(*search_conditions))

        # Get total count
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

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
        """Update an existing object."""
        obj = await self.get_by_id(db, obj_id, tenant_id)

        update_data = obj_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(obj, field, value)

        await db.commit()
        await db.refresh(obj)
        return obj

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
    ) -> tuple[List[ModelType], int]:
        """Get filtered objects with pagination and optional tenant filtering."""
        query = select(self.model)

        if tenant_id and hasattr(self.model, "tenant_id"):
            query = query.where(self.model.tenant_id == tenant_id)

        if filters is not None:
            query = query.where(filters)

        # Get total count
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        offset = PaginationUtil.get_offset(page, size)
        query = query.offset(offset).limit(size)
        result = await db.execute(query)
        objects = result.scalars().all()

        return objects, total
